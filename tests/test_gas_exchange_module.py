from pathlib import Path

import pytest

from neoecmo import (
    MAX_FDO2,
    MIN_FDO2,
    OxygenatorGasExchangeParameters,
    co2_clearance_efficiency,
    outlet_o2_saturation,
    outlet_paco2_mmhg,
    oxygenator_transfer_efficiency,
    round_fdo2_to_blender_step,
    run_gas_exchange_bench,
)

ROOT = Path(__file__).resolve().parents[1]


# --- transfer efficiency: full at/below rated flow, tapers beyond it -----


def test_efficiency_is_full_at_or_below_rated_flow():
    assert oxygenator_transfer_efficiency(500.0, rated_flow_ml_min=1500.0) == 1.0
    assert oxygenator_transfer_efficiency(1500.0, rated_flow_ml_min=1500.0) == 1.0


def test_efficiency_falls_off_beyond_rated_flow():
    at_rated = oxygenator_transfer_efficiency(1500.0, rated_flow_ml_min=1500.0)
    beyond_rated = oxygenator_transfer_efficiency(3000.0, rated_flow_ml_min=1500.0)
    assert beyond_rated < at_rated
    assert beyond_rated == pytest.approx(0.5)


def test_obstruction_reduces_effective_rated_flow():
    clean = oxygenator_transfer_efficiency(1200.0, rated_flow_ml_min=1500.0, obstruction_fraction=0.0)
    clotted = oxygenator_transfer_efficiency(1200.0, rated_flow_ml_min=1500.0, obstruction_fraction=0.5)
    assert clotted < clean


# --- O2 saturation: rises toward the fdo2-limited ceiling ------------------


def test_outlet_saturation_rises_toward_ceiling_at_low_flow():
    out_sat = outlet_o2_saturation(0.65, blood_flow_ml_min=200.0, fdo2=1.0)
    assert out_sat > 0.95  # well below rated flow -> near-full transfer


def test_outlet_saturation_lower_at_flow_far_beyond_rated():
    low_flow = outlet_o2_saturation(0.65, blood_flow_ml_min=200.0, fdo2=1.0)
    high_flow = outlet_o2_saturation(0.65, blood_flow_ml_min=6000.0, fdo2=1.0)
    assert high_flow < low_flow


def test_lower_fdo2_caps_achievable_saturation():
    full_fdo2 = outlet_o2_saturation(0.65, blood_flow_ml_min=200.0, fdo2=1.0)
    half_fdo2 = outlet_o2_saturation(0.65, blood_flow_ml_min=200.0, fdo2=0.5)
    assert half_fdo2 < full_fdo2


def test_oxygenator_never_actively_desaturates_blood():
    # If the FdO2-derived PO2 target is below the inlet PO2, the oxygenator
    # leaves the inlet O2 state unchanged rather than actively deoxygenating it.
    out_sat = outlet_o2_saturation(0.999, blood_flow_ml_min=200.0, fdo2=0.21)
    assert out_sat == pytest.approx(0.999)


def test_clotted_membrane_reduces_outlet_saturation_at_high_flow():
    clean = OxygenatorGasExchangeParameters(obstruction_fraction=0.0)
    clotted = OxygenatorGasExchangeParameters(obstruction_fraction=0.6)
    clean_sat = outlet_o2_saturation(0.65, blood_flow_ml_min=1400.0, fdo2=1.0, params=clean)
    clotted_sat = outlet_o2_saturation(0.65, blood_flow_ml_min=1400.0, fdo2=1.0, params=clotted)
    assert clotted_sat < clean_sat


# --- CO2 clearance: governed by sweep:blood ratio --------------------------


def test_co2_clearance_full_once_sweep_matches_blood_flow():
    assert co2_clearance_efficiency(sweep_gas_flow_ml_min=500.0, blood_flow_ml_min=500.0) == 1.0
    assert co2_clearance_efficiency(sweep_gas_flow_ml_min=1000.0, blood_flow_ml_min=500.0) == 1.0


def test_co2_clearance_reduced_when_sweep_insufficient():
    efficiency = co2_clearance_efficiency(sweep_gas_flow_ml_min=100.0, blood_flow_ml_min=500.0)
    assert 0.0 < efficiency < 1.0
    assert efficiency == pytest.approx(0.2)


def test_outlet_paco2_drops_toward_floor_with_adequate_sweep():
    outlet = outlet_paco2_mmhg(
        inlet_paco2_mmhg=55.0, blood_flow_ml_min=500.0, sweep_gas_flow_ml_min=500.0
    )
    assert outlet == pytest.approx(20.0, rel=1e-6)


def test_outlet_paco2_stays_high_with_insufficient_sweep():
    outlet = outlet_paco2_mmhg(
        inlet_paco2_mmhg=55.0, blood_flow_ml_min=500.0, sweep_gas_flow_ml_min=50.0
    )
    assert outlet > 45.0


# --- bench sanity -----------------------------------------------------------


def test_bench_sweep_returns_one_point_per_flow_step():
    steps = (200, 500, 1000)
    points = run_gas_exchange_bench(flow_steps_ml_min=steps)
    assert [p.blood_flow_ml_min for p in points] == [float(s) for s in steps]


# --- Spectrum O2 blender: real 21-100% range, 1% increments ---------------


def test_blender_clamps_below_room_air_floor():
    assert round_fdo2_to_blender_step(0.05) == MIN_FDO2


def test_blender_clamps_above_pure_o2_ceiling():
    assert round_fdo2_to_blender_step(1.5) == MAX_FDO2


def test_blender_rounds_to_nearest_one_percent():
    assert round_fdo2_to_blender_step(0.654) == pytest.approx(0.65)
    assert round_fdo2_to_blender_step(0.656) == pytest.approx(0.66)


def test_outlet_saturation_floors_fdo2_at_room_air():
    # A value below the blender's physical floor should behave the same
    # as the floor itself (0.21), not as if lower FdO2 were achievable.
    at_floor = outlet_o2_saturation(0.65, blood_flow_ml_min=200.0, fdo2=0.21)
    below_floor = outlet_o2_saturation(0.65, blood_flow_ml_min=200.0, fdo2=0.05)
    assert at_floor == pytest.approx(below_floor)


# --- module boundary ---------------------------------------------------------


def test_gas_exchange_modules_do_not_import_patient_physiology_modules():
    forbidden = ("neocirculation", "neolung", "neokidney", "neocoupling", "neopatient")
    for filename in ("oxygenator_gas_exchange.py", "gas_exchange_bench.py"):
        text = (ROOT / "src" / "neoecmo" / filename).read_text(encoding="utf-8")
        for name in forbidden:
            assert f"import {name}" not in text
            assert f"from {name}" not in text
