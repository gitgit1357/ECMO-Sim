from __future__ import annotations
from dataclasses import dataclass
from neokidney import KidneyParameters, KidneyState, calculate_kidney_state, RenalTherapyInputs, update_fluid_balance

@dataclass(frozen=True)
class RenalTherapyStep:
    renal_flow_ml_min: float
    urine_ml_kg_hr: float
    urine_ml_min: float
    net_fluid_ml_min: float
    cumulative_net_ml: float
    estimated_blood_volume_delta_ml: float

def run_renal_therapy_step(
    *,
    map_mmhg: float,
    cvp_mmhg: float,
    systemic_flow_ml_min: float,
    therapy: RenalTherapyInputs,
    cumulative_net_ml: float = 0.0,
    dt_min: float = 1.0,
    intravascular_fraction: float = 0.25,
) -> RenalTherapyStep:
    k = calculate_kidney_state(
        KidneyParameters(), KidneyState(),
        map_mmhg=map_mmhg,
        cvp_mmhg=cvp_mmhg,
        systemic_flow_ml_min=systemic_flow_ml_min,
        renal_vaso_tone=therapy.renal_vaso_tone,
        function_fraction=therapy.function_fraction,
        diuretic_multiplier=therapy.diuretic_multiplier,
        dt_s=dt_min*60.0,
    )
    fb = update_fluid_balance(
        cumulative_net_ml,
        fluid_in_ml_min=therapy.fluid_in_ml_min,
        external_fluid_out_ml_min=therapy.external_fluid_out_ml_min,
        urine_ml_min=k.urine_ml_min,
        dt_min=dt_min,
    )
    # Deliberately simple teaching approximation:
    # only a fraction of net body fluid immediately changes circulating blood volume.
    iv_delta = fb.cumulative_net_ml * max(0.0, min(1.0, intravascular_fraction))
    return RenalTherapyStep(
        renal_flow_ml_min=k.renal_flow_ml_min,
        urine_ml_kg_hr=k.urine_ml_kg_hr,
        urine_ml_min=k.urine_ml_min,
        net_fluid_ml_min=fb.net_fluid_ml_min,
        cumulative_net_ml=fb.cumulative_net_ml,
        estimated_blood_volume_delta_ml=iv_delta,
    )
