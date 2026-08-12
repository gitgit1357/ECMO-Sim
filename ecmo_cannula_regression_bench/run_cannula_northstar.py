from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from neoecmo import DRAIN_10FR, RETURN_8FR, run_cannula_hydraulic_bench

FLOW_STEPS = (0, 100, 200, 300, 400, 500, 600, 800, 1000, 1200)

CASES = {
    "return_8fr": RETURN_8FR,
    "drain_10fr": DRAIN_10FR,
}

out = {"schema": "ecmo-cannula-northstar-v1", "cases": {}}
for case_name, params in CASES.items():
    points = run_cannula_hydraulic_bench(flow_steps_ml_min=FLOW_STEPS, params=params)
    out["cases"][case_name] = {
        str(int(p.flow_ml_min)): {"delta_p_mmhg": p.delta_p_mmhg} for p in points
    }

path = ROOT / "ecmo_cannula_regression_bench" / "current_ecmo_cannula_northstar.json"
path.write_text(json.dumps(out, indent=2) + "\n")
print(path)
