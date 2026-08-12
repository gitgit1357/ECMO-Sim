from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from neoecmo import run_oxygenator_hydraulic_bench

FLOW_STEPS = (0, 100, 200, 300, 400, 500, 600, 800)

CASES = {
    "clean_membrane": 0.0,
    "mild_clot": 0.3,
    "severe_clot": 0.8,
}

out = {"schema": "ecmo-oxygenator-northstar-v1", "cases": {}}
for case_name, obstruction in CASES.items():
    points = run_oxygenator_hydraulic_bench(
        flow_steps_ml_min=FLOW_STEPS, obstruction_fraction=obstruction
    )
    out["cases"][case_name] = {
        str(int(p.flow_ml_min)): {"delta_p_mmhg": p.delta_p_mmhg} for p in points
    }

path = ROOT / "ecmo_oxygenator_regression_bench" / "current_ecmo_oxygenator_northstar.json"
path.write_text(json.dumps(out, indent=2) + "\n")
print(path)
