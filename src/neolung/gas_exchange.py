from __future__ import annotations

from dataclasses import dataclass, replace
from math import log

from .metrics import LungMetrics


@dataclass(frozen=True)
class GasExchangeParameters:
    """Reduced-order standalone neonatal gas-exchange parameters.

    This module does not own cardiovascular physiology. Venous blood values are
    boundary inputs/placeholders until the circulation is coupled later.
    """

    weight_kg: float = 3.5
    fio2: float = 0.21
    barometric_pressure_mmhg: float = 760.0
    water_vapor_pressure_mmhg: float = 47.0
    oxygen_consumption_ml_kg_min: float = 6.0
    co2_production_ml_kg_min: float = 5.0
    anatomic_dead_space_ml_kg: float = 2.2
    alveolar_dead_space_fraction: float = 0.05
    high_vq_fraction: float = 0.0
    low_vq_fraction: float = 0.0
    shunt_fraction: float = 0.02
    diffusion_efficiency: float = 0.92
    hemoglobin_g_dl: float = 16.5
    fetal_hb_p50_mmhg: float = 22.5
    hill_coefficient: float = 2.7
    mixed_venous_po2_mmhg: float = 35.0
    mixed_venous_pco2_mmhg: float = 46.0

    @property
    def respiratory_quotient(self) -> float:
        vo2 = max(1e-6, self.oxygen_consumption_ml_kg_min)
        return self.co2_production_ml_kg_min / vo2


@dataclass(frozen=True)
class GasExchangeResult:
    fio2: float
    tidal_volume_ml: float
    respiratory_rate_bpm: float
    minute_ventilation_ml_min: float
    dead_space_ml: float
    alveolar_ventilation_ml_min: float
    effective_co2_clearance_ventilation_ml_min: float
    pulmonary_perfusion_fraction: float
    vo2_ml_min: float
    vco2_ml_min: float
    respiratory_quotient: float
    alveolar_po2_mmhg: float
    alveolar_pco2_mmhg: float
    end_capillary_po2_mmhg: float
    arterial_po2_mmhg: float
    arterial_pco2_mmhg: float
    arterial_saturation_pct: float
    end_capillary_saturation_pct: float
    mixed_venous_saturation_pct: float
    shunt_fraction: float
    diffusion_efficiency: float


def _sat_from_po2(po2_mmhg: float, p50_mmhg: float, hill_n: float) -> float:
    po2 = max(0.01, po2_mmhg)
    return (po2 ** hill_n) / (po2 ** hill_n + p50_mmhg ** hill_n)


def _po2_from_sat(sat: float, p50_mmhg: float, hill_n: float) -> float:
    s = min(0.9999, max(0.0001, sat))
    return p50_mmhg * (s / (1.0 - s)) ** (1.0 / hill_n)


def _oxygen_content_ml_dl(po2_mmhg: float, sat_fraction: float, hb_g_dl: float) -> float:
    return 1.34 * hb_g_dl * sat_fraction + 0.003 * po2_mmhg


def _sat_from_content(content_ml_dl: float, hb_g_dl: float) -> float:
    # Dissolved O2 is a very small component in the neonatal operating range;
    # this inversion is intentionally approximate for a reduced-order simulator.
    return min(0.9999, max(0.0001, content_ml_dl / max(1e-6, 1.34 * hb_g_dl)))



def effective_alveolar_clearance_capacity(
    alveolar_ventilation_ml_min: float,
    pulmonary_perfusion_fraction: float = 1.0,
    recruitment_scale: float = 1.0,
) -> tuple[float, float]:
    """Reduced-order ventilated-and-perfused alveolar capacity.

    Standalone lung/gas-exchange ownership:
    - ventilation determines available alveolar turnover,
    - pulmonary perfusion is a boundary input that determines how much of that
      ventilation is useful for blood-gas exchange,
    - recruitment_scale allows only a modest capped improvement from lung-state
      changes such as PEEP-related recruitment.

    Returns (effective_clearance_ventilation, perfusion_efficiency).
    """
    va = max(1.0, alveolar_ventilation_ml_min) * max(0.25, min(1.25, recruitment_scale))
    qfrac = max(0.05, min(1.5, pulmonary_perfusion_fraction))
    perfusion_efficiency = max(0.20, min(1.05, 0.25 + 0.75 * (qfrac ** 0.5)))
    return max(1.0, va * perfusion_efficiency), perfusion_efficiency


