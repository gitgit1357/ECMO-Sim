from dataclasses import replace

import pytest

from neoecmo import EcmoConsoleControls, run_ecmo_console
from neoecmocoupling import (
    EcmoPatientCouplingContract,
    EcmoToPatientState,
    PatientToEcmoState,
    build_coupling_contract,
)
from neopatient import UnifiedNeonatalPatient


def _running_console():
    return run_ecmo_console(
        EcmoConsoleControls(rpm=3000, fdo2=1.0, sweep_gas_flow_ml_min=600),
        native_venous_saturation=0.65,
        native_venous_paco2_mmhg=55,
    )


def test_contract_translates_existing_patient_and_ecmo_without_changing_solvers():
    patient = UnifiedNeonatalPatient()
    patient_snapshot = patient.snapshot()
    ecmo_state = _running_console()

    contract = build_coupling_contract(
        patient_snapshot,
        ecmo_state,
        weight_kg=patient.config.weight_kg,
    )

    assert contract.patient.venous_pressure_mmhg == pytest.approx(
        patient_snapshot.venous.preload.intrathoracic_relative_preload_proxy_mmhg
    )
    assert contract.patient.arterial_pressure_mmhg == patient_snapshot.map_mmhg
    assert contract.ecmo.ecmo_return_flow_ml_min == ecmo_state.circuit.solved_patient_flow_ml_min
    assert contract.ecmo.ecmo_return_flow_ml_min != ecmo_state.circuit.solved_total_flow_ml_min
    assert contract.ecmo.return_oxygen_saturation == ecmo_state.post_oxygenator_saturation


def test_ecmo_contract_preserves_branch_flow_conservation():
    state = _running_console()
    contract = build_coupling_contract(
        UnifiedNeonatalPatient().snapshot(),
        state,
        weight_kg=3.5,
    )
    assert contract.ecmo.total_circuit_flow_ml_min == pytest.approx(
        contract.ecmo.ecmo_return_flow_ml_min
        + contract.ecmo.shunt_flow_ml_min
        + contract.ecmo.bridge_flow_ml_min,
        abs=0.1,
    )


def test_invalid_saturation_is_rejected():
    patient = PatientToEcmoState(
        weight_kg=3.5,
        venous_pressure_mmhg=5,
        arterial_pressure_mmhg=50,
        blood_volume_fraction=1.0,
        native_cardiac_output_ml_min=200,
        native_venous_oxygen_saturation=1.2,
        native_venous_paco2_mmhg=50,
    )
    with pytest.raises(ValueError, match="saturation"):
        patient.validate()


def test_nonconserving_ecmo_delivery_is_rejected():
    state = _running_console()
    valid = build_coupling_contract(
        UnifiedNeonatalPatient().snapshot(), state, weight_kg=3.5
    ).ecmo
    invalid = replace(valid, total_circuit_flow_ml_min=valid.total_circuit_flow_ml_min + 20)
    with pytest.raises(ValueError, match="do not conserve"):
        invalid.validate()


def test_contract_validation_is_explicit_and_side_effect_free():
    contract = EcmoPatientCouplingContract(
        patient=PatientToEcmoState(3.5, 5, 50, 1.0, 200, 0.65, 55),
        ecmo=EcmoToPatientState(
            enabled=False,
            ecmo_drainage_flow_ml_min=0,
            ecmo_return_flow_ml_min=0,
            return_oxygen_saturation=1.0,
            return_po2_mmhg=300,
            return_paco2_mmhg=40,
            return_pressure_mmhg=0,
            external_fluid_removal_ml_min=0,
            total_circuit_flow_ml_min=0,
            shunt_flow_ml_min=0,
            bridge_flow_ml_min=0,
            p1_mmhg=0,
            p2_mmhg=0,
            p3_mmhg=0,
        ),
    )
    contract.validate()
