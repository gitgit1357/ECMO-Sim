from __future__ import annotations

from dataclasses import dataclass

# Confirmed sweep-gas hardware and practice (chat 2026-07-26): a Spectrum
# O2 blender fed by both medical air and O2, adjustable in 1% increments
# from 21% (room air, the physical floor — the blender cannot go lower)
# to 100% O2. The unit typically runs at 100% FdO2, but this is a real
# titratable control, not fixed — the same way ventilator FiO2 is
# titrated, per the "as close to real life as possible" governing rule.
MIN_FDO2 = 0.21
MAX_FDO2 = 1.00
FDO2_BLENDER_STEP = 0.01


def round_fdo2_to_blender_step(fdo2: float) -> float:
    """Snap an arbitrary fdo2 value to what the Spectrum blender can
    actually dial in: clamped to [0.21, 1.00] and rounded to the nearest
    1% increment. Useful for any future interface layer that lets a
    learner turn a blender dial rather than type an arbitrary float."""
    clamped = min(max(fdo2, MIN_FDO2), MAX_FDO2)
    return round(clamped / FDO2_BLENDER_STEP) * FDO2_BLENDER_STEP


@dataclass(frozen=True)
class OxygenatorGasExchangeParameters:
    """
    Gas transfer parameters for the Eurosets AMG PMP Infant oxygenator
    (the ECMO-cleared Eurosets pediatric/infant line, indicated for
    infants up to 20 kg — confirmed as the correct device family in chat
    2026-07-26, though its own detailed transfer curve is not publicly
    available).

    min_flow_ml_min is REAL and confirmed directly: 250 mL/min is the
    Eurosets AMG PMP Infant's stated minimum flow to prevent clot
    formation (chat 2026-07-26) — not a placeholder. This mirrors (and
    should stay consistent with) OxygenatorHydraulicParameters'
    min_recommended_flow_ml_min in oxygenator.py.

    rated_flow_ml_min is PROVISIONAL: grounded in a comparable neonatal
    oxygenator (Maquet Quadrox-i Neonatal), which is rated to 1.5 L/min
    and transfers ~90 mL O2/min and ~73 mL CO2/min at that flow with a
    high-FdO2 sweep, tapering to ~15 mL O2/min and ~10 mL CO2/min at 0.2
    L/min. This is a stand-in for the AMG PMP Infant's real rated flow
    and must be replaced once that specific number is available.

    obstruction_fraction represents the same physical clot/fouling state
    as OxygenatorHydraulicParameters.obstruction_fraction (oxygenator.py)
    — the same membrane, so the same real-world clot state should drive
    both, though this module keeps its own field rather than sharing a
    dataclass, consistent with how clot/obstruction state is handled
    independently per-component elsewhere in this package.

    fdo2 (fraction of sweep gas that is oxygen) defaults to 1.0 (pure O2),
    matching the clinical author's confirmed typical practice: a Spectrum
    O2 blender fed by both medical air and O2, normally run at 100% FdO2
    but adjustable in 1% increments from 21% (room air floor) to 100%
    (chat 2026-07-26) — a real titratable control, not fixed, the same
    way ventilator FiO2 is titrated. See round_fdo2_to_blender_step() for
    snapping an arbitrary value to what the blender can actually dial in.
    """

    rated_flow_ml_min: float = 1500.0
    min_flow_ml_min: float = 250.0
    obstruction_fraction: float = 0.0


def oxygenator_transfer_efficiency(
    blood_flow_ml_min: float,
    rated_flow_ml_min: float,
    obstruction_fraction: float = 0.0,
) -> float:
    """
    Reduced-order gas transfer efficiency (0-1): 1.0 while blood flow is
    at or below the (obstruction-reduced) rated flow, falling off as flow
    is pushed beyond what the membrane can fully transfer across — the
    "outpacing the oxygenator" phenomenon. This is a simple
    effective-rated-flow/actual-flow ratio, not a full membrane diffusion
    model, deliberately kept reduced-order per the same "clinically
    relevant, not over-engineered" standard used throughout this package.

    Clot/obstruction reduces the effective functioning membrane area,
    modeled as proportionally reducing the effective rated flow.
    """
    if blood_flow_ml_min <= 0.0:
        return 1.0
    obstruction = min(max(obstruction_fraction, 0.0), 0.99)
    effective_rated_flow = rated_flow_ml_min * (1.0 - obstruction)
    return min(1.0, effective_rated_flow / blood_flow_ml_min)


def outlet_o2_saturation(
    inlet_saturation: float,
    blood_flow_ml_min: float,
    fdo2: float = 1.0,
    params: OxygenatorGasExchangeParameters = OxygenatorGasExchangeParameters(),
) -> float:
    """Post-oxygenator O2 saturation (fraction 0-1).

    Saturation and PO2 are two views of the same modeled outlet oxygen state.
    The authoritative reduced-order transfer calculation is therefore the
    FdO2/efficiency-based outlet PO2 model below; saturation is derived from
    that PO2 through the matching Hill relationship.  This avoids the prior
    defect where independent saturation and PO2 approximations could report
    mutually inconsistent post-oxygenator values.
    """
    outlet_po2 = outlet_po2_mmhg(
        inlet_saturation,
        blood_flow_ml_min,
        fdo2,
        params,
    )
    return saturation_from_po2_mmhg(outlet_po2)


