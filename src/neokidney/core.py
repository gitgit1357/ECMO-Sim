from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class KidneyParameters:
    weight_kg: float = 3.5
    baseline_map_mmhg: float = 52.0
    baseline_cvp_mmhg: float = 4.0
    baseline_renal_flow_ml_min: float = 55.0
    baseline_urine_ml_kg_hr: float = 2.0
    autoreg_low_mmhg: float = 40.0
    autoreg_high_mmhg: float = 70.0
    critical_perfusion_mmhg: float = 20.0

@dataclass
class KidneyState:
    cumulative_urine_ml: float = 0.0

@dataclass(frozen=True)
class KidneyResult:
    renal_flow_ml_min: float
    renal_flow_fraction_of_systemic: float
    renal_perfusion_pressure_mmhg: float
    filtration_index: float
    urine_ml_kg_hr: float
    urine_ml_min: float

def calculate_kidney_state(
    params: KidneyParameters,
    state: KidneyState,
    *,
    map_mmhg: float,
    cvp_mmhg: float,
    systemic_flow_ml_min: float,
    renal_vaso_tone: float = 1.0,
    function_fraction: float = 1.0,
    diuretic_multiplier: float = 1.0,
    circulating_volume_fraction: float = 1.0,
    dt_s: float = 1.0,
) -> KidneyResult:
    """Reduced-order neonatal renal teaching model.

    This is not a nephron model. It maps live perfusion, venous backpressure,
    vascular tone and global renal function into renal flow, filtration, and
    urine output with a simple autoregulatory plateau.
    """
    tone = max(0.4, min(2.5, renal_vaso_tone))
    perf = max(0.0, map_mmhg - cvp_mmhg)
    baseline_perf = params.baseline_map_mmhg - params.baseline_cvp_mmhg

    if map_mmhg < params.critical_perfusion_mmhg:
        pressure_factor = max(0.0, map_mmhg / params.critical_perfusion_mmhg) * 0.25
    elif map_mmhg < params.autoreg_low_mmhg:
        pressure_factor = 0.25 + 0.75 * (
            (map_mmhg - params.critical_perfusion_mmhg) /
            (params.autoreg_low_mmhg - params.critical_perfusion_mmhg)
        )
    elif map_mmhg <= params.autoreg_high_mmhg:
        pressure_factor = 1.0
    else:
        pressure_factor = 1.0 + min(0.25, 0.004 * (map_mmhg - params.autoreg_high_mmhg))

    target_flow = params.baseline_renal_flow_ml_min * pressure_factor / tone
    # Do not let a small-system approximation claim impossible renal flow.
    flow_cap = max(0.0, systemic_flow_ml_min * 0.16)
    renal_flow = min(target_flow, flow_cap)

    perf_index = max(0.0, min(1.5, perf / max(1e-6, baseline_perf)))
    flow_index = max(0.0, min(1.5, renal_flow / params.baseline_renal_flow_ml_min))
    filtration = max(0.0, min(1.5, perf_index * flow_index * max(0.0, function_fraction)))

    urine = params.baseline_urine_ml_kg_hr * (0.30 + 0.70 * filtration)
    if perf < 25.0:
        urine *= max(0.05, perf / 25.0)
    # Volume-depletion guardrail. This is intentionally simple and steep:
    # normal above ~90% baseline circulating volume, progressive oliguria below,
    # near-anuria with severe depletion. A diuretic cannot override absent perfusion.
    vf = max(0.0, min(1.5, circulating_volume_fraction))
    if vf >= 0.90:
        volume_modifier = 1.0
    elif vf >= 0.75:
        volume_modifier = 0.35 + 0.65 * ((vf - 0.75) / 0.15)
    elif vf >= 0.60:
        volume_modifier = 0.05 + 0.30 * ((vf - 0.60) / 0.15)
    else:
        volume_modifier = max(0.0, 0.05 * (vf / 0.60))

    # Perfusion/flow guardrails dominate pharmacologic stimulation.
    if perf_index < 0.35 or flow_index < 0.35:
        perfusion_guard = max(0.0, min(perf_index, flow_index) / 0.35)
    else:
        perfusion_guard = 1.0

    urine *= max(0.0, min(5.0, diuretic_multiplier))
    urine *= volume_modifier * perfusion_guard
    urine = max(0.0, urine)
    urine_ml_min = urine * params.weight_kg / 60.0
    state.cumulative_urine_ml += urine_ml_min * dt_s / 60.0

    frac = renal_flow / max(1e-6, systemic_flow_ml_min)
    return KidneyResult(
        renal_flow_ml_min=renal_flow,
        renal_flow_fraction_of_systemic=frac,
        renal_perfusion_pressure_mmhg=perf,
        filtration_index=filtration,
        urine_ml_kg_hr=urine,
        urine_ml_min=urine_ml_min,
    )
