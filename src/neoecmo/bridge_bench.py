from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, List

from .bridge import BridgeParameters, bridge_flow_ml_min


@dataclass(frozen=True)
class BridgeBenchPoint:
    clamp_position: float
    upstream_pressure_mmhg: float
    downstream_pressure_mmhg: float
    solved_flow_ml_min: float


def run_bridge_clamp_sweep_bench(
    clamp_position_steps: Iterable[float] = (0.0, 0.1, 0.25, 0.5, 0.75, 1.0),
    upstream_pressure_mmhg: float = 150.0,
    downstream_pressure_mmhg: float = 50.0,
    params: BridgeParameters = BridgeParameters(),
) -> List[BridgeBenchPoint]:
    """Sweep clamp position at a fixed pressure boundary (Stage 4 bench)."""
    points = []
    for clamp in clamp_position_steps:
        active_params = replace(params, clamp_position=float(clamp))
        points.append(
            BridgeBenchPoint(
                clamp_position=float(clamp),
                upstream_pressure_mmhg=upstream_pressure_mmhg,
                downstream_pressure_mmhg=downstream_pressure_mmhg,
                solved_flow_ml_min=bridge_flow_ml_min(
                    upstream_pressure_mmhg, downstream_pressure_mmhg, active_params
                ),
            )
        )
    return points


def format_bridge_bench_report(points: Iterable[BridgeBenchPoint]) -> str:
    lines = [
        "BRIDGE HYDRAULICS-ONLY BENCH — STANDALONE (no stagnation/risk tracking)",
        "",
        "Clamp   Upstream(mmHg)   Downstream(mmHg)   Flow(mL/min)",
    ]
    for p in points:
        lines.append(
            f"{p.clamp_position:5.2f}  {p.upstream_pressure_mmhg:14.1f}  "
            f"{p.downstream_pressure_mmhg:16.1f}  {p.solved_flow_ml_min:12.1f}"
        )
    return "\n".join(lines)
