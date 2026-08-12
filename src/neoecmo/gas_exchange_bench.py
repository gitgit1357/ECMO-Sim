from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .oxygenator_gas_exchange import (
    OxygenatorGasExchangeParameters,
    outlet_o2_saturation,
    outlet_paco2_mmhg,
)


@dataclass(frozen=True)
class GasExchangeBenchPoint:
    blood_flow_ml_min: float
    inlet_saturation: float
    fdo2: float
    outlet_saturation: float
    inlet_paco2_mmhg: float
    sweep_gas_flow_ml_min: float
    outlet_paco2_mmhg: float


def run_gas_exchange_bench(
    flow_steps_ml_min: Iterable[float] = (100, 250, 500, 800, 1200, 1500, 2000),
    inlet_saturation: float = 0.65,
    fdo2: float = 1.0,
    inlet_paco2_mmhg: float = 55.0,
    sweep_gas_flow_ml_min: float = 600.0,
    params: OxygenatorGasExchangeParameters = OxygenatorGasExchangeParameters(),
) -> List[GasExchangeBenchPoint]:
    """Sweep blood flow at a fixed inlet condition and sweep-gas setting
    (Stage: oxygenator gas exchange bench)."""
    points = []
    for flow in flow_steps_ml_min:
        flow = float(flow)
        out_sat = outlet_o2_saturation(inlet_saturation, flow, fdo2, params)
        out_paco2 = outlet_paco2_mmhg(
            inlet_paco2_mmhg, flow, sweep_gas_flow_ml_min, params.obstruction_fraction
        )
        points.append(
            GasExchangeBenchPoint(
                blood_flow_ml_min=flow,
                inlet_saturation=inlet_saturation,
                fdo2=fdo2,
                outlet_saturation=out_sat,
                inlet_paco2_mmhg=inlet_paco2_mmhg,
                sweep_gas_flow_ml_min=sweep_gas_flow_ml_min,
                outlet_paco2_mmhg=out_paco2,
            )
        )
    return points


def format_gas_exchange_bench_report(points: Iterable[GasExchangeBenchPoint]) -> str:
    lines = [
        "OXYGENATOR GAS EXCHANGE BENCH — STANDALONE",
        "",
        "Flow(mL/min)   OutSat   OutPaCO2(mmHg)",
    ]
    for p in points:
        lines.append(
            f"{p.blood_flow_ml_min:12.1f}  {p.outlet_saturation:6.3f}  {p.outlet_paco2_mmhg:14.1f}"
        )
    return "\n".join(lines)
