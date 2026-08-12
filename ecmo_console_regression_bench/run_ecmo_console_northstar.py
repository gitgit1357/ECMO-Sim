from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from neoecmo import EcmoConsoleControls, ShuntLineConfiguration, run_ecmo_console

NATIVE_SAT = 0.65
NATIVE_PACO2 = 55.0

CASES = {
    "baseline_bridge_closed": EcmoConsoleControls(rpm=3000.0, sweep_gas_flow_ml_min=600.0),
    "bridge_titrated_100": EcmoConsoleControls(
        rpm=3000.0, sweep_gas_flow_ml_min=600.0, bridge_target_flow_ml_min=100.0
    ),
    "hemofilter_active": EcmoConsoleControls(
        rpm=3000.0,
        sweep_gas_flow_ml_min=600.0,
        shunt_configuration=ShuntLineConfiguration.HEMOFILTER,
        shunt_scuffing_active=True,
    ),
    "ckrt_running": EcmoConsoleControls(
        rpm=3000.0,
        sweep_gas_flow_ml_min=600.0,
        shunt_configuration=ShuntLineConfiguration.CKRT,
        shunt_ckrt_blood_flow_ml_min=30.0,
        shunt_ckrt_net_ultrafiltration_rate_ml_min=2.0,
    ),
    "low_fdo2_low_sweep": EcmoConsoleControls(
        rpm=3000.0, sweep_gas_flow_ml_min=100.0, fdo2=0.4
    ),
}

out = {"schema": "ecmo-console-northstar-v1", "cases": {}}
for case_name, controls in CASES.items():
    state = run_ecmo_console(controls, NATIVE_SAT, NATIVE_PACO2)
    out["cases"][case_name] = {
        "solved_total_flow_ml_min": state.circuit.solved_total_flow_ml_min,
        "solved_shunt_flow_ml_min": state.circuit.solved_shunt_flow_ml_min,
        "solved_bridge_flow_ml_min": state.circuit.solved_bridge_flow_ml_min,
        "solved_patient_flow_ml_min": state.circuit.solved_patient_flow_ml_min,
        "resolved_bridge_clamp_position": state.resolved_bridge_clamp_position,
        "resolved_fdo2": state.resolved_fdo2,
        "post_oxygenator_saturation": state.post_oxygenator_saturation,
        "post_oxygenator_paco2_mmhg": state.post_oxygenator_paco2_mmhg,
        "cdi_mixed_saturation": state.cdi.mixed_saturation,
        "cdi_recirculation_fraction": state.cdi.recirculation_fraction,
        "cdi_mixed_paco2_mmhg": state.cdi.mixed_paco2_mmhg,
    }

path = ROOT / "ecmo_console_regression_bench" / "current_ecmo_console_northstar.json"
path.write_text(json.dumps(out, indent=2) + "\n")
print(path)
