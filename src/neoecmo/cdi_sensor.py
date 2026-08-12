from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .main_circuit_full import MainCircuitFullPoint


@dataclass(frozen=True)
class CDIReading:
    """A single simulated CDI (continuous blood gas monitor) reading on
    the drain limb, at its real confirmed position: downstream of the
    bridge tee, upstream of the shunt/transducer T (chat 2026-07-26 —
    patient -> 8" -> bridge tee -> 8" -> CDI -> 4" -> venous access
    pigtail -> 6" -> manifold -> 6" -> shunt/transducer T -> 4" -> pump).

    Because of that position, this reading is a flow-weighted mix of
    native patient venous blood and bridge recirculation ONLY. Shunt
    recirculation never reaches this sensor under normal forward flow —
    the shunt tee is downstream of the CDI — so shunt flow is deliberately
    NOT a parameter anywhere in this module. It would only matter here
    during genuine retrograde flow past the CDI, which is not modeled by
    this reduced-order sensor (a real abnormal-flow-direction case, not
    routine operation).
    """

    mixed_saturation: float
    recirculation_fraction: float  # fraction of what the CDI reads that is bridge recirculation, not native venous blood
    mixed_paco2_mmhg: Optional[float] = None


def cdi_mixed_saturation(
    patient_flow_ml_min: float,
    bridge_flow_ml_min: float,
    native_venous_saturation: float,
    post_oxygenator_saturation: float,
) -> float:
    """
    Flow-weighted O2 saturation the CDI would read: a blend of true
    native venous blood (patient_flow) and bridge-recirculated,
    near-post-oxygenator-saturation blood (bridge_flow). With the bridge
    closed (bridge_flow = 0) this reduces to exactly native_venous_saturation
    — the CDI reads true venous blood, per the confirmed anatomy.

    If total flow past the sensor is zero (a degenerate no-flow state),
    returns native_venous_saturation as the least-arbitrary fallback.
    """
    total_flow = patient_flow_ml_min + bridge_flow_ml_min
    if total_flow <= 0.0:
        return native_venous_saturation
    return (
        patient_flow_ml_min * native_venous_saturation
        + bridge_flow_ml_min * post_oxygenator_saturation
    ) / total_flow


def cdi_mixed_paco2_mmhg(
    patient_flow_ml_min: float,
    bridge_flow_ml_min: float,
    native_venous_paco2_mmhg: float,
    post_oxygenator_paco2_mmhg: float,
) -> float:
    """
    Flow-weighted pCO2 the CDI would read, same mixing logic as
    cdi_mixed_saturation. Mixing partial pressures directly (rather than
    CO2 content) is a simplification consistent with the same reduced-order
    level used throughout oxygenator_gas_exchange.py.
    """
    total_flow = patient_flow_ml_min + bridge_flow_ml_min
    if total_flow <= 0.0:
        return native_venous_paco2_mmhg
    return (
        patient_flow_ml_min * native_venous_paco2_mmhg
        + bridge_flow_ml_min * post_oxygenator_paco2_mmhg
    ) / total_flow


def recirculation_fraction(patient_flow_ml_min: float, bridge_flow_ml_min: float) -> float:
    """Fraction of flow past the CDI that is bridge recirculation rather
    than true native venous blood. Zero whenever the bridge is closed."""
    total_flow = patient_flow_ml_min + bridge_flow_ml_min
    if total_flow <= 0.0:
        return 0.0
    return bridge_flow_ml_min / total_flow


def cdi_reading_from_circuit_point(
    point: MainCircuitFullPoint,
    native_venous_saturation: float,
    post_oxygenator_saturation: float,
    native_venous_paco2_mmhg: Optional[float] = None,
    post_oxygenator_paco2_mmhg: Optional[float] = None,
) -> CDIReading:
    """
    Convenience wrapper: build a CDIReading directly from an already-solved
    MainCircuitFullPoint (using its solved_patient_flow_ml_min and
    solved_bridge_flow_ml_min — solved_shunt_flow_ml_min is deliberately
    never read here) plus the saturation/pCO2 values on either side of the
    mixing point.
    """
    mixed_sat = cdi_mixed_saturation(
        point.solved_patient_flow_ml_min,
        point.solved_bridge_flow_ml_min,
        native_venous_saturation,
        post_oxygenator_saturation,
    )
    recirc = recirculation_fraction(
        point.solved_patient_flow_ml_min, point.solved_bridge_flow_ml_min
    )
    mixed_paco2 = None
    if native_venous_paco2_mmhg is not None and post_oxygenator_paco2_mmhg is not None:
        mixed_paco2 = cdi_mixed_paco2_mmhg(
            point.solved_patient_flow_ml_min,
            point.solved_bridge_flow_ml_min,
            native_venous_paco2_mmhg,
            post_oxygenator_paco2_mmhg,
        )
    return CDIReading(
        mixed_saturation=mixed_sat,
        recirculation_fraction=recirc,
        mixed_paco2_mmhg=mixed_paco2,
    )
