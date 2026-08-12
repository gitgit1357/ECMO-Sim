import json
from pathlib import Path

import pytest

from neoecmo import (
    EcmoConsoleControls,
    run_ecmo_console,
    saturation_from_po2_mmhg,
)

CONTRACT_PATH = Path(__file__).parents[1] / "clinical_behavior_contracts" / "fdo2_oxygen_fraction_control_v1.json"


def _contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _run(contract, fdo2):
    p = contract["preconditions"]
    return run_ecmo_console(
        EcmoConsoleControls(
            rpm=float(p["rpm"]),
            sweep_gas_flow_ml_min=float(p["sweep_gas_flow_ml_min"]),
            fdo2=float(fdo2),
            bridge_clamp_position=float(p["bridge_clamp_position"]),
        ),
        native_venous_saturation=float(p["representative_inlet_venous_saturation"]),
        native_venous_paco2_mmhg=float(p["representative_inlet_paco2_mmhg"]),
    )


def test_contract_definition_preserves_validation_boundary_and_future_retest_conditions():
    contract = _contract()
    assert contract["contract_id"] == "cbc.ecmo.fdo2-oxygen-fraction-control.v1"
    assert contract["status"] == "automated-behavior-contract"
    assert contract["clinical_review_status"] == "expert-review-pending"
    assert any("ownership or derivation of native mixed-venous oxygen" in item for item in contract["future_retest_conditions"])
    assert any("persistent" in item for item in contract["future_retest_conditions"])
    assert any("Phase 11" in item for item in contract["future_retest_conditions"])


def test_fdo2_reduction_monotonically_lowers_post_oxy_oxygen_state_with_coherent_sat_po2_pair():
    contract = _contract()
    tol = float(contract["tolerances"]["oxygen_state_coherence_absolute"])
    states = [_run(contract, f) for f in contract["preconditions"]["graded_probe_fdo2"]]

    po2_values = [state.post_oxygenator_po2_mmhg for state in states]
    saturation_values = [state.post_oxygenator_saturation for state in states]

    assert all(a > b for a, b in zip(po2_values, po2_values[1:]))
    assert all(a > b for a, b in zip(saturation_values, saturation_values[1:]))
    for state in states:
        assert state.post_oxygenator_saturation == pytest.approx(
            saturation_from_po2_mmhg(state.post_oxygenator_po2_mmhg), abs=tol
        )


def test_fdo2_only_change_does_not_change_co2_clearance_or_hydraulic_flow():
    contract = _contract()
    states = [_run(contract, f) for f in contract["preconditions"]["graded_probe_fdo2"]]
    paco2_tol = float(contract["tolerances"]["paco2_absolute_mmhg"])
    flow_rel = float(contract["tolerances"]["flow_relative"])
    baseline = states[0]

    for state in states[1:]:
        assert state.post_oxygenator_paco2_mmhg == pytest.approx(
            baseline.post_oxygenator_paco2_mmhg, abs=paco2_tol
        )
        assert state.circuit.solved_patient_flow_ml_min == pytest.approx(
            baseline.circuit.solved_patient_flow_ml_min, rel=flow_rel
        )
        assert state.circuit.solved_total_flow_ml_min == pytest.approx(
            baseline.circuit.solved_total_flow_ml_min, rel=flow_rel
        )


def test_fdo2_restoration_reproduces_baseline_membrane_state():
    contract = _contract()
    baseline = _run(contract, contract["preconditions"]["baseline_fdo2"])
    _ = _run(contract, contract["stimulus"]["lowest_fdo2"])
    restored = _run(contract, contract["preconditions"]["baseline_fdo2"])

    assert restored.post_oxygenator_po2_mmhg == pytest.approx(baseline.post_oxygenator_po2_mmhg)
    assert restored.post_oxygenator_saturation == pytest.approx(baseline.post_oxygenator_saturation)
    assert restored.post_oxygenator_paco2_mmhg == pytest.approx(baseline.post_oxygenator_paco2_mmhg)
    assert restored.circuit.solved_patient_flow_ml_min == pytest.approx(
        baseline.circuit.solved_patient_flow_ml_min
    )
