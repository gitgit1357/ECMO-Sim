from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional

from .models import (
    MechanismAvailability,
    MechanismDescriptor,
    MechanismInvocation,
    MechanismResult,
)

MechanismHandler = Callable[[MechanismInvocation], MechanismResult]


class MechanismNotAvailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class RegisteredMechanism:
    descriptor: MechanismDescriptor
    handler: Optional[MechanismHandler]


class MechanismRegistry:
    """Explicit boundary between scenario intent and simulator mechanisms."""

    def __init__(self) -> None:
        self._mechanisms: Dict[str, RegisteredMechanism] = {}

    def register(
        self,
        descriptor: MechanismDescriptor,
        handler: Optional[MechanismHandler] = None,
    ) -> None:
        if descriptor.mechanism_id in self._mechanisms:
            raise ValueError(f"mechanism already registered: {descriptor.mechanism_id}")
        if descriptor.availability == MechanismAvailability.AVAILABLE and handler is None:
            raise ValueError("available mechanisms require a handler")
        self._mechanisms[descriptor.mechanism_id] = RegisteredMechanism(descriptor, handler)

    def descriptor(self, mechanism_id: str) -> Optional[MechanismDescriptor]:
        item = self._mechanisms.get(mechanism_id)
        return item.descriptor if item else None

    def invoke(self, invocation: MechanismInvocation) -> MechanismResult:
        registered = self._mechanisms.get(invocation.mechanism_id)
        if registered is None:
            raise MechanismNotAvailableError(f"mechanism not registered: {invocation.mechanism_id}")
        if registered.descriptor.availability != MechanismAvailability.AVAILABLE or registered.handler is None:
            raise MechanismNotAvailableError(
                f"mechanism not available: {invocation.mechanism_id} "
                f"({registered.descriptor.availability.value})"
            )
        result = registered.handler(invocation)
        if not isinstance(result, MechanismResult):
            raise TypeError("mechanism handlers must return MechanismResult")
        return result

    @property
    def descriptors(self):
        return tuple(item.descriptor for item in self._mechanisms.values())


def register_unified_patient_volume_mechanism(registry: MechanismRegistry, patient) -> None:
    """Register the one Phase 1b action already backed by a complete patient mechanism."""

    mechanism_id = "patient.add_intravascular_input"

    def _handler(invocation: MechanismInvocation) -> MechanismResult:
        volume_ml = float(invocation.parameters["volume_ml"])
        fraction = float(invocation.parameters.get("intravascular_fraction", 1.0))
        before = float(patient.state.blood_volume_delta_ml)
        patient.add_intravascular_input(volume_ml, intravascular_fraction=fraction)
        return MechanismResult(
            old_value=before,
            new_value=float(patient.state.blood_volume_delta_ml),
            metadata={"volume_ml": volume_ml, "intravascular_fraction": fraction},
        )

    registry.register(
        MechanismDescriptor(
            mechanism_id=mechanism_id,
            availability=MechanismAvailability.AVAILABLE,
            description="Add intravascular volume through UnifiedNeonatalPatient's real volume ledger.",
            capability_ref="legacy action volume-bolus",
        ),
        _handler,
    )


