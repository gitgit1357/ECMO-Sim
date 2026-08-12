from __future__ import annotations

from dataclasses import dataclass, replace

from neoecmo import EcmoConsoleControls, EcmoConsoleState

from .contracts import PatientToEcmoState
from .hydraulics import solve_ecmo_against_patient


@dataclass(frozen=True)
class VaMapCouplingConfig:
    """Reduced-order VA-ECMO arterial-pressure coupling.

    The gain is intentionally isolated and provisional. It represents the
    general increase in mean arterial pressure produced by patient-directed
    VA return flow at unchanged vascular tone. It is not a device-specific or
    patient-specific clinical target.
    """

    map_gain_mmhg_per_100_ml_kg_min: float = 5.0
    minimum_map_mmhg: float = 5.0
    maximum_map_mmhg: float = 100.0
    damping: float = 0.55
    convergence_tolerance_mmhg: float = 0.02
    maximum_iterations: int = 40
    baseline_pulse_pressure_mmhg: float = 24.0
    minimum_pulse_pressure_fraction: float = 0.30


@dataclass(frozen=True)
class ClosedLoopVaResult:
    initial_patient_boundary: PatientToEcmoState
    settled_patient_boundary: PatientToEcmoState
    ecmo_state: EcmoConsoleState
    baseline_map_mmhg: float
    settled_map_mmhg: float
    map_support_mmhg: float
    estimated_pulse_pressure_mmhg: float
    effective_systemic_flow_ml_min: float
    iterations: int
    converged: bool


def _map_from_patient_flow(
    *,
    baseline_map_mmhg: float,
    patient_flow_ml_min: float,
    weight_kg: float,
    config: VaMapCouplingConfig,
) -> float:
    flow_ml_kg_min = patient_flow_ml_min / max(weight_kg, 1e-9)
    support = config.map_gain_mmhg_per_100_ml_kg_min * flow_ml_kg_min / 100.0
    return min(max(baseline_map_mmhg + support, config.minimum_map_mmhg), config.maximum_map_mmhg)


def solve_closed_loop_va_ecmo(
    controls: EcmoConsoleControls,
    patient: PatientToEcmoState,
    *,
    config: VaMapCouplingConfig = VaMapCouplingConfig(),
) -> ClosedLoopVaResult:
    """Settle the two-way VA-ECMO flow/MAP relationship.

    Patient MAP acts as circuit return afterload. True patient-directed ECMO
    flow then supports MAP. Shunt and bridge flows are excluded because they
    never reach the patient. The solve iterates until MAP and circuit flow
    reach a stable reduced-order operating point.
    """

    patient.validate()
    if config.map_gain_mmhg_per_100_ml_kg_min < 0.0:
        raise ValueError("map gain cannot be negative")
    if not 0.0 < config.damping <= 1.0:
        raise ValueError("damping must be greater than 0 and at most 1")
    if config.maximum_iterations < 1:
        raise ValueError("maximum_iterations must be at least 1")

    baseline_map = patient.arterial_pressure_mmhg
    current_map = baseline_map
    converged = False
    state: EcmoConsoleState | None = None
    iterations = 0

    for iterations in range(1, config.maximum_iterations + 1):
        boundary = replace(patient, arterial_pressure_mmhg=current_map)
        hydraulic = solve_ecmo_against_patient(controls, boundary)
        state = hydraulic.ecmo_state
        target_map = _map_from_patient_flow(
            baseline_map_mmhg=baseline_map,
            patient_flow_ml_min=state.circuit.solved_patient_flow_ml_min,
            weight_kg=patient.weight_kg,
            config=config,
        )
        next_map = current_map + config.damping * (target_map - current_map)
        if abs(next_map - current_map) <= config.convergence_tolerance_mmhg:
            current_map = next_map
            converged = True
            break
        current_map = next_map

    settled_boundary = replace(patient, arterial_pressure_mmhg=current_map)
    final_hydraulic = solve_ecmo_against_patient(controls, settled_boundary)
    state = final_hydraulic.ecmo_state

    patient_flow = state.circuit.solved_patient_flow_ml_min
    effective_flow = patient.native_cardiac_output_ml_min + patient_flow
    native_fraction = patient.native_cardiac_output_ml_min / max(effective_flow, 1e-9)
    pulse_fraction = max(
        config.minimum_pulse_pressure_fraction,
        min(1.0, native_fraction),
    )
    pulse_pressure = config.baseline_pulse_pressure_mmhg * pulse_fraction

    return ClosedLoopVaResult(
        initial_patient_boundary=patient,
        settled_patient_boundary=settled_boundary,
        ecmo_state=state,
        baseline_map_mmhg=baseline_map,
        settled_map_mmhg=current_map,
        map_support_mmhg=current_map - baseline_map,
        estimated_pulse_pressure_mmhg=pulse_pressure,
        effective_systemic_flow_ml_min=effective_flow,
        iterations=iterations,
        converged=converged,
    )
