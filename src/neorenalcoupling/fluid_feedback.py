from __future__ import annotations
from dataclasses import dataclass
from neocirculation import build_normal_term_neonate,TARGETS,build_with_blood_volume_delta
from neocirculation.metrics import calculate_baseline_metrics
from neocoupling import run_coupled_neonate
from neokidney import KidneyParameters,KidneyState,RenalTherapyInputs,calculate_kidney_state,update_fluid_balance
@dataclass(frozen=True)
class FluidFeedbackResult:
    cumulative_net_body_fluid_ml: float; intravascular_delta_ml: float; total_blood_volume_ml: float
    map_mmhg: float; cvp_mmhg: float; cardiac_output_ml_min: float; renal_flow_ml_min: float; urine_ml_kg_hr: float
    pao2_mmhg: float|None=None; paco2_mmhg: float|None=None
def _balance(map_mmhg,cvp_mmhg,flow,therapy,duration_min):
    k=calculate_kidney_state(KidneyParameters(),KidneyState(),map_mmhg=map_mmhg,cvp_mmhg=cvp_mmhg,systemic_flow_ml_min=flow,renal_vaso_tone=therapy.renal_vaso_tone,function_fraction=therapy.function_fraction,diuretic_multiplier=therapy.diuretic_multiplier)
    fb=update_fluid_balance(0.0,fluid_in_ml_min=therapy.fluid_in_ml_min,external_fluid_out_ml_min=therapy.external_fluid_out_ml_min,urine_ml_min=k.urine_ml_min,dt_min=duration_min)
    return fb.cumulative_net_ml
def run_cv_fluid_feedback(therapy:RenalTherapyInputs,*,duration_min:float,intravascular_fraction:float=0.25):
    b=build_normal_term_neonate(); s=b.simulate(12.0,sample_hz=50.0); c0=calculate_baseline_metrics(s,TARGETS.heart_rate_bpm,tail_seconds=4.0)
    net=_balance(c0.mean_aortic_mmhg,c0.mean_ra_mmhg,c0.native_output_ml_min,therapy,duration_min); iv=net*max(0,min(1,intravascular_fraction))
    m=build_with_blood_volume_delta(build_normal_term_neonate(),iv); s=m.simulate(12.0,sample_hz=50.0); c=calculate_baseline_metrics(s,TARGETS.heart_rate_bpm,tail_seconds=4.0)
    k=calculate_kidney_state(KidneyParameters(),KidneyState(),map_mmhg=c.mean_aortic_mmhg,cvp_mmhg=c.mean_ra_mmhg,systemic_flow_ml_min=c.native_output_ml_min,renal_vaso_tone=therapy.renal_vaso_tone,function_fraction=therapy.function_fraction,diuretic_multiplier=therapy.diuretic_multiplier)
    return FluidFeedbackResult(net,iv,m.total_blood_volume_ml,c.mean_aortic_mmhg,c.mean_ra_mmhg,c.native_output_ml_min,k.renal_flow_ml_min,k.urine_ml_kg_hr)
def run_cvlung_fluid_feedback(therapy:RenalTherapyInputs,*,duration_min:float,intravascular_fraction:float=0.25,lung_params=None,gas_params=None):
    cp0=run_coupled_neonate(lung_params=lung_params,gas_params=gas_params,duration_lung_s=12.0,duration_circulation_s=12.0)
    c0=cp0.circulation_metrics; net=_balance(c0.mean_aortic_mmhg,c0.mean_ra_mmhg,c0.native_output_ml_min,therapy,duration_min); iv=net*max(0,min(1,intravascular_fraction))
    cp=run_coupled_neonate(lung_params=lung_params,gas_params=gas_params,duration_lung_s=12.0,duration_circulation_s=12.0,blood_volume_delta_ml=iv)
    c=cp.circulation_metrics
    k=calculate_kidney_state(KidneyParameters(),KidneyState(),map_mmhg=c.mean_aortic_mmhg,cvp_mmhg=c.mean_ra_mmhg,systemic_flow_ml_min=c.native_output_ml_min,renal_vaso_tone=therapy.renal_vaso_tone,function_fraction=therapy.function_fraction,diuretic_multiplier=therapy.diuretic_multiplier)
    return FluidFeedbackResult(net,iv,TARGETS.total_blood_volume_ml+iv,c.mean_aortic_mmhg,c.mean_ra_mmhg,c.native_output_ml_min,k.renal_flow_ml_min,k.urine_ml_kg_hr,cp.gas.arterial_po2_mmhg,cp.gas.arterial_pco2_mmhg)
