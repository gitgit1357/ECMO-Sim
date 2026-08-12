from __future__ import annotations

from dataclasses import dataclass, replace

from neoecmo import EcmoConsoleControls, EcmoConsoleState

from .closed_loop import ClosedLoopVaResult, VaMapCouplingConfig, solve_closed_loop_va_ecmo
from .contracts import PatientToEcmoState


@dataclass(frozen=True)
class PreloadDrainageConfig:
    """Reduced-order blood-volume and drainage-availability model.

    Values are behavioral placeholders isolated for later clinical tuning.
    The purpose is to preserve directionally correct interactions:
    hypovolemia lowers venous preload, limits sustainable drainage, makes P1
    more negative, and can create intermittent chatter at excessive RPM.
    """

    cvp_change_mmhg_per_volume_fraction: float = 18.0
    normal_drainage_capacity_ml_kg_min: float = 180.0
    minimum_drainage_capacity_fraction: float = 0.18
    capacity_volume_exponent: float = 2.2
    cvp_capacity_gain_per_mmhg: float = 0.025
    chatter_onset_ratio: float = 1.03
    severe_chatter_ratio: float = 1.35
    minimum_search_cvp_mmhg: float = -40.0
    maximum_search_iterations: int = 45
    flow_tolerance_ml_min: float = 0.5


@dataclass(frozen=True)
class VolumeLimitedVaResult:
    patient_boundary: PatientToEcmoState
    effective_patient_boundary: PatientToEcmoState
    closed_loop: ClosedLoopVaResult
    unconstrained_patient_flow_ml_min: float
    sustainable_drainage_flow_ml_min: float
    delivered_patient_flow_ml_min: float
    effective_venous_pressure_mmhg: float
    drainage_demand_ratio: float
    chatter_active: bool
    chatter_severity: float
    chatter_low_flow_ml_min: float
    chatter_high_flow_ml_min: float
    preload_fraction: float


def _preload_fraction(volume_fraction: float) -> float:
    # Preserve mild tolerance near normal volume but make depletion increasingly
    # consequential. The lower bound prevents numerical collapse.
    return min(1.20, max(0.10, volume_fraction))


def _effective_cvp(patient: PatientToEcmoState, config: PreloadDrainageConfig) -> float:
    return patient.venous_pressure_mmhg + config.cvp_change_mmhg_per_volume_fraction * (
        patient.blood_volume_fraction - 1.0
    )


def _drainage_capacity(patient: PatientToEcmoState, effective_cvp: float, config: PreloadDrainageConfig) -> float:
    vf = _preload_fraction(patient.blood_volume_fraction)
    volume_factor = max(config.minimum_drainage_capacity_fraction, vf ** config.capacity_volume_exponent)
    cvp_factor = max(0.35, 1.0 + config.cvp_capacity_gain_per_mmhg * (effective_cvp - 5.0))
    return patient.weight_kg * config.normal_drainage_capacity_ml_kg_min * volume_factor * cvp_factor


