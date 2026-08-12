from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class PressureControlSettings:
    """Deterministic pressure-control ventilator settings.

    This object owns only the ventilator pressure waveform and learner settings.
    Lung mechanics and gas exchange remain owned by ``neolung``.
    """

    pip_cmh2o: float = 18.0
    peep_cmh2o: float = 5.0
    rate_bpm: float = 40.0
    inspiratory_time_s: float = 0.35
    fio2: float = 0.21
    rise_time_s: float = 0.04
    fall_time_s: float = 0.04

    def __post_init__(self) -> None:
        values = {
            "pip_cmh2o": self.pip_cmh2o,
            "peep_cmh2o": self.peep_cmh2o,
            "rate_bpm": self.rate_bpm,
            "inspiratory_time_s": self.inspiratory_time_s,
            "fio2": self.fio2,
            "rise_time_s": self.rise_time_s,
            "fall_time_s": self.fall_time_s,
        }
        for name, value in values.items():
            if not math.isfinite(float(value)):
                raise ValueError(f"{name} must be finite")
        if self.pip_cmh2o < 0.0 or self.peep_cmh2o < 0.0:
            raise ValueError("PIP and PEEP must be non-negative")
        if self.pip_cmh2o < self.peep_cmh2o:
            raise ValueError("PIP must be greater than or equal to PEEP")
        if self.rate_bpm <= 0.0:
            raise ValueError("rate_bpm must be positive")
        if self.inspiratory_time_s <= 0.0:
            raise ValueError("inspiratory_time_s must be positive")
        if not 0.21 <= self.fio2 <= 1.0:
            raise ValueError("fio2 must be between 0.21 and 1.0")
        if self.rise_time_s < 0.0 or self.fall_time_s < 0.0:
            raise ValueError("rise_time_s and fall_time_s must be non-negative")
        if self.inspiratory_time_s >= self.cycle_s:
            raise ValueError("inspiratory_time_s must be shorter than the ventilator cycle")
        if self.rise_time_s + self.fall_time_s > self.inspiratory_time_s:
            raise ValueError("rise_time_s + fall_time_s cannot exceed inspiratory_time_s")

    @property
    def cycle_s(self) -> float:
        return 60.0 / self.rate_bpm

    @property
    def inspiratory_fraction(self) -> float:
        return self.inspiratory_time_s / self.cycle_s

    @property
    def expiratory_time_s(self) -> float:
        return self.cycle_s - self.inspiratory_time_s

    @property
    def ie_ratio_text(self) -> str:
        return f"1:{self.expiratory_time_s / self.inspiratory_time_s:.2f}"

    def airway_pressure(self, time_s: float) -> float:
        phase = float(time_s) % self.cycle_s
        if phase >= self.inspiratory_time_s:
            return self.peep_cmh2o

        drive = self.pip_cmh2o - self.peep_cmh2o
        if self.rise_time_s > 0.0 and phase < self.rise_time_s:
            return self.peep_cmh2o + drive * (phase / self.rise_time_s)

        remaining = self.inspiratory_time_s - phase
        if self.fall_time_s > 0.0 and remaining < self.fall_time_s:
            return self.peep_cmh2o + drive * (remaining / self.fall_time_s)

        return self.pip_cmh2o