def po2_from_saturation_mmhg(
    saturation: float,
    *,
    p50_mmhg: float = 26.8,
    hill_coefficient: float = 2.7,
    max_po2_mmhg: float = 760.0,
) -> float:
    """Reduced-order conversion from O2 saturation to PO2.

    This gives the oxygenator an explicit outlet PO2 for post-oxy monitoring.
    It is intentionally bounded and is not a full neonatal dissociation model.
    Patient arterial PO2 remains a separate later mixing result.
    """
    sat = min(max(saturation, 0.0), 0.9999)
    if sat <= 0.0:
        return 0.0
    ratio = sat / max(1.0 - sat, 1e-9)
    po2 = p50_mmhg * (ratio ** (1.0 / hill_coefficient))
    return min(max(po2, 0.0), max_po2_mmhg)



def saturation_from_po2_mmhg(
    po2_mmhg: float,
    *,
    p50_mmhg: float = 26.8,
    hill_coefficient: float = 2.7,
) -> float:
    """Inverse of :func:`po2_from_saturation_mmhg` for model coherence.

    This is the same reduced-order Hill relationship used by the existing
    PO2-from-saturation helper. It is not a full neonatal/fetal-hemoglobin
    dissociation model; its role here is to keep the oxygenator's paired PO2
    and saturation outputs internally consistent.
    """
    po2 = max(float(po2_mmhg), 0.0)
    if po2 <= 0.0:
        return 0.0
    numerator = po2 ** hill_coefficient
    denominator = numerator + p50_mmhg ** hill_coefficient
    if denominator <= 0.0:
        return 0.0
    return min(max(numerator / denominator, 0.0), 0.9999)

def outlet_po2_mmhg(
    inlet_saturation: float,
    blood_flow_ml_min: float,
    fdo2: float = 1.0,
    params: OxygenatorGasExchangeParameters = OxygenatorGasExchangeParameters(),
    room_air_target_po2_mmhg: float = 100.0,
    pure_o2_target_po2_mmhg: float = 450.0,
) -> float:
    """Reduced-order explicit post-oxygenator PO2.

    PO2 cannot be recovered uniquely from a near-100% saturation because the
    dissociation curve is flat in the hyperoxic range.  Therefore this function
    uses FdO2 and membrane transfer efficiency to move inlet PO2 toward a
    provisional gas-side target.  The targets are intentionally isolated here
    for later device-specific validation.
    """
    inlet_po2 = po2_from_saturation_mmhg(inlet_saturation)
    resolved_fdo2 = min(max(fdo2, MIN_FDO2), MAX_FDO2)
    fdo2_fraction = (resolved_fdo2 - MIN_FDO2) / (MAX_FDO2 - MIN_FDO2)
    target_po2 = room_air_target_po2_mmhg + (pure_o2_target_po2_mmhg - room_air_target_po2_mmhg) * fdo2_fraction
    efficiency = oxygenator_transfer_efficiency(
        blood_flow_ml_min, params.rated_flow_ml_min, params.obstruction_fraction
    )
    if target_po2 <= inlet_po2:
        return inlet_po2
    return inlet_po2 + (target_po2 - inlet_po2) * efficiency

def co2_clearance_efficiency(
    sweep_gas_flow_ml_min: float,
    blood_flow_ml_min: float,
    obstruction_fraction: float = 0.0,
) -> float:
    """
    Reduced-order CO2 clearance efficiency (0-1), governed primarily by
    the sweep-gas-to-blood-flow ratio (the real clinical lever for CO2
    removal) rather than by blood flow alone: efficiency approaches 1.0
    once sweep flow reaches roughly the blood flow rate (a commonly cited
    1:1-2:1 sweep:blood ratio for adequate clearance), and falls off
    proportionally below that. Obstruction reduces effective sweep
    delivery the same way it reduces effective rated flow for O2.
    """
    if blood_flow_ml_min <= 0.0:
        return 1.0
    obstruction = min(max(obstruction_fraction, 0.0), 0.99)
    effective_sweep = max(sweep_gas_flow_ml_min, 0.0) * (1.0 - obstruction)
    return min(1.0, effective_sweep / blood_flow_ml_min)


def outlet_paco2_mmhg(
    inlet_paco2_mmhg: float,
    blood_flow_ml_min: float,
    sweep_gas_flow_ml_min: float,
    obstruction_fraction: float = 0.0,
    min_achievable_paco2_mmhg: float = 20.0,
) -> float:
    """
    Post-oxygenator pCO2 (mmHg). min_achievable_paco2_mmhg is a floor
    representing the lowest pCO2 the membrane could plausibly drive blood
    toward given unlimited sweep — not a claim about any specific
    patient's minimum safe or achievable value.
    """
    efficiency = co2_clearance_efficiency(
        sweep_gas_flow_ml_min, blood_flow_ml_min, obstruction_fraction
    )
    outlet = inlet_paco2_mmhg - (inlet_paco2_mmhg - min_achievable_paco2_mmhg) * efficiency
    return max(outlet, min_achievable_paco2_mmhg)
