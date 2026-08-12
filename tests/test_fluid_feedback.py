import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
from neokidney import RenalTherapyInputs
from neorenalcoupling import run_cv_fluid_feedback,run_cvlung_fluid_feedback
def test_fluid_changes_true_blood_volume():
 b=run_cv_fluid_feedback(RenalTherapyInputs(),duration_min=10); f=run_cv_fluid_feedback(RenalTherapyInputs(fluid_in_ml_min=5),duration_min=10); assert f.total_blood_volume_ml>b.total_blood_volume_ml
def test_uf_reduces_true_blood_volume_and_flow():
 b=run_cv_fluid_feedback(RenalTherapyInputs(),duration_min=30); u=run_cv_fluid_feedback(RenalTherapyInputs(external_fluid_out_ml_min=2),duration_min=30); assert u.total_blood_volume_ml<b.total_blood_volume_ml and u.cvp_mmhg<b.cvp_mmhg and u.cardiac_output_ml_min<b.cardiac_output_ml_min
def test_fluid_increases_preload():
 b=run_cv_fluid_feedback(RenalTherapyInputs(),duration_min=10); f=run_cv_fluid_feedback(RenalTherapyInputs(fluid_in_ml_min=5),duration_min=10); assert f.cvp_mmhg>b.cvp_mmhg
def test_cvlung_uf_keeps_gas_and_reduces_flow():
 b=run_cvlung_fluid_feedback(RenalTherapyInputs(),duration_min=20); u=run_cvlung_fluid_feedback(RenalTherapyInputs(external_fluid_out_ml_min=2),duration_min=20); assert u.cardiac_output_ml_min<b.cardiac_output_ml_min and u.pao2_mmhg>0 and u.paco2_mmhg>0
