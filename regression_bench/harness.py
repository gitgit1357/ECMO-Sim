from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from neocirculation.metrics import calculate_baseline_metrics
from neocirculation.baseline import build_normal_term_neonate
from neocirculation.va_ecmo_bench import run_closed_loop_va_ecmo_bench
from bench_fixtures.cannulas import load_medtronic_life_support_mini
from bench_fixtures.pumps import NORTHSTAR_TEST_PUMP_V1

SCHEMA_VERSION = "1.0"
BENCH_ID = "neonatal-circulation-northstar-v1"
FIXED_FLOW_STEPS = (0, 50, 100, 150, 200)
RPM_STEPS = (2000, 3000, 4000, 5000)
CANNULA_SIZES = (9, 11, 13, 15)


def _hash_manifest(data: dict) -> str:
    blob = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def _baseline_metrics() -> dict:
    patient = build_normal_term_neonate()
    result = patient.simulate(30.0, sample_hz=100.0)
    m = calculate_baseline_metrics(result, heart_rate_bpm=130.0, tail_seconds=4.0)
    # Fixed, explicit public metrics only.
    return {
        "systolic_aortic_mmhg": m.systolic_aortic_mmhg,
        "diastolic_aortic_mmhg": m.diastolic_aortic_mmhg,
        "mean_aortic_mmhg": m.mean_aortic_mmhg,
        "pulse_pressure_mmhg": m.pulse_pressure_mmhg,
        "cardiac_output_ml_min": m.native_output_ml_min,
        "mean_ra_pressure_mmhg": m.mean_ra_mmhg,
        "mean_pa_pressure_mmhg": m.mean_pa_mmhg,
        "total_blood_volume_ml": m.total_volume_end_ml,
    }


def _fixed_flow_va() -> List[dict]:
    points = run_closed_loop_va_ecmo_bench(
        flow_steps_ml_kg_min=FIXED_FLOW_STEPS,
        stabilization_s=30.0,
        support_s=12.0,
        sample_hz=100.0,
    )
    keys = (
        "pump_flow_ml_kg_min", "delivered_pump_flow_ml_min",
        "native_rv_output_ml_min", "native_lv_output_ml_min",
        "circuit_fraction_of_aortic_inflow", "aortic_valve_open_fraction",
        "mean_aortic_mmhg", "pulse_pressure_mmhg", "mean_ra_pressure_mmhg",
        "mean_la_pressure_mmhg", "mean_pa_pressure_mmhg",
        "mean_lv_volume_ml", "mean_rv_volume_ml", "volume_conservation_error_ml",
    )
    return [{k: getattr(p, k) for k in keys} for p in points]


def _interp(x: float, xs: List[float], ys: List[float]) -> float:
    if x <= xs[0]: return ys[0]
    if x >= xs[-1]: return ys[-1]
    for i in range(len(xs)-1):
        if xs[i] <= x <= xs[i+1]:
            f = (x-xs[i])/(xs[i+1]-xs[i])
            return ys[i] + f*(ys[i+1]-ys[i])
    return ys[-1]


def _solve_fixture_flow(rpm: float, cannula, va_points: List[dict]) -> dict:
    xs = [p["delivered_pump_flow_ml_min"] / 1000.0 for p in va_points]
    gradients = [max(p["mean_aortic_mmhg"] - p["mean_ra_pressure_mmhg"], 0.0) for p in va_points]
    max_q = min(NORTHSTAR_TEST_PUMP_V1.free_flow_l_min(rpm), 2.5)

    def load_head(q: float) -> float:
        patient_dp = _interp(q, xs, gradients)
        cannula_dp = cannula.estimated_pressure_loss_mmhg(q)
        return patient_dp + 2.0 * cannula_dp

    lo, hi = 0.0, max_q
    for _ in range(80):
        mid = (lo + hi) / 2.0
        residual = NORTHSTAR_TEST_PUMP_V1.head_mmhg(rpm, mid) - load_head(mid)
        if residual >= 0:
            lo = mid
        else:
            hi = mid
    q = (lo + hi) / 2.0
    return {
        "rpm": rpm,
        "cannula_size_fr": cannula.size_fr,
        "equilibrium_flow_l_min": q,
        "pump_head_mmhg": NORTHSTAR_TEST_PUMP_V1.head_mmhg(rpm, q),
        "estimated_load_head_mmhg": load_head(q),
        "manufacturer_anchor_extrapolated": q > max(cannula.flow_l_min_at_plus_100_mmhg, cannula.flow_l_min_at_minus_40_mmhg),
    }


