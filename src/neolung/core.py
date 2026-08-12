from __future__ import annotations

from dataclasses import dataclass, replace
from math import cos, pi
from typing import Callable, List


@dataclass(frozen=True)
class LungParameters:
    weight_kg: float = 3.5
    respiratory_rate_bpm: float = 40.0
    inspiratory_fraction: float = 0.35
    frc_ml: float = 105.0  # 30 mL/kg
    compliance_ml_per_cmh2o: float = 5.25  # 1.5 mL/kg/cmH2O
    airway_resistance_cmh2o_s_per_l: float = 45.0
    pleural_baseline_cmh2o: float = -5.0
    inspiratory_muscle_swing_cmh2o: float = 6.0
    airway_opening_pressure_cmh2o: float = 0.0
    peep_cmh2o: float = 0.0
    min_volume_ml: float = 45.0
    max_volume_ml: float = 180.0


@dataclass(frozen=True)
class LungState:
    time_s: float
    volume_ml: float


@dataclass(frozen=True)
class LungSample:
    time_s: float
    lung_volume_ml: float
    volume_above_frc_ml: float
    pleural_pressure_cmh2o: float
    alveolar_pressure_cmh2o: float
    airway_opening_pressure_cmh2o: float
    flow_ml_s: float
    transpulmonary_pressure_cmh2o: float


@dataclass(frozen=True)
class LungSimulationResult:
    samples: List[LungSample]
    parameters: LungParameters


class NeonatalLungModel:
    """Standalone single-compartment neonatal respiratory mechanics model.

    No circulation dependency. Gas exchange is intentionally absent in v0.6.0.
    """

    def __init__(self, params: LungParameters | None = None):
        self.params = params or LungParameters()
        self.state = LungState(time_s=0.0, volume_ml=self.params.frc_ml)
        # Choose a relaxed volume so baseline FRC is in equilibrium at Pao=0.
        self._relaxed_volume_ml = (
            self.params.frc_ml
            + self.params.compliance_ml_per_cmh2o * self.params.pleural_baseline_cmh2o
        )

    def copy_with(self, **changes) -> "NeonatalLungModel":
        return NeonatalLungModel(replace(self.params, **changes))

    def pleural_pressure(self, t: float) -> float:
        p = self.params
        cycle = 60.0 / p.respiratory_rate_bpm
        phase = (t % cycle) / cycle
        if phase < p.inspiratory_fraction:
            x = phase / p.inspiratory_fraction
            # Smooth negative muscle-pressure excursion: 0 -> max -> 0.
            muscle = -p.inspiratory_muscle_swing_cmh2o * 0.5 * (1.0 - cos(2.0 * pi * x))
        else:
            muscle = 0.0
        return p.pleural_baseline_cmh2o + muscle

    def sample(self, airway_opening_pressure_cmh2o: float | None = None) -> LungSample:
        p = self.params
        s = self.state
        ppl = self.pleural_pressure(s.time_s)
        elastic = (s.volume_ml - self._relaxed_volume_ml) / p.compliance_ml_per_cmh2o
        palv = ppl + elastic
        pao = (
            p.airway_opening_pressure_cmh2o + p.peep_cmh2o
            if airway_opening_pressure_cmh2o is None
            else airway_opening_pressure_cmh2o
        )
        resistance_cmh2o_s_per_ml = p.airway_resistance_cmh2o_s_per_l / 1000.0
        flow_ml_s = (pao - palv) / resistance_cmh2o_s_per_ml
        return LungSample(
            time_s=s.time_s,
            lung_volume_ml=s.volume_ml,
            volume_above_frc_ml=s.volume_ml - p.frc_ml,
            pleural_pressure_cmh2o=ppl,
            alveolar_pressure_cmh2o=palv,
            airway_opening_pressure_cmh2o=pao,
            flow_ml_s=flow_ml_s,
            transpulmonary_pressure_cmh2o=palv - ppl,
        )

    def step(self, dt_s: float, airway_opening_pressure_cmh2o: float | None = None) -> LungSample:
        current = self.sample(airway_opening_pressure_cmh2o)
        p = self.params
        new_volume = self.state.volume_ml + current.flow_ml_s * dt_s
        new_volume = max(p.min_volume_ml, min(p.max_volume_ml, new_volume))
        self.state = LungState(time_s=self.state.time_s + dt_s, volume_ml=new_volume)
        return self.sample(airway_opening_pressure_cmh2o)

    def run(
        self,
        duration_s: float,
        dt_s: float = 0.002,
        airway_pressure_fn: Callable[[float], float] | None = None,
    ) -> LungSimulationResult:
        samples: List[LungSample] = []
        n = int(duration_s / dt_s)
        for _ in range(n):
            pao = airway_pressure_fn(self.state.time_s) if airway_pressure_fn is not None else None
            samples.append(self.step(dt_s, airway_opening_pressure_cmh2o=pao))
        return LungSimulationResult(samples=samples, parameters=self.params)
