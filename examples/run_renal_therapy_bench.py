from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from neokidney import RenalTherapyInputs
from neorenalcoupling import run_renal_therapy_step

BASE=dict(map_mmhg=52.0,cvp_mmhg=4.0,systemic_flow_ml_min=836.0)

cases=[
    ("baseline", RenalTherapyInputs()),
    ("fluid bolus +5 mL/min", RenalTherapyInputs(fluid_in_ml_min=5.0)),
    ("diuresis x2", RenalTherapyInputs(diuretic_multiplier=2.0)),
    ("vasoconstriction", RenalTherapyInputs(renal_vaso_tone=1.7)),
    ("vasodilation", RenalTherapyInputs(renal_vaso_tone=0.7)),
    ("poor renal function", RenalTherapyInputs(function_fraction=0.4)),
    ("external fluid removal", RenalTherapyInputs(external_fluid_out_ml_min=2.0)),
]

for name,therapy in cases:
    r=run_renal_therapy_step(**BASE,therapy=therapy,dt_min=10.0)
    print(f"{name:24s} RBF={r.renal_flow_ml_min:5.1f} "
          f"UO={r.urine_ml_kg_hr:4.2f} mL/kg/hr "
          f"net={r.net_fluid_ml_min:+5.2f} mL/min "
          f"10-min balance={r.cumulative_net_ml:+6.1f} mL")
