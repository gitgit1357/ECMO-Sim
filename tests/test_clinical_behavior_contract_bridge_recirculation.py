import json
from pathlib import Path

import pytest

from neoecmo import EcmoConsoleControls
from neoecmocoupling import PatientToEcmoState, solve_closed_loop_va_ecmo

CONTRACT_PATH = Path(__file__).parents[1] / "clinical_behavior_contracts" / "bridge_recirculation_flow_diversion_v1.json"


def _contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _patient(contract):
    p = contract["preconditions"]
    return PatientToEcmoState(
        weight_kg=float(p["weight_kg"]),
        venous_pressure_mmhg=float(p["cvp_mmhg"]),
        arterial_pressure_mmhg=float(p["baseline_map_mmhg"]),
        blood_volume_fraction=1.0,
        native_cardiac_output_ml_min=float(p["native_cardiac_output_ml_min"]),
        native_venous_oxygen_saturation=float(p["native_venous_saturation"]),
        native_venous_paco2_mmhg=float(p["native_venous_paco2_mmhg"]),
    )


def _run(contract, target):
    p = contract["preconditions"]
    return solve_closed_loop_va_ecmo(
        EcmoConsoleControls(
            rpm=float(p["rpm"]),
            bridge_target_flow_ml_min=float(target),
            sweep_gas_flow_ml_min=float(p["sweep_gas_flow_ml_min"]),
            fdo2=float(p["fdo2"]),
        ),
        _patient(contract),
    )


def test_contract_definition_preserves_validation_boundary():
    c = _contract()
    assert c["contract_id"] == "cbc.ecmo.bridge-recirculation-flow-diversion.v1"
    assert c["clinical_review_status"] == "expert-review-pending"
    assert any("persistent" in item for item in c["future_retest_conditions"])
    assert any("validated" in item for item in c["future_retest_conditions"])


def test_bridge_target_flow_is_honored_under_live_patient_boundary():
    c = _contract()
    tol = float(c["tolerances"]["bridge_target_absolute_ml_min"])
    for target in c["preconditions"]["bridge_target_flow_probe_ml_min"]:
        result = _run(c, target)
        assert result.ecmo_state.circuit.solved_bridge_flow_ml_min == pytest.approx(float(target), abs=tol)


def test_more_bridge_recirculation_reduces_patient_flow_and_map_support():
    c = _contract()
    states = [_run(c, t) for t in c["preconditions"]["bridge_target_flow_probe_ml_min"]]
    patient_flows = [s.ecmo_state.circuit.solved_patient_flow_ml_min for s in states]
    maps = [s.settled_map_mmhg for s in states]
    assert all(a > b for a, b in zip(patient_flows, patient_flows[1:]))
    assert all(a > b for a, b in zip(maps, maps[1:]))


def test_bridge_opening_contaminates_venous_cdi_in_expected_direction():
    c = _contract()
    states = [_run(c, t) for t in c["preconditions"]["bridge_target_flow_probe_ml_min"]]
    recirc = [s.ecmo_state.cdi.recirculation_fraction for s in states]
    sats = [s.ecmo_state.cdi.mixed_saturation for s in states]
    co2 = [s.ecmo_state.cdi.mixed_paco2_mmhg for s in states]
    assert all(a < b for a, b in zip(recirc, recirc[1:]))
    assert all(a < b for a, b in zip(sats, sats[1:]))
    assert all(a > b for a, b in zip(co2, co2[1:]))


def test_branch_conservation_and_closed_bridge_restoration():
    c = _contract()
    tol = float(c["tolerances"]["branch_conservation_absolute_ml_min"])
    baseline = _run(c, 0)
    _ = _run(c, 100)
    restored = _run(c, 0)
    for result in (baseline, restored):
        p = result.ecmo_state.circuit
        assert p.solved_total_flow_ml_min == pytest.approx(
            p.solved_patient_flow_ml_min + p.solved_shunt_flow_ml_min + p.solved_bridge_flow_ml_min,
            abs=tol,
        )
    assert restored.ecmo_state.circuit.solved_patient_flow_ml_min == pytest.approx(
        baseline.ecmo_state.circuit.solved_patient_flow_ml_min
    )
    assert restored.settled_map_mmhg == pytest.approx(baseline.settled_map_mmhg)
    assert restored.ecmo_state.cdi.mixed_saturation == pytest.approx(baseline.ecmo_state.cdi.mixed_saturation)
