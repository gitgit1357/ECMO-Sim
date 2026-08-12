from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from scipy.optimize import brentq

from .pump import DEFAULT_REVOLUTION_CURVE, PumpHeadCurveParameters, pump_head_mmhg


@dataclass(frozen=True)
class PumpBenchPoint:
    rpm: float
    inlet_reservoir_mmhg: float
    outlet_reservoir_mmhg: float
    resistance_in_mmhg_per_ml_min: float
    resistance_out_mmhg_per_ml_min: float
    solved_flow_ml_min: float
    p1_mmhg: float
    p2_mmhg: float
    pump_head_mmhg: float


def _required_head(
    flow_ml_min: float,
    inlet_reservoir_mmhg: float,
    outlet_reservoir_mmhg: float,
    resistance_in: float,
    resistance_out: float,
) -> float:
    """Head the pump would need to supply, at a candidate flow, to satisfy
    the pressure boundary conditions and tubing resistances on both sides."""
    return (outlet_reservoir_mmhg - inlet_reservoir_mmhg) + flow_ml_min * (
        resistance_in + resistance_out
    )


def solve_pump_operating_point(
    rpm: float,
    inlet_reservoir_mmhg: float,
    outlet_reservoir_mmhg: float,
    resistance_in_mmhg_per_ml_min: float,
    resistance_out_mmhg_per_ml_min: float,
    curve: PumpHeadCurveParameters = DEFAULT_REVOLUTION_CURVE,
    flow_search_bounds_ml_min: tuple[float, float] = (-20000.0, 20000.0),
) -> PumpBenchPoint:
    """
    Solve for the actual operating flow at a given RPM against simple inlet/
    outlet pressure reservoirs and tubing resistances.

    This deliberately does NOT map RPM directly to flow (handoff 12.3 / 31.1).
    Instead it finds the flow at which the pump head curve intersects the
    head required by the boundary conditions:

        pump_head(rpm, Q) - required_head(Q) = 0

    A stopped or very slow pump (rpm <= 0, zero head at all flows) still
    produces a defined operating point: flow is then set purely by the
    pressure difference and resistances, exactly like an unpowered tubing
    loop, which is the correct degenerate case.
    """

    def f(q: float) -> float:
        return pump_head_mmhg(rpm, q, curve) - _required_head(
            q,
            inlet_reservoir_mmhg,
            outlet_reservoir_mmhg,
            resistance_in_mmhg_per_ml_min,
            resistance_out_mmhg_per_ml_min,
        )

    lo, hi = flow_search_bounds_ml_min
    f_lo, f_hi = f(lo), f(hi)
    if f_lo * f_hi > 0.0:
        raise RuntimeError(
            "No sign change across the search bracket — widen "
            "flow_search_bounds_ml_min for this RPM/resistance/pressure "
            "combination."
        )
    solved_flow = brentq(f, lo, hi, xtol=1e-6, rtol=1e-10)
    head = pump_head_mmhg(rpm, solved_flow, curve)
    p1 = inlet_reservoir_mmhg - solved_flow * resistance_in_mmhg_per_ml_min
    p2 = p1 + head

    return PumpBenchPoint(
        rpm=rpm,
        inlet_reservoir_mmhg=inlet_reservoir_mmhg,
        outlet_reservoir_mmhg=outlet_reservoir_mmhg,
        resistance_in_mmhg_per_ml_min=resistance_in_mmhg_per_ml_min,
        resistance_out_mmhg_per_ml_min=resistance_out_mmhg_per_ml_min,
        solved_flow_ml_min=solved_flow,
        p1_mmhg=p1,
        p2_mmhg=p2,
        pump_head_mmhg=head,
    )


def run_pump_head_bench(
    rpm_steps: Iterable[float] = (0, 1500, 2000, 2500, 3000, 3500, 4000),
    inlet_reservoir_mmhg: float = 0.0,
    outlet_reservoir_mmhg: float = 0.0,
    resistance_in_mmhg_per_ml_min: float = 0.001697,
    resistance_out_mmhg_per_ml_min: float = 0.05,
    curve: PumpHeadCurveParameters = DEFAULT_REVOLUTION_CURVE,
) -> List[PumpBenchPoint]:
    """
    Sweep RPM at fixed boundary pressures/resistances (Stage 1 bench).

    resistance_in_mmhg_per_ml_min now defaults to the Hagen-Poiseuille
    resistance of the actual measured pre-pump tubing segment (3/8" ID,
    3 ft — see tubing_geometry.MEASURED_SEGMENTS["main_pre_pump"]), since
    that segment exists on its own regardless of what's downstream.

    resistance_out_mmhg_per_ml_min remains an arbitrary placeholder: the
    real downstream path (pump-to-oxygenator tubing, the oxygenator
    itself, return tubing, return cannula) is not yet composed into this
    standalone bench, so there is no single "outlet resistance" to ground
    yet. It stands in for "some downstream load" for solver-testing
    purposes only.
    """
    return [
        solve_pump_operating_point(
            rpm,
            inlet_reservoir_mmhg,
            outlet_reservoir_mmhg,
            resistance_in_mmhg_per_ml_min,
            resistance_out_mmhg_per_ml_min,
            curve,
        )
        for rpm in rpm_steps
    ]


def format_pump_head_bench_report(points: Iterable[PumpBenchPoint]) -> str:
    lines = [
        "PUMP-HEAD HYDRAULIC BENCH — STANDALONE, NO PATIENT/CIRCUIT ATTACHED",
        "PROVISIONAL pump curve — see pump.py PumpHeadCurveParameters docstring.",
        "",
        "RPM     Flow(mL/min)   P1(mmHg)   P2(mmHg)   Head(mmHg)",
    ]
    for p in points:
        lines.append(
            f"{p.rpm:6.0f}  {p.solved_flow_ml_min:12.1f}  "
            f"{p.p1_mmhg:9.2f}  {p.p2_mmhg:9.2f}  {p.pump_head_mmhg:10.2f}"
        )
    return "\n".join(lines)