def calculate_gas_exchange(
    mechanics: LungMetrics,
    params: GasExchangeParameters | None = None,
    pulmonary_perfusion_fraction: float = 1.0,
    ventilation_scale: float = 1.0,
    **changes,
) -> GasExchangeResult:
    p = params or GasExchangeParameters()
    if changes:
        p = replace(p, **changes)

    vt = max(0.1, mechanics.tidal_volume_ml)
    rr = max(0.1, mechanics.respiratory_rate_bpm)
    minute_vent = vt * rr

    anatomic_dead = p.anatomic_dead_space_ml_kg * p.weight_kg
    effective_dead_fraction = max(0.0, p.alveolar_dead_space_fraction) + 0.70 * max(0.0, p.high_vq_fraction)
    effective_dead = min(vt * 0.95, anatomic_dead + vt * effective_dead_fraction)
    alveolar_vent = max(1.0, (vt - effective_dead) * rr)
    alveolar_vent *= max(0.25, min(2.0, ventilation_scale))

    vo2 = p.oxygen_consumption_ml_kg_min * p.weight_kg
    vco2 = p.co2_production_ml_kg_min * p.weight_kg
    rq = max(0.5, min(1.2, p.respiratory_quotient))

    # CO2 clearance requires both ventilated alveoli and pulmonary blood flow.
    # Poor pulmonary perfusion increases wasted/alveolar-dead-space ventilation.
    qfrac = max(0.05, min(1.5, pulmonary_perfusion_fraction))
    effective_co2_clearance_vent, perfusion_efficiency = effective_alveolar_clearance_capacity(
        alveolar_vent,
        pulmonary_perfusion_fraction=qfrac,
        recruitment_scale=1.0,
    )

    paco2 = 863.0 * vco2 / effective_co2_clearance_vent
    inspired_o2 = p.fio2 * (p.barometric_pressure_mmhg - p.water_vapor_pressure_mmhg)
    pao2 = max(0.0, inspired_o2 - paco2 / rq)

    # Diffusion/perfusion efficiency moves end-capillary gas toward alveolar gas
    # from the incoming mixed-venous boundary condition.
    diff = min(1.0, max(0.0, p.diffusion_efficiency))
    peco2 = p.mixed_venous_pco2_mmhg + diff * (paco2 - p.mixed_venous_pco2_mmhg)
    peco2 = max(5.0, peco2)
    pec_o2 = p.mixed_venous_po2_mmhg + diff * (pao2 - p.mixed_venous_po2_mmhg)
    pec_o2 = max(1.0, pec_o2)

    cap_sat = _sat_from_po2(pec_o2, p.fetal_hb_p50_mmhg, p.hill_coefficient)
    ven_sat = _sat_from_po2(p.mixed_venous_po2_mmhg, p.fetal_hb_p50_mmhg, p.hill_coefficient)
    cap_content = _oxygen_content_ml_dl(pec_o2, cap_sat, p.hemoglobin_g_dl)
    ven_content = _oxygen_content_ml_dl(p.mixed_venous_po2_mmhg, ven_sat, p.hemoglobin_g_dl)

    shunt = min(0.95, max(0.0, p.shunt_fraction) + 0.60 * max(0.0, p.low_vq_fraction))
    art_content = (1.0 - shunt) * cap_content + shunt * ven_content
    art_sat = _sat_from_content(art_content, p.hemoglobin_g_dl)
    art_po2 = min(pec_o2, _po2_from_sat(art_sat, p.fetal_hb_p50_mmhg, p.hill_coefficient))

    # CO2 content/PCO2 relation is approximated linearly for this first model.
    art_pco2 = (1.0 - shunt) * peco2 + shunt * p.mixed_venous_pco2_mmhg

    return GasExchangeResult(
        fio2=p.fio2,
        tidal_volume_ml=vt,
        respiratory_rate_bpm=rr,
        minute_ventilation_ml_min=minute_vent,
        dead_space_ml=effective_dead,
        alveolar_ventilation_ml_min=alveolar_vent,
        effective_co2_clearance_ventilation_ml_min=effective_co2_clearance_vent,
        pulmonary_perfusion_fraction=qfrac,
        vo2_ml_min=vo2,
        vco2_ml_min=vco2,
        respiratory_quotient=rq,
        alveolar_po2_mmhg=pao2,
        alveolar_pco2_mmhg=paco2,
        end_capillary_po2_mmhg=pec_o2,
        arterial_po2_mmhg=art_po2,
        arterial_pco2_mmhg=art_pco2,
        arterial_saturation_pct=art_sat * 100.0,
        end_capillary_saturation_pct=cap_sat * 100.0,
        mixed_venous_saturation_pct=ven_sat * 100.0,
        shunt_fraction=shunt,
        diffusion_efficiency=diff,
    )
