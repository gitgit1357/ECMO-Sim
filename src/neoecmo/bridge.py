from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BridgeParameters:
    """
    Provisional, replaceable bridge branch parameters (handoff section 15).

    Hydraulics-only scope for this stage, deliberately: the bridge's clamp
    position is modeled here as a continuous, controllable resistance
    (closed / partially open for weaning trials / fully open for patient
    isolation), but the stagnation-clock, clot-risk-from-dwell-time, and
    flush-validity logic described in the handoff are NOT part of this
    stage. Those are cross-branch risk-tracking concerns (the bridge,
    cannulas, and main circuit each have their own stagnation clock) and
    are deliberately deferred to a later stage so this stage stays pure
    hydraulics, matching how the pump/oxygenator/shunt stages were scoped.

    clamp_position: 0.0 = fully clamped shut (no flow possible, regardless
    of pressure gradient — a real mechanical clamp is not modeled as very
    high resistance, it is a hard zero). 1.0 = fully open. Values in
    between represent a weaning-trial partial opening.

    STATUS: PARTIALLY GROUNDED. tubing_resistance_linear_mmhg_per_ml_min
    below is now derived from measured geometry (3/8" ID, ~1 ft bridge
    tubing — see tubing_geometry.py MEASURED_SEGMENTS["bridge_tubing"])
    via Hagen-Poiseuille, not guessed. tubing_resistance_quad_mmhg_per_ml_min2
    is left at 0.0: this bore/length combination stays laminar across
    realistic neonatal ECMO flows (confirmed via
    tubing_geometry.reynolds_number), so the linear term is the physically
    correct model, not an approximation. No specific bridge tubing/clamp
    hardware beyond bore and length is locked (handoff section 32).
    clot_fraction reuses the same reduced-order 1/(1-clot_fraction)^2
    shape used elsewhere in this package.
    """

    tubing_resistance_linear_mmhg_per_ml_min: float = 0.000566
    tubing_resistance_quad_mmhg_per_ml_min2: float = 0.0
    clot_fraction: float = 0.0  # 0 = clean, approaches 1 = fully occluded
    clamp_position: float = 0.0  # 0 = fully clamped shut (clinical default), 1 = fully open


CLOSED_CLAMP_EPSILON = 1e-6


def _bridge_resistance_terms(params: BridgeParameters) -> tuple[float, float]:
    """Effective linear/quadratic resistance at the current clamp position
    and clot state. Only meaningful when the clamp is not fully closed —
    callers must check for the closed case separately (see
    bridge_flow_ml_min)."""
    clot = min(max(params.clot_fraction, 0.0), 0.99)
    clot_multiplier = 1.0 / (1.0 - clot) ** 2

    clamp = min(max(params.clamp_position, 0.0), 1.0)
    clamp_multiplier = 1.0 / clamp**2

    lin = params.tubing_resistance_linear_mmhg_per_ml_min * clot_multiplier * clamp_multiplier
    quad = params.tubing_resistance_quad_mmhg_per_ml_min2 * clot_multiplier * clamp_multiplier
    return lin, quad


def _solve_signed_quadratic_flow(delta_p_mmhg: float, r_lin: float, r_quad: float) -> float:
    """Solve delta_p = r_lin * Q + r_quad * Q * |Q| for Q, preserving sign."""
    if delta_p_mmhg == 0.0:
        return 0.0
    sign = 1.0 if delta_p_mmhg > 0.0 else -1.0
    magnitude = abs(delta_p_mmhg)
    if r_quad == 0.0:
        q_mag = magnitude / r_lin
    else:
        q_mag = (-r_lin + (r_lin**2 + 4.0 * r_quad * magnitude) ** 0.5) / (2.0 * r_quad)
    return sign * q_mag


def bridge_flow_ml_min(
    upstream_pressure_mmhg: float,
    downstream_pressure_mmhg: float,
    params: BridgeParameters = BridgeParameters(),
) -> float:
    """
    Flow through the bridge branch given the pressure at its two ends and
    the current clamp position.

    A fully (or near-fully) closed clamp always yields exactly zero flow,
    regardless of pressure gradient — this is a hard physical cutoff, not
    an asymptote of rising resistance. Any nonzero opening solves the same
    signed-quadratic resistance model used for the fixed shunt, so reversed
    flow direction (patient-side pressure exceeding the other end) is a
    valid weaning-trial state, not an error.
    """
    clamp = min(max(params.clamp_position, 0.0), 1.0)
    if clamp <= CLOSED_CLAMP_EPSILON:
        return 0.0
    r_lin, r_quad = _bridge_resistance_terms(params)
    delta_p = upstream_pressure_mmhg - downstream_pressure_mmhg
    return _solve_signed_quadratic_flow(delta_p, r_lin, r_quad)
