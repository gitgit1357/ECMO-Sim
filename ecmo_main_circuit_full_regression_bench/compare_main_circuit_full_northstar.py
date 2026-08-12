from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
subprocess.run(
    [
        sys.executable,
        str(ROOT / "ecmo_main_circuit_full_regression_bench" / "run_main_circuit_full_northstar.py"),
    ],
    check=True,
)
a = json.loads(
    (
        ROOT
        / "ecmo_main_circuit_full_regression_bench"
        / "accepted_ecmo_main_circuit_full_northstar_v1.json"
    ).read_text()
)
c = json.loads(
    (
        ROOT
        / "ecmo_main_circuit_full_regression_bench"
        / "current_ecmo_main_circuit_full_northstar.json"
    ).read_text()
)

tols = {
    "solved_total_flow_ml_min": 0.5,
    "solved_shunt_flow_ml_min": 0.5,
    "solved_bridge_flow_ml_min": 0.5,
    "solved_patient_flow_ml_min": 0.5,
    "shunt_fraction": 0.001,
    "bridge_fraction": 0.001,
    "patient_fraction": 0.001,
}

fail = []
for case_name, accepted_keys in a["cases"].items():
    for key, accepted_values in accepted_keys.items():
        current_values = c["cases"][case_name][key]
        for field, accepted_value in accepted_values.items():
            diff = abs(current_values[field] - accepted_value)
            if diff > tols[field]:
                fail.append((case_name, key, field, accepted_value, current_values[field], diff))

if fail:
    print("ECMO Main Circuit Full NorthStar differences outside tolerance:")
    for x in fail:
        print(x)
    raise SystemExit(1)
print("ECMO Main Circuit Full NorthStar v1: PASS — 0 differences outside tolerance")
