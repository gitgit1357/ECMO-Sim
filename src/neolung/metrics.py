from __future__ import annotations

from dataclasses import dataclass
from .core import LungSimulationResult


@dataclass(frozen=True)
class LungMetrics:
    respiratory_rate_bpm: float
    tidal_volume_ml: float
    tidal_volume_ml_per_kg: float
    minute_ventilation_ml_min: float
    peak_inspiratory_flow_ml_s: float
    peak_expiratory_flow_ml_s: float
    min_pleural_pressure_cmh2o: float
    mean_lung_volume_ml: float
    end_expiratory_volume_ml: float


def derive_lung_metrics(result: LungSimulationResult, window_s: float = 15.0) -> LungMetrics:
    samples = result.samples
    if not samples:
        raise ValueError("No lung samples")
    t_end = samples[-1].time_s
    selected = [s for s in samples if s.time_s >= max(0.0, t_end - window_s)]
    vols = [s.lung_volume_ml for s in selected]
    flows = [s.flow_ml_s for s in selected]
    ppls = [s.pleural_pressure_cmh2o for s in selected]
    vt = max(vols) - min(vols)
    rr = result.parameters.respiratory_rate_bpm
    return LungMetrics(
        respiratory_rate_bpm=rr,
        tidal_volume_ml=vt,
        tidal_volume_ml_per_kg=vt / result.parameters.weight_kg,
        minute_ventilation_ml_min=vt * rr,
        peak_inspiratory_flow_ml_s=max(flows),
        peak_expiratory_flow_ml_s=min(flows),
        min_pleural_pressure_cmh2o=min(ppls),
        mean_lung_volume_ml=sum(vols) / len(vols),
        end_expiratory_volume_ml=min(vols),
    )
