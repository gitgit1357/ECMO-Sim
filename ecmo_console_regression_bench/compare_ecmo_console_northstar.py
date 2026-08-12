from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
subprocess.run(
    [sys.executable, str(ROOT / "ecmo_console_regression_bench" / "run_ecmo_console_northstar.py")],
    check=True,
)
a = json.loads(
    (ROOT / "ecmo_console_regression_bench" / "accepted_ecmo_console_northstar_v1.json").read_text()
)
c = json.loads(
    (ROOT / "ecmo_console_regression_bench" / "current_ecmo_console_northstar.json").read_text()
)

tol = 0.01

fail = []
for case_name, accepted_values in a["cases"].items():
    current_values = c["cases"][case_name]
    for field, accepted_value in accepted_values.items():
        if accepted_value is None:
            if current_values[field] is not None:
                fail.append((case_name, field, accepted_value, current_values[field], None))
            continue
        diff = abs(current_values[field] - accepted_value)
        if diff > tol:
            fail.append((case_name, field, accepted_value, current_values[field], diff))

if fail:
    print("ECMO Console NorthStar differences outside tolerance:")
    for x in fail:
        print(x)
    raise SystemExit(1)
print("ECMO Console NorthStar v1: PASS — 0 differences outside tolerance")
