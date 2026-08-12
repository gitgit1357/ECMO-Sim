from __future__ import annotations

from dataclasses import dataclass

from scipy.optimize import brentq

from .oxygenator import OxygenatorHydraulicParameters, oxygenator_delta_p_mmhg
from .pump import DEFAULT_REVOLUTION_CURVE, PumpHeadCurveParameters, pump_head_mmhg
from .tubing_geometry import resistance_for_segment


@dataclass(frozen=True)
class MainCircuitSeriesPoint:
    """
    One solved operating point for the pump + oxygenator wired in series
    (no fixed shunt or bridge branch yet — those are separate later wiring
    stages). Nodes, per the handoff topology:

        inlet_reservoir --(R pre-pump)--> P1 --pump--> P2
            --oxygenator--> P3 --(R return)--> outlet_reservoir
    """

    rpm: float
    inlet_reservoir_mmhg: float
    outlet_reservoir_mmhg: float
    resistance_pre_pump_mmhg_per_ml_min: float
    resistance_return_mmhg_per_ml_min: float
    solved_flow_ml_min: float
    p1_mmhg: float
    p2_mmhg: float
    p3_mmhg: float
    pump_head_mmhg: float
    oxygenator_delta_p_mmhg: float


def solve_main_circuit_series_operating_point(
    rpm: float,
    inlet_reservoir_mmhg: float,
    outlet_reservoir_mmhg: float,
    resistance_pre_pump_mmhg_per_ml_min: float = resistance_for_segment("main_pre_pump"),
    resistance_return_mmhg_per_ml_min: float = resistance_for_segment("main_return"),
    pump_curve: PumpHeadCurveParameters = DEFAULT_REVOLUTION_CURVE,
    oxygenator_params: OxygenatorHydraulicParameters = OxygenatorHydraulicParameters(),
    flow_search_bounds_ml_min: tuple[float, float] = (0.0, 20000.0),
) -> MainCircuitSeriesPoint:
    """
    Solve for the actual main-circuit flow with the pump and oxygenator
    wired in series (still no fixed shunt or bridge — this is the first
    wiring stage per the roadmap). The governing equation:

        pump_head(rpm, Q) = (outlet - inlet)
                             + Q * (R_pre_pump + R_return)
                             + oxygenator_delta_p(Q)

    Flow is bounded to [0, ...) here rather than allowing reversal like
    the standalone branch benches did: once the oxygenator (a one-way,
    non-reversible device in real use) is in the loop, negative flow is
    not a physically meaningful state for this wiring stage to represent,
    and is deliberately left as a later validity check rather than solved
    for here.
    """

    def f(q: float) -> float:
        required_head = (
            (outlet_reservoir_mmhg - inlet_reservoir_mmhg)
            + q * (resistance_pre_pump_mmhg_per_ml_min + resistance_return_mmhg_per_ml_min)
            + oxygenator_delta_p_mmhg(q, oxygenator_params)
        )
        return pump_head_mmhg(rpm, q, pump_curve) - required_head

    lo, hi = flow_search_bounds_ml_min
    f_lo, f_hi = f(lo), f(hi)
    if f_lo * f_hi > 0.0:
        raise RuntimeError(
            "No sign change across the search bracket — widen "
            "flow_search_bounds_ml_min for this RPM/resistance/pressure "
            "combination."
        )
    solved_flow = brentq(f, lo, hi, xtol=1e-6, rtol=1e-10)

    p1 = inlet_reservoir_mmhg - solved_flow * resistance_pre_pump_mmhg_per_ml_min
    head = pump_head_mmhg(rpm, solved_flow, pump_curve)
    p2 = p1 + head
    oxy_dp = oxygenator_delta_p_mmhg(solved_flow, oxygenator_params)
    p3 = p2 - oxy_dp

    return MainCircuitSeriesPoint(
        rpm=rpm,
        inlet_reservoir_mmhg=inlet_reservoir_mmhg,
        outlet_reservoir_mmhg=outlet_reservoir_mmhg,
        resistance_pre_pump_mmhg_per_ml_min=resistance_pre_pump_mmhg_per_ml_min,
        resistance_return_mmhg_per_ml_min=resistance_return_mmhg_per_ml_min,
        solved_flow_ml_min=solved_flow,
        p1_mmhg=p1,
        p2_mmhg=p2,
        p3_mmhg=p3,
        pump_head_mmhg=head,
        oxygenator_delta_p_mmhg=oxy_dp,
    )
