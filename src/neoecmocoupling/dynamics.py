from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Tuple

from neoecmo import EcmoConsoleControls

from .time_step import CoupledPatientEcmoSnapshot, CoupledVaEcmoPatient


@dataclass(frozen=True)
class DynamicResponseConfig:
    """Reduced-order monitor response and advisory timing.

    These values are simulator-behavior settings, not device specifications.
    True values remain available immediately; only the learner-facing display
    is smoothed. Advisory thresholds are isolated for scenario-specific tuning.
    """

    flow_display_time_constant_s: float = 15.0
    pressure_display_time_constant_s: float = 4.0
    oxygen_display_time_constant_s: float = 12.0
    co2_display_time_constant_s: float = 18.0
    chatter_activation_delay_s: float = 1.0
    chatter_clear_delay_s: float = 3.0
    low_preload_fraction: float = 0.75
    low_patient_flow_ml_kg_min: float = 80.0
    very_negative_p1_mmhg: float = -20.0

    def validate(self) -> None:
        for name in (
            "flow_display_time_constant_s",
            "pressure_display_time_constant_s",
            "oxygen_display_time_constant_s",
            "co2_display_time_constant_s",
        ):
            if getattr(self, name) <= 0.0:
                raise ValueError(f"{name} must be greater than zero")
        if self.chatter_activation_delay_s < 0.0 or self.chatter_clear_delay_s < 0.0:
            raise ValueError("chatter delays cannot be negative")
        if not 0.0 < self.low_preload_fraction <= 1.0:
            raise ValueError("low_preload_fraction must be greater than zero and at most one")
        if self.low_patient_flow_ml_kg_min < 0.0:
            raise ValueError("low_patient_flow_ml_kg_min cannot be negative")


@dataclass(frozen=True)
class DisplayedCoupledState:
    patient_flow_ml_min: float
    total_circuit_flow_ml_min: float
    map_mmhg: float
    p1_mmhg: float
    p2_mmhg: float
    p3_mmhg: float
    pao2_mmhg: float
    paco2_mmhg: float
    sao2_pct: float


@dataclass(frozen=True)
class DynamicCoupledSnapshot:
    elapsed_s: float
    true: CoupledPatientEcmoSnapshot
    displayed: DisplayedCoupledState
    chatter_display_active: bool
    advisories: Tuple[str, ...]


@dataclass
class _DisplayedMutable:
    patient_flow_ml_min: float
    total_circuit_flow_ml_min: float
    map_mmhg: float
    p1_mmhg: float
    p2_mmhg: float
    p3_mmhg: float
    pao2_mmhg: float
    paco2_mmhg: float
    sao2_pct: float


def _approach(current: float, target: float, dt_s: float, tau_s: float) -> float:
    if dt_s <= 0.0:
        return current
    alpha = 1.0 - math.exp(-dt_s / tau_s)
    return current + alpha * (target - current)


