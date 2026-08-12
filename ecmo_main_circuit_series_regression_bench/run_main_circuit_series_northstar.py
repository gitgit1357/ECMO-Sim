from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from neoecmo import OxygenatorHydraulicParameters, solve_main_circuit_series_operating_point

RPM_STEPS = (0, 1500, 2000, 2500, 3000, 3500, 4000)

CASES = {
    "clean_oxygenator": OxygenatorHydraulicParameters(obstruction_fraction=0.0),
    "clotted_oxygenator": OxygenatorHydraulicParameters(obstruction_fraction=0.5),
}

out = {"schema": "ecmo-main-circuit-series-northstar-v1", "cases": {}}
for case_name, oxy_params in CASES.items():
    case_out = {}
    for rpm in RPM_STEPS:
        point = solve_main_circuit_series_operating_point(
            float(rpm), 0.0, 0.0, oxygenator_params=oxy_params
        )
        case_out[str(int(rpm))] = {
            "solved_flow_ml_min": point.solved_flow_ml_min,
            "p1_mmhg": point.p1_mmhg,
            "p2_mmhg": point.p2_mmhg,
            "p3_mmhg": point.p3_mmhg,
        }
    out["cases"][case_name] = case_out

path = (
    ROOT
    / "ecmo_main_circuit_series_regression_bench"
    / "current_ecmo_main_circuit_series_northstar.json"
)
path.write_text(json.dumps(out, indent=2) + "\n")
print(path)
