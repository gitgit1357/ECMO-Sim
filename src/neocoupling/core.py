from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite
from typing import Dict

import numpy as np

from neocirculation import build_normal_term_neonate, TARGETS, build_with_blood_volume_delta
from neocirculation.engineering import PatientModifiers, build_modified_neonate
from neocirculation.core import CirculationModel, EdgeSpec, NodeSpec
from neocirculation.metrics import BaselineMetrics, calculate_baseline_metrics
from neolung.core import LungParameters, NeonatalLungModel
from neolung.metrics import LungMetrics, derive_lung_metrics
from neolung.gas_exchange import GasExchangeParameters, GasExchangeResult, calculate_gas_exchange
from neolung.peep_gas_bench import _dynamic_metrics_without_static_peep_inflation
from neoventilator import PressureControlSettings

CMH2O_TO_MMHG = 0.735559


@dataclass(frozen=True)
class CouplingConfig:
    """Reduced-order cardiopulmonary coupling controls.

    Values are intentionally modest. The goal is clinically coherent teaching
    behavior, not a tissue-level digital twin.
    """

    reference_mean_pleural_cmh2o: float = -6.0
    reference_mean_lung_volume_ml: float = 105.0
    thoracic_pressure_gain: float = 1.0
    airway_to_pleural_transmission: float = 0.25
    lung_volume_pvr_gain: float = 0.75
    hypoxic_pvr_gain: float = 1.0
    hypoxic_threshold_pao2_mmhg: float = 60.0
    max_pvr_multiplier: float = 4.0
    iterations: int = 3


@dataclass(frozen=True)
class CoupledResult:
    lung_metrics: LungMetrics
    circulation_metrics: BaselineMetrics
    gas: GasExchangeResult
    pvr_multiplier: float
    pleural_delta_mmhg: float
    mixed_venous_po2_mmhg: float
    mixed_venous_saturation_pct: float
    mixed_venous_oxygen_content_ml_dl: float
    pulmonary_flow_ml_min: float
    arterial_oxygen_content_ml_dl: float
    systemic_oxygen_delivery_ml_min: float


def _mean_pleural(result, tail_s: float = 10.0) -> float:
    t_end = result.samples[-1].time_s
    vals = [s.pleural_pressure_cmh2o for s in result.samples if s.time_s >= t_end - tail_s]
    return float(sum(vals) / len(vals))


def _mean_airway(result, tail_s: float = 10.0) -> float:
    t_end = result.samples[-1].time_s
    vals = [s.airway_opening_pressure_cmh2o for s in result.samples if s.time_s >= t_end - tail_s]
    return float(sum(vals) / len(vals))


def _gas_exchange_mechanics(
    lung_params: LungParameters,
    actual_metrics: LungMetrics,
    pressure_control: PressureControlSettings | None = None,
) -> tuple[LungMetrics, float]:
    """Delegate PEEP/ventilation semantics to the standalone lung module."""
    if pressure_control is not None:
        recruitment_scale = min(1.12, 1.0 + 0.012 * max(0.0, pressure_control.peep_cmh2o))
        return actual_metrics, recruitment_scale
    if lung_params.peep_cmh2o <= 0.0 and lung_params.airway_opening_pressure_cmh2o <= 0.0:
        return actual_metrics, 1.0
    neutral_metrics = _dynamic_metrics_without_static_peep_inflation(lung_params)
    recruitment_scale = min(1.12, 1.0 + 0.012 * max(0.0, lung_params.peep_cmh2o))
    return neutral_metrics, recruitment_scale


def _sat_from_po2(po2: float, p50: float = 22.5, n: float = 2.7) -> float:
    p = max(0.01, po2)
    return p**n / (p**n + p50**n)


def _po2_from_sat(sat: float, p50: float = 22.5, n: float = 2.7) -> float:
    s = min(0.999, max(0.01, sat))
    return p50 * (s / (1.0 - s)) ** (1.0 / n)


