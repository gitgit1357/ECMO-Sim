from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum


class ShuntLineConfiguration(Enum):
    """
    The shunt line has two stopcocks (confirmed anatomy, chat 2026-07-26).
    Exactly one of these configurations applies at a time — they are
    mutually exclusive by physical construction, not just convention:

    OPEN: the two stopcocks are connected directly to each other. Normal
    ECMO-pump-driven shunt flow, no filter, no CKRT.

    HEMOFILTER: the two stopcocks are disconnected from each other, and
    the scuffing hemofilter is placed inline between them instead. Blood
    still flows through this branch continuously, still driven by the
    ECMO pump/circuit pressure — the filter just adds substantial
    resistance in series (handoff section 19).

    CKRT: each stopcock is a 3-WAY stopcock, not a simple on/off valve —
    the main shunt flow path continues to pass straight through it
    unaffected, while a side port on each stopcock accepts a CKRT
    machine's own pigtail (drain pigtail to the upstream/first-encountered
    stopcock, return pigtail to the downstream one). Attaching CKRT does
    NOT interrupt, redirect, or share the shunt's own ECMO-driven flow —
    the shunt keeps flowing exactly as it would with nothing attached
    (same as OPEN — no built-in filter is present in this configuration
    either, since HEMOFILTER and CKRT are alternate uses of the same two
    stopcock positions). CKRT draws its own separate blood flow via its
    own independent pump from the side port; that flow does not come out
    of, reduce, or otherwise interact with the shunt's own flow in this
    reduced-order model (confirmed directly, chat 2026-07-26 — CKRT "does
    not use the total blood volume flowing through the shunt line"). See
    ckrt_blood_flow_ml_min below.
    """

    OPEN = "open"
    HEMOFILTER = "hemofilter"
    CKRT = "ckrt"


@dataclass(frozen=True)
class FixedShuntParameters:
    """
    Provisional, replaceable fixed-shunt branch parameters (handoff
    sections 18-19).

    The fixed shunt is always completely open (in the OPEN configuration),
    not learner-adjustable, and has no dedicated flow probe (its flow can
    only ever be derived from other measurements, never measured directly)
    — none of that display/derivation logic belongs in this module; this
    module only owns the branch's own hydraulics.

    STATUS: PARTIALLY GROUNDED. tubing_resistance_linear_mmhg_per_ml_min
    below is derived from measured geometry (1/16" ID, ~1 ft shunt tubing
    without anything installed — see tubing_geometry.py
    MEASURED_SEGMENTS["fixed_shunt_tubing"]) via Hagen-Poiseuille, not
    guessed. tubing_resistance_quad_mmhg_per_ml_min2 is left at 0.0: a
    Reynolds-number check (tubing_geometry.reynolds_number) confirms the
    shunt stays laminar across every flow it should realistically ever
    carry, so the pure linear Poiseuille term is the physically correct
    model here, not an approximation of one. The filter resistance terms
    remain fully provisional — no scuffing-filter make/model is locked
    (handoff section 32) and a filter is not straight tubing, so
    Poiseuille does not apply to it. clot_fraction reuses the same
    reduced-order 1/(1-clot_fraction)^2 shape used elsewhere in this
    package, and only applies to the OPEN/HEMOFILTER tubing itself (a
    CKRT machine's own circuit is not modeled here at all).

    ckrt_blood_flow_ml_min is informational/tracked only when
    configuration is CKRT — it represents the CKRT machine's own
    independent pump flow, drawn via a 3-way stopcock's side port. The
    CKRT machine is blood-primed on initiation, so connecting it never
    steals a volume bolus from the ECMO circuit at start-up. During
    operation it does pull some (not all) of the blood flowing through
    the shunt line, but returns that same volume minus only the amount
    intentionally removed (net ultrafiltration — see
    ckrt_net_ultrafiltration_rate_ml_min below), which is typically small
    relative to blood flow. This module does not compute or constrain
    CKRT's own blood flow (that's the CKRT device's own prescription/
    settings) and does not adjust fixed_shunt_flow_ml_min's result for
    it — the net effect on shunt hydraulics is treated as negligible at
    this reduced-order stage, consistent with the confirmed clinical
    description (chat 2026-07-26).

    ckrt_net_ultrafiltration_rate_ml_min is the CKRT machine's own net
    fluid removal rate — structurally the same concept as the built-in
    hemofilter's ultrafiltration_rate_ml_min, just via a different
    mechanism/pump. See step_filtrate_removal below, which now handles
    both HEMOFILTER and CKRT net removal.
    """

    tubing_resistance_linear_mmhg_per_ml_min: float = 0.733309
    tubing_resistance_quad_mmhg_per_ml_min2: float = 0.0
    clot_fraction: float = 0.0  # 0 = clean, approaches 1 = fully occluded

    configuration: ShuntLineConfiguration = ShuntLineConfiguration.OPEN

    filter_resistance_linear_mmhg_per_ml_min: float = 0.03
    filter_resistance_quad_mmhg_per_ml_min2: float = 0.00002
    scuffing_active: bool = False  # only meaningful when configuration == HEMOFILTER
    ultrafiltration_rate_ml_min: float = 10.0  # only applies while scuffing_active AND HEMOFILTER

    ckrt_blood_flow_ml_min: float = 0.0  # only meaningful when configuration == CKRT; not used in hydraulics
    ckrt_net_ultrafiltration_rate_ml_min: float = 0.0  # CKRT's own net fluid removal rate; only meaningful when configuration == CKRT


