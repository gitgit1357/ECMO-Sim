from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from neoecmo import run_pump_head_bench

CASES = {
    "default_boundary": dict(
        inlet_reservoir_mmhg=0.0,
        outlet_reservoir_mmhg=0.0,
        resistance_in_mmhg_per_ml_min=0.02,
        resistance_out_mmhg_per_ml_min=0.05,
    ),
    "elevated_outlet_pressure": dict(
        inlet_reservoir_mmhg=0.0,
        outlet_reservoir_mmhg=300.0,
        resistance_in_mmhg_per_ml_min=0.02,
        resistance_out_mmhg_per_ml_min=0.05,
    ),
    "depleted_inlet_pressure": dict(
        inlet_reservoir_mmhg=-80.0,
        outlet_reservoir_mmhg=0.0,
        resistance_in_mmhg_per_ml_min=0.02,
        resistance_out_mmhg_per_ml_min=0.05,
    ),
    "high_resistance": dict(
        inlet_reservoir_mmhg=0.0,
        outlet_reservoir_mmhg=0.0,
        resistance_in_mmhg_per_ml_min=0.10,
        resistance_out_mmhg_per_ml_min=0.20,
    ),
}

RPM_STEPS = (0, 1500, 2000, 2500, 3000, 3500, 4000)

out = {"schema": "ecmo-pump-northstar-v1", "cases": {}}
for case_name, boundary in CASES.items():
    points = run_pump_head_bench(rpm_steps=RPM_STEPS, **boundary)
    out["cases"][case_name] = {
        str(int(p.rpm)): {
            "solved_flow_ml_min": p.solved_flow_ml_min,
            "p1_mmhg": p.p1_mmhg,
            "p2_mmhg": p.p2_mmhg,
            "pump_head_mmhg": p.pump_head_mmhg,
        }
        for p in points
    }

path = ROOT / "ecmo_pump_regression_bench" / "current_ecmo_pump_northstar.json"
path.write_text(json.dumps(out, indent=2) + "\n")
print(path)