def _derive_mixed_venous_po2(
    arterial_po2: float,
    arterial_sat_pct: float,
    hemoglobin_g_dl: float,
    oxygen_consumption_ml_min: float,
    systemic_flow_ml_min: float,
) -> tuple[float, float]:
    """Approximate mixed venous oxygen from Fick extraction.

    This is a deliberately compact bridge between flow and gas exchange.
    It does not attempt regional oxygen extraction or full blood chemistry.
    """
    q = max(50.0, systemic_flow_ml_min)
    sa = min(0.999, max(0.01, arterial_sat_pct / 100.0))
    ca = 1.34 * hemoglobin_g_dl * sa + 0.003 * arterial_po2
    extraction_ml_dl = oxygen_consumption_ml_min * 100.0 / q
    cv = max(1.0, ca - extraction_ml_dl)
    sv = min(0.99, max(0.05, cv / max(1e-6, 1.34 * hemoglobin_g_dl)))
    pv = _po2_from_sat(sv)
    return pv, sv * 100.0


def _coupled_circulation_model(
    pvr_multiplier: float,
    pleural_delta_mmhg: float,
    blood_volume_delta_ml: float = 0.0,
    lv_contractility_scale: float = 1.0,
    rv_contractility_scale: float = 1.0,
) -> CirculationModel:
    modified = build_modified_neonate(PatientModifiers(
        lv_contractility_scale=lv_contractility_scale,
        rv_contractility_scale=rv_contractility_scale,
    ))
    base = build_with_blood_volume_delta(modified, blood_volume_delta_ml)
    thoracic_nodes = {
        "RA", "RV", "MPA", "RPA", "LPA", "RIGHT_LUNG", "LEFT_LUNG",
        "RPV", "LPV", "LA", "LV",
    }
    nodes = []
    for node in base.nodes.values():
        if node.name in thoracic_nodes:
            if node.pressure_fn is not None:
                original_fn = node.pressure_fn
                delta = pleural_delta_mmhg
                def shifted(t, v, fn=original_fn, d=delta):
                    return fn(t, v) + d
                nodes.append(replace(node, pressure_fn=shifted))
            else:
                nodes.append(replace(node, external_pressure_mmhg=node.external_pressure_mmhg + pleural_delta_mmhg))
        else:
            nodes.append(node)

    pulmonary_resistance_edges = {
        "rpa_to_right_lung", "lpa_to_left_lung", "right_lung_to_rpv", "left_lung_to_lpv"
    }
    edges = [
        replace(e, resistance_mmhg_s_per_ml=e.resistance_mmhg_s_per_ml * pvr_multiplier)
        if e.name in pulmonary_resistance_edges else e
        for e in base.edges
    ]
    initial = {name: float(base.initial_volumes_ml[base.index[name]]) for name in base.node_order}
    return CirculationModel(nodes, edges, initial)


