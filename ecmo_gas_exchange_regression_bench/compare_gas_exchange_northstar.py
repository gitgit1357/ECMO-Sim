from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
subprocess.run(
    [sys.executable, str(ROOT / "ecmo_gas_exchange_regression_bench" / "run_gas_exchange_northstar.py")],
    check=True,
)
a = json.loads(
    (ROOT / "ecmo_gas_exchange_regression_bench" / "accepted_ecmo_gas_exchange_northstar_v1.json").read_text()
)
c = json.loads(
    (ROOT / "ecmo_gas_exchange_regression_bench" / "current_ecmo_gas_exchange_northstar.json").read_text()
)

tols = {"outlet_saturation": 0.001, "outlet_paco2_mmhg": 0.05}

fail = []
for case_name, accepted_flows in a["cases"].items():
    for flow_key, accepted_values in accepted_flows.items():
        current_values = c["cases"][case_name][flow_key]
        for key, accepted_value in accepted_values.items():
            diff = abs(current_values[key] - accepted_value)
            if diff > tols[key]:
                fail.append((case_name, flow_key, key, accepted_value, current_values[key], diff))

if fail:
    print("ECMO Gas Exchange NorthStar differences outside tolerance:")
    for x in fail:
        print(x)
    raise SystemExit(1)
print("ECMO Gas Exchange NorthStar v1: PASS — 0 differences outside tolerance")