def solve_volume_limited_va_ecmo(
    controls: EcmoConsoleControls,
    patient: PatientToEcmoState,
    *,
    preload_config: PreloadDrainageConfig = PreloadDrainageConfig(),
    map_config: VaMapCouplingConfig = VaMapCouplingConfig(),
) -> VolumeLimitedVaResult:
    """Solve VA ECMO with blood-volume-dependent drainage limitation.

    The initial solve estimates pump demand against the volume-adjusted venous
    boundary. If demand exceeds sustainable venous drainage, the coupling
    layer lowers the effective inlet boundary until the hydraulic solve is
    close to the sustainable limit. The result reports chatter separately from
    the stable hydraulic state so later time-stepping can animate oscillation.
    """

    patient.validate()
    effective_cvp = _effective_cvp(patient, preload_config)
    volume_boundary = replace(patient, venous_pressure_mmhg=effective_cvp)
    unconstrained = solve_closed_loop_va_ecmo(controls, volume_boundary, config=map_config)
    demand = unconstrained.ecmo_state.circuit.solved_patient_flow_ml_min
    capacity = _drainage_capacity(patient, effective_cvp, preload_config)
    ratio = demand / max(capacity, 1e-9)

    final = unconstrained
    final_boundary = unconstrained.settled_patient_boundary

    if demand > capacity + preload_config.flow_tolerance_ml_min and controls.rpm > 0.0:
        high = effective_cvp
        low = preload_config.minimum_search_cvp_mmhg
        best = unconstrained
        for _ in range(preload_config.maximum_search_iterations):
            mid = (low + high) / 2.0
            candidate_boundary = replace(patient, venous_pressure_mmhg=mid)
            candidate = solve_closed_loop_va_ecmo(controls, candidate_boundary, config=map_config)
            q = candidate.ecmo_state.circuit.solved_patient_flow_ml_min
            best = candidate
            if abs(q - capacity) <= preload_config.flow_tolerance_ml_min:
                break
            if q > capacity:
                high = mid
            else:
                low = mid
        final = best
        final_boundary = best.settled_patient_boundary

    raw_delivered = final.ecmo_state.circuit.solved_patient_flow_ml_min
    delivered = min(raw_delivered, capacity) if controls.rpm > 0.0 else 0.0

    # When venous supply is the limiting element, preserve commanded RPM but
    # cap the patient branch at sustainable drainage. Shunt and bridge remain
    # circuit-owned recirculation branches. This is a reduced-order collapse
    # state; detailed transient pump/cannula dynamics remain future work.
    if delivered < raw_delivered - preload_config.flow_tolerance_ml_min:
        circuit = final.ecmo_state.circuit
        total = delivered + circuit.solved_shunt_flow_ml_min + circuit.solved_bridge_flow_ml_min
        denom = max(total, 1e-9)
        adjusted_circuit = replace(
            circuit,
            solved_total_flow_ml_min=total,
            solved_patient_flow_ml_min=delivered,
            shunt_fraction=circuit.solved_shunt_flow_ml_min / denom,
            bridge_fraction=circuit.solved_bridge_flow_ml_min / denom,
            patient_fraction=delivered / denom,
            p1_mmhg=min(circuit.p1_mmhg, final_boundary.venous_pressure_mmhg - 2.0),
        )
        adjusted_state = replace(final.ecmo_state, circuit=adjusted_circuit)
        support_fraction = delivered / max(demand, 1e-9)
        adjusted_map_support = final.map_support_mmhg * support_fraction
        adjusted_map = final.baseline_map_mmhg + adjusted_map_support
        adjusted_boundary = replace(final.settled_patient_boundary, arterial_pressure_mmhg=adjusted_map)
        final = replace(
            final,
            settled_patient_boundary=adjusted_boundary,
            ecmo_state=adjusted_state,
            settled_map_mmhg=adjusted_map,
            map_support_mmhg=adjusted_map_support,
            effective_systemic_flow_ml_min=patient.native_cardiac_output_ml_min + delivered,
        )
        final_boundary = adjusted_boundary

    chatter = ratio >= preload_config.chatter_onset_ratio and controls.rpm > 0.0
    severity = 0.0
    if chatter:
        span = max(preload_config.severe_chatter_ratio - preload_config.chatter_onset_ratio, 1e-9)
        severity = min(1.0, max(0.0, (ratio - preload_config.chatter_onset_ratio) / span))

    # Chatter is an intermittent drainage-collapse range, not a second source
    # of mean flow. A future dynamic layer can move between these bounds.
    high_flow = min(demand, max(delivered, capacity))
    low_fraction = 0.78 - 0.58 * severity if chatter else 1.0
    low_flow = max(0.0, high_flow * low_fraction)

    return VolumeLimitedVaResult(
        patient_boundary=patient,
        effective_patient_boundary=final_boundary,
        closed_loop=final,
        unconstrained_patient_flow_ml_min=demand,
        sustainable_drainage_flow_ml_min=capacity,
        delivered_patient_flow_ml_min=delivered,
        effective_venous_pressure_mmhg=final_boundary.venous_pressure_mmhg,
        drainage_demand_ratio=ratio,
        chatter_active=chatter,
        chatter_severity=severity,
        chatter_low_flow_ml_min=low_flow,
        chatter_high_flow_ml_min=high_flow,
        preload_fraction=_preload_fraction(patient.blood_volume_fraction),
    )
