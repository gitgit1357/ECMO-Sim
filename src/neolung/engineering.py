from __future__ import annotations
from dataclasses import dataclass
from .core import NeonatalLungModel
from .metrics import derive_lung_metrics


@dataclass(frozen=True)
class LungBenchCase:
    name: str
    changes: dict


def run_case(case: LungBenchCase, duration_s: float = 30.0):
    model = NeonatalLungModel().copy_with(**case.changes)
    return derive_lung_metrics(model.run(duration_s))


def default_bench_cases():
    return [
        LungBenchCase("baseline", {}),
        LungBenchCase("low_compliance", {"compliance_ml_per_cmh2o": 3.5}),
        LungBenchCase("high_airway_resistance", {"airway_resistance_cmh2o_s_per_l": 90.0}),
        LungBenchCase("tachypnea", {"respiratory_rate_bpm": 60.0}),
        LungBenchCase("reduced_effort", {"inspiratory_muscle_swing_cmh2o": 2.5}),
        LungBenchCase("peep_5", {"peep_cmh2o": 5.0}),
    ]
