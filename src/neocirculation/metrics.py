from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict

import numpy as np

from .core import SimulationResult


@dataclass(frozen=True)
class BaselineMetrics:
    heart_rate_bpm: float
    systolic_aortic_mmhg: float
    diastolic_aortic_mmhg: float
    mean_aortic_mmhg: float
    pulse_pressure_mmhg: float
    mean_ra_mmhg: float
    mean_pa_mmhg: float
    mean_la_mmhg: float
    native_output_ml_min: float
    pulmonary_output_ml_min: float
    total_volume_start_ml: float
    total_volume_end_ml: float
    conservation_error_ml: float

    def as_dict(self) -> Dict[str, float]:
        return asdict(self)


def _tail_mask(result: SimulationResult, tail_seconds: float) -> np.ndarray:
    start = max(result.time_s[-1] - tail_seconds, result.time_s[0])
    return result.time_s >= start


def calculate_baseline_metrics(
    result: SimulationResult,
    heart_rate_bpm: float,
    tail_seconds: float = 10.0,
) -> BaselineMetrics:
    mask = _tail_mask(result, tail_seconds)
    aorta = result.pressure_series("AORTIC_ROOT")[mask]
    ra = result.pressure_series("RA")[mask]
    pa = result.pressure_series("MPA")[mask]
    la = result.pressure_series("LA")[mask]
    q_ao = result.edge_flows_ml_s["aortic_valve"][mask]
    q_pv = result.edge_flows_ml_s["pulmonary_valve"][mask]
    start_total = float(np.sum(result.volumes_ml[:, 0]))
    end_total = float(np.sum(result.volumes_ml[:, -1]))
    return BaselineMetrics(
        heart_rate_bpm=heart_rate_bpm,
        systolic_aortic_mmhg=float(np.max(aorta)),
        diastolic_aortic_mmhg=float(np.min(aorta)),
        mean_aortic_mmhg=float(np.mean(aorta)),
        pulse_pressure_mmhg=float(np.max(aorta) - np.min(aorta)),
        mean_ra_mmhg=float(np.mean(ra)),
        mean_pa_mmhg=float(np.mean(pa)),
        mean_la_mmhg=float(np.mean(la)),
        native_output_ml_min=float(np.mean(q_ao) * 60.0),
        pulmonary_output_ml_min=float(np.mean(q_pv) * 60.0),
        total_volume_start_ml=start_total,
        total_volume_end_ml=end_total,
        conservation_error_ml=end_total - start_total,
    )
