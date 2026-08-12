import inspect
from pathlib import Path

import pytest

from neoecmo import (
    BridgeParameters,
    cdi_mixed_paco2_mmhg,
    cdi_mixed_saturation,
    cdi_reading_from_circuit_point,
    recirculation_fraction,
    solve_main_circuit_full_operating_point,
)

ROOT = Path(__file__).resolve().parents[1]


# --- the key topology finding: bridge closed -> CDI reads TRUE venous ----


def test_bridge_closed_cdi_reads_pure_native_venous_saturation():
    native_sv02 = 0.65
    reading = cdi_mixed_saturation(
        patient_flow_ml_min=360.0,
        bridge_flow_ml_min=0.0,
        native_venous_saturation=native_sv02,
        post_oxygenator_saturation=0.99,
    )
    assert reading == native_sv02


def test_bridge_open_cdi_reads_elevated_blend_above_native():
    native_svo2 = 0.65
    reading = cdi_mixed_saturation(
        patient_flow_ml_min=300.0,
        bridge_flow_ml_min=100.0,
        native_venous_saturation=native_svo2,
        post_oxygenator_saturation=0.99,
    )
    assert reading > native_svo2


def test_recirculation_fraction_zero_when_bridge_closed():
    assert recirculation_fraction(patient_flow_ml_min=360.0, bridge_flow_ml_min=0.0) == 0.0


def test_recirculation_fraction_increases_with_bridge_flow():
    fractions = [
        recirculation_fraction(patient_flow_ml_min=360.0, bridge_flow_ml_min=b)
        for b in (0.0, 50.0, 150.0, 400.0)
    ]
    assert fractions == sorted(fractions)
    assert fractions[0] == 0.0
    assert fractions[-1] > 0.0


# --- shunt flow structurally never enters this calculation ----------------


def test_shunt_flow_is_not_a_parameter_of_cdi_mixed_saturation():
    sig = inspect.signature(cdi_mixed_saturation)
    for param_name in sig.parameters:
        assert "shunt" not in param_name.lower()


def test_shunt_flow_is_not_a_parameter_of_cdi_reading_from_circuit_point():
    sig = inspect.signature(cdi_reading_from_circuit_point)
    for param_name in sig.parameters:
        assert "shunt" not in param_name.lower()


def test_cdi_sensor_module_never_reads_solved_shunt_flow_attribute():
    text = (ROOT / "src" / "neoecmo" / "cdi_sensor.py").read_text(encoding="utf-8")
    assert "point.solved_shunt_flow_ml_min" not in text


# --- degenerate zero-flow case ----------------------------------------------


def test_zero_total_flow_falls_back_to_native_venous_saturation():
    reading = cdi_mixed_saturation(
        patient_flow_ml_min=0.0,
        bridge_flow_ml_min=0.0,
        native_venous_saturation=0.65,
        post_oxygenator_saturation=0.99,
    )
    assert reading == 0.65


# --- pCO2 mixing mirrors the same logic -------------------------------------


def test_bridge_closed_cdi_reads_pure_native_paco2():
    reading = cdi_mixed_paco2_mmhg(
        patient_flow_ml_min=360.0,
        bridge_flow_ml_min=0.0,
        native_venous_paco2_mmhg=55.0,
        post_oxygenator_paco2_mmhg=35.0,
    )
    assert reading == 55.0


def test_bridge_open_cdi_paco2_shifts_toward_post_oxygenator_value():
    reading = cdi_mixed_paco2_mmhg(
        patient_flow_ml_min=300.0,
        bridge_flow_ml_min=100.0,
        native_venous_paco2_mmhg=55.0,
        post_oxygenator_paco2_mmhg=35.0,
    )
    assert reading < 55.0


# --- convenience wrapper against an actual solved circuit ------------------


def test_cdi_reading_from_circuit_point_matches_manual_calculation():
    point = solve_main_circuit_full_operating_point(
        3000.0, bridge_params=BridgeParameters(clamp_position=0.05)
    )
    reading = cdi_reading_from_circuit_point(
        point, native_venous_saturation=0.65, post_oxygenator_saturation=0.99
    )
    expected = cdi_mixed_saturation(
        point.solved_patient_flow_ml_min,
        point.solved_bridge_flow_ml_min,
        0.65,
        0.99,
    )
    assert reading.mixed_saturation == pytest.approx(expected)
    assert reading.recirculation_fraction == pytest.approx(
        recirculation_fraction(point.solved_patient_flow_ml_min, point.solved_bridge_flow_ml_min)
    )


def test_cdi_reading_from_circuit_point_bridge_closed_reads_native():
    point = solve_main_circuit_full_operating_point(3000.0)  # bridge closed by default
    reading = cdi_reading_from_circuit_point(
        point, native_venous_saturation=0.65, post_oxygenator_saturation=0.99
    )
    assert reading.mixed_saturation == 0.65
    assert reading.recirculation_fraction == 0.0


def test_cdi_reading_from_circuit_point_optional_paco2():
    point = solve_main_circuit_full_operating_point(3000.0)
    reading_without_paco2 = cdi_reading_from_circuit_point(
        point, native_venous_saturation=0.65, post_oxygenator_saturation=0.99
    )
    assert reading_without_paco2.mixed_paco2_mmhg is None

    reading_with_paco2 = cdi_reading_from_circuit_point(
        point,
        native_venous_saturation=0.65,
        post_oxygenator_saturation=0.99,
        native_venous_paco2_mmhg=55.0,
        post_oxygenator_paco2_mmhg=35.0,
    )
    assert reading_with_paco2.mixed_paco2_mmhg == pytest.approx(55.0)


# --- module boundary ---------------------------------------------------------


def test_cdi_sensor_does_not_import_patient_physiology_modules():
    forbidden = ("neocirculation", "neolung", "neokidney", "neocoupling", "neopatient")
    text = (ROOT / "src" / "neoecmo" / "cdi_sensor.py").read_text(encoding="utf-8")
    for name in forbidden:
        assert f"import {name}" not in text
        assert f"from {name}" not in text
