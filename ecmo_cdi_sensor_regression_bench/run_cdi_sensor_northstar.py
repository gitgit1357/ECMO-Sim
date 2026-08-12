from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from neoecmo import (
    BridgeParameters,
    cdi_reading_from_circuit_point,
    outlet_o2_saturation,
    outlet_paco2_mmhg,
    solve_main_circuit_full_operating_point,
)

CLAMP_STEPS = (0.0, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0)
RPM = 3000.0
NATIVE_VENOUS_SATURATION = 0.65
NATIVE_VENOUS_PACO2 = 55.0
SWEEP_GAS_FLOW_ML_MIN = 600.0
FDO2 = 1.0

out = {"schema": "ecmo-cdi-sensor-northstar-v1", "cases": {}}

case = {}
for clamp in CLAMP_STEPS:
    point = solve_main_circuit_full_operating_point(
        RPM, bridge_params=BridgeParameters(clamp_position=clamp)
    )
    post_oxy_sat = outlet_o2_saturation(
        NATIVE_VENOUS_SATURATION, point.solved_total_flow_ml_min, FDO2
    )
    post_oxy_paco2 = outlet_paco2_mmhg(
        NATIVE_VENOUS_PACO2, point.solved_total_flow_ml_min, SWEEP_GAS_FLOW_ML_MIN
    )
    reading = cdi_reading_from_circuit_point(
        point,
        NATIVE_VENOUS_SATURATION,
        post_oxy_sat,
        NATIVE_VENOUS_PACO2,
        post_oxy_paco2,
    )
    case[f"{clamp:.2f}"] = {
        "mixed_saturation": reading.mixed_saturation,
        "recirculation_fraction": reading.recirculation_fraction,
        "mixed_paco2_mmhg": reading.mixed_paco2_mmhg,
    }
out["cases"]["clamp_sweep_at_3000rpm"] = case

path = ROOT / "ecmo_cdi_sensor_regression_bench" / "current_ecmo_cdi_sensor_northstar.json"
path.write_text(json.dumps(out, indent=2) + "\n")
print(path)
