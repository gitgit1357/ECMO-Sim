from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class PatientArterialGasState:
    """Patient-side arterial blood after native and ECMO return streams mix.

    This is intentionally distinct from post-oxygenator blood.  It represents
    the blood available at the systemic perfusion site in the current reduced-
    order VA coupling stage.
    """

    pao2_mmhg: float
    paco2_mmhg: float
    sao2_pct: float
    oxygen_content_ml_dl: float
    oxygen_delivery_ml_min: float
    total_systemic_flow_ml_min: float
    ecmo_flow_fraction: float


def _sat_from_po2(po2_mmhg: float, p50_mmhg: float, hill_n: float) -> float:
    po2 = max(0.01, po2_mmhg)
    return po2**hill_n / (po2**hill_n + p50_mmhg**hill_n)


def _oxygen_content(po2_mmhg: float, saturation: float, hemoglobin_g_dl: float) -> float:
    return 1.34 * hemoglobin_g_dl * saturation + 0.003 * po2_mmhg


def _po2_from_content(
    content_ml_dl: float,
    hemoglobin_g_dl: float,
    *,
    p50_mmhg: float,
    hill_n: float,
    upper_po2_mmhg: float = 760.0,
) -> float:
    """Invert the reduced-order oxygen-content relation by bisection."""
    low, high = 0.01, max(1.0, upper_po2_mmhg)
    for _ in range(80):
        mid = (low + high) / 2.0
        sat = _sat_from_po2(mid, p50_mmhg, hill_n)
        content = _oxygen_content(mid, sat, hemoglobin_g_dl)
        if content < content_ml_dl:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def mix_native_and_ecmo_arterial_blood(
    *,
    native_flow_ml_min: float,
    native_pao2_mmhg: float,
    native_paco2_mmhg: float,
    ecmo_flow_ml_min: float,
    ecmo_return_po2_mmhg: float,
    ecmo_return_paco2_mmhg: float,
    hemoglobin_g_dl: float = 16.5,
    fetal_hb_p50_mmhg: float = 22.5,
    hill_coefficient: float = 2.7,
) -> PatientArterialGasState:
    """Mix native arterial and ECMO-return blood for Stage 2B.

    Oxygen is mixed by blood oxygen content rather than by directly averaging
    PO2.  CO2 is currently represented by a flow-weighted PCO2 mixture.  That
    reduced-order CO2 rule is deliberately simple: sweep controls the return
    PCO2, while ECMO blood flow controls how much of that treated blood reaches
    the patient.

    Native cardiac output is not yet reduced by ECMO drainage in this stage;
    that two-way preload interaction belongs to the later hydraulic coupling.
    """
    values = {
        "native_flow_ml_min": native_flow_ml_min,
        "native_pao2_mmhg": native_pao2_mmhg,
        "native_paco2_mmhg": native_paco2_mmhg,
        "ecmo_flow_ml_min": ecmo_flow_ml_min,
        "ecmo_return_po2_mmhg": ecmo_return_po2_mmhg,
        "ecmo_return_paco2_mmhg": ecmo_return_paco2_mmhg,
        "hemoglobin_g_dl": hemoglobin_g_dl,
    }
    for name, value in values.items():
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite")
    if native_flow_ml_min < 0 or ecmo_flow_ml_min < 0:
        raise ValueError("blood flows cannot be negative")
    if min(native_pao2_mmhg, native_paco2_mmhg, ecmo_return_po2_mmhg, ecmo_return_paco2_mmhg) < 0:
        raise ValueError("blood-gas values cannot be negative")
    if hemoglobin_g_dl <= 0:
        raise ValueError("hemoglobin_g_dl must be greater than zero")

    total_flow = native_flow_ml_min + ecmo_flow_ml_min
    if total_flow <= 0.0:
        return PatientArterialGasState(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    native_sat = _sat_from_po2(native_pao2_mmhg, fetal_hb_p50_mmhg, hill_coefficient)
    ecmo_sat = _sat_from_po2(ecmo_return_po2_mmhg, fetal_hb_p50_mmhg, hill_coefficient)
    native_content = _oxygen_content(native_pao2_mmhg, native_sat, hemoglobin_g_dl)
    ecmo_content = _oxygen_content(ecmo_return_po2_mmhg, ecmo_sat, hemoglobin_g_dl)

    mixed_content = (
        native_content * native_flow_ml_min + ecmo_content * ecmo_flow_ml_min
    ) / total_flow
    mixed_po2 = _po2_from_content(
        mixed_content,
        hemoglobin_g_dl,
        p50_mmhg=fetal_hb_p50_mmhg,
        hill_n=hill_coefficient,
    )
    mixed_sat = _sat_from_po2(mixed_po2, fetal_hb_p50_mmhg, hill_coefficient)

    mixed_pco2 = (
        native_paco2_mmhg * native_flow_ml_min
        + ecmo_return_paco2_mmhg * ecmo_flow_ml_min
    ) / total_flow
    oxygen_delivery = mixed_content * total_flow / 100.0

    return PatientArterialGasState(
        pao2_mmhg=mixed_po2,
        paco2_mmhg=mixed_pco2,
        sao2_pct=mixed_sat * 100.0,
        oxygen_content_ml_dl=mixed_content,
        oxygen_delivery_ml_min=oxygen_delivery,
        total_systemic_flow_ml_min=total_flow,
        ecmo_flow_fraction=ecmo_flow_ml_min / total_flow,
    )
