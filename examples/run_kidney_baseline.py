from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT))
from neokidney import KidneyParameters,KidneyState,calculate_kidney_state

r=calculate_kidney_state(KidneyParameters(),KidneyState(),
    map_mmhg=52,cvp_mmhg=4,systemic_flow_ml_min=800)
print(f"Renal flow: {r.renal_flow_ml_min:.1f} mL/min")
print(f"Renal share: {100*r.renal_flow_fraction_of_systemic:.1f}%")
print(f"Filtration index: {r.filtration_index:.2f}")
print(f"Urine output: {r.urine_ml_kg_hr:.2f} mL/kg/hr")
