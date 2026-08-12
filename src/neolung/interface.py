from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class LungToCirculationBoundary:
    """Read-only future coupling contract. No circulation import required."""
    pleural_pressure_cmh2o: float
    alveolar_pressure_cmh2o: float
    lung_volume_ml: float
    pulmonary_vascular_resistance_multiplier: float = 1.0


@dataclass(frozen=True)
class CirculationToLungBoundary:
    """Future inputs from circulation. Gas exchange intentionally not active yet."""
    pulmonary_blood_flow_ml_min: float
    pulmonary_arterial_pressure_mmHg: float
    pulmonary_venous_pressure_mmHg: float
