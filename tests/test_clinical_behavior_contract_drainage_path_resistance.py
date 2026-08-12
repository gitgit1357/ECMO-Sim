import json
from pathlib import Path

import pytest

from neoecmo import EcmoConsoleControls, run_ecmo_console
from neoecmo.cannula import CannulaHydraulicParameters, DRAIN_10FR

CONTRACT_PATH = Path(__file__).parents[1] / "clinical_behavior_contracts" / "drainage_path_resistance_v1.json"


def _contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _solve(rpm: float, resistance_multiplier: float):
    c = _contract()
    p = c["preconditions"]
    drain = CannulaHydraulicParameters(
        quadratic_resistance_mmhg_per_ml_min2=(
            DRAIN_10FR.quadratic_resistance_mmhg_per_ml_min2 * resistance_multiplier
        )
    )
    state = run_ecmo_console(
        EcmoConsoleControls(
            rpm=float(rpm),
            bridge_clamp_position=float(p["bridge_clamp_position"]),
            sweep_gas_flow_ml_min=float(p["sweep_gas_flow_ml_min"]),
        ),
        native_venous_saturation=float(p["native_venous_saturation"]),
        native_venous_paco2_mmhg=float(p["native_venous_paco2_mmhg"]),
        drain_cannula_params=drain,
        patient_arterial_pressure_mmhg=float(p["patient_arterial_pressure_mmhg"]),
        patient_venous_pressure_mmhg=float(p["patient_venous_pressure_mmhg"]),
    )
    return state.circuit


def test_contract_definition_preserves_split_and_model_boundaries():
    c = _contract()
    assert c["contract_id"] == "cbc.ecmo.drainage-path-resistance.v1"
    assert c["legacy_scenario_id"] == "lf-04-kink"
    assert c["legacy_complication_id"] == "drainage-cannula-kink"
    assert c["scope_decision"]["cbc05b"].startswith("common pre-pump mechanical obstruction; blocked")
    assert c["scope_decision"]["cbc05c"].startswith("position-sensitive maldrainage; blocked")
    assert c["p1_requirement"].startswith("no directional assertion")
    assert "persistent kink severity state" in c["not_modeled"]
    assert c["future_retest_conditions"]


def test_drainage_path_resistance_reduces_patient_and_total_flow_and_increases_recirc_fraction():
    c = _contract()
    p = c["preconditions"]
    multiplier = float(c["stimulus"]["drain_cannula_resistance_multiplier"])
    baseline = _solve(float(p["rpm"]), 1.0)
    obstructed = _solve(float(p["rpm"]), multiplier)

    assert obstructed.solved_patient_flow_ml_min < baseline.solved_patient_flow_ml_min
    assert obstructed.solved_total_flow_ml_min < baseline.solved_total_flow_ml_min
    assert obstructed.shunt_fraction > baseline.shunt_fraction
    assert obstructed.junction_delta_p_mmhg > baseline.junction_delta_p_mmhg


def test_rpm_escalation_can_raise_flow_but_does_not_remove_obstruction_signature():
    c = _contract()
    p = c["preconditions"]
    multiplier = float(c["stimulus"]["drain_cannula_resistance_multiplier"])

    obstructed_low = _solve(float(p["rpm"]), multiplier)
    clean_high = _solve(float(p["elevated_rpm"]), 1.0)
    obstructed_high = _solve(float(p["elevated_rpm"]), multiplier)

    # Unlike CBC01 hypovolemia, RPM may improve flow against a mechanical
    # resistance.  The obstruction is still present because same-RPM
    # performance remains inferior to the clean circuit.
    assert obstructed_high.solved_patient_flow_ml_min > obstructed_low.solved_patient_flow_ml_min
    assert obstructed_high.solved_patient_flow_ml_min < clean_high.solved_patient_flow_ml_min
    assert obstructed_high.shunt_fraction > clean_high.shunt_fraction
    assert obstructed_high.junction_delta_p_mmhg > clean_high.junction_delta_p_mmhg


def test_baseline_re_evaluation_is_deterministic_not_stateful_fault_recovery():
    c = _contract()
    rpm = float(c["preconditions"]["rpm"])
    baseline = _solve(rpm, 1.0)
    _solve(rpm, float(c["stimulus"]["drain_cannula_resistance_multiplier"]))
    restored = _solve(rpm, 1.0)

    for attr in (
        "solved_patient_flow_ml_min",
        "solved_total_flow_ml_min",
        "solved_shunt_flow_ml_min",
        "shunt_fraction",
        "p1_mmhg",
        "p2_mmhg",
        "p3_mmhg",
        "junction_delta_p_mmhg",
    ):
        assert getattr(restored, attr) == pytest.approx(getattr(baseline, attr), rel=1e-12, abs=1e-12)
