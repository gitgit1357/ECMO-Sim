import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
from neopatient import UnifiedNeonatalPatient,AirwayPort,RenalTherapyPort
p=UnifiedNeonatalPatient()
for label in ["normal"]:
    s=p.snapshot(); print(label,s)
p.set_airway(AirwayPort(peep_cmh2o=8)); print("peep8",p.snapshot())
q=UnifiedNeonatalPatient(); q.set_renal_therapy(RenalTherapyPort(external_fluid_out_ml_min=2))
print("depleted",q.advance(30))
