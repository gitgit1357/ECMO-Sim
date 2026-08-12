from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class RenalTherapyInputs:
    """Generic teaching-facing interventions.

    These are effect classes, not drug-specific PK/PD models.
    """
    fluid_in_ml_min: float = 0.0
    external_fluid_out_ml_min: float = 0.0
    diuretic_multiplier: float = 1.0
    renal_vaso_tone: float = 1.0
    function_fraction: float = 1.0

@dataclass(frozen=True)
class FluidBalanceResult:
    net_fluid_ml_min: float
    urine_ml_min: float
    cumulative_net_ml: float

def update_fluid_balance(
    cumulative_net_ml: float,
    *,
    fluid_in_ml_min: float,
    external_fluid_out_ml_min: float,
    urine_ml_min: float,
    dt_min: float,
) -> FluidBalanceResult:
    net = fluid_in_ml_min - external_fluid_out_ml_min - urine_ml_min
    return FluidBalanceResult(
        net_fluid_ml_min=net,
        urine_ml_min=urine_ml_min,
        cumulative_net_ml=cumulative_net_ml + net * dt_min,
    )
