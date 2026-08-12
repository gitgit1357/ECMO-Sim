from __future__ import annotations

import math
from dataclasses import dataclass

INCH_TO_M = 0.0254
FOOT_TO_M = 0.3048
DEFAULT_BLOOD_VISCOSITY_CP = 3.0  # literature-typical whole blood at 37C.
# Hemodiluted ECMO blood commonly runs somewhat lower (~2.5-3 cP); this is a
# reasonable default, not a patient-specific measured value. Callers who
# have an actual circuit hematocrit/viscosity can pass viscosity_cp
# explicitly to any function below.
DEFAULT_BLOOD_DENSITY_KG_M3 = 1060.0


def poiseuille_linear_resistance_mmhg_per_ml_min(
    inner_diameter_in: float,
    length_ft: float,
    viscosity_cp: float = DEFAULT_BLOOD_VISCOSITY_CP,
) -> float:
    """
    Hagen-Poiseuille linear (laminar-flow) resistance of a straight tube
    segment, in mmHg per mL/min:

        R = 8 * mu * L / (pi * r^4)      [SI: Pa / (m^3/s)]

    This returns ONLY the linear Poiseuille term. It does not include
    entrance/exit minor losses (e.g. the abrupt contraction where 3/8"
    tubing narrows into 1/16" shunt tubing) or any turbulent component —
    those are real but secondary effects at the flows this circuit sees
    (see reynolds_number below) and are deliberately left out to avoid
    over-fitting a reduced-order model with unmeasured loss coefficients.

    Valid only while flow stays laminar in that segment. Always confirm
    with reynolds_number() for the flow range you actually care about
    before trusting this as the sole resistance estimate.
    """
    radius_m = (inner_diameter_in * INCH_TO_M) / 2.0
    length_m = length_ft * FOOT_TO_M
    viscosity_pa_s = viscosity_cp * 0.001
    r_si = 8.0 * viscosity_pa_s * length_m / (math.pi * radius_m**4)  # Pa / (m^3/s)
    # 1 m^3/s = 6e7 mL/min ; 1 Pa = 0.00750062 mmHg
    return (r_si / 6.0e7) * 0.00750062


def reynolds_number(
    flow_ml_min: float,
    inner_diameter_in: float,
    viscosity_cp: float = DEFAULT_BLOOD_VISCOSITY_CP,
    blood_density_kg_m3: float = DEFAULT_BLOOD_DENSITY_KG_M3,
) -> float:
    """
    Reynolds number for flow through a straight tube of the given inner
    diameter. Re below roughly 2300 indicates laminar flow (Poiseuille
    valid); above that, turbulence is expected and the linear resistance
    above will under-predict the true pressure drop.
    """
    if flow_ml_min < 0.0:
        flow_ml_min = abs(flow_ml_min)
    diameter_m = inner_diameter_in * INCH_TO_M
    radius_m = diameter_m / 2.0
    area_m2 = math.pi * radius_m**2
    flow_m3_s = (flow_ml_min * 1e-6) / 60.0
    velocity_m_s = flow_m3_s / area_m2
    viscosity_pa_s = viscosity_cp * 0.001
    return blood_density_kg_m3 * velocity_m_s * diameter_m / viscosity_pa_s


@dataclass(frozen=True)
class MeasuredTubingSegment:
    inner_diameter_in: float
    length_ft: float


# Measured/reported directly by the clinical author (2026-07-25): 3/8"
# inner diameter for the main circuit and bridge tubing, 1/16" inner
# diameter for the fixed-shunt tubing (without the scuffing filter
# installed). Main circuit is 8 ft cannula-to-cannula in three segments;
# shunt and bridge are each about 1 ft. These lengths/diameters are
# measured facts, not provisional guesses — only the assumed blood
# viscosity above, and any component that isn't straight tubing (pump
# head, oxygenator fiber bundle, cannula tip geometry), remain provisional.
MEASURED_SEGMENTS = {
    "main_pre_pump": MeasuredTubingSegment(inner_diameter_in=0.375, length_ft=3.0),
    "main_pump_to_oxygenator": MeasuredTubingSegment(inner_diameter_in=0.375, length_ft=2.0),
    "main_return": MeasuredTubingSegment(inner_diameter_in=0.375, length_ft=3.0),
    "fixed_shunt_tubing": MeasuredTubingSegment(inner_diameter_in=0.0625, length_ft=1.0),
    "bridge_tubing": MeasuredTubingSegment(inner_diameter_in=0.375, length_ft=1.0),
}


def resistance_for_segment(
    segment_name: str, viscosity_cp: float = DEFAULT_BLOOD_VISCOSITY_CP
) -> float:
    """Convenience lookup: Poiseuille linear resistance for one of the
    named MEASURED_SEGMENTS, in mmHg per mL/min."""
    segment = MEASURED_SEGMENTS[segment_name]
    return poiseuille_linear_resistance_mmhg_per_ml_min(
        segment.inner_diameter_in, segment.length_ft, viscosity_cp
    )
