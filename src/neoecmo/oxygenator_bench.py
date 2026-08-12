from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .oxygenator import OxygenatorHydraulicParameters, oxygenator_delta_p_mmhg


@dataclass(frozen=True)
class OxygenatorBenchPoint:
    flow_ml_min: float
    obstruction_fraction: float
    delta_p_mmhg: float


def run_oxygenator_hydraulic_bench(
    flow_steps_ml_min: Iterable[float] = (0, 100, 200, 300, 400, 500, 600, 800),
    obstruction_fraction: float = 0.0,
    params: OxygenatorHydraulicParameters | None = None,
) -> List[OxygenatorBenchPoint]:
    """Sweep flow at a fixed obstruction/clot state (Stage 2 bench)."""
    base_params = params or OxygenatorHydraulicParameters()
    active_params = OxygenatorHydraulicParameters(
        baseline_resistance_linear_mmhg_per_ml_min=base_params.baseline_resistance_linear_mmhg_per_ml_min,
        baseline_resistance_quad_mmhg_per_ml_min2=base_params.baseline_resistance_quad_mmhg_per_ml_min2,
        min_recommended_flow_ml_min=base_params.min_recommended_flow_ml_min,
        obstruction_fraction=obstruction_fraction,
    )
    return [
        OxygenatorBenchPoint(
            flow_ml_min=float(flow),
            obstruction_fraction=obstruction_fraction,
            delta_p_mmhg=oxygenator_delta_p_mmhg(float(flow), active_params),
        )
        for flow in flow_steps_ml_min
    ]


def format_oxygenator_hydraulic_bench_report(points: Iterable[OxygenatorBenchPoint]) -> str:
    lines = [
        "OXYGENATOR HYDRAULICS-ONLY BENCH — STANDALONE, NO GAS EXCHANGE",
        "PROVISIONAL resistance model — see oxygenator.py docstring.",
        "",
        "Flow(mL/min)   Obstruction   DeltaP(mmHg)",
    ]
    for p in points:
        lines.append(
            f"{p.flow_ml_min:12.1f}  {p.obstruction_fraction:11.2f}  {p.delta_p_mmhg:12.2f}"
        )
    return "\n".join(lines)
