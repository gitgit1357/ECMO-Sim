from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .fixed_shunt import FixedShuntParameters, fixed_shunt_flow_ml_min


@dataclass(frozen=True)
class FixedShuntBenchPoint:
    upstream_pressure_mmhg: float
    downstream_pressure_mmhg: float
    solved_flow_ml_min: float


def run_fixed_shunt_bench(
    downstream_pressure_steps_mmhg: Iterable[float] = (-50, 0, 50, 100, 150, 200),
    upstream_pressure_mmhg: float = 150.0,
    params: FixedShuntParameters = FixedShuntParameters(),
) -> List[FixedShuntBenchPoint]:
    """Sweep downstream (pre-pump) pressure at a fixed upstream
    (post-oxygenator) pressure (Stage 3 bench)."""
    return [
        FixedShuntBenchPoint(
            upstream_pressure_mmhg=upstream_pressure_mmhg,
            downstream_pressure_mmhg=float(downstream),
            solved_flow_ml_min=fixed_shunt_flow_ml_min(
                upstream_pressure_mmhg, float(downstream), params
            ),
        )
        for downstream in downstream_pressure_steps_mmhg
    ]


def format_fixed_shunt_bench_report(points: Iterable[FixedShuntBenchPoint]) -> str:
    lines = [
        "FIXED SHUNT HYDRAULICS-ONLY BENCH — STANDALONE",
        "",
        "Upstream(mmHg)   Downstream(mmHg)   Flow(mL/min)",
    ]
    for p in points:
        lines.append(
            f"{p.upstream_pressure_mmhg:14.1f}  {p.downstream_pressure_mmhg:16.1f}  "
            f"{p.solved_flow_ml_min:12.1f}"
        )
    return "\n".join(lines)