class DynamicCoupledVaEcmoPatient:
    """Adds display timing and consequence signals around the Stage-5 loop.

    The wrapped coordinator owns physiology. This class owns only elapsed
    simulation time, learner-display response, and non-destructive advisories.
    """

    def __init__(
        self,
        coupled: CoupledVaEcmoPatient,
        *,
        config: DynamicResponseConfig = DynamicResponseConfig(),
    ) -> None:
        config.validate()
        self.coupled = coupled
        self.config = config
        self.elapsed_s = 0.0
        initial = coupled.snapshot()
        self._displayed = self._from_true(initial)
        self._chatter_on_s = 0.0
        self._chatter_off_s = 0.0
        self._chatter_display_active = False
        self._last_true = initial

    def set_controls(self, controls: EcmoConsoleControls) -> None:
        self.coupled.set_controls(controls)

    @staticmethod
    def _from_true(snapshot: CoupledPatientEcmoSnapshot) -> _DisplayedMutable:
        circuit = snapshot.volume_limited_ecmo.closed_loop.ecmo_state.circuit
        return _DisplayedMutable(
            patient_flow_ml_min=snapshot.delivery.ecmo_return_flow_ml_min,
            total_circuit_flow_ml_min=circuit.solved_total_flow_ml_min,
            map_mmhg=snapshot.patient.map_mmhg,
            p1_mmhg=circuit.p1_mmhg,
            p2_mmhg=circuit.p2_mmhg,
            p3_mmhg=circuit.p3_mmhg,
            pao2_mmhg=snapshot.patient.pao2_mmhg,
            paco2_mmhg=snapshot.patient.paco2_mmhg,
            sao2_pct=snapshot.patient.sao2_pct,
        )

    def _update_display(self, true: CoupledPatientEcmoSnapshot, dt_s: float) -> None:
        target = self._from_true(true)
        d = self._displayed
        d.patient_flow_ml_min = _approach(d.patient_flow_ml_min, target.patient_flow_ml_min, dt_s, self.config.flow_display_time_constant_s)
        d.total_circuit_flow_ml_min = _approach(d.total_circuit_flow_ml_min, target.total_circuit_flow_ml_min, dt_s, self.config.flow_display_time_constant_s)
        d.map_mmhg = _approach(d.map_mmhg, target.map_mmhg, dt_s, self.config.pressure_display_time_constant_s)
        d.p1_mmhg = _approach(d.p1_mmhg, target.p1_mmhg, dt_s, self.config.pressure_display_time_constant_s)
        d.p2_mmhg = _approach(d.p2_mmhg, target.p2_mmhg, dt_s, self.config.pressure_display_time_constant_s)
        d.p3_mmhg = _approach(d.p3_mmhg, target.p3_mmhg, dt_s, self.config.pressure_display_time_constant_s)
        d.pao2_mmhg = _approach(d.pao2_mmhg, target.pao2_mmhg, dt_s, self.config.oxygen_display_time_constant_s)
        d.sao2_pct = _approach(d.sao2_pct, target.sao2_pct, dt_s, self.config.oxygen_display_time_constant_s)
        d.paco2_mmhg = _approach(d.paco2_mmhg, target.paco2_mmhg, dt_s, self.config.co2_display_time_constant_s)

    def _update_chatter_latch(self, true_active: bool, dt_s: float) -> None:
        if true_active:
            self._chatter_on_s += dt_s
            self._chatter_off_s = 0.0
            if self._chatter_on_s >= self.config.chatter_activation_delay_s:
                self._chatter_display_active = True
        else:
            self._chatter_off_s += dt_s
            self._chatter_on_s = 0.0
            if self._chatter_off_s >= self.config.chatter_clear_delay_s:
                self._chatter_display_active = False

    def _advisories(self, true: CoupledPatientEcmoSnapshot) -> Tuple[str, ...]:
        result = true.volume_limited_ecmo
        circuit = result.closed_loop.ecmo_state.circuit
        weight = max(self.coupled.patient.config.weight_kg, 1e-9)
        flow_index = true.delivery.ecmo_return_flow_ml_min / weight
        messages: list[str] = []
        if result.preload_fraction < self.config.low_preload_fraction:
            messages.append("LOW EFFECTIVE VENOUS VOLUME")
        if result.chatter_active:
            messages.append("DRAINAGE CHATTER")
        if self.coupled.controls.rpm > 0.0 and flow_index < self.config.low_patient_flow_ml_kg_min:
            messages.append("LOW PATIENT-DIRECTED ECMO FLOW")
        if circuit.p1_mmhg < self.config.very_negative_p1_mmhg:
            messages.append("EXCESSIVE NEGATIVE DRAINAGE PRESSURE")
        return tuple(messages)

    def snapshot(self) -> DynamicCoupledSnapshot:
        true = self.coupled.snapshot()
        self._last_true = true
        return self._snapshot_from(true)

    def advance(self, dt_s: float) -> DynamicCoupledSnapshot:
        if dt_s < 0.0:
            raise ValueError("dt_s cannot be negative")
        true = self.coupled.advance(dt_s / 60.0) if dt_s > 0.0 else self.coupled.snapshot()
        self.elapsed_s += dt_s
        self._update_display(true, dt_s)
        self._update_chatter_latch(true.volume_limited_ecmo.chatter_active, dt_s)
        self._last_true = true
        return self._snapshot_from(true)

    def _snapshot_from(self, true: CoupledPatientEcmoSnapshot) -> DynamicCoupledSnapshot:
        d = self._displayed
        return DynamicCoupledSnapshot(
            elapsed_s=self.elapsed_s,
            true=true,
            displayed=DisplayedCoupledState(
                patient_flow_ml_min=d.patient_flow_ml_min,
                total_circuit_flow_ml_min=d.total_circuit_flow_ml_min,
                map_mmhg=d.map_mmhg,
                p1_mmhg=d.p1_mmhg,
                p2_mmhg=d.p2_mmhg,
                p3_mmhg=d.p3_mmhg,
                pao2_mmhg=d.pao2_mmhg,
                paco2_mmhg=d.paco2_mmhg,
                sao2_pct=d.sao2_pct,
            ),
            chatter_display_active=self._chatter_display_active,
            advisories=self._advisories(true),
        )
