import json
from pathlib import Path

import pytest

from neoecmo import EcmoConsoleControls, ShuntLineConfiguration
from neoecmocoupling import CoupledVaEcmoPatient
from neopatient import RenalTherapyPort, UnifiedNeonatalPatient, UnifiedPatientConfig

CONTRACT_PATH = Path(__file__).parents[1] / "clinical_behavior_contracts" / "ckrt_net_ultrafiltration_v1.json"


def _contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _controls(*, configuration=ShuntLineConfiguration.CKRT, blood_flow=30.0, uf_rate=0.0):
    p = _contract()["preconditions"]
    return EcmoConsoleControls(
        rpm=float(p["rpm"]),
        sweep_gas_flow_ml_min=float(p["sweep_gas_flow_ml_min"]),
        bridge_clamp_position=float(p["bridge_clamp_position"]),
        shunt_configuration=configuration,
        shunt_ckrt_blood_flow_ml_min=float(blood_flow),
        shunt_ckrt_net_ultrafiltration_rate_ml_min=float(uf_rate),
    )


def _system(*, configuration=ShuntLineConfiguration.CKRT, blood_flow=30.0, uf_rate=0.0):
    p = _contract()["preconditions"]
    patient = UnifiedNeonatalPatient(
        UnifiedPatientConfig(
            weight_kg=float(p["weight_kg"]),
            lung_run_s=1.0,
            circulation_run_s=1.0,
        )
    )
    return patient, CoupledVaEcmoPatient(
        patient,
        _controls(configuration=configuration, blood_flow=blood_flow, uf_rate=uf_rate),
    )


def _metrics(patient, snapshot):
    volume = snapshot.volume_limited_ecmo
    circuit = volume.closed_loop.ecmo_state.circuit
    ledger = patient.state.volume_ledger
    return {
        "blood_volume": snapshot.patient.total_blood_volume_ml,
        "blood_volume_fraction": snapshot.patient.blood_volume_fraction,
        "preload": volume.preload_fraction,
        "patient_flow": snapshot.delivery.ecmo_return_flow_ml_min,
        "p1": circuit.p1_mmhg,
        "map": snapshot.patient.map_mmhg,
        "cvp": snapshot.patient.cvp_mmhg,
        "net_body_fluid": snapshot.patient.cumulative_net_body_fluid_ml,
        "urine": snapshot.patient.cumulative_urine_ml,
        "ckrt_removed": ledger.cumulative_ckrt_removal_ml,
    }


def test_contract_definition_preserves_scope_and_future_retest_boundary():
    contract = _contract()
    assert contract["contract_id"] == "cbc.ecmo.ckrt-net-ultrafiltration.v1"
    assert contract["status"] == "automated-behavior-contract"
    assert contract["clinical_review_status"] == "expert-review-pending"
    assert contract["stop_model"] == "set authoritative CKRT net-UF rate to zero"
    assert "CKRT solute clearance or dialysis dose" in contract["not_modeled"]
    assert contract["future_retest_conditions"]


@pytest.mark.parametrize(
    "configuration,blood_flow",
    [
        (ShuntLineConfiguration.OPEN, 0.0),
        (ShuntLineConfiguration.OPEN, 30.0),
        (ShuntLineConfiguration.CKRT, 0.0),
    ],
)
def test_configured_ckrt_uf_does_not_remove_fluid_unless_ckrt_is_selected_and_running(configuration, blood_flow):
    rate = float(_contract()["stimulus"]["net_ultrafiltration_rate_ml_min"])
    duration = float(_contract()["stimulus"]["active_duration_min"])
    patient, system = _system(configuration=configuration, blood_flow=blood_flow, uf_rate=rate)
    system.advance(duration)
    assert patient.state.volume_ledger.cumulative_ckrt_removal_ml == pytest.approx(0.0)


def test_active_ckrt_uf_diverges_from_matched_zero_uf_control_in_expected_direction():
    contract = _contract()
    rate = float(contract["stimulus"]["net_ultrafiltration_rate_ml_min"])
    duration = float(contract["stimulus"]["active_duration_min"])

    active_patient, active = _system(uf_rate=rate)
    control_patient, control = _system(uf_rate=0.0)
    active_after = _metrics(active_patient, active.advance(duration))
    control_after = _metrics(control_patient, control.advance(duration))

    expected_removed = rate * duration
    assert active_after["ckrt_removed"] == pytest.approx(expected_removed)
    assert control_after["ckrt_removed"] == pytest.approx(0.0)
    assert active_after["net_body_fluid"] == pytest.approx(
        control_after["net_body_fluid"] - expected_removed, rel=1e-9, abs=1e-9
    )
    assert active_after["urine"] == pytest.approx(control_after["urine"], rel=1e-9, abs=1e-9)

    assert active_after["blood_volume"] < control_after["blood_volume"]
    assert active_after["preload"] < control_after["preload"]
    assert active_after["patient_flow"] < control_after["patient_flow"]
    assert active_after["p1"] < control_after["p1"]
    assert active_after["map"] < control_after["map"]
    assert active_after["cvp"] < control_after["cvp"]


def test_stopping_uf_freezes_ckrt_removal_ledger_without_claiming_immediate_recovery():
    contract = _contract()
    rate = float(contract["stimulus"]["net_ultrafiltration_rate_ml_min"])
    duration = float(contract["stimulus"]["active_duration_min"])
    patient, system = _system(uf_rate=rate)
    system.advance(duration)
    removed_at_stop = patient.state.volume_ledger.cumulative_ckrt_removal_ml

    system.set_controls(_controls(uf_rate=0.0))
    system.advance(10.0)

    assert patient.state.volume_ledger.cumulative_ckrt_removal_ml == pytest.approx(removed_at_stop)


def test_stateful_replacement_returns_near_matched_no_uf_counterfactual_without_erasing_history():
    contract = _contract()
    rate = float(contract["stimulus"]["net_ultrafiltration_rate_ml_min"])
    active_duration = float(contract["stimulus"]["active_duration_min"])
    replacement_duration = float(contract["stimulus"]["replacement_duration_min"])

    treated_patient, treated = _system(uf_rate=rate)
    treated.advance(active_duration)
    treated.set_controls(_controls(uf_rate=0.0))
    treated_patient.set_renal_therapy(RenalTherapyPort(fluid_in_ml_min=rate))
    treated_final = _metrics(treated_patient, treated.advance(replacement_duration))

    control_patient, control = _system(uf_rate=0.0)
    control_final = _metrics(control_patient, control.advance(active_duration + replacement_duration))

    rel = float(contract["tolerances"]["counterfactual_recovery_relative"])
    abs_tol = float(contract["tolerances"]["counterfactual_recovery_absolute"])
    for key in ("blood_volume", "blood_volume_fraction", "preload", "patient_flow", "p1", "map", "cvp", "net_body_fluid"):
        assert treated_final[key] == pytest.approx(control_final[key], rel=rel, abs=abs_tol)

    assert treated_final["ckrt_removed"] == pytest.approx(rate * active_duration)
    assert control_final["ckrt_removed"] == pytest.approx(0.0)
