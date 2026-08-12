from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List
import numpy as np
from scipy.integrate import solve_ivp

from .baseline import TARGETS, build_normal_term_neonate


@dataclass(frozen=True)
class VAECMOBenchPoint:
    pump_flow_ml_kg_min: float
    requested_pump_flow_ml_min: float
    delivered_pump_flow_ml_min: float
    native_rv_output_ml_min: float
    native_lv_output_ml_min: float
    total_aortic_inflow_ml_min: float
    native_fraction_of_aortic_inflow: float
    circuit_fraction_of_aortic_inflow: float
    aortic_valve_open_fraction: float
    systolic_aortic_mmhg: float
    diastolic_aortic_mmhg: float
    mean_aortic_mmhg: float
    pulse_pressure_mmhg: float
    mean_ra_pressure_mmhg: float
    mean_la_pressure_mmhg: float
    mean_pa_pressure_mmhg: float
    mean_lv_volume_ml: float
    mean_rv_volume_ml: float
    volume_conservation_error_ml: float


def _mean_positive(values: np.ndarray) -> float:
    return float(np.mean(np.clip(values, 0.0, None)))


def run_closed_loop_va_ecmo_bench(
    flow_steps_ml_kg_min: Iterable[float] = (0, 25, 50, 75, 100, 125, 150, 175, 200),
    stabilization_s: float = 30.0,
    support_s: float = 12.0,
    sample_hz: float = 200.0,
) -> List[VAECMOBenchPoint]:
    """Bench native-heart response to isolated closed-loop VA support.

    A prescribed extracorporeal flow transfers blood directly from the right
    atrium to the aortic root. Drainage and return are always matched, so total
    patient blood volume is conserved. This deliberately isolates the hydraulic
    effects of venous preload diversion plus arterial return/afterload.

    Not modeled here: oxygenator gas exchange, cannula pressure-flow curves,
    recirculation, pump RPM curves, vascular-tone changes, lung mechanics, or
    changes in intrinsic myocardial contractility.
    """
    base = build_normal_term_neonate()
    stable = base.simulate(stabilization_s, sample_hz=sample_hz)
    y0 = stable.volumes_ml[:, -1].copy()
    idx = base.index
    initial_total = float(np.sum(y0))

    results: List[VAECMOBenchPoint] = []
    for indexed_flow in flow_steps_ml_kg_min:
        requested_q = float(indexed_flow) * TARGETS.weight_kg / 60.0  # mL/s

        delivered_samples: List[float] = []

        def pump_flow(patient: np.ndarray) -> float:
            # Soft drainage availability limit only at extremely low RA volume.
            ra_v = max(float(patient[idx["RA"]]), 0.0)
            factor = min(1.0, ra_v / 0.5) if ra_v < 0.5 else 1.0
            return requested_q * factor

        def derivative(t_s: float, patient: np.ndarray) -> np.ndarray:
            absolute_t = t_s + stabilization_s
            dv = base.derivative(absolute_t, patient)
            q = pump_flow(patient)
            dv[idx["RA"]] -= q
            dv[idx["AORTIC_ROOT"]] += q
            return dv

        samples = int(round(support_s * sample_hz)) + 1
        t_eval = np.linspace(0.0, support_s, samples)
        sol = solve_ivp(
            derivative,
            (0.0, support_s),
            y0.copy(),
            method="LSODA",
            t_eval=t_eval,
            rtol=1e-7,
            atol=1e-9,
            max_step=min(0.005, 1.0 / sample_hz),
        )
        if not sol.success:
            raise RuntimeError(sol.message)

        # Analyze the last four beats after the immediate transient.
        analysis_window_s = min(4.0 * 60.0 / TARGETS.heart_rate_bpm, support_s)
        mask = sol.t >= max(0.0, support_s - analysis_window_s)
        times = sol.t[mask] + stabilization_s
        states = sol.y[:, mask]
        pressures = np.column_stack(
            [base.pressures(t, states[:, i]) for i, t in enumerate(times)]
        )
        flow_samples = {edge.name: [] for edge in base.edges}
        pump_samples = []
        for i, t in enumerate(times):
            f = base.edge_flows(t, states[:, i])
            for name, value in f.items():
                flow_samples[name].append(value)
            pump_samples.append(pump_flow(states[:, i]))

        q_rv = np.asarray(flow_samples["pulmonary_valve"])
        q_lv = np.asarray(flow_samples["aortic_valve"])
        q_pump = np.asarray(pump_samples)
        native_rv = _mean_positive(q_rv) * 60.0
        native_lv = _mean_positive(q_lv) * 60.0
        delivered = float(np.mean(q_pump)) * 60.0
        total_aortic = native_lv + delivered
        aortic = pressures[idx["AORTIC_ROOT"]]
        p = lambda node: float(np.mean(pressures[idx[node]]))
        total_end = float(np.sum(sol.y[:, -1]))

        results.append(
            VAECMOBenchPoint(
                pump_flow_ml_kg_min=float(indexed_flow),
                requested_pump_flow_ml_min=requested_q * 60.0,
                delivered_pump_flow_ml_min=delivered,
                native_rv_output_ml_min=native_rv,
                native_lv_output_ml_min=native_lv,
                total_aortic_inflow_ml_min=total_aortic,
                native_fraction_of_aortic_inflow=(native_lv / total_aortic if total_aortic else 0.0),
                circuit_fraction_of_aortic_inflow=(delivered / total_aortic if total_aortic else 0.0),
                aortic_valve_open_fraction=float(np.mean(q_lv > 1e-5)),
                systolic_aortic_mmhg=float(np.max(aortic)),
                diastolic_aortic_mmhg=float(np.min(aortic)),
                mean_aortic_mmhg=float(np.mean(aortic)),
                pulse_pressure_mmhg=float(np.max(aortic) - np.min(aortic)),
                mean_ra_pressure_mmhg=p("RA"),
                mean_la_pressure_mmhg=p("LA"),
                mean_pa_pressure_mmhg=p("MPA"),
                mean_lv_volume_ml=float(np.mean(states[idx["LV"]])),
                mean_rv_volume_ml=float(np.mean(states[idx["RV"]])),
                volume_conservation_error_ml=total_end - initial_total,
            )
        )
    return results


