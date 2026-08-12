from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import math
from typing import Deque, Dict, Iterable, Iterator, Mapping, Protocol

import numpy as np

from .core import SimulationResult


@dataclass(frozen=True)
class MonitorFrame:
    """Display-neutral snapshot exported by the circulation engine."""

    time_s: float
    values: Mapping[str, float]


class TelemetrySource(Protocol):
    """Minimal contract any temporary or production monitor can consume."""

    def frames(self) -> Iterable[MonitorFrame]: ...


class ResultTelemetryAdapter:
    """
    Converts a completed SimulationResult into display-neutral raw frames.

    The adapter is intentionally separate from the solver. Removing the demo
    monitor, or replacing it with the eventual simulator monitor, does not
    change circulation state or equations.
    """

    def __init__(self, result: SimulationResult, heart_rate_bpm: float) -> None:
        self.result = result
        self.heart_rate_bpm = float(heart_rate_bpm)

    def frames(self) -> Iterator[MonitorFrame]:
        p = {name: self.result.pressure_series(name) for name in self.result.node_order}
        q_ao = self.result.edge_flows_ml_s["aortic_valve"] * 60.0
        q_pv = self.result.edge_flows_ml_s["pulmonary_valve"] * 60.0
        for i, t in enumerate(self.result.time_s):
            yield MonitorFrame(
                time_s=float(t),
                values={
                    "heart_rate_bpm": self.heart_rate_bpm,
                    "aortic_pressure_mmhg": float(p["AORTIC_ROOT"][i]),
                    "pulmonary_pressure_mmhg": float(p["MPA"][i]),
                    "right_atrial_pressure_mmhg": float(p["RA"][i]),
                    "left_atrial_pressure_mmhg": float(p["LA"][i]),
                    "native_output_ml_min": float(q_ao[i]),
                    "pulmonary_output_ml_min": float(q_pv[i]),
                    "lv_volume_ml": float(self.result.node_series("LV")[i]),
                    "rv_volume_ml": float(self.result.node_series("RV")[i]),
                },
            )


@dataclass
class _SecondAccumulator:
    second_index: int
    count: int = 0
    aortic_min: float = math.inf
    aortic_max: float = -math.inf
    sums: Dict[str, float] | None = None

    def add(self, values: Mapping[str, float]) -> None:
        ao = float(values["aortic_pressure_mmhg"])
        self.aortic_min = min(self.aortic_min, ao)
        self.aortic_max = max(self.aortic_max, ao)
        if self.sums is None:
            self.sums = {}
        for key in (
            "heart_rate_bpm",
            "aortic_pressure_mmhg",
            "pulmonary_pressure_mmhg",
            "right_atrial_pressure_mmhg",
            "left_atrial_pressure_mmhg",
            "native_output_ml_min",
            "pulmonary_output_ml_min",
            "lv_volume_ml",
            "rv_volume_ml",
        ):
            self.sums[key] = self.sums.get(key, 0.0) + float(values[key])
        self.count += 1

    def finalize(self) -> Dict[str, float]:
        if self.count <= 0 or self.sums is None:
            raise ValueError("Cannot finalize an empty telemetry second")
        means = {key: total / self.count for key, total in self.sums.items()}
        systolic = self.aortic_max
        diastolic = self.aortic_min
        return {
            "display_heart_rate_bpm": means["heart_rate_bpm"],
            "arterial_systolic_mmhg": systolic,
            "arterial_diastolic_mmhg": diastolic,
            "map_mmhg": diastolic + (systolic - diastolic) / 3.0,
            "mean_pa_mmhg": means["pulmonary_pressure_mmhg"],
            "mean_ra_mmhg": means["right_atrial_pressure_mmhg"],
            "mean_la_mmhg": means["left_atrial_pressure_mmhg"],
            "display_native_output_ml_min": means["native_output_ml_min"],
            "display_pulmonary_output_ml_min": means["pulmonary_output_ml_min"],
            "display_lv_volume_ml": means["lv_volume_ml"],
            "display_rv_volume_ml": means["rv_volume_ml"],
        }


class RollingTelemetryAverager:
    """
    Adds bedside-style numeric values using completed one-second observations.

    Raw waveform values remain untouched in every frame. Numeric display values
    update only at one-second boundaries and are the arithmetic mean of the most
    recent `window_seconds` completed seconds. Once full, each new second drops
    the oldest second from the window.
    """

    def __init__(self, frames: Iterable[MonitorFrame], window_seconds: int = 15) -> None:
        if window_seconds < 1:
            raise ValueError("window_seconds must be at least 1")
        self._frames = iter(frames)
        self.window_seconds = int(window_seconds)
        self._seconds: Deque[Dict[str, float]] = deque(maxlen=self.window_seconds)
        self._current: _SecondAccumulator | None = None
        self._display_values: Dict[str, float] = {}

    @property
    def completed_seconds(self) -> int:
        return len(self._seconds)

    def _commit_current(self) -> None:
        if self._current is None or self._current.count == 0:
            return
        self._seconds.append(self._current.finalize())
        keys = self._seconds[0].keys()
        self._display_values = {
            key: sum(second[key] for second in self._seconds) / len(self._seconds)
            for key in keys
        }
        self._display_values["rolling_window_seconds"] = float(len(self._seconds))

    def frames(self) -> Iterator[MonitorFrame]:
        for frame in self._frames:
            second_index = int(math.floor(frame.time_s + 1e-9))
            if self._current is None:
                self._current = _SecondAccumulator(second_index)
            elif second_index != self._current.second_index:
                self._commit_current()
                self._current = _SecondAccumulator(second_index)

            self._current.add(frame.values)
            merged = dict(frame.values)
            merged.update(self._display_values)
            yield MonitorFrame(time_s=frame.time_s, values=merged)
