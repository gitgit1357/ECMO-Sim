import json
from dataclasses import replace
from pathlib import Path

import pytest

from neoecmo import EcmoConsoleControls
from neoecmocoupling import CoupledVaEcmoPatient
from neopatient import UnifiedNeonatalPatient, UnifiedPatientConfig

CONTRACT_PATH = Path(__file__).parents[1] / "clinical_behavior_contracts" / "hypovolemia_preload_low_flow_v1.json"


def _contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _system():
    contract = _contract()
    p = contract["preconditions"]
    patient = UnifiedNeonatalPatient(
        UnifiedPatientConfig(
            weight_kg=float(p["weight_kg"]),
            lung_run_s=1.0,
            circulation_run_s=1.0,
        )
    )
    coupled = CoupledVaEcmoPatient(
        patient,
        EcmoConsoleControls(
            rpm=float(p["rpm"]),
            sweep_gas_flow_ml_min=float(p["sweep_gas_flow_ml_min"]),
            bridge_clamp_position=float(p["bridge_clamp_position"]),
        ),
    )
    return contract, patient, coupled


def _metrics(snapshot):
    volume = snapshot.volume_limited_ecmo
    circuit = volume.closed_loop.ecmo_state.circuit
    return {
        "preload": volume.preload_fraction,
        "patient_flow": snapshot.delivery.ecmo_return_flow_ml_min,
        "p1": circuit.p1_mmhg,
        "map": snapshot.patient.map_mmhg,
        "cvp": snapshot.patient.cvp_mmhg,
        "chatter": volume.chatter_active,
    }


def test_contract_definition_preserves_validation_boundary():
    contract = _contract()
    assert contract["contract_id"] == "cbc.lowflow.hypovolemia.v1"
    assert contract["status"] == "automated-behavior-contract"
    assert contract["clinical_review_status"] == "expert-review-pending"
    assert contract["notes"]


def test_hypovolemia_contract_direction_recovery_and_rpm_escalation():
    contract, patient, coupled = _system()
    baseline_snapshot = coupled.snapshot()
    baseline = _metrics(baseline_snapshot)
    assert baseline["chatter"] is contract["preconditions"]["baseline_chatter"]

    baseline_blood_volume_ml = patient.volume_config.baseline_blood_volume_ml(patient.config.weight_kg)
    loss_ml = (
        baseline_blood_volume_ml
        * float(contract["stimulus"]["blood_loss_fraction_of_baseline_blood_volume"])
    )
    patient.record_blood_loss(loss_ml)
    low_snapshot = coupled.snapshot()
    low = _metrics(low_snapshot)

    assert low["preload"] < baseline["preload"]
    assert low["patient_flow"] < baseline["patient_flow"]
    assert low["p1"] < baseline["p1"]
    assert low["map"] < baseline["map"]
    assert low["cvp"] < baseline["cvp"]

    escalation_rpm = float(contract["rpm_escalation_branch"]["rpm"])
    coupled.set_controls(replace(coupled.controls, rpm=escalation_rpm))
    high_rpm_snapshot = coupled.snapshot()
    high_rpm = _metrics(high_rpm_snapshot)
    max_gain = float(contract["tolerances"]["rpm_escalation_flow_gain_fraction_max"])

    assert high_rpm["p1"] < low["p1"]
    assert high_rpm["chatter"]
    assert high_rpm["patient_flow"] <= low["patient_flow"] * (1.0 + max_gain)
    assert high_rpm["map"] < baseline["map"]

    # Definitive correction for this isolated mechanism: restore volume and the
    # original pump setting.  The result should return to the original state,
    # not a scenario-authored monitor patch.
    coupled.set_controls(replace(coupled.controls, rpm=float(contract["preconditions"]["rpm"])))
    patient.add_intravascular_input(
        loss_ml * float(contract["stimulus"]["replacement_fraction_of_removed_volume"]),
        intravascular_fraction=1.0,
    )
    recovered = _metrics(coupled.snapshot())
    tol = float(contract["tolerances"]["recovery_relative"])

    for key in ("preload", "patient_flow", "p1", "map", "cvp"):
        assert recovered[key] == pytest.approx(baseline[key], rel=tol, abs=1e-6)
    assert not recovered["chatter"]
