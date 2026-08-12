from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from neolung import run_standalone_peep_gas_point

print("Standalone lung/gas exchange: PEEP effect at fixed pulmonary perfusion")
for peep in [0,5,8,12]:
    r=run_standalone_peep_gas_point(peep,pulmonary_perfusion_fraction=1.0)
    print(f"PEEP {peep:>2}: VT={r.tidal_volume_ml:4.1f} "
          f"VA={r.alveolar_ventilation_ml_min:6.1f} "
          f"PaCO2={r.paco2_mmhg:5.1f} PaO2={r.pao2_mmhg:5.1f}")

print("\nStandalone lung/gas exchange: perfusion effect at fixed PEEP 5")
for q in [1.2,1.0,0.8,0.6,0.4]:
    r=run_standalone_peep_gas_point(5,pulmonary_perfusion_fraction=q)
    print(f"Qfrac {q:>3.1f}: effectiveVA={r.effective_clearance_ventilation_ml_min:6.1f} "
          f"PaCO2={r.paco2_mmhg:5.1f}")
