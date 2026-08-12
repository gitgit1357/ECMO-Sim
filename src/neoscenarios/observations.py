from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Callable, Mapping, Optional

from neoevents import EventStream


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"observation value is not JSON-compatible: {type(value).__name__}")


@dataclass(frozen=True)
class FrozenObservation:
    observation_id: str
    sample_time_s: float
    values: Mapping[str, Any]
    available_time_s: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.observation_id.strip():
            raise ValueError("observation_id must be non-empty")
        object.__setattr__(self, "sample_time_s", float(self.sample_time_s))
        object.__setattr__(self, "values", _freeze(dict(self.values)))
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata)))
        if self.available_time_s is not None:
            object.__setattr__(self, "available_time_s", float(self.available_time_s))

    def is_available(self, simulation_time_s: float) -> bool:
        return self.available_time_s is None or float(simulation_time_s) >= self.available_time_s

    def to_dict(self) -> dict[str, Any]:
        def thaw(value):
            if isinstance(value, Mapping):
                return {str(k): thaw(v) for k, v in value.items()}
            if isinstance(value, tuple):
                return [thaw(v) for v in value]
            return value
        return {
            "observation_id": self.observation_id,
            "sample_time_s": self.sample_time_s,
            "available_time_s": self.available_time_s,
            "values": thaw(self.values),
            "metadata": thaw(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "FrozenObservation":
        return cls(
            observation_id=str(payload["observation_id"]),
            sample_time_s=float(payload["sample_time_s"]),
            available_time_s=None if payload.get("available_time_s") is None else float(payload["available_time_s"]),
            values=dict(payload.get("values", {})),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(frozen=True)
class ObservationDescriptor:
    provider_id: str
    description: str = ""
    capability_ref: str | None = None
    partial: bool = False

    def __post_init__(self) -> None:
        if not self.provider_id.strip():
            raise ValueError("provider_id must be non-empty")


ObservationProvider = Callable[[float, Mapping[str, Any]], FrozenObservation]


@dataclass(frozen=True)
class RegisteredObservation:
    descriptor: ObservationDescriptor
    provider: ObservationProvider


class ObservationRegistry:
    """Read-only boundary from scenarios into authoritative simulator state."""

    def __init__(self) -> None:
        self._providers: dict[str, RegisteredObservation] = {}

    def register(self, descriptor: ObservationDescriptor, provider: ObservationProvider) -> None:
        if descriptor.provider_id in self._providers:
            raise ValueError(f"observation already registered: {descriptor.provider_id}")
        self._providers[descriptor.provider_id] = RegisteredObservation(descriptor, provider)

    def descriptor(self, provider_id: str) -> ObservationDescriptor | None:
        item = self._providers.get(provider_id)
        return item.descriptor if item else None

    def sample(
        self,
        provider_id: str,
        *,
        simulation_time_s: float,
        parameters: Mapping[str, Any] | None = None,
    ) -> FrozenObservation:
        try:
            registered = self._providers[provider_id]
        except KeyError as exc:
            raise KeyError(f"observation provider not registered: {provider_id}") from exc
        observation = registered.provider(float(simulation_time_s), dict(parameters or {}))
        if not isinstance(observation, FrozenObservation):
            raise TypeError("observation providers must return FrozenObservation")
        return observation

    @property
    def descriptors(self) -> tuple[ObservationDescriptor, ...]:
        return tuple(item.descriptor for item in self._providers.values())


def _patient_snapshot_values(snapshot) -> dict[str, float | bool]:
    return {
        "map_mmhg": float(snapshot.map_mmhg),
        "systolic_mmhg": float(snapshot.systolic_mmhg),
        "diastolic_mmhg": float(snapshot.diastolic_mmhg),
        "cvp_mmhg": float(snapshot.cvp_mmhg),
        "native_cardiac_output_ml_min": float(snapshot.native_cardiac_output_ml_min),
        "pao2_mmhg": float(snapshot.pao2_mmhg),
        "paco2_mmhg": float(snapshot.paco2_mmhg),
        "sao2_pct": float(snapshot.sao2_pct),
        "urine_ml_kg_hr": float(snapshot.urine_ml_kg_hr),
        "cumulative_urine_ml": float(snapshot.cumulative_urine_ml),
        "cumulative_net_body_fluid_ml": float(snapshot.cumulative_net_body_fluid_ml),
        "blood_volume_fraction": float(snapshot.blood_volume_fraction),
        "third_space_volume_ml": float(snapshot.third_space_volume_ml),
        "vascular_support_enabled": bool(snapshot.vascular_support_enabled),
        "vascular_support_flow_ml_min": float(snapshot.vascular_support_flow_ml_min),
    }


def register_ready_state_observations(
    registry: ObservationRegistry,
    *,
    patient,
    dynamic_patient=None,
) -> None:
    """Register the six Phase-1b observations marked READY_OBSERVATION_FROM_STATE.

    Providers expose only state the Python runtime already owns.  They do not
    infer diagnoses, fabricate findings, or add missing alarm/fault semantics.
    """

    def patient_snapshot():
        return patient.snapshot()

    def dynamic_snapshot():
        return dynamic_patient.snapshot() if dynamic_patient is not None else None

    def hemodynamics(now: float, params: Mapping[str, Any]) -> FrozenObservation:
        snap = patient_snapshot()
        values = _patient_snapshot_values(snap)
        dyn = dynamic_snapshot()
        if dyn is not None:
            values.update({
                "ecmo_patient_flow_ml_min": float(dyn.displayed.patient_flow_ml_min),
                "ecmo_total_circuit_flow_ml_min": float(dyn.displayed.total_circuit_flow_ml_min),
                "drainage_pressure_mmhg": float(dyn.displayed.p1_mmhg),
                "pre_oxygenator_pressure_mmhg": float(dyn.displayed.p2_mmhg),
                "post_oxygenator_pressure_mmhg": float(dyn.displayed.p3_mmhg),
            })
        return FrozenObservation("assess-hemodynamics", now, values,
                                 metadata={"provider_id": "assess-hemodynamics"})

    def pump_function(now: float, params: Mapping[str, Any]) -> FrozenObservation:
        if dynamic_patient is None:
            raise RuntimeError("pump observation requires dynamic VA ECMO patient")
        dyn = dynamic_snapshot()
        controls = dynamic_patient.coupled.controls
        return FrozenObservation("assess-pump-function", now, {
            "rpm": float(controls.rpm),
            "patient_flow_ml_min": float(dyn.displayed.patient_flow_ml_min),
            "total_circuit_flow_ml_min": float(dyn.displayed.total_circuit_flow_ml_min),
            "p1_mmhg": float(dyn.displayed.p1_mmhg),
            "p2_mmhg": float(dyn.displayed.p2_mmhg),
            "p3_mmhg": float(dyn.displayed.p3_mmhg),
            "chatter_display_active": bool(dyn.chatter_display_active),
            "advisories": tuple(dyn.advisories),
        }, metadata={"provider_id": "assess-pump-function", "alarm_semantics": "partial"})

    def oxygenator(now: float, params: Mapping[str, Any]) -> FrozenObservation:
        if dynamic_patient is None:
            raise RuntimeError("oxygenator observation requires dynamic VA ECMO patient")
        dyn = dynamic_snapshot()
        console = dyn.true.volume_limited_ecmo.closed_loop.ecmo_state
        return FrozenObservation("assess-oxygenator", now, {
            "pre_oxygenator_pressure_mmhg": float(dyn.displayed.p2_mmhg),
            "post_oxygenator_pressure_mmhg": float(dyn.displayed.p3_mmhg),
            "delta_p_mmhg": float(dyn.displayed.p2_mmhg - dyn.displayed.p3_mmhg),
            "post_oxygenator_saturation": float(console.post_oxygenator_saturation),
            "post_oxygenator_po2_mmhg": float(console.post_oxygenator_po2_mmhg),
            "post_oxygenator_paco2_mmhg": float(console.post_oxygenator_paco2_mmhg),
        }, metadata={"provider_id": "assess-oxygenator", "failure_state_semantics": "not_implemented"})

    def sweep(now: float, params: Mapping[str, Any]) -> FrozenObservation:
        if dynamic_patient is None:
            raise RuntimeError("sweep observation requires dynamic VA ECMO patient")
        controls = dynamic_patient.coupled.controls
        return FrozenObservation("verify-sweep-gas", now, {
            "sweep_gas_flow_ml_min": float(controls.sweep_gas_flow_ml_min),
            "fdo2": float(controls.fdo2),
        }, metadata={"provider_id": "verify-sweep-gas", "gas_source_failure_state": "not_implemented"})

    def gas_exchange(now: float, params: Mapping[str, Any]) -> FrozenObservation:
        snap = patient_snapshot()
        values = {
            "patient_pao2_mmhg": float(snap.pao2_mmhg),
            "patient_paco2_mmhg": float(snap.paco2_mmhg),
            "patient_sao2_pct": float(snap.sao2_pct),
        }
        dyn = dynamic_snapshot()
        if dyn is not None:
            console = dyn.true.volume_limited_ecmo.closed_loop.ecmo_state
            values.update({
                "post_oxygenator_po2_mmhg": float(console.post_oxygenator_po2_mmhg),
                "post_oxygenator_paco2_mmhg": float(console.post_oxygenator_paco2_mmhg),
                "post_oxygenator_saturation": float(console.post_oxygenator_saturation),
            })
        return FrozenObservation("assess-gas-exchange", now, values,
                                 metadata={"provider_id": "assess-gas-exchange"})

    def renal_fluid(now: float, params: Mapping[str, Any]) -> FrozenObservation:
        snap = patient_snapshot()
        values = {
            "urine_ml_kg_hr": float(snap.urine_ml_kg_hr),
            "cumulative_urine_ml": float(snap.cumulative_urine_ml),
            "cumulative_net_body_fluid_ml": float(snap.cumulative_net_body_fluid_ml),
            "blood_volume_fraction": float(snap.blood_volume_fraction),
            "third_space_volume_ml": float(snap.third_space_volume_ml),
            "external_fluid_out_ml_min": float(patient.renal_therapy.external_fluid_out_ml_min),
        }
        if dynamic_patient is not None:
            controls = dynamic_patient.coupled.controls
            values.update({
                "ckrt_blood_flow_ml_min": float(controls.shunt_ckrt_blood_flow_ml_min),
                "ckrt_net_ultrafiltration_rate_ml_min": float(controls.shunt_ckrt_net_ultrafiltration_rate_ml_min),
            })
        return FrozenObservation("assess-renal-fluid", now, values,
                                 metadata={"provider_id": "assess-renal-fluid", "ckrt_semantics": "partial"})

    providers = (
        ("assess-hemodynamics", hemodynamics, False, "legacy action assess-hemodynamics"),
        ("assess-pump-function", pump_function, True, "legacy action assess-pump-function"),
        ("assess-oxygenator", oxygenator, True, "legacy action assess-oxygenator"),
        ("verify-sweep-gas", sweep, True, "legacy action verify-sweep-gas"),
        ("assess-gas-exchange", gas_exchange, False, "legacy action assess-gas-exchange"),
        ("assess-renal-fluid", renal_fluid, False, "legacy action assess-renal-fluid"),
    )
    for provider_id, provider, partial, capability_ref in providers:
        registry.register(
            ObservationDescriptor(
                provider_id=provider_id,
                description="Read authoritative simulator state without changing physiology.",
                capability_ref=capability_ref,
                partial=partial,
            ),
            provider,
        )
