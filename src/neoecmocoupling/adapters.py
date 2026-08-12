from __future__ import annotations

from neoecmo import EcmoConsoleState
from neopatient import UnifiedPatientSnapshot, VascularSupportPort

from .contracts import EcmoPatientCouplingContract, EcmoToPatientState, PatientToEcmoState


def patient_boundary_from_snapshot(
    snapshot: UnifiedPatientSnapshot,
    *,
    weight_kg: float,
) -> PatientToEcmoState:
    """Translate the current patient snapshot into the Stage-1 ECMO boundary.

    The unified patient exposes both measured CVP and an intrathoracic-relative
    preload proxy through its immutable ``VenousState`` boundary.  The ECMO
    drainage boundary consumes the latter so positive airway pressure cannot
    masquerade as improved drainage merely because measured CVP rose.  This is
    a reduced-order teaching proxy, not a validated transmural-pressure
    measurement or patient/device-specific quantitative model.

    Venous PCO2 is still not authoritative, so arterial PaCO2 remains an
    explicit temporary surrogate for that field only.
    """

    boundary = PatientToEcmoState(
        weight_kg=weight_kg,
        venous_pressure_mmhg=snapshot.venous.preload.intrathoracic_relative_preload_proxy_mmhg,
        arterial_pressure_mmhg=snapshot.map_mmhg,
        blood_volume_fraction=snapshot.venous.preload.effective_venous_volume_fraction,
        native_cardiac_output_ml_min=snapshot.native_cardiac_output_ml_min,
        native_venous_oxygen_saturation=snapshot.venous.oxygen.native_mixed_venous_saturation_pct / 100.0,
        native_venous_paco2_mmhg=snapshot.paco2_mmhg,
    )
    boundary.validate()
    return boundary


def ecmo_delivery_from_console_state(
    state: EcmoConsoleState,
    *,
    external_fluid_removal_ml_min: float = 0.0,
) -> EcmoToPatientState:
    """Translate a solved ECMO state into patient-directed support.

    Patient flow—not total circuit flow—is used for drainage and return.
    Bridge and shunt recirculation remain circuit-owned branches.
    """

    circuit = state.circuit
    delivery = EcmoToPatientState(
        enabled=circuit.rpm > 0.0 and circuit.solved_patient_flow_ml_min > 0.0,
        ecmo_drainage_flow_ml_min=circuit.solved_patient_flow_ml_min,
        ecmo_return_flow_ml_min=circuit.solved_patient_flow_ml_min,
        return_oxygen_saturation=state.post_oxygenator_saturation,
        return_po2_mmhg=state.post_oxygenator_po2_mmhg,
        return_paco2_mmhg=state.post_oxygenator_paco2_mmhg,
        return_pressure_mmhg=circuit.p3_mmhg,
        external_fluid_removal_ml_min=external_fluid_removal_ml_min,
        total_circuit_flow_ml_min=circuit.solved_total_flow_ml_min,
        shunt_flow_ml_min=circuit.solved_shunt_flow_ml_min,
        bridge_flow_ml_min=circuit.solved_bridge_flow_ml_min,
        p1_mmhg=circuit.p1_mmhg,
        p2_mmhg=circuit.p2_mmhg,
        p3_mmhg=circuit.p3_mmhg,
    )
    delivery.validate()
    return delivery


def build_coupling_contract(
    patient_snapshot: UnifiedPatientSnapshot,
    ecmo_state: EcmoConsoleState,
    *,
    weight_kg: float,
    external_fluid_removal_ml_min: float = 0.0,
) -> EcmoPatientCouplingContract:
    contract = EcmoPatientCouplingContract(
        patient=patient_boundary_from_snapshot(patient_snapshot, weight_kg=weight_kg),
        ecmo=ecmo_delivery_from_console_state(
            ecmo_state,
            external_fluid_removal_ml_min=external_fluid_removal_ml_min,
        ),
    )
    contract.validate()
    return contract


def vascular_support_port_from_delivery(delivery: EcmoToPatientState) -> VascularSupportPort:
    """Create the patient-facing support port from solved ECMO delivery.

    This carries patient-directed flow and true post-oxygenator gases into the
    one-way Stage-2B patient mixing model.  Total circuit, shunt, and bridge
    flows are intentionally excluded from patient support.
    """
    delivery.validate()
    return VascularSupportPort(
        enabled=delivery.enabled,
        support_flow_ml_min=delivery.ecmo_return_flow_ml_min,
        return_oxygen_saturation_pct=delivery.return_oxygen_saturation * 100.0,
        return_po2_mmhg=delivery.return_po2_mmhg,
        return_paco2_mmhg=delivery.return_paco2_mmhg,
    )