def format_closed_loop_va_ecmo_report(points: Iterable[VAECMOBenchPoint]) -> str:
    lines = [
        "CLOSED-LOOP VA-ECMO HYDRAULIC BENCH — RA DRAINAGE -> AORTIC ROOT RETURN",
        "NOTE: matched drainage/return; no gas exchange, RPM curve, lung mechanics, or autonomic compensation.",
        "",
        "Pump      Native RV  Native LV  Total Ao   Circuit%  Ao valve%  Ao sys/dia   MAP   PP   RA   LA   PA",
        "mL/kg/min mL/min     mL/min     mL/min     %         open       mmHg         mmHg  mmHg mmHg mmHg mmHg",
    ]
    for p in points:
        lines.append(
            f"{p.pump_flow_ml_kg_min:8.0f}  {p.native_rv_output_ml_min:9.0f}  {p.native_lv_output_ml_min:9.0f}  "
            f"{p.total_aortic_inflow_ml_min:9.0f}  {p.circuit_fraction_of_aortic_inflow*100:8.1f}  "
            f"{p.aortic_valve_open_fraction*100:8.1f}  {p.systolic_aortic_mmhg:5.1f}/{p.diastolic_aortic_mmhg:4.1f}  "
            f"{p.mean_aortic_mmhg:5.1f} {p.pulse_pressure_mmhg:5.1f} {p.mean_ra_pressure_mmhg:4.1f} "
            f"{p.mean_la_pressure_mmhg:4.1f} {p.mean_pa_pressure_mmhg:4.1f}"
        )
    return "\n".join(lines)
