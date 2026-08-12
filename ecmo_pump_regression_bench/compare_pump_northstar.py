from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
subprocess.run(
    [sys.executable, str(ROOT / "ecmo_pump_regression_bench" / "run_pump_northstar.py")],
    check=True,
)
a = json.loads((ROOT / "ecmo_pump_regression_bench" / "accepted_ecmo_pump_northstar_v1.json").read_text())
c = json.loads((ROOT / "ecmo_pump_regression_bench" / "current_ecmo_pump_northstar.json").read_text())

tols = {
    "solved_flow_ml_min": 0.5,
    "p1_mmhg": 0.05,
    "p2_mmhg": 0.05,
    "pump_head_mmhg": 0.05,
}

fail = []
for case_name, accepted_rpms in a["cases"].items():
    for rpm_key, accepted_values in accepted_rpms.items():
        current_values = c["cases"][case_name][rpm_key]
        for key, accepted_value in accepted_values.items():
            diff = abs(current_values[key] - accepted_value)
            if diff > tols[key]:
                fail.append((case_name, rpm_key, key, accepted_value, current_values[key], diff))

if fail:
    print("ECMO Pump NorthStar differences outside tolerance:")
    for x in fail:
        print(x)
    raise SystemExit(1)
print("ECMO Pump NorthStar v1: PASS — 0 differences outside tolerance")
