from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from neokidney import KidneyParameters,KidneyState,calculate_kidney_state

print("Direct renal guardrail sweep at otherwise preserved MAP/flow")
for vf in [1.00,0.90,0.80,0.70,0.60,0.50,0.40]:
    r=calculate_kidney_state(
        KidneyParameters(),KidneyState(),
        map_mmhg=52,cvp_mmhg=4,systemic_flow_ml_min=836,
        diuretic_multiplier=2.0,
        circulating_volume_fraction=vf,
    )
    print(f"Volume {vf:4.2f} -> UO {r.urine_ml_kg_hr:5.2f} mL/kg/hr")
