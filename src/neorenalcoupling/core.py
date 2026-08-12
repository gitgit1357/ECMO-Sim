from __future__ import annotations
from dataclasses import dataclass, replace
from neocirculation import build_normal_term_neonate, TARGETS
from neocirculation.metrics import BaselineMetrics, calculate_baseline_metrics
from neocirculation.core import CirculationModel
from neocoupling import run_coupled_neonate
from neolung import LungParameters
from neolung.gas_exchange import GasExchangeParameters
from neokidney import KidneyParameters, KidneyState, KidneyResult, calculate_kidney_state

@dataclass(frozen=True)
class RenalCoupledResult:
    circulation_metrics: BaselineMetrics
    kidney: KidneyResult
    gas_pao2_mmhg: float | None = None
    gas_paco2_mmhg: float | None = None
    pvr_multiplier: float | None = None

def _renal_tone_adjusted_model(renal_vaso_tone: float) -> CirculationModel:
    """Apply only the kidney's weighted share of vascular-tone change.

    The current CV engine has lumped systemic beds. We therefore avoid
    pretending an explicit renal artery exists. A 10% renal vascular share
    modestly perturbs the lower systemic bed resistance while the kidney
    module separately calculates renal flow.
    """
    base = build_normal_term_neonate()
    renal_share = 0.10
    weighted = 1.0 + renal_share * (max(0.4, min(2.5, renal_vaso_tone)) - 1.0)
    edges = [
        replace(e, resistance_mmhg_s_per_ml=e.resistance_mmhg_s_per_ml * weighted)
        if e.name == "lower_arterial_bed" else e
        for e in base.edges
    ]
    initial = {name: float(base.initial_volumes_ml[base.index[name]]) for name in base.node_order}
    return CirculationModel(list(base.nodes.values()), edges, initial)

def run_cv_kidney(
    renal_vaso_tone: float = 1.0,
    function_fraction: float = 1.0,
    duration_s: float = 18.0,
) -> RenalCoupledResult:
    model = _renal_tone_adjusted_model(renal_vaso_tone)
    sim = model.simulate(duration_s, sample_hz=100.0)
    c = calculate_baseline_metrics(sim, TARGETS.heart_rate_bpm, tail_seconds=6.0)
    k = calculate_kidney_state(
        KidneyParameters(), KidneyState(),
        map_mmhg=c.mean_aortic_mmhg,
        cvp_mmhg=c.mean_ra_mmhg,
        systemic_flow_ml_min=c.native_output_ml_min,
        renal_vaso_tone=renal_vaso_tone,
        function_fraction=function_fraction,
    )
    return RenalCoupledResult(c, k)

def run_cvlung_kidney(
    renal_vaso_tone: float = 1.0,
    function_fraction: float = 1.0,
    lung_params: LungParameters | None = None,
    gas_params: GasExchangeParameters | None = None,
) -> RenalCoupledResult:
    # First obtain the live heart-lung state.
    cp = run_coupled_neonate(lung_params=lung_params, gas_params=gas_params)
    c = cp.circulation_metrics
    # Renal vaso-tone feeds back only as a small weighted systemic-resistance
    # perturbation. Re-run CV-only for that effect, then preserve the live
    # heart-lung PVR/respiratory state as observable context.
    if abs(renal_vaso_tone - 1.0) > 1e-9:
        cvk = run_cv_kidney(renal_vaso_tone=renal_vaso_tone, function_fraction=function_fraction)
        # Use the tone-adjusted MAP/flow while retaining lung gas state.
        c = cvk.circulation_metrics

    k = calculate_kidney_state(
        KidneyParameters(), KidneyState(),
        map_mmhg=c.mean_aortic_mmhg,
        cvp_mmhg=c.mean_ra_mmhg,
        systemic_flow_ml_min=c.native_output_ml_min,
        renal_vaso_tone=renal_vaso_tone,
        function_fraction=function_fraction,
    )
    return RenalCoupledResult(
        circulation_metrics=c,
        kidney=k,
        gas_pao2_mmhg=cp.gas.arterial_po2_mmhg,
        gas_paco2_mmhg=cp.gas.arterial_pco2_mmhg,
        pvr_multiplier=cp.pvr_multiplier,
    )
