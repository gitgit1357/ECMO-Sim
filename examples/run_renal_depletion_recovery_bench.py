from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from neokidney import KidneyParameters,KidneyState,calculate_kidney_state

sequence=[1.00,0.90,0.80,0.70,0.60,0.50,0.70,0.85,1.00]
print("Depletion then recovery with diuretic x2 still active")
for vf in sequence:
    # Couple simple pressure/flow deterioration to volume depletion for the bench.
    mapv=52 if vf>=0.9 else max(22,52*(0.55+0.5*vf))
    flow=836 if vf>=0.9 else max(250,836*(0.45+0.6*vf))
    cvp=max(1.0,4.0*vf)
    r=calculate_kidney_state(
        KidneyParameters(),KidneyState(),
        map_mmhg=mapv,cvp_mmhg=cvp,systemic_flow_ml_min=flow,
        diuretic_multiplier=2.0,circulating_volume_fraction=vf,
    )
    print(f"vf={vf:4.2f} MAP={mapv:4.1f} flow={flow:5.0f} -> UO={r.urine_ml_kg_hr:5.2f}")
