from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict

from .core import NeonatalLungModel
from .metrics import derive_lung_metrics
from .gas_exchange import GasExchangeParameters, GasExchangeResult, calculate_gas_exchange


@dataclass(frozen=True)
class GasBenchCase:
    name: str
    mechanics_changes: Dict[str, float]
    gas_changes: Dict[str, float]


def run_gas_case(case: GasBenchCase, duration_s: float = 30.0) -> GasExchangeResult:
    lung = NeonatalLungModel().copy_with(**case.mechanics_changes)
    mechanics = derive_lung_metrics(lung.run(duration_s))
    return calculate_gas_exchange(mechanics, GasExchangeParameters(), **case.gas_changes)


def default_gas_bench_cases() -> list[GasBenchCase]:
    return [
        GasBenchCase("normal_room_air", {}, {}),
        GasBenchCase("fio2_0_40", {}, {"fio2": 0.40}),
        GasBenchCase("fio2_1_00", {}, {"fio2": 1.00}),
        GasBenchCase("hypoventilation_low_effort", {"inspiratory_muscle_swing_cmh2o": 3.5}, {}),
        GasBenchCase("tachypnea_60", {"respiratory_rate_bpm": 60.0}, {}),
        GasBenchCase("high_dead_space", {}, {"alveolar_dead_space_fraction": 0.35}),
        GasBenchCase("high_vq_mismatch", {}, {"high_vq_fraction": 0.30}),
        GasBenchCase("low_vq_mismatch", {}, {"low_vq_fraction": 0.20}),
        GasBenchCase("shunt_10pct", {}, {"shunt_fraction": 0.10}),
        GasBenchCase("shunt_30pct", {}, {"shunt_fraction": 0.30}),
        GasBenchCase("diffusion_60pct", {}, {"diffusion_efficiency": 0.60}),
    ]