def run_coupled_neonate(
    lung_params: LungParameters | None = None,
    gas_params: GasExchangeParameters | None = None,
    config: CouplingConfig | None = None,
    duration_lung_s: float = 20.0,
    duration_circulation_s: float = 18.0,
    blood_volume_delta_ml: float = 0.0,
    pressure_control: PressureControlSettings | None = None,
    lv_contractility_scale: float = 1.0,
    rv_contractility_scale: float = 1.0,
) -> CoupledResult:
    cfg = config or CouplingConfig()
    lp = lung_params or LungParameters()
    gp = gas_params or GasExchangeParameters(weight_kg=lp.weight_kg)

    if pressure_control is not None:
        lp = replace(
            lp,
            respiratory_rate_bpm=pressure_control.rate_bpm,
            inspiratory_fraction=pressure_control.inspiratory_fraction,
            inspiratory_muscle_swing_cmh2o=0.0,
            peep_cmh2o=0.0,
            airway_opening_pressure_cmh2o=0.0,
        )
        gp = replace(gp, fio2=pressure_control.fio2)

    lung = NeonatalLungModel(lp)
    # Pressure-control metrics need a settled breath window. The standalone
    # ventilator NorthStar uses a trailing 15 s measurement window; ensure the
    # production solve has enough pre-window settling time without changing the
    # legacy/native duration requested by callers. Lung stepping is inexpensive
    # relative to the circulation equilibrium solve and remains cacheable.
    effective_lung_duration_s = max(duration_lung_s, 20.0) if pressure_control is not None else duration_lung_s
    lung_result = lung.run(
        effective_lung_duration_s,
        airway_pressure_fn=pressure_control.airway_pressure if pressure_control is not None else None,
    )
    lung_metrics = derive_lung_metrics(lung_result)
    gas_mechanics, peep_ventilation_scale = _gas_exchange_mechanics(lp, lung_metrics, pressure_control)
    mean_pleural = _mean_pleural(lung_result)
    transmitted_airway = max(0.0, _mean_airway(lung_result)) * cfg.airway_to_pleural_transmission
    pleural_delta = ((mean_pleural - cfg.reference_mean_pleural_cmh2o) + transmitted_airway) * CMH2O_TO_MMHG * cfg.thoracic_pressure_gain

    # Start with gas exchange using the placeholder venous condition, then
    # iterate flow -> venous extraction -> gas -> PVR a few times.
    venous_po2 = gp.mixed_venous_po2_mmhg
    venous_sat = _sat_from_po2(venous_po2) * 100.0
    pvr_mult = 1.0
    circ_metrics = None
    gas = None

    volume_ratio = (lung_metrics.mean_lung_volume_ml - cfg.reference_mean_lung_volume_ml) / max(1.0, cfg.reference_mean_lung_volume_ml)
    volume_pvr = 1.0 + cfg.lung_volume_pvr_gain * (volume_ratio ** 2)

    for _ in range(max(1, cfg.iterations)):
        model = _coupled_circulation_model(
            pvr_mult, pleural_delta, blood_volume_delta_ml,
            lv_contractility_scale=lv_contractility_scale,
            rv_contractility_scale=rv_contractility_scale,
        )
        result = model.simulate(duration_circulation_s, sample_hz=100.0)
        circ_metrics = calculate_baseline_metrics(result, TARGETS.heart_rate_bpm, tail_seconds=6.0)
        flow = max(50.0, circ_metrics.pulmonary_output_ml_min)

        pulmonary_flow_fraction = flow / max(1.0, TARGETS.systemic_flow_ml_s * 60.0)
        gas = calculate_gas_exchange(
            gas_mechanics,
            gp,
            pulmonary_perfusion_fraction=pulmonary_flow_fraction,
            ventilation_scale=peep_ventilation_scale,
            mixed_venous_po2_mmhg=venous_po2,
        )
        venous_po2, venous_sat = _derive_mixed_venous_po2(
            gas.arterial_po2_mmhg,
            gas.arterial_saturation_pct,
            gp.hemoglobin_g_dl,
            gas.vo2_ml_min,
            circ_metrics.native_output_ml_min,
        )

        hypoxic_fraction = max(0.0, (cfg.hypoxic_threshold_pao2_mmhg - gas.arterial_po2_mmhg) / cfg.hypoxic_threshold_pao2_mmhg)
        hypoxic_pvr = 1.0 + cfg.hypoxic_pvr_gain * hypoxic_fraction
        pvr_mult = min(cfg.max_pvr_multiplier, max(0.5, volume_pvr * hypoxic_pvr))

    assert circ_metrics is not None and gas is not None
    # Final gas calculation uses the iterated venous boundary.
    final_flow_fraction = max(0.05, circ_metrics.pulmonary_output_ml_min / max(1.0, TARGETS.systemic_flow_ml_s * 60.0))
    gas = calculate_gas_exchange(
        gas_mechanics,
        gp,
        pulmonary_perfusion_fraction=final_flow_fraction,
        ventilation_scale=peep_ventilation_scale,
        mixed_venous_po2_mmhg=venous_po2,
    )
    sa = gas.arterial_saturation_pct / 100.0
    ca = 1.34 * gp.hemoglobin_g_dl * sa + 0.003 * gas.arterial_po2_mmhg
    do2 = ca * circ_metrics.native_output_ml_min / 100.0
    sv = min(0.999, max(0.0, venous_sat / 100.0))
    cv = 1.34 * gp.hemoglobin_g_dl * sv + 0.003 * venous_po2
    return CoupledResult(
        lung_metrics=lung_metrics,
        circulation_metrics=circ_metrics,
        gas=gas,
        pvr_multiplier=pvr_mult,
        pleural_delta_mmhg=pleural_delta,
        mixed_venous_po2_mmhg=venous_po2,
        mixed_venous_saturation_pct=venous_sat,
        mixed_venous_oxygen_content_ml_dl=cv,
        pulmonary_flow_ml_min=circ_metrics.pulmonary_output_ml_min,
        arterial_oxygen_content_ml_dl=ca,
        systemic_oxygen_delivery_ml_min=do2,
    )
