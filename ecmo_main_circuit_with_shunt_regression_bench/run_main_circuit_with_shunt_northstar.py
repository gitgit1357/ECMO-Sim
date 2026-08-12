from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from neoecmo import FixedShuntParameters, solve_main_circuit_with_shunt_operating_point

RPM_STEPS = (0, 1500, 2000, 2500, 3000, 3500, 4000)

CASES = {
    "clean_shunt": FixedShuntParameters(clot_fraction=0.0),
    "clotted_shunt": FixedShuntParameters(clot_fraction=0.5),
}

out = {"schema": "ecmo-main-circuit-with-shunt-northstar-v1", "cases": {}}
for case_name, shunt_params in CASES.items():
    case_out = {}
    for rpm in RPM_STEPS:
        point = solve_main_circuit_with_shunt_operating_point(
            float(rpm), shunt_params=shunt_params
        )
        case_out[str(int(rpm))] = {
            "solved_total_flow_ml_min": point.solved_total_flow_ml_min,
            "solved_shunt_flow_ml_min": point.solved_shunt_flow_ml_min,
            "solved_patient_flow_ml_min": point.solved_patient_flow_ml_min,
            "shunt_fraction": point.shunt_fraction,
        }
    out["cases"][case_name] = case_out

path = (
    ROOT
    / "ecmo_main_circuit_with_shunt_regression_bench"
    / "current_ecmo_main_circuit_with_shunt_northstar.json"
)
path.write_text(json.dumps(out, indent=2) + "\n")
print(path)
