from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, Iterable, Mapping

import numpy as np

from .baseline import TARGETS, build_normal_term_neonate
from .core import CirculationModel, EdgeSpec, NodeSpec, periodic_elastance
from .metrics import BaselineMetrics, calculate_baseline_metrics


SYSTEMIC_RESISTANCE_EDGES = {
    "upper_arterial_bed", "lower_arterial_bed", "upper_bed_to_veins", "lower_bed_to_veins"
}
PULMONARY_RESISTANCE_EDGES = {
    "rpa_to_right_lung", "lpa_to_left_lung", "right_lung_to_rpv", "left_lung_to_lpv"
}
SYSTEMIC_ARTERIAL_NODES = {"AORTIC_ROOT", "AORTIC_ARCH", "UPPER_ARTERY", "LOWER_ARTERY"}


@dataclass(frozen=True)
class PatientModifiers:
    """Removable engineering inputs used to create a new model instance."""

    blood_volume_scale: float = 1.0
    systemic_resistance_scale: float = 1.0
    pulmonary_resistance_scale: float = 1.0
    systemic_arterial_compliance_scale: float = 1.0
    heart_rate_bpm: float = TARGETS.heart_rate_bpm
    lv_contractility_scale: float = 1.0
    rv_contractility_scale: float = 1.0
    external_pressure_offset_mmhg: float = 0.0

    def validate(self) -> None:
        for name, value in self.__dict__.items():
            if name == "external_pressure_offset_mmhg":
                continue
            if value <= 0:
                raise ValueError(f"{name} must be positive")


def _scaled_chamber(node: NodeSpec, modifiers: PatientModifiers) -> NodeSpec:
    if node.name not in {"RA", "RV", "LA", "LV"}:
        return node
    hr = modifiers.heart_rate_bpm
    if node.name == "RA":
        pressure_fn = periodic_elastance(hr, 0.18, 0.95, 2.0, 0.78, 0.20, 1.5 + modifiers.external_pressure_offset_mmhg)
    elif node.name == "RV":
        pressure_fn = periodic_elastance(hr, 0.16, 32.0 * modifiers.rv_contractility_scale, 1.0, 0.00, 0.38, 1.5 + modifiers.external_pressure_offset_mmhg, 0.30, 8.0, 2.0)
    elif node.name == "LA":
        pressure_fn = periodic_elastance(hr, 0.20, 1.05, 2.0, 0.78, 0.20, 1.5 + modifiers.external_pressure_offset_mmhg)
    else:
        pressure_fn = periodic_elastance(hr, 0.20, 76.0 * modifiers.lv_contractility_scale, 1.0, 0.00, 0.38, 1.5 + modifiers.external_pressure_offset_mmhg, 0.30, 8.0, 2.0)
    return replace(node, pressure_fn=pressure_fn)


def build_modified_neonate(modifiers: PatientModifiers) -> CirculationModel:
    """Build a fresh patient; no active model is mutated and no controller is installed."""
    modifiers.validate()
    base = build_normal_term_neonate()
    nodes = []
    for node in base.nodes.values():
        updated = _scaled_chamber(node, modifiers)
        if updated.name in SYSTEMIC_ARTERIAL_NODES and updated.compliance_ml_per_mmhg is not None:
            updated = replace(
                updated,
                compliance_ml_per_mmhg=updated.compliance_ml_per_mmhg * modifiers.systemic_arterial_compliance_scale,
            )
        elif updated.pressure_fn is None:
            updated = replace(updated, external_pressure_mmhg=updated.external_pressure_mmhg + modifiers.external_pressure_offset_mmhg)
        nodes.append(updated)

    edges = []
    for edge in base.edges:
        scale = 1.0
        if edge.name in SYSTEMIC_RESISTANCE_EDGES:
            scale *= modifiers.systemic_resistance_scale
        if edge.name in PULMONARY_RESISTANCE_EDGES:
            scale *= modifiers.pulmonary_resistance_scale
        source_scale = 1.0
        if edge.name == "aortic_valve":
            source_scale = 1.0 / (modifiers.lv_contractility_scale ** 2)
        elif edge.name == "pulmonary_valve":
            source_scale = 1.0 / (modifiers.rv_contractility_scale ** 2)
        edges.append(replace(
            edge,
            resistance_mmhg_s_per_ml=edge.resistance_mmhg_s_per_ml * scale,
            source_resistance_mmhg_s_per_ml=edge.source_resistance_mmhg_s_per_ml * source_scale,
        ))

    initial = {
        name: float(base.initial_volumes_ml[base.index[name]]) * modifiers.blood_volume_scale
        for name in base.node_order
    }
    return CirculationModel(nodes, edges, initial)


@dataclass(frozen=True)
class PerturbationReport:
    name: str
    modifiers: PatientModifiers
    metrics: BaselineMetrics


def run_perturbation_suite(duration_s: float = 30.0, sample_hz: float = 100.0) -> Mapping[str, PerturbationReport]:
    cases = {
        "baseline": PatientModifiers(),
        "hypovolemia_10pct": PatientModifiers(blood_volume_scale=0.90),
        "hypervolemia_10pct": PatientModifiers(blood_volume_scale=1.10),
        "svr_up_25pct": PatientModifiers(systemic_resistance_scale=1.25),
        "svr_down_25pct": PatientModifiers(systemic_resistance_scale=0.75),
        "pvr_up_50pct": PatientModifiers(pulmonary_resistance_scale=1.50),
        "lv_contractility_down_30pct": PatientModifiers(lv_contractility_scale=0.70),
        "rv_contractility_down_30pct": PatientModifiers(rv_contractility_scale=0.70),
        "tachycardia_160": PatientModifiers(heart_rate_bpm=160.0),
    }
    reports: Dict[str, PerturbationReport] = {}
    for name, modifiers in cases.items():
        model = build_modified_neonate(modifiers)
        result = model.simulate(duration_s=duration_s, sample_hz=sample_hz)
        metrics = calculate_baseline_metrics(result, modifiers.heart_rate_bpm)
        reports[name] = PerturbationReport(name, modifiers, metrics)
    return reports


def calculate_drift(result, tail_seconds: float = 10.0) -> Dict[str, float]:
    totals = np.sum(result.volumes_ml, axis=0)
    half = result.time_s[-1] / 2.0
    early = (result.time_s >= half - tail_seconds) & (result.time_s < half)
    late = result.time_s >= result.time_s[-1] - tail_seconds
    return {
        "total_volume_range_ml": float(np.max(totals) - np.min(totals)),
        "aortic_mean_shift_mmhg": float(np.mean(result.pressure_series("AORTIC_ROOT")[late]) - np.mean(result.pressure_series("AORTIC_ROOT")[early])),
        "ra_mean_shift_mmhg": float(np.mean(result.pressure_series("RA")[late]) - np.mean(result.pressure_series("RA")[early])),
        "lv_volume_mean_shift_ml": float(np.mean(result.node_series("LV")[late]) - np.mean(result.node_series("LV")[early])),
        "rv_volume_mean_shift_ml": float(np.mean(result.node_series("RV")[late]) - np.mean(result.node_series("RV")[early])),
    }
