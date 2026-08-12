from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
subprocess.run(
    [sys.executable, str(ROOT / "ecmo_cdi_sensor_regression_bench" / "run_cdi_sensor_northstar.py")],
    check=True,
)
a = json.loads(
    (ROOT / "ecmo_cdi_sensor_regression_bench" / "accepted_ecmo_cdi_sensor_northstar_v1.json").read_text()
)
c = json.loads(
    (ROOT / "ecmo_cdi_sensor_regression_bench" / "current_ecmo_cdi_sensor_northstar.json").read_text()
)

tols = {"mixed_saturation": 0.001, "recirculation_fraction": 0.001, "mixed_paco2_mmhg": 0.05}

fail = []
for case_name, accepted_keys in a["cases"].items():
    for key, accepted_values in accepted_keys.items():
        current_values = c["cases"][case_name][key]
        for field, accepted_value in accepted_values.items():
            diff = abs(current_values[field] - accepted_value)
            if diff > tols[field]:
                fail.append((case_name, key, field, accepted_value, current_values[field], diff))

if fail:
    print("ECMO CDI Sensor NorthStar differences outside tolerance:")
    for x in fail:
        print(x)
    raise SystemExit(1)

# Extra hard check: bridge closed (clamp 0.00) must show ZERO recirculation.
closed = c["cases"]["clamp_sweep_at_3000rpm"]["0.00"]
if closed["recirculation_fraction"] != 0.0 or closed["mixed_saturation"] != 0.65:
    print("CRITICAL: bridge-closed CDI reading is contaminated — topology guarantee broken.")
    raise SystemExit(1)

print("ECMO CDI Sensor NorthStar v1: PASS — 0 differences outside tolerance")
