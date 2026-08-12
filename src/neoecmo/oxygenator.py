from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class OxygenatorHydraulicParameters:
    """
    Provisional, replaceable oxygenator blood-path hydraulic parameters.

    STATUS: PROVISIONAL. No specific oxygenator make/model has been locked
    (handoff section 32 — "exact oxygenator make/model" is an open question).
    These coefficients are a reduced-order, literature-typical shape only:
    a baseline linear+quadratic resistance (laminar + turbulent-ish
    components across the fiber bundle) that rises as clot/obstruction
    narrows the effective flow path. This must be replaced with real
    manufacturer or bench-derived ΔP-vs-flow data before any value here is
    treated as clinically accurate.

    Gas exchange, membrane oxygen/CO2 transfer, and the heat exchanger are
    NOT part of this stage (handoff section 21) — this module is hydraulics
    only, mirroring how neolung's mechanical model preceded its gas-exchange
    layer.
    """

    baseline_resistance_linear_mmhg_per_ml_min: float = 0.03
    baseline_resistance_quad_mmhg_per_ml_min2: float = 0.00002
    # 250 mL/min is the Eurosets AMG PMP Infant oxygenator's real stated
    # minimum flow to prevent clot formation (confirmed directly, not a
    # placeholder — chat 2026-07-26), replacing the earlier 200.0 guess.
    min_recommended_flow_ml_min: float = 250.0
    obstruction_fraction: float = 0.0  # 0 = clean membrane, approaches 1 = fully occluded


def oxygenator_delta_p_mmhg(
    flow_ml_min: float,
    params: OxygenatorHydraulicParameters = OxygenatorHydraulicParameters(),
) -> float:
    """
    Blood-side pressure drop across the oxygenator (P2 - P3), as a function
    of flow and current obstruction/clot state.

    Governing rules (handoff section 21 hydraulic behavior):
      - baseline ΔP rises with flow (flow-dependent ΔP);
      - rising clot/obstruction raises resistance at any given flow;
      - reduced order only — this is a lumped resistance, not a fiber-bundle
        pressure-flow simulation.

    obstruction_fraction narrows the effective flow path; resistance scales
    as 1 / (1 - obstruction_fraction) ** 2, clipped below 0.99 to avoid a
    divide-by-zero singularity at full occlusion (a fully occluded
    oxygenator is a zero-flow degenerate case handled by the circuit
    hydraulics, not by this function returning infinity).
    """
    obstruction = min(max(params.obstruction_fraction, 0.0), 0.99)
    resistance_multiplier = 1.0 / (1.0 - obstruction) ** 2
    linear_term = params.baseline_resistance_linear_mmhg_per_ml_min * resistance_multiplier
    quad_term = params.baseline_resistance_quad_mmhg_per_ml_min2 * resistance_multiplier
    flow = max(flow_ml_min, 0.0)
    return linear_term * flow + quad_term * flow**2


@dataclass(frozen=True)
class OxygenatorLowFlowExposureState:
    """
    Tracks cumulative time spent below the minimum recommended blood flow.

    This is exposure tracking only (handoff section 13 Stage 3 test list),
    not a complication/risk engine. It never resets to zero when flow
    recovers — it only stops accumulating — consistent with the handoff's
    "correcting the cause reduces future risk but does not automatically
    reverse established [exposure]" philosophy (section 2.5 / 15). Turning
    accumulated exposure into actual risk or damage is a later stage
    (section 29, complication engine), deliberately not built here.
    """

    cumulative_low_flow_exposure_s: float = 0.0


def step_low_flow_exposure(
    state: OxygenatorLowFlowExposureState,
    flow_ml_min: float,
    dt_s: float,
    params: OxygenatorHydraulicParameters = OxygenatorHydraulicParameters(),
) -> OxygenatorLowFlowExposureState:
    """Advance the low-flow exposure clock by dt_s given the current flow."""
    if dt_s < 0.0:
        raise ValueError("dt_s must be non-negative")
    if flow_ml_min < params.min_recommended_flow_ml_min:
        return replace(
            state,
            cumulative_low_flow_exposure_s=state.cumulative_low_flow_exposure_s + dt_s,
        )
    return state
