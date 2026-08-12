from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from neoecmo import OxygenatorGasExchangeParameters, run_gas_exchange_bench

FLOW_STEPS = (100, 250, 500, 800, 1200, 1500, 2000, 3000)

CASES = {
    "clean_membrane": OxygenatorGasExchangeParameters(obstruction_fraction=0.0),
    "clotted_membrane": OxygenatorGasExchangeParameters(obstruction_fraction=0.5),
}

out = {"schema": "ecmo-gas-exchange-northstar-v1", "cases": {}}
for case_name, params in CASES.items():
    points = run_gas_exchange_bench(flow_steps_ml_min=FLOW_STEPS, params=params)
    out["cases"][case_name] = {
        str(int(p.blood_flow_ml_min)): {
            "outlet_saturation": p.outlet_saturation,
            "outlet_paco2_mmhg": p.outlet_paco2_mmhg,
        }
        for p in points
    }

path = ROOT / "ecmo_gas_exchange_regression_bench" / "current_ecmo_gas_exchange_northstar.json"
path.write_text(json.dumps(out, indent=2) + "\n")
print(path)
