from pathlib import Path

import pytest

from neoecmo import (
    OxygenatorHydraulicParameters,
    solve_main_circuit_series_operating_point,
)
from neoecmo.pump_bench import solve_pump_operating_point

ROOT = Path(__file__).resolve().parents[1]


# --- basic consistency: internal node pressures reconcile with the -------
# --- component functions they came from ------------------------------------


def test_solved_point_pressures_are_internally_consistent():
    point = solve_main_circuit_series_operating_point(3000.0, 0.0, 0.0)
    assert point.p2_mmhg - point.p1_mmhg == pytest.approx(point.pump_head_mmhg)
    assert point.p2_mmhg - point.p3_mmhg == pytest.approx(point.oxygenator_delta_p_mmhg)


def test_solved_flow_is_nonnegative_by_construction():
    point = solve_main_circuit_series_operating_point(3000.0, 0.0, 0.0)
    assert point.solved_flow_ml_min >= 0.0


# --- adding the oxygenator in series must reduce flow versus pump-only ----


def test_oxygenator_in_series_reduces_flow_versus_pump_alone():
    rpm = 3000.0
    inlet = 0.0
    outlet = 0.0
    r_pre = 0.001697
    r_ret = 0.001697

    pump_only = solve_pump_operating_point(rpm, inlet, outlet, r_pre, r_ret)
    with_oxygenator = solve_main_circuit_series_operating_point(
        rpm,
        inlet,
        outlet,
        resistance_pre_pump_mmhg_per_ml_min=r_pre,
        resistance_return_mmhg_per_ml_min=r_ret,
    )
    assert with_oxygenator.solved_flow_ml_min < pump_only.solved_flow_ml_min


# --- oxygenator obstruction/clot reduces series flow at fixed RPM ----------


def test_oxygenator_obstruction_reduces_series_flow_at_fixed_rpm():
    clean = OxygenatorHydraulicParameters(obstruction_fraction=0.0)
    clotted = OxygenatorHydraulicParameters(obstruction_fraction=0.7)

    clean_point = solve_main_circuit_series_operating_point(
        3000.0, 0.0, 0.0, oxygenator_params=clean
    )
    clotted_point = solve_main_circuit_series_operating_point(
        3000.0, 0.0, 0.0, oxygenator_params=clotted
    )
    assert clotted_point.solved_flow_ml_min < clean_point.solved_flow_ml_min


# --- increasing RPM increases series flow ----------------------------------


def test_increasing_rpm_increases_series_flow():
    flows = [
        solve_main_circuit_series_operating_point(rpm, 0.0, 0.0).solved_flow_ml_min
        for rpm in (1500.0, 2500.0, 3500.0)
    ]
    assert flows == sorted(flows)
    assert flows[0] < flows[-1]


# --- zero RPM still yields a defined degenerate operating point -----------


def test_zero_rpm_yields_zero_flow_with_matched_reservoirs():
    point = solve_main_circuit_series_operating_point(0.0, 0.0, 0.0)
    assert point.solved_flow_ml_min == pytest.approx(0.0, abs=1e-6)
    assert point.pump_head_mmhg == 0.0


# --- default resistances are grounded in measured tubing geometry ---------


def test_default_resistances_match_measured_tubing_segments():
    from neoecmo import resistance_for_segment

    point = solve_main_circuit_series_operating_point(3000.0, 0.0, 0.0)
    assert point.resistance_pre_pump_mmhg_per_ml_min == pytest.approx(
        resistance_for_segment("main_pre_pump")
    )
    assert point.resistance_return_mmhg_per_ml_min == pytest.approx(
        resistance_for_segment("main_return")
    )


# --- module boundary ---------------------------------------------------------


def test_main_circuit_series_does_not_import_patient_physiology_modules():
    forbidden = ("neocirculation", "neolung", "neokidney", "neocoupling", "neopatient")
    text = (ROOT / "src" / "neoecmo" / "main_circuit_series.py").read_text(encoding="utf-8")
    for name in forbidden:
        assert f"import {name}" not in text
        assert f"from {name}" not in text
