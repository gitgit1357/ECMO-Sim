from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .cannulas import CannulaRecord


@dataclass(frozen=True)
class CannulaHydraulicPoint:
    size_fr: int
    flow_ml_kg_min: float
    flow_l_min: float
    drainage_cannula_loss_mmhg: float
    return_cannula_loss_mmhg: float
    patient_gradient_mmhg: float
    estimated_total_pump_head_mmhg: float
    within_manufacturer_anchor_range: bool


def overlay_cannula_hydraulics(
    circulation_points: Iterable[object],
    cannulas: Iterable[CannulaRecord],
) -> List[CannulaHydraulicPoint]:
    """Overlay external cannula pressure burden on circulation bench outputs.

    This function does not modify the circulation model. It consumes already
    calculated circulation bench points and estimates the external pressure head
    required to move the same flow through a paired drainage/return cannula set.
    """
    points: List[CannulaHydraulicPoint] = []
    for c in cannulas:
        max_anchor_flow = max(c.flow_l_min_at_plus_100_mmhg, c.flow_l_min_at_minus_40_mmhg)
        for p in circulation_points:
            flow_l_min = float(p.delivered_pump_flow_ml_min) / 1000.0
            loss = c.estimated_pressure_loss_mmhg(flow_l_min)
            # Patient-side static gradient that the pump must also overcome:
            # aortic return pressure minus venous drainage pressure.
            patient_gradient = max(float(p.mean_aortic_mmhg) - float(p.mean_ra_pressure_mmhg), 0.0)
            points.append(
                CannulaHydraulicPoint(
                    size_fr=c.size_fr,
                    flow_ml_kg_min=float(p.pump_flow_ml_kg_min),
                    flow_l_min=flow_l_min,
                    drainage_cannula_loss_mmhg=loss,
                    return_cannula_loss_mmhg=loss,
                    patient_gradient_mmhg=patient_gradient,
                    estimated_total_pump_head_mmhg=2.0 * loss + patient_gradient,
                    within_manufacturer_anchor_range=flow_l_min <= max_anchor_flow,
                )
            )
    return points


def format_cannula_overlay(points: Iterable[CannulaHydraulicPoint]) -> str:
    lines = [
        "EXTERNAL CANNULA HYDRAULIC OVERLAY — DOES NOT MODIFY PATIENT ENGINE",
        "Pressure losses are interpolation estimates from manufacturer water-bench anchors.",
        "Pump head estimate = drainage cannula loss + patient RA-to-aorta gradient + return cannula loss.",
        "",
        "Fr  Flow       L/min   Drain dP  Return dP  Patient dP  Total head  Anchor range",
        "    mL/kg/min          mmHg      mmHg       mmHg        mmHg",
    ]
    for p in points:
        lines.append(
            f"{p.size_fr:2d}  {p.flow_ml_kg_min:8.0f}  {p.flow_l_min:6.3f}  "
            f"{p.drainage_cannula_loss_mmhg:8.1f}  {p.return_cannula_loss_mmhg:9.1f}  "
            f"{p.patient_gradient_mmhg:10.1f}  {p.estimated_total_pump_head_mmhg:10.1f}  "
            f"{'yes' if p.within_manufacturer_anchor_range else 'EXTRAP'}"
        )
    return "\n".join(lines)