def register_dynamic_va_ecmo_control_mechanisms(registry: MechanismRegistry, dynamic_patient) -> None:
    """Register Phase 1b's two ready ECMO controls without exposing flow as a control."""
    from dataclasses import replace

    def _rpm(invocation: MechanismInvocation) -> MechanismResult:
        old = float(dynamic_patient.coupled.controls.rpm)
        new = float(invocation.parameters["rpm"])
        dynamic_patient.set_controls(replace(dynamic_patient.coupled.controls, rpm=new))
        return MechanismResult(old_value=old, new_value=new)

    def _sweep(invocation: MechanismInvocation) -> MechanismResult:
        old = float(dynamic_patient.coupled.controls.sweep_gas_flow_ml_min)
        new = float(invocation.parameters["sweep_gas_flow_ml_min"])
        dynamic_patient.set_controls(replace(dynamic_patient.coupled.controls, sweep_gas_flow_ml_min=new))
        return MechanismResult(old_value=old, new_value=new)

    registry.register(
        MechanismDescriptor(
            mechanism_id="ecmo.set_rpm",
            availability=MechanismAvailability.AVAILABLE,
            description="Set pump RPM; flow remains a hydraulic outcome.",
            capability_ref="legacy action increase-rpm",
        ),
        _rpm,
    )
    registry.register(
        MechanismDescriptor(
            mechanism_id="ecmo.set_sweep",
            availability=MechanismAvailability.AVAILABLE,
            description="Set ECMO sweep gas flow through the authoritative console controls.",
            capability_ref="legacy action increase-sweep",
        ),
        _sweep,
    )


def register_unified_patient_blood_loss_mechanism(registry: MechanismRegistry, patient) -> None:
    """Register authoritative blood-volume loss through UnifiedNeonatalPatient."""
    mechanism_id = "patient.record_blood_loss"

    def _handler(invocation: MechanismInvocation) -> MechanismResult:
        volume_ml = float(invocation.parameters["volume_ml"])
        before = float(patient.state.blood_volume_delta_ml)
        patient.record_blood_loss(volume_ml)
        return MechanismResult(
            old_value=before,
            new_value=float(patient.state.blood_volume_delta_ml),
            metadata={"volume_ml": volume_ml},
        )

    registry.register(
        MechanismDescriptor(
            mechanism_id=mechanism_id,
            availability=MechanismAvailability.AVAILABLE,
            description="Record blood loss through UnifiedNeonatalPatient's authoritative volume ledger.",
            capability_ref="hypovolemia / hemorrhage volume mechanism",
        ),
        _handler,
    )



def register_unified_patient_myocardial_mechanism(registry: MechanismRegistry, patient) -> None:
    """Register LV/RV contractility as an authoritative native-patient mechanism."""
    from neopatient import MyocardialFunctionPort

    mechanism_id = "patient.set_myocardial_function"

    def _handler(invocation: MechanismInvocation) -> MechanismResult:
        current = patient.myocardial_function
        lv = float(invocation.parameters.get("lv_contractility_scale", current.lv_contractility_scale))
        rv = float(invocation.parameters.get("rv_contractility_scale", current.rv_contractility_scale))
        new_port = MyocardialFunctionPort(lv_contractility_scale=lv, rv_contractility_scale=rv)
        patient.set_myocardial_function(new_port)
        return MechanismResult(
            old_value={"lv_contractility_scale": current.lv_contractility_scale, "rv_contractility_scale": current.rv_contractility_scale},
            new_value={"lv_contractility_scale": lv, "rv_contractility_scale": rv},
        )

    registry.register(
        MechanismDescriptor(
            mechanism_id=mechanism_id,
            availability=MechanismAvailability.AVAILABLE,
            description="Set native LV/RV contractility scales through the unified patient's cardiopulmonary solve.",
            capability_ref="Phase 4 myocardial dysfunction runtime mechanism",
        ),
        _handler,
    )

def build_supported_mechanism_registry(*, patient, dynamic_patient=None) -> MechanismRegistry:
    """Build the scenario mutation surface from mechanisms currently marked ready.

    This function intentionally does not register partial legacy interventions as
    available.  Missing/partial capabilities must remain explicit until the
    authoritative patient/circuit layer owns them.
    """
    registry = MechanismRegistry()
    register_unified_patient_volume_mechanism(registry, patient)
    register_unified_patient_blood_loss_mechanism(registry, patient)
    register_unified_patient_myocardial_mechanism(registry, patient)
    if dynamic_patient is not None:
        register_dynamic_va_ecmo_control_mechanisms(registry, dynamic_patient)
    return registry
