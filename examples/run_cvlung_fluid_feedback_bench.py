import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
from neokidney import RenalTherapyInputs
from neorenalcoupling import run_cvlung_fluid_feedback
for name,t,mins in [("baseline",RenalTherapyInputs(),20),("fluid",RenalTherapyInputs(fluid_in_ml_min=5),10),("UF",RenalTherapyInputs(external_fluid_out_ml_min=2),30)]:
 r=run_cvlung_fluid_feedback(t,duration_min=mins); print(name,r)
