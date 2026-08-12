import json
from pathlib import Path

import pytest

from neoecmo import EcmoConsoleControls
from neoecmocoupling import CoupledVaEcmoPatient
from neopatient import UnifiedNeonatalPatient, UnifiedPatientConfig

CONTRACT_PATH = Path(__file__).parents[1] / "clinical_behavior_contracts" / "ongoing_major_bleeding_v1.json"


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


def _metrics(patient, snapshot):
    volume = snapshot.volume_limited_ecmo
    circuit = volume.closed_loop.ecmo_state.circuit
    ledger = patient.state.volume_ledger
    return {
        "blood_volume_fraction": snapshot.patient.blood_volume_fraction,
        "preload": volume.preload_fraction,
        "patient_flow": snapshot.delivery.ecmo_return_flow_ml_min,
        "p1": circuit.p1_mmhg,
        "map": snapshot.patient.map_mmhg,
        "cvp": snapshot.patient.cvp_mmhg,
        "chatter": volume.chatter_active,
        "blood_loss": ledger.cumulative_blood_loss_ml,
        "input": ledger.cumulative_input_ml,
        "iv_delta": ledger.intravascular_delta_ml,
    }


def _assert_more_depleted(after, before):
    assert after["blood_volume_fraction"] < before["blood_volume_fraction"]
    assert after["preload"] < before["preload"]
    assert after["patient_flow"] < before["patient_flow"]
    assert after["p1"] < before["p1"]
    assert after["map"] < before["map"]
    assert after["cvp"] < before["cvp"]


def test_contract_definition_preserves_validation_and_model_boundaries():
    contract = _contract()
    assert contract["contract_id"] == "cbc.patient.ongoing-major-bleeding.v1"
    assert contract["legacy_scenario_id"] == "ce-06-major-bleeding"
    assert contract["status"] == "automated-behavior-contract"
    assert contract["clinical_review_status"] == "expert-review-pending"
    assert contract["cessation_model"] == "no further calls to patient.record_blood_loss"
    assert "persistent bleeding-rate state" in contract["not_modeled"]
    assert contract["future_retest_conditions"]


def test_ongoing_bleeding_serial_loss_partial_replacement_and_stateful_recovery():
    contract, patient, coupled = _system()
    baseline = _metrics(patient, coupled.snapshot())
    assert baseline["chatter"] is contract["preconditions"]["baseline_chatter"]

    baseline_blood_volume_ml = patient.volume_config.baseline_blood_volume_ml(patient.config.weight_kg)
    increment = baseline_blood_volume_ml * float(
        contract["stimulus"]["loss_increment_fraction_of_baseline_blood_volume"]
    )
    partial_replacement = increment * float(
        contract["stimulus"]["partial_replacement_fraction_of_one_increment"]
    )

    patient.record_blood_loss(increment)
    loss1 = _metrics(patient, coupled.snapshot())
    _assert_more_depleted(loss1, baseline)
    assert loss1["blood_loss"] == pytest.approx(increment)
    assert loss1["input"] == pytest.approx(0.0)

    patient.record_blood_loss(increment)
    loss2 = _metrics(patient, coupled.snapshot())
    _assert_more_depleted(loss2, loss1)
    assert loss2["blood_loss"] == pytest.approx(increment * 2)

    # Replacement while bleeding continues: improve true state but do not erase
    # the accumulated volume deficit or rewrite the blood-loss ledger.
    patient.add_intravascular_input(partial_replacement, intravascular_fraction=1.0)
    partial = _metrics(patient, coupled.snapshot())
    assert partial["preload"] > loss2["preload"]
    assert partial["patient_flow"] > loss2["patient_flow"]
    assert partial["p1"] > loss2["p1"]
    assert partial["map"] > loss2["map"]
    assert partial["cvp"] > loss2["cvp"]
    assert partial["preload"] < baseline["preload"]
    assert partial["patient_flow"] < baseline["patient_flow"]
    assert partial["map"] < baseline["map"]
    assert partial["cvp"] < baseline["cvp"]
    assert partial["blood_loss"] == pytest.approx(increment * 2)
    assert partial["input"] == pytest.approx(partial_replacement)

    # Ongoing process is represented by another authoritative loss event.
    patient.record_blood_loss(increment)
    loss3 = _metrics(patient, coupled.snapshot())
    _assert_more_depleted(loss3, partial)
    assert loss3["blood_loss"] == pytest.approx(increment * 3)
    assert loss3["input"] == pytest.approx(partial_replacement)

    # CBC04 v1 has no bleeding_active state.  Cessation means no more loss calls.
    # Replace only the remaining net deficit in the same mutable patient object.
    remaining_net_deficit = loss3["blood_loss"] - loss3["input"]
    patient.add_intravascular_input(remaining_net_deficit, intravascular_fraction=1.0)
    recovered = _metrics(patient, coupled.snapshot())
    tol = float(contract["tolerances"]["recovery_relative"])

    for key in ("blood_volume_fraction", "preload", "patient_flow", "p1", "map", "cvp"):
        assert recovered[key] == pytest.approx(baseline[key], rel=tol, abs=1e-6)
    assert recovered["blood_loss"] == pytest.approx(increment * 3)
    assert recovered["input"] == pytest.approx(increment * 3)
    assert recovered["iv_delta"] == pytest.approx(0.0, abs=1e-9)
    assert not recovered["chatter"]
