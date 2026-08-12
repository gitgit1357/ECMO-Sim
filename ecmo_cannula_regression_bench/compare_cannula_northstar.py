from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
subprocess.run(
    [sys.executable, str(ROOT / "ecmo_cannula_regression_bench" / "run_cannula_northstar.py")],
    check=True,
)
a = json.loads(
    (ROOT / "ecmo_cannula_regression_bench" / "accepted_ecmo_cannula_northstar_v1.json").read_text()
)
c = json.loads(
    (ROOT / "ecmo_cannula_regression_bench" / "current_ecmo_cannula_northstar.json").read_text()
)

tol_mmhg = 0.05

fail = []
for case_name, accepted_flows in a["cases"].items():
    for flow_key, accepted_values in accepted_flows.items():
        current_values = c["cases"][case_name][flow_key]
        diff = abs(current_values["delta_p_mmhg"] - accepted_values["delta_p_mmhg"])
        if diff > tol_mmhg:
            fail.append((case_name, flow_key, accepted_values["delta_p_mmhg"], current_values["delta_p_mmhg"], diff))

if fail:
    print("ECMO Cannula NorthStar differences outside tolerance:")
    for x in fail:
        print(x)
    raise SystemExit(1)
print("ECMO Cannula NorthStar v1: PASS — 0 differences outside tolerance")
