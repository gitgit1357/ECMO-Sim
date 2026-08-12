from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from neoecmo import FixedShuntParameters, ShuntLineConfiguration, run_fixed_shunt_bench

DOWNSTREAM_STEPS = (-50, 0, 50, 100, 150, 200)
UPSTREAM = 150.0

CASES = {
    "no_filter": FixedShuntParameters(configuration=ShuntLineConfiguration.OPEN),
    "filter_inactive": FixedShuntParameters(
        configuration=ShuntLineConfiguration.HEMOFILTER, scuffing_active=False
    ),
    "filter_active": FixedShuntParameters(
        configuration=ShuntLineConfiguration.HEMOFILTER, scuffing_active=True
    ),
    "ckrt": FixedShuntParameters(configuration=ShuntLineConfiguration.CKRT),
}

out = {"schema": "ecmo-fixed-shunt-northstar-v1", "cases": {}}
for case_name, params in CASES.items():
    points = run_fixed_shunt_bench(
        downstream_pressure_steps_mmhg=DOWNSTREAM_STEPS,
        upstream_pressure_mmhg=UPSTREAM,
        params=params,
    )
    out["cases"][case_name] = {
        str(int(p.downstream_pressure_mmhg)): {"solved_flow_ml_min": p.solved_flow_ml_min}
        for p in points
    }

path = ROOT / "ecmo_fixed_shunt_regression_bench" / "current_ecmo_fixed_shunt_northstar.json"
path.write_text(json.dumps(out, indent=2) + "\n")
print(path)
