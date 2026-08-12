from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from neoecmo import BridgeParameters, bridge_flow_ml_min, run_bridge_clamp_sweep_bench

CLAMP_STEPS = (0.0, 0.1, 0.25, 0.5, 0.75, 1.0)
UPSTREAM = 150.0
DOWNSTREAM = 50.0

out = {"schema": "ecmo-bridge-northstar-v1", "cases": {}}

sweep_points = run_bridge_clamp_sweep_bench(
    clamp_position_steps=CLAMP_STEPS,
    upstream_pressure_mmhg=UPSTREAM,
    downstream_pressure_mmhg=DOWNSTREAM,
)
out["cases"]["clamp_sweep"] = {
    f"{p.clamp_position:.2f}": {"solved_flow_ml_min": p.solved_flow_ml_min} for p in sweep_points
}

closed_gradients = {
    "forward": (150.0, 50.0),
    "large_forward": (500.0, -200.0),
    "equal": (0.0, 0.0),
    "reversed": (50.0, 150.0),
}
out["cases"]["closed_clamp_gradients"] = {
    name: {
        "solved_flow_ml_min": bridge_flow_ml_min(
            up, down, BridgeParameters(clamp_position=0.0)
        )
    }
    for name, (up, down) in closed_gradients.items()
}

path = ROOT / "ecmo_bridge_regression_bench" / "current_ecmo_bridge_northstar.json"
path.write_text(json.dumps(out, indent=2) + "\n")
print(path)
