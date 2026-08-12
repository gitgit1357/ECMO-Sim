from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
subprocess.run(
    [sys.executable, str(ROOT / "ecmo_fixed_shunt_regression_bench" / "run_fixed_shunt_northstar.py")],
    check=True,
)
a = json.loads(
    (ROOT / "ecmo_fixed_shunt_regression_bench" / "accepted_ecmo_fixed_shunt_northstar_v1.json").read_text()
)
c = json.loads(
    (ROOT / "ecmo_fixed_shunt_regression_bench" / "current_ecmo_fixed_shunt_northstar.json").read_text()
)

tol_ml_min = 0.5

fail = []
for case_name, accepted_pressures in a["cases"].items():
    for pressure_key, accepted_values in accepted_pressures.items():
        current_values = c["cases"][case_name][pressure_key]
        diff = abs(current_values["solved_flow_ml_min"] - accepted_values["solved_flow_ml_min"])
        if diff > tol_ml_min:
            fail.append(
                (case_name, pressure_key, accepted_values["solved_flow_ml_min"], current_values["solved_flow_ml_min"], diff)
            )

if fail:
    print("ECMO Fixed Shunt NorthStar differences outside tolerance:")
    for x in fail:
        print(x)
    raise SystemExit(1)
print("ECMO Fixed Shunt NorthStar v1: PASS — 0 differences outside tolerance")
