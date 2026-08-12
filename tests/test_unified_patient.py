import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
from neopatient import UnifiedNeonatalPatient,AirwayPort,RenalTherapyPort,VascularSupportPort

def test_baseline_three_systems():
    s=UnifiedNeonatalPatient().snapshot()
    assert 30<s.map_mmhg<80 and s.pao2_mmhg>60 and s.renal_flow_ml_min>20

def test_peep_changes_live_patient():
    p=UnifiedNeonatalPatient(); b=p.snapshot(); p.set_airway(AirwayPort(peep_cmh2o=8)); h=p.snapshot()
    assert h.native_cardiac_output_ml_min < b.native_cardiac_output_ml_min

def test_fluid_removal_changes_volume():
    p=UnifiedNeonatalPatient(); b=p.snapshot(); p.set_renal_therapy(RenalTherapyPort(external_fluid_out_ml_min=2)); a=p.advance(30)
    assert a.total_blood_volume_ml<b.total_blood_volume_ml and a.urine_ml_kg_hr<=b.urine_ml_kg_hr

def test_equipment_port_contract():
    p=UnifiedNeonatalPatient(); p.set_vascular_support(VascularSupportPort(True,350,100)); s=p.snapshot()
    assert s.vascular_support_enabled and s.vascular_support_flow_ml_min==350
