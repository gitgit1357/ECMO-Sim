from __future__ import annotations
from dataclasses import dataclass, replace

from .core import LungParameters, NeonatalLungModel
from .metrics import derive_lung_metrics
from .gas_exchange import GasExchangeParameters, GasExchangeResult, calculate_gas_exchange

@dataclass(frozen=True)
class StandalonePeepGasPoint:
    peep_cmh2o: float
    tidal_volume_ml: float
    alveolar_ventilation_ml_min: float
    effective_clearance_ventilation_ml_min: float
    pulmonary_perfusion_fraction: float
    pao2_mmhg: float
    paco2_mmhg: float

def _dynamic_metrics_without_static_peep_inflation(params: LungParameters):
    neutral = replace(params, peep_cmh2o=0.0, airway_opening_pressure_cmh2o=0.0)
    model = NeonatalLungModel(neutral)
    return derive_lung_metrics(model.run(15.0))

def run_standalone_peep_gas_point(
    peep_cmh2o: float,
    *,
    pulmonary_perfusion_fraction: float = 1.0,
    fio2: float = 0.21,
) -> StandalonePeepGasPoint:
    """Standalone lung/gas-exchange PEEP bench.

    PEEP can modestly improve effective alveolar ventilation by recruitment,
    but static PEEP inflation is not counted as tidal ventilation.
    Pulmonary perfusion is an explicit boundary input, not owned by the lung.
    """
    lp = LungParameters(peep_cmh2o=peep_cmh2o)
    mechanics = _dynamic_metrics_without_static_peep_inflation(lp)

    recruitment_scale = min(1.12, 1.0 + 0.012 * max(0.0, peep_cmh2o))
    gas = calculate_gas_exchange(
        mechanics,
        GasExchangeParameters(fio2=fio2),
        pulmonary_perfusion_fraction=pulmonary_perfusion_fraction,
        ventilation_scale=recruitment_scale,
    )
    return StandalonePeepGasPoint(
        peep_cmh2o=peep_cmh2o,
        tidal_volume_ml=gas.tidal_volume_ml,
        alveolar_ventilation_ml_min=gas.alveolar_ventilation_ml_min,
        effective_clearance_ventilation_ml_min=gas.effective_co2_clearance_ventilation_ml_min,
        pulmonary_perfusion_fraction=gas.pulmonary_perfusion_fraction,
        pao2_mmhg=gas.arterial_po2_mmhg,
        paco2_mmhg=gas.arterial_pco2_mmhg,
    )
