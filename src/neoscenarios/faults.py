from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from .models import ActionDefinition, FaultDefinition


FaultBuilder = Callable[[Mapping[str, object]], FaultDefinition]


@dataclass(frozen=True)
class FaultRegistration:
    fault_id: str
    mechanism_id: str
    label: str
    legacy_id: str | None
    builder: FaultBuilder


class FaultCatalog:
    """Catalog of complication/fault definitions backed by real mechanisms."""

    def __init__(self) -> None:
        self._registrations: dict[str, FaultRegistration] = {}

    def register(self, registration: FaultRegistration) -> None:
        if registration.fault_id in self._registrations:
            raise ValueError(f"fault already registered: {registration.fault_id}")
        self._registrations[registration.fault_id] = registration

    def registration(self, fault_id: str) -> FaultRegistration | None:
        return self._registrations.get(fault_id)

    def build(self, fault_id: str, **parameters: object) -> FaultDefinition:
        try:
            registration = self._registrations[fault_id]
        except KeyError as exc:
            raise KeyError(f"fault not registered: {fault_id}") from exc
        return registration.builder(dict(parameters))

    @property
    def registrations(self) -> tuple[FaultRegistration, ...]:
        return tuple(self._registrations.values())


def build_supported_fault_catalog() -> FaultCatalog:
    """Register only legacy complications with a complete authoritative mechanism."""
    catalog = FaultCatalog()

    def hypovolemia(parameters: Mapping[str, object]) -> FaultDefinition:
        volume_ml = float(parameters["volume_ml"])
        if volume_ml <= 0:
            raise ValueError("hypovolemia volume_ml must be > 0")
        return FaultDefinition(
            fault_id="hypovolemia",
            legacy_id="hypovolemia",
            label="Hidden preload limitation / hypovolemia",
            activation_action=ActionDefinition(
                "apply-blood-volume-loss",
                "patient.record_blood_loss",
                {"volume_ml": volume_ml},
            ),
        )

    catalog.register(FaultRegistration(
        fault_id="hypovolemia",
        mechanism_id="patient.record_blood_loss",
        label="Preload limitation / hypovolemia",
        legacy_id="hypovolemia",
        builder=hypovolemia,
    ))
    return catalog
