from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List
import numpy as np
from scipy.integrate import solve_ivp

from .baseline import TARGETS, build_normal_term_neonate


@dataclass(frozen=True)
class PumpDrainageBenchPoint:
    pump_flow_ml_kg_min: float
    pump_flow_ml_min: float
    native_rv_output_ml_min: float
    native_lv_output_ml_min: float
    native_lv_fraction_of_baseline: float
    mean_ra_pressure_mmhg: float
    mean_la_pressure_mmhg: float
    mean_pa_pressure_mmhg: float
    mean_aortic_pressure_mmhg: float
    ra_end_volume_ml: float
    patient_volume_removed_ml: float


def _mean_positive_flow(flow_ml_s: np.ndarray) -> float:
    return float(np.mean(np.clip(flow_ml_s, 0.0, None)))


def run_preload_extraction_bench(
    flow_steps_ml_kg_min: Iterable[float] = (0, 25, 50, 75, 100, 125, 150, 175, 200),
    stabilization_s: float = 30.0,
    extraction_s: float = 3.0,
    sample_hz: float = 200.0,
) -> List[PumpDrainageBenchPoint]:
    """
    Isolate the immediate effect of pump drainage from the right atrium.

    This is deliberately NOT a complete VA-ECMO model. A prescribed pump flow
    transfers blood from the RA to an external bench reservoir with no arterial
    return. Each flow step starts from the exact same stabilized baseline and is
    limited to a short interval so the result primarily reflects acute preload
    extraction rather than progressive whole-patient exsanguination.

    Total blood volume is conserved across patient + external reservoir, but
    patient intravascular volume falls during the short extraction window.
    """
    base = build_normal_term_neonate()
    stable = base.simulate(stabilization_s, sample_hz=sample_hz)
    y0_patient = stable.volumes_ml[:, -1].copy()
    idx = base.index
    baseline_window_s = 4.0 * 60.0 / TARGETS.heart_rate_bpm
    baseline_mask = stable.time_s >= (stable.time_s[-1] - baseline_window_s)
    baseline_lv = _mean_positive_flow(stable.edge_flows_ml_s["aortic_valve"][baseline_mask]) * 60.0

    results: List[PumpDrainageBenchPoint] = []
    for indexed_flow in flow_steps_ml_kg_min:
        q_pump = float(indexed_flow) * TARGETS.weight_kg / 60.0  # mL/s
        y0 = np.concatenate([y0_patient, np.array([0.0])])

        def derivative(t_s: float, y: np.ndarray) -> np.ndarray:
            patient = y[:-1]
            dv_patient = base.derivative(t_s + stabilization_s, patient)
            # Prescribed RA drainage with a soft availability limiter.
            ra_v = max(float(patient[idx["RA"]]), 0.0)
            available_factor = min(1.0, ra_v / 0.5) if ra_v < 0.5 else 1.0
            q = q_pump * available_factor
            dv_patient[idx["RA"]] -= q
            return np.concatenate([dv_patient, np.array([q])])

        samples = int(round(extraction_s * sample_hz)) + 1
        t_eval = np.linspace(0.0, extraction_s, samples)
        sol = solve_ivp(
            derivative,
            (0.0, extraction_s),
            y0,
            method="LSODA",
            t_eval=t_eval,
            rtol=1e-7,
            atol=1e-9,
            max_step=min(0.005, 1.0 / sample_hz),
        )
        if not sol.success:
            raise RuntimeError(sol.message)

        # Analyze up to the final 2 s (multiple neonatal beats) to avoid phase bias
        # while preserving the short transient nature of the isolation test.
        analysis_window_s = min(4.0 * 60.0 / TARGETS.heart_rate_bpm, extraction_s)
        mask = sol.t >= max(0.0, extraction_s - analysis_window_s)
        times = sol.t[mask] + stabilization_s
        patient_states = sol.y[:-1, mask]
        pressure_samples = np.column_stack(
            [base.pressures(t, patient_states[:, i]) for i, t in enumerate(times)]
        )
        flow_samples = {edge.name: [] for edge in base.edges}
        for i, t in enumerate(times):
            f = base.edge_flows(t, patient_states[:, i])
            for name, value in f.items():
                flow_samples[name].append(value)

        rv = _mean_positive_flow(np.asarray(flow_samples["pulmonary_valve"])) * 60.0
        lv = _mean_positive_flow(np.asarray(flow_samples["aortic_valve"])) * 60.0
        p = lambda node: float(np.mean(pressure_samples[idx[node]]))

        results.append(
            PumpDrainageBenchPoint(
                pump_flow_ml_kg_min=float(indexed_flow),
                pump_flow_ml_min=q_pump * 60.0,
                native_rv_output_ml_min=rv,
                native_lv_output_ml_min=lv,
                native_lv_fraction_of_baseline=(lv / baseline_lv if baseline_lv else 0.0),
                mean_ra_pressure_mmhg=p("RA"),
                mean_la_pressure_mmhg=p("LA"),
                mean_pa_pressure_mmhg=p("MPA"),
                mean_aortic_pressure_mmhg=p("AORTIC_ROOT"),
                ra_end_volume_ml=float(sol.y[idx["RA"], -1]),
                patient_volume_removed_ml=float(sol.y[-1, -1]),
            )
        )
    return results


def format_preload_extraction_report(points: Iterable[PumpDrainageBenchPoint]) -> str:
    lines = [
        "PRELOAD EXTRACTION BENCH — RIGHT-ATRIAL PUMP DRAINAGE ONLY",
        "NOTE: short transient isolation test; no arterial return and no ECMO afterload effect.",
        "",
        "Pump       Native RV   Native LV   LV %base   RA mean  LA mean  PA mean  Ao mean  Removed",
        "mL/kg/min  mL/min      mL/min      %          mmHg     mmHg     mmHg     mmHg     mL",
    ]
    for p in points:
        lines.append(
            f"{p.pump_flow_ml_kg_min:8.0f}  {p.native_rv_output_ml_min:9.0f}  "
            f"{p.native_lv_output_ml_min:9.0f}  {p.native_lv_fraction_of_baseline*100:8.1f}  "
            f"{p.mean_ra_pressure_mmhg:7.2f}  {p.mean_la_pressure_mmhg:7.2f}  "
            f"{p.mean_pa_pressure_mmhg:7.2f}  {p.mean_aortic_pressure_mmhg:7.2f}  "
            f"{p.patient_volume_removed_ml:7.2f}"
        )
    return "\n".join(lines)
