from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from neoecmo import BridgeParameters, solve_main_circuit_full_operating_point

RPM_STEPS = (0, 1500, 2000, 2500, 3000, 3500, 4000)
CLAMP_STEPS = (0.0, 0.05, 0.1, 0.3, 0.6, 1.0)

out = {"schema": "ecmo-main-circuit-full-northstar-v1", "cases": {}}

rpm_sweep = {}
for rpm in RPM_STEPS:
    point = solve_main_circuit_full_operating_point(float(rpm))
    rpm_sweep[str(int(rpm))] = {
        "solved_total_flow_ml_min": point.solved_total_flow_ml_min,
        "solved_shunt_flow_ml_min": point.solved_shunt_flow_ml_min,
        "solved_bridge_flow_ml_min": point.solved_bridge_flow_ml_min,
        "solved_patient_flow_ml_min": point.solved_patient_flow_ml_min,
        "shunt_fraction": point.shunt_fraction,
    }
out["cases"]["rpm_sweep_bridge_closed"] = rpm_sweep

clamp_sweep = {}
for clamp in CLAMP_STEPS:
    point = solve_main_circuit_full_operating_point(
        3000.0, bridge_params=BridgeParameters(clamp_position=clamp)
    )
    clamp_sweep[f"{clamp:.2f}"] = {
        "solved_total_flow_ml_min": point.solved_total_flow_ml_min,
        "shunt_fraction": point.shunt_fraction,
        "bridge_fraction": point.bridge_fraction,
        "patient_fraction": point.patient_fraction,
    }
out["cases"]["clamp_sweep_at_3000rpm"] = clamp_sweep

path = (
    ROOT / "ecmo_main_circuit_full_regression_bench" / "current_ecmo_main_circuit_full_northstar.json"
)
path.write_text(json.dumps(out, indent=2) + "\n")
print(path)