def _combined_resistance_terms(params: FixedShuntParameters) -> tuple[float, float]:
    """Tubing resistance, plus filter resistance if the HEMOFILTER
    configuration is active, both scaled by clot_fraction. Fluid-removal
    state (scuffing_active) does NOT change resistance — the filter's
    presence is what adds resistance, not its activity. CKRT adds no
    resistance term here either (its pigtails tap a side port rather than
    occupying the inline path), so CKRT resolves to the same bare tubing
    resistance as OPEN."""
    clot = min(max(params.clot_fraction, 0.0), 0.99)
    multiplier = 1.0 / (1.0 - clot) ** 2

    lin = params.tubing_resistance_linear_mmhg_per_ml_min
    quad = params.tubing_resistance_quad_mmhg_per_ml_min2
    if params.configuration == ShuntLineConfiguration.HEMOFILTER:
        lin += params.filter_resistance_linear_mmhg_per_ml_min
        quad += params.filter_resistance_quad_mmhg_per_ml_min2
    return lin * multiplier, quad * multiplier


def _solve_signed_quadratic_flow(delta_p_mmhg: float, r_lin: float, r_quad: float) -> float:
    """
    Solve delta_p = r_lin * Q + r_quad * Q * |Q| for Q, preserving the sign
    of delta_p (i.e. flow runs from high pressure to low pressure, in
    whichever direction that is — the shunt has no check valve).
    """
    if delta_p_mmhg == 0.0:
        return 0.0
    sign = 1.0 if delta_p_mmhg > 0.0 else -1.0
    magnitude = abs(delta_p_mmhg)
    if r_quad == 0.0:
        q_mag = magnitude / r_lin
    else:
        q_mag = (-r_lin + (r_lin**2 + 4.0 * r_quad * magnitude) ** 0.5) / (2.0 * r_quad)
    return sign * q_mag


def fixed_shunt_flow_ml_min(
    upstream_pressure_mmhg: float,
    downstream_pressure_mmhg: float,
    params: FixedShuntParameters = FixedShuntParameters(),
) -> float:
    """
    ECMO-pump-driven flow through the fixed shunt branch given the
    pressure at its two ends.

    CKRT does NOT change this calculation at all: the stopcocks are
    3-way, so the main shunt flow continues to pass straight through
    exactly as in OPEN (no filter resistance either, since HEMOFILTER and
    CKRT are alternate uses of the same two stopcock positions — only one
    of them can have something occupying the inline path at a time, and
    CKRT's pigtails tap a side port rather than occupying it). CKRT's own
    independent pump flow is tracked separately (ckrt_blood_flow_ml_min)
    and never enters this function's calculation.

    Positive result: flow runs upstream -> downstream (the normal
    post-oxygenator -> pre-pump direction). Negative result is a valid
    reversed-flow state, not an error, since this branch is passive
    tubing with no valve.
    """
    r_lin, r_quad = _combined_resistance_terms(params)
    delta_p = upstream_pressure_mmhg - downstream_pressure_mmhg
    return _solve_signed_quadratic_flow(delta_p, r_lin, r_quad)


@dataclass(frozen=True)
class ScuffingFiltrationState:
    """Cumulative net fluid removed from the patient via whichever
    fluid-removal mechanism is currently in use on the shunt line: the
    built-in scuffing hemofilter (HEMOFILTER configuration), or a CKRT
    machine's own net ultrafiltration (CKRT configuration). Independent
    of shunt blood flow — this stage models removal as a simple rate
    constant, not a transmembrane-pressure-derived or solute-clearance
    model (handoff section 19: the filter "does not own full CKRT solute
    clearance"; CKRT's own solute clearance math is a real CKRT device's
    own concern, not modeled by this package at all — only its net fluid
    removal rate is tracked)."""

    cumulative_filtrate_volume_ml: float = 0.0


def step_filtrate_removal(
    state: ScuffingFiltrationState,
    dt_s: float,
    params: FixedShuntParameters = FixedShuntParameters(),
) -> ScuffingFiltrationState:
    """
    Advance cumulative net fluid removed.

    HEMOFILTER: requires scuffing_active — activity alone (with the
    filter not actually in place) removes nothing. Uses
    ultrafiltration_rate_ml_min.

    CKRT: removal happens whenever the CKRT machine is actually running
    (ckrt_blood_flow_ml_min > 0 — a stopped/unplugged machine draws no
    flow and removes nothing). Uses ckrt_net_ultrafiltration_rate_ml_min,
    which is typically small relative to ckrt_blood_flow_ml_min (the
    machine returns nearly all of what it draws, minus only the
    intentionally removed amount).

    OPEN: always a no-op, nothing is installed to remove fluid.
    """
    if dt_s < 0.0:
        raise ValueError("dt_s must be non-negative")

    if params.configuration == ShuntLineConfiguration.HEMOFILTER and params.scuffing_active:
        rate = params.ultrafiltration_rate_ml_min
    elif params.configuration == ShuntLineConfiguration.CKRT and params.ckrt_blood_flow_ml_min > 0.0:
        rate = params.ckrt_net_ultrafiltration_rate_ml_min
    else:
        return state

    removed_ml = rate * (dt_s / 60.0)
    return replace(
        state,
        cumulative_filtrate_volume_ml=state.cumulative_filtrate_volume_ml + removed_ml,
    )
