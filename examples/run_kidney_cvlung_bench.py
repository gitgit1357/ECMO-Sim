from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT))
from neorenalcoupling import run_cvlung_kidney
from neolung import LungParameters
from neolung.gas_exchange import GasExchangeParameters

cases=[
    ("normal heart+lung",{},{}),
    ("PEEP 8",{"peep_cmh2o":8.0},{}),
    ("hypoxia",{},{"fio2":0.12}),
    ("low compliance",{"compliance_ml_per_cmh2o":2.6},{}),
]
for name,lkw,gkw in cases:
    lp=LungParameters(**lkw) if lkw else None
    gp=GasExchangeParameters(**gkw) if gkw else None
    r=run_cvlung_kidney(lung_params=lp,gas_params=gp)
    c,k=r.circulation_metrics,r.kidney
    print(f"{name:20s} MAP={c.mean_aortic_mmhg:5.1f} CO={c.native_output_ml_min:6.0f} "
          f"PaO2={r.gas_pao2_mmhg:5.1f} RBF={k.renal_flow_ml_min:5.1f} UO={k.urine_ml_kg_hr:4.2f}")
