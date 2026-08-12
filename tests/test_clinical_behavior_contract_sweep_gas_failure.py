import json
from dataclasses import replace
from pathlib import Path

import pytest

from neoecmo import EcmoConsoleControls, po2_from_saturation_mmhg, run_ecmo_console
from neoecmocoupling import CoupledVaEcmoPatient
from neopatient import UnifiedNeonatalPatient, UnifiedPatientConfig

CONTRACT_PATH = Path(__file__).parents[1] / "clinical_behavior_contracts" / "sweep_gas_failure_v1.json"


def _contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _console(contract, sweep):
    p = contract["preconditions"]
    return run_ecmo_console(
        EcmoConsoleControls(
            rpm=float(p["rpm"]),
            sweep_gas_flow_ml_min=float(sweep),
            fdo2=float(p["fdo2"]),
            bridge_clamp_position=float(p["bridge_clamp_position"]),
        ),
        native_venous_saturation=float(p["representative_inlet_venous_saturation"]),
        native_venous_paco2_mmhg=float(p["representative_inlet_paco2_mmhg"]),
    )


def _coupled(contract):
    p = contract["preconditions"]
    patient = UnifiedNeonatalPatient(
        UnifiedPatientConfig(weight_kg=float(p["weight_kg"]), lung_run_s=1.0, circulation_run_s=1.0)
    )
    coupled = CoupledVaEcmoPatient(
        patient,
        EcmoConsoleControls(
            rpm=float(p["rpm"]),
            sweep_gas_flow_ml_min=float(p["sweep_gas_flow_ml_min"]),
            fdo2=float(p["fdo2"]),
            bridge_clamp_position=float(p["bridge_clamp_position"]),
        ),
    )
    return coupled


def test_contract_definition_preserves_validation_boundary_and_known_scope_limit():
    contract = _contract()
    assert contract["contract_id"] == "cbc.ecmo.sweep-gas-failure.v1"
    assert contract["status"] == "automated-behavior-contract"
    assert contract["clinical_review_status"] == "expert-review-pending"
    assert any("native venous saturation" in item for item in contract["allowed_exceptions"])


def test_zero_sweep_disables_membrane_o2_addition_and_co2_removal_without_changing_flow():
    contract = _contract()
    p = contract["preconditions"]
    tol = contract["tolerances"]
    baseline = _console(contract, p["sweep_gas_flow_ml_min"])
    failed = _console(contract, contract["stimulus"]["failed_sweep_gas_flow_ml_min"])

    assert failed.circuit.solved_patient_flow_ml_min == pytest.approx(
        baseline.circuit.solved_patient_flow_ml_min, rel=float(tol["flow_relative"])
    )
    assert failed.post_oxygenator_paco2_mmhg == pytest.approx(
        float(p["representative_inlet_paco2_mmhg"]), rel=float(tol["gas_boundary_relative"])
    )
    assert failed.post_oxygenator_saturation == pytest.approx(
        float(p["representative_inlet_venous_saturation"]), rel=float(tol["gas_boundary_relative"])
    )
    inlet_po2 = po2_from_saturation_mmhg(float(p["representative_inlet_venous_saturation"]))
    assert failed.post_oxygenator_po2_mmhg == pytest.approx(
        inlet_po2, rel=float(tol["gas_boundary_relative"])
    )
    assert baseline.post_oxygenator_po2_mmhg > failed.post_oxygenator_po2_mmhg
    assert baseline.post_oxygenator_paco2_mmhg < failed.post_oxygenator_paco2_mmhg


def test_nonzero_sweep_titration_remains_co2_dominant_not_o2_control():
    contract = _contract()
    low = _console(contract, 100.0)
    high = _console(contract, 1000.0)
    abs_tol = float(contract["tolerances"]["nonzero_sweep_po2_absolute_mmhg"])

    assert high.post_oxygenator_paco2_mmhg < low.post_oxygenator_paco2_mmhg
    assert high.post_oxygenator_po2_mmhg == pytest.approx(low.post_oxygenator_po2_mmhg, abs=abs_tol)
    assert high.circuit.solved_patient_flow_ml_min == pytest.approx(low.circuit.solved_patient_flow_ml_min)


def test_coupled_patient_co2_rises_with_complete_sweep_loss_and_recovers_when_restored():
    contract = _contract()
    p = contract["preconditions"]
    tol = contract["tolerances"]
    coupled = _coupled(contract)
    baseline = coupled.snapshot()

    coupled.set_controls(replace(coupled.controls, sweep_gas_flow_ml_min=0.0))
    failed = coupled.snapshot()

    assert failed.patient.paco2_mmhg > baseline.patient.paco2_mmhg
    assert failed.delivery.ecmo_return_flow_ml_min == pytest.approx(
        baseline.delivery.ecmo_return_flow_ml_min, rel=float(tol["flow_relative"])
    )

    coupled.set_controls(replace(coupled.controls, sweep_gas_flow_ml_min=float(p["sweep_gas_flow_ml_min"])))
    restored = coupled.snapshot()
    assert restored.patient.paco2_mmhg == pytest.approx(
        baseline.patient.paco2_mmhg, rel=float(tol["coupled_paco2_recovery_relative"])
    )
