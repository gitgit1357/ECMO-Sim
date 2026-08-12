from __future__ import annotations

from dataclasses import dataclass


def resistance_coefficient_from_datapoint(delta_p_mmhg: float, flow_ml_min: float) -> float:
    """
    Derive a quadratic resistance coefficient k (mmHg per (mL/min)^2) from
    a single measured pressure-drop-at-flow data point, assuming
    delta_p = k * Q^2. This is the standard way cannula hydraulics are
    calibrated in practice (manufacturer/bench nomograms), since cannulae
    are not straight pipes (see CannulaHydraulicParameters docstring).
    """
    if flow_ml_min <= 0.0:
        raise ValueError("flow_ml_min must be positive to derive a coefficient")
    return delta_p_mmhg / (flow_ml_min**2)


@dataclass(frozen=True)
class CannulaHydraulicParameters:
    """
    Empirical, replaceable cannula hydraulics.

    Unlike straight circuit tubing (see tubing_geometry.py, which uses
    Hagen-Poiseuille), ECMO cannulae are deliberately NOT modeled that way
    here. The field itself treats cannula pressure-flow behavior as an
    empirical, manufacturer-measured nomogram rather than a pipe-flow
    calculation, because side holes, tip geometry, and high local
    velocities through a narrow lumen make simple straight-tube laminar
    flow physically inapplicable (see e.g. the public ecmo-calculations
    project's own note that "it is more accurate to empirically measure
    the performance of each cannula" than to use Hagen-Poiseuille).

    delta_p = k * Q * |Q| (an orifice/turbulent-entrance-dominated model,
    signed to allow reversed flow), NOT delta_p = k * Q as tubing uses.

    STATUS: PROVISIONAL, LITERATURE-DERIVED — not your specific cannula
    make/model.

    RETURN_8FR default is derived from a published bench measurement of a
    Medtronic DLP 8-Fr pediatric ARTERIAL (single end-hole) cannula:
    approximately 600 mL/min at a 100 mmHg pressure drop (Performance
    Evaluation of Geometrically Different Pediatric Arterial Cannulae in a
    Pediatric Cardiopulmonary Bypass Model, PMC10655309), giving
    k = 100 / 600^2 = 2.778e-4 mmHg/(mL/min)^2. This is a reasonable
    stand-in for your 8-Fr return cannula since return cannulae are
    typically the same single-end-hole design as the arterial cannulae
    that study measured.

    DRAIN_10FR default is NOT directly measured for a multi-side-hole
    venous cannula — no venous-specific nomogram was available at build
    time. It reuses the same-size-class ARTERIAL bench figure from the
    same study (Medtronic DLP 10-Fr: approximately 1100 mL/min at 100 mmHg,
    k = 100 / 1100^2 = 8.264e-5) as a placeholder. This is very likely an
    OVERESTIMATE of true drain resistance: multi-side-hole venous
    cannulae generally have lower resistance than a single-end-hole
    arterial cannula of the same French size (more entry area, lower local
    entrance velocity per hole). Treat the drain-side number as a
    conservative upper bound until replaced with real manufacturer or
    bench data for your actual drain cannula.
    """

    quadratic_resistance_mmhg_per_ml_min2: float = 2.778e-4  # default: RETURN_8FR


RETURN_8FR = CannulaHydraulicParameters(quadratic_resistance_mmhg_per_ml_min2=2.778e-4)
DRAIN_10FR = CannulaHydraulicParameters(quadratic_resistance_mmhg_per_ml_min2=8.264e-5)


def cannula_delta_p_mmhg(
    flow_ml_min: float,
    params: CannulaHydraulicParameters = RETURN_8FR,
) -> float:
    """Pressure drop across a cannula at the given flow. Sign-preserving
    (reversed flow gives a negative/reversed pressure drop), consistent
    with how the other neoecmo branch modules handle direction."""
    k = params.quadratic_resistance_mmhg_per_ml_min2
    sign = 1.0 if flow_ml_min >= 0.0 else -1.0
    return sign * k * flow_ml_min**2
