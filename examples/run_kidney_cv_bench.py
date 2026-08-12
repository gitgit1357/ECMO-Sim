from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT))
from neorenalcoupling import run_cv_kidney

for name,tone,func in [
    ("normal",1.0,1.0),
    ("renal vasoconstriction",1.7,1.0),
    ("renal vasodilation",0.7,1.0),
    ("50% renal function",1.0,0.5),
]:
    r=run_cv_kidney(tone,func)
    c,k=r.circulation_metrics,r.kidney
    print(f"{name:22s} MAP={c.mean_aortic_mmhg:5.1f} CVP={c.mean_ra_mmhg:4.1f} "
          f"CO={c.native_output_ml_min:6.0f} RBF={k.renal_flow_ml_min:5.1f} "
          f"UO={k.urine_ml_kg_hr:4.2f}")
