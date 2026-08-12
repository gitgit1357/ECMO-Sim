from __future__ import annotations

from dataclasses import dataclass, replace

from neoecmo import EcmoConsoleControls, ShuntLineConfiguration
from neopatient import UnifiedNeonatalPatient, UnifiedPatientSnapshot, VascularSupportPort

from .adapters import ecmo_delivery_from_console_state, patient_boundary_from_snapshot
from .closed_loop import VaMapCouplingConfig
from .contracts import EcmoToPatientState, PatientToEcmoState
from .preload import PreloadDrainageConfig, VolumeLimitedVaResult, solve_volume_limited_va_ecmo


@dataclass(frozen=True)
class TimeStepCouplingConfig:
    """Reduced-order time-step settings for a coupled VA-ECMO patient.

    This is deliberately behavioral rather than a beat-to-beat cardiovascular
    model. True patient-directed ECMO drainage can reduce native preload and
    native cardiac contribution, but the response is bounded and isolated for
    later scenario-specific tuning.
    """

    native_output_suppression_gain: float = 0.55
    minimum_native_output_fraction: float = 0.25
    native_output_convergence_tolerance: float = 0.002
    maximum_native_output_iterations: int = 12


@dataclass(frozen=True)
class CoupledPatientEcmoSnapshot:
    patient: UnifiedPatientSnapshot
    native_patient: UnifiedPatientSnapshot
    volume_limited_ecmo: VolumeLimitedVaResult
    delivery: EcmoToPatientState
    native_output_multiplier: float
    effective_systemic_flow_ml_min: float
    coupled_map_mmhg: float
    estimated_pulse_pressure_mmhg: float


def _native_output_multiplier(
    native_output_ml_min: float,
    ecmo_patient_flow_ml_min: float,
    config: TimeStepCouplingConfig,
) -> float:
    if ecmo_patient_flow_ml_min <= 0.0:
        return 1.0
    support_fraction = ecmo_patient_flow_ml_min / max(
        native_output_ml_min + ecmo_patient_flow_ml_min, 1e-9
    )
    multiplier = 1.0 - config.native_output_suppression_gain * support_fraction
    return min(1.0, max(config.minimum_native_output_fraction, multiplier))


class CoupledVaEcmoPatient:
    """Time-stepped coordinator for the modular patient and VA-ECMO circuit.

    The patient and circuit remain independently testable. This coordinator
    owns only their exchange, reduced-order native-output interaction, and the
    sequencing of renal/fluid feedback into the next circuit solve.
    """

    def __init__(
        self,
        patient: UnifiedNeonatalPatient,
        controls: EcmoConsoleControls = EcmoConsoleControls(),
        *,
        config: TimeStepCouplingConfig = TimeStepCouplingConfig(),
        preload_config: PreloadDrainageConfig = PreloadDrainageConfig(),
        map_config: VaMapCouplingConfig = VaMapCouplingConfig(),
    ) -> None:
        if not 0.0 <= config.native_output_suppression_gain <= 1.0:
            raise ValueError("native_output_suppression_gain must be between 0 and 1")
        if not 0.0 < config.minimum_native_output_fraction <= 1.0:
            raise ValueError("minimum_native_output_fraction must be greater than 0 and at most 1")
        self.patient = patient
        self.controls = controls
        self.config = config
        self.preload_config = preload_config
        self.map_config = map_config

    def set_controls(self, controls: EcmoConsoleControls) -> None:
        self.controls = controls

    def _solve_current(self) -> CoupledPatientEcmoSnapshot:
        native_snapshot = self.patient.snapshot(include_vascular_support=False)
        base_boundary = patient_boundary_from_snapshot(
            native_snapshot,
            weight_kg=self.patient.config.weight_kg,
        )
        baseline_native_output = base_boundary.native_cardiac_output_ml_min
        multiplier = 1.0
        result: VolumeLimitedVaResult | None = None

        for _ in range(self.config.maximum_native_output_iterations):
            boundary: PatientToEcmoState = replace(
                base_boundary,
                native_cardiac_output_ml_min=baseline_native_output * multiplier,
            )
            result = solve_volume_limited_va_ecmo(
                self.controls,
                boundary,
                preload_config=self.preload_config,
                map_config=self.map_config,
            )
            next_multiplier = _native_output_multiplier(
                baseline_native_output,
                result.delivered_patient_flow_ml_min,
                self.config,
            )
            if abs(next_multiplier - multiplier) <= self.config.native_output_convergence_tolerance:
                multiplier = next_multiplier
                break
            multiplier = next_multiplier

        assert result is not None
        # Final solve uses the converged native contribution.
        final_boundary = replace(
            base_boundary,
            native_cardiac_output_ml_min=baseline_native_output * multiplier,
        )
        result = solve_volume_limited_va_ecmo(
            self.controls,
            final_boundary,
            preload_config=self.preload_config,
            map_config=self.map_config,
        )
        ckrt_running = (
            self.controls.shunt_configuration == ShuntLineConfiguration.CKRT
            and self.controls.shunt_ckrt_blood_flow_ml_min > 0.0
        )
        external_removal = (
            max(0.0, self.controls.shunt_ckrt_net_ultrafiltration_rate_ml_min)
            if ckrt_running
            else 0.0
        )
        delivery = ecmo_delivery_from_console_state(
            result.closed_loop.ecmo_state,
            external_fluid_removal_ml_min=external_removal,
        )
        support_port = VascularSupportPort(
            enabled=delivery.enabled,
            support_flow_ml_min=delivery.ecmo_return_flow_ml_min,
            return_oxygen_saturation_pct=delivery.return_oxygen_saturation * 100.0,
            return_po2_mmhg=delivery.return_po2_mmhg,
            return_paco2_mmhg=delivery.return_paco2_mmhg,
            supported_map_mmhg=result.closed_loop.settled_map_mmhg if delivery.enabled else None,
            estimated_pulse_pressure_mmhg=(
                result.closed_loop.estimated_pulse_pressure_mmhg if delivery.enabled else None
            ),
            native_output_multiplier=multiplier if delivery.enabled else 1.0,
        )
        self.patient.set_vascular_support(support_port)
        patient_snapshot = self.patient.snapshot()
        effective_flow = (
            patient_snapshot.native_cardiac_output_ml_min
            + delivery.ecmo_return_flow_ml_min
        )
        return CoupledPatientEcmoSnapshot(
            patient=patient_snapshot,
            native_patient=native_snapshot,
            volume_limited_ecmo=result,
            delivery=delivery,
            native_output_multiplier=multiplier if delivery.enabled else 1.0,
            effective_systemic_flow_ml_min=effective_flow,
            coupled_map_mmhg=patient_snapshot.map_mmhg,
            estimated_pulse_pressure_mmhg=(
                patient_snapshot.systolic_mmhg - patient_snapshot.diastolic_mmhg
            ),
        )

    def snapshot(self) -> CoupledPatientEcmoSnapshot:
        return self._solve_current()

    def advance(self, dt_min: float) -> CoupledPatientEcmoSnapshot:
        if dt_min < 0.0:
            raise ValueError("dt_min cannot be negative")
        current = self._solve_current()
        if dt_min > 0.0:
            self.patient.advance(
                dt_min,
                additional_external_fluid_out_ml_min=current.delivery.external_fluid_removal_ml_min,
            )
        return self._solve_current()
