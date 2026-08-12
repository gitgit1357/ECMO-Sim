from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from .core import SimulationResult


@dataclass(frozen=True)
class PressureVolumeLoop:
    chamber: str
    volume_ml: np.ndarray
    pressure_mmhg: np.ndarray
    time_s: np.ndarray


def extract_pressure_volume_loop(
    result: SimulationResult,
    chamber: Literal["LV", "RV"],
    heart_rate_bpm: float,
    beats: int = 3,
) -> PressureVolumeLoop:
    if beats <= 0:
        raise ValueError("beats must be positive")
    duration = beats * 60.0 / heart_rate_bpm
    start = max(0.0, result.time_s[-1] - duration)
    mask = result.time_s >= start
    return PressureVolumeLoop(
        chamber=chamber,
        volume_ml=result.node_series(chamber)[mask].copy(),
        pressure_mmhg=result.pressure_series(chamber)[mask].copy(),
        time_s=result.time_s[mask].copy(),
    )
