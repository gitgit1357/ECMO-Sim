from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping

import numpy as np

from .core import CirculationModel, SimulationResult
from .engineering import PatientModifiers, build_modified_neonate
from .metrics import BaselineMetrics, calculate_baseline_metrics


@dataclass(frozen=True)
class FailureProfile:
    name: str
    metrics: BaselineMetrics
    lv_end_diastolic_proxy_ml: float
    rv_end_diastolic_proxy_ml: float
    lv_peak_volume_ml: float
    rv_peak_volume_ml: float


def _profile(name: str, result: SimulationResult, hr: float) -> FailureProfile:
    tail = result.time_s >= max(0.0, result.time_s[-1] - 10.0)
    lv = result.node_series("LV")[tail]
    rv = result.node_series("RV")[tail]
    return FailureProfile(
        name=name,
        metrics=calculate_baseline_metrics(result, hr),
        lv_end_diastolic_proxy_ml=float(np.percentile(lv, 95)),
        rv_end_diastolic_proxy_ml=float(np.percentile(rv, 95)),
        lv_peak_volume_ml=float(np.max(lv)),
        rv_peak_volume_ml=float(np.max(rv)),
    )


def run_failure_suite(duration_s: float = 30.0, sample_hz: float = 100.0) -> Mapping[str, FailureProfile]:
    cases = {
        "baseline": PatientModifiers(),
        "lv_moderate": PatientModifiers(lv_contractility_scale=0.30),
        "lv_severe": PatientModifiers(lv_contractility_scale=0.15),
        "rv_moderate": PatientModifiers(rv_contractility_scale=0.30),
        "rv_severe": PatientModifiers(rv_contractility_scale=0.15),
    }
    out: Dict[str, FailureProfile] = {}
    for name, modifiers in cases.items():
        model = build_modified_neonate(modifiers)
        result = model.simulate(duration_s, sample_hz)
        out[name] = _profile(name, result, modifiers.heart_rate_bpm)
    return out


def _model_with_initial_volumes(model: CirculationModel, volumes: Mapping[str, float]) -> CirculationModel:
    return CirculationModel(model.nodes.values(), model.edges, volumes)


def run_recovery_sequence(
    failure_side: str = "lv",
    failure_scale: float = 0.20,
    phase_s: float = 20.0,
    sample_hz: float = 100.0,
) -> Mapping[str, BaselineMetrics]:
    if failure_side not in {"lv", "rv"}:
        raise ValueError("failure_side must be 'lv' or 'rv'")

    base_mod = PatientModifiers()
    fail_mod = PatientModifiers(**{f"{failure_side}_contractility_scale": failure_scale})

    baseline_model = build_modified_neonate(base_mod)
    baseline_result = baseline_model.simulate(phase_s, sample_hz)
    initial_failure = {
        name: float(baseline_result.volumes_ml[baseline_result.node_order.index(name), -1])
        for name in baseline_result.node_order
    }

    failure_model = _model_with_initial_volumes(build_modified_neonate(fail_mod), initial_failure)
    failure_result = failure_model.simulate(phase_s, sample_hz)
    initial_recovery = {
        name: float(failure_result.volumes_ml[failure_result.node_order.index(name), -1])
        for name in failure_result.node_order
    }

    recovery_model = _model_with_initial_volumes(build_modified_neonate(base_mod), initial_recovery)
    recovery_result = recovery_model.simulate(phase_s * 2.0, sample_hz)

    return {
        "baseline": calculate_baseline_metrics(baseline_result, base_mod.heart_rate_bpm),
        "failure": calculate_baseline_metrics(failure_result, fail_mod.heart_rate_bpm),
        "recovery": calculate_baseline_metrics(recovery_result, base_mod.heart_rate_bpm),
    }