def run_northstar_bench() -> dict:
    va = _fixed_flow_va()
    cannulas = {c.size_fr: c for c in load_medtronic_life_support_mini()}
    hardware = [
        _solve_fixture_flow(rpm, cannulas[size], va)
        for size in CANNULA_SIZES for rpm in RPM_STEPS
    ]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "bench_id": BENCH_ID,
        "patient_profile": "normal-term-neonate-3.5kg-72h",
        "fixed_flow_steps_ml_kg_min": list(FIXED_FLOW_STEPS),
        "rpm_steps": list(RPM_STEPS),
        "cannula_sizes_fr": list(CANNULA_SIZES),
        "pump_fixture_id": NORTHSTAR_TEST_PUMP_V1.fixture_id,
        "notes": [
            "Patient physiology owns no cannula or pump models.",
            "Cannula and pump fixtures are external regression equipment.",
            "Synthetic pump fixture is deterministic and not a clinical manufacturer model.",
            "Manufacturer cannula curves remain external water-bench approximations.",
        ],
    }
    return {
        "manifest": {**manifest, "manifest_hash": _hash_manifest(manifest)},
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "baseline": _baseline_metrics(),
        "va_fixed_flow": va,
        "hardware_fixture": hardware,
    }


def save_result(path: Path) -> dict:
    data = run_northstar_bench()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def compare(reference: dict, current: dict) -> dict:
    # Metric-specific regression tolerances: strict enough to detect model drift,
    # loose enough for deterministic solver/platform numerical differences.
    abs_tol = {
        "pressure": 0.75,
        "flow": 15.0,
        "fraction": 0.025,
        "volume": 0.25,
        "conservation": 1e-5,
        "hardware_flow_l_min": 0.03,
        "head": 5.0,
    }
    failures = []

    def check(path: str, a: float, b: float, tol: float):
        if abs(a-b) > tol:
            failures.append({"path": path, "reference": a, "current": b, "abs_diff": abs(a-b), "tolerance": tol})

    for k, a in reference["baseline"].items():
        b = current["baseline"][k]
        if "volume" in k: tol = abs_tol["volume"]
        elif "output" in k: tol = abs_tol["flow"]
        else: tol = abs_tol["pressure"]
        check(f"baseline.{k}", a, b, tol)

    for i, (ra, rb) in enumerate(zip(reference["va_fixed_flow"], current["va_fixed_flow"])):
        for k, a in ra.items():
            if k == "pump_flow_ml_kg_min": continue
            b = rb[k]
            if "fraction" in k: tol = abs_tol["fraction"]
            elif "volume_conservation" in k: tol = abs_tol["conservation"]
            elif "volume_ml" in k: tol = abs_tol["volume"]
            elif "flow" in k or "output" in k: tol = abs_tol["flow"]
            else: tol = abs_tol["pressure"]
            check(f"va_fixed_flow[{i}].{k}", a, b, tol)

    for i, (ra, rb) in enumerate(zip(reference["hardware_fixture"], current["hardware_fixture"])):
        check(f"hardware_fixture[{i}].equilibrium_flow_l_min", ra["equilibrium_flow_l_min"], rb["equilibrium_flow_l_min"], abs_tol["hardware_flow_l_min"])
        check(f"hardware_fixture[{i}].pump_head_mmhg", ra["pump_head_mmhg"], rb["pump_head_mmhg"], abs_tol["head"])

    return {"passed": not failures, "failure_count": len(failures), "failures": failures, "tolerances": abs_tol}
