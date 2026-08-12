from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .cannula import RETURN_8FR, CannulaHydraulicParameters, cannula_delta_p_mmhg


@dataclass(frozen=True)
class CannulaBenchPoint:
    flow_ml_min: float
    delta_p_mmhg: float


def run_cannula_hydraulic_bench(
    flow_steps_ml_min: Iterable[float] = (0, 100, 200, 300, 400, 500, 600, 800, 1000),
    params: CannulaHydraulicParameters = RETURN_8FR,
) -> List[CannulaBenchPoint]:
    """Sweep flow through a single cannula (Stage 5 bench)."""
    return [
        CannulaBenchPoint(
            flow_ml_min=float(flow),
            delta_p_mmhg=cannula_delta_p_mmhg(float(flow), params),
        )
        for flow in flow_steps_ml_min
    ]


def format_cannula_bench_report(points: Iterable[CannulaBenchPoint]) -> str:
    lines = [
        "CANNULA HYDRAULICS-ONLY BENCH — STANDALONE, EMPIRICAL QUADRATIC MODEL",
        "",
        "Flow(mL/min)   DeltaP(mmHg)",
    ]
    for p in points:
        lines.append(f"{p.flow_ml_min:12.1f}  {p.delta_p_mmhg:12.2f}")
    return "\n".join(lines)
