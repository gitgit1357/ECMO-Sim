from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from neokidney import RenalTherapyInputs
from neorenalcoupling import run_renal_therapy_step

# Demonstrates the deliberately simple volume-feedback estimate only.
scenarios=[
    ("10 min 5 mL/min bolus",RenalTherapyInputs(fluid_in_ml_min=5.0),10),
    ("30 min diuresis x2",RenalTherapyInputs(diuretic_multiplier=2.0),30),
    ("30 min UF 2 mL/min",RenalTherapyInputs(external_fluid_out_ml_min=2.0),30),
]
for name,therapy,mins in scenarios:
    r=run_renal_therapy_step(map_mmhg=52,cvp_mmhg=4,systemic_flow_ml_min=836,
                             therapy=therapy,dt_min=mins)
    print(f"{name:24s} net={r.cumulative_net_ml:+6.1f} mL "
          f"estimated immediate intravascular effect={r.estimated_blood_volume_delta_ml:+5.1f} mL")
