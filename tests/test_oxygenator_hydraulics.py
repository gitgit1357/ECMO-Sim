from pathlib import Path

import pytest

from neoecmo import (
    OxygenatorHydraulicParameters,
    OxygenatorLowFlowExposureState,
    oxygenator_delta_p_mmhg,
    run_oxygenator_hydraulic_bench,
    step_low_flow_exposure,
)

ROOT = Path(__file__).resolve().parents[1]


# --- baseline ΔP: zero flow gives zero pressure drop -----------------------


def test_zero_flow_gives_zero_delta_p():
    assert oxygenator_delta_p_mmhg(0.0) == 0.0


# --- flow dependence: ΔP rises with flow -----------------------------------


def test_delta_p_increases_with_flow():
    deltas = [oxygenator_delta_p_mmhg(flow) for flow in (0, 200, 400, 600, 800)]
    assert deltas == sorted(deltas)
    assert deltas[0] < deltas[-1]


# --- rising resistance / clot burden raises ΔP at fixed flow ---------------


def test_obstruction_raises_delta_p_at_fixed_flow():
    clean = OxygenatorHydraulicParameters(obstruction_fraction=0.0)
    mild = OxygenatorHydraulicParameters(obstruction_fraction=0.3)
    severe = OxygenatorHydraulicParameters(obstruction_fraction=0.8)
    d_clean = oxygenator_delta_p_mmhg(400.0, clean)
    d_mild = oxygenator_delta_p_mmhg(400.0, mild)
    d_severe = oxygenator_delta_p_mmhg(400.0, severe)
    assert d_clean < d_mild < d_severe


# --- partial vs severe obstruction: monotonic across a continuum ----------


def test_obstruction_delta_p_is_monotonic_across_continuum():
    fractions = [0.0, 0.1, 0.2, 0.4, 0.6, 0.8, 0.95]
    deltas = [
        oxygenator_delta_p_mmhg(400.0, OxygenatorHydraulicParameters(obstruction_fraction=f))
        for f in fractions
    ]
    assert deltas == sorted(deltas)


def test_obstruction_fraction_is_clipped_near_full_occlusion_not_infinite():
    # obstruction_fraction >= 1 must not divide by zero / return inf or NaN
    near_total = oxygenator_delta_p_mmhg(
        400.0, OxygenatorHydraulicParameters(obstruction_fraction=1.5)
    )
    assert near_total == pytest.approx(
        oxygenator_delta_p_mmhg(400.0, OxygenatorHydraulicParameters(obstruction_fraction=0.99))
    )


# --- low-flow exposure tracking --------------------------------------------


def test_low_flow_exposure_accumulates_below_minimum_flow():
    params = OxygenatorHydraulicParameters(min_recommended_flow_ml_min=200.0)
    state = OxygenatorLowFlowExposureState()
    state = step_low_flow_exposure(state, flow_ml_min=100.0, dt_s=10.0, params=params)
    assert state.cumulative_low_flow_exposure_s == pytest.approx(10.0)
    state = step_low_flow_exposure(state, flow_ml_min=50.0, dt_s=5.0, params=params)
    assert state.cumulative_low_flow_exposure_s == pytest.approx(15.0)


def test_low_flow_exposure_does_not_accumulate_at_or_above_minimum_flow():
    params = OxygenatorHydraulicParameters(min_recommended_flow_ml_min=200.0)
    state = OxygenatorLowFlowExposureState()
    state = step_low_flow_exposure(state, flow_ml_min=200.0, dt_s=30.0, params=params)
    assert state.cumulative_low_flow_exposure_s == 0.0
    state = step_low_flow_exposure(state, flow_ml_min=500.0, dt_s=30.0, params=params)
    assert state.cumulative_low_flow_exposure_s == 0.0


def test_low_flow_exposure_does_not_reset_when_flow_recovers():
    params = OxygenatorHydraulicParameters(min_recommended_flow_ml_min=200.0)
    state = OxygenatorLowFlowExposureState()
    state = step_low_flow_exposure(state, flow_ml_min=50.0, dt_s=20.0, params=params)
    assert state.cumulative_low_flow_exposure_s == pytest.approx(20.0)
    # Flow recovers above minimum — exposure clock must not erase established exposure.
    state = step_low_flow_exposure(state, flow_ml_min=600.0, dt_s=120.0, params=params)
    assert state.cumulative_low_flow_exposure_s == pytest.approx(20.0)


def test_low_flow_exposure_rejects_negative_dt():
    params = OxygenatorHydraulicParameters()
    state = OxygenatorLowFlowExposureState()
    with pytest.raises(ValueError):
        step_low_flow_exposure(state, flow_ml_min=50.0, dt_s=-1.0, params=params)


# --- Sanity check on the bench sweep helper itself -------------------------


def test_bench_sweep_returns_one_point_per_flow_step():
    steps = (0, 200, 400, 600)
    points = run_oxygenator_hydraulic_bench(flow_steps_ml_min=steps)
    assert [p.flow_ml_min for p in points] == [float(s) for s in steps]
    assert points[0].delta_p_mmhg == 0.0


# --- Module boundary: this stage must not add gas exchange or coupling ----
# --- logic, and neoecmo must still not import patient physiology modules --


def test_oxygenator_module_does_not_import_patient_physiology_modules():
    forbidden = ("neocirculation", "neolung", "neokidney", "neocoupling", "neopatient")
    for filename in ("oxygenator.py", "oxygenator_bench.py"):
        text = (ROOT / "src" / "neoecmo" / filename).read_text(encoding="utf-8")
        for name in forbidden:
            assert f"import {name}" not in text
            assert f"from {name}" not in text

