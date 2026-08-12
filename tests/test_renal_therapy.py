from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from neokidney import RenalTherapyInputs
from neorenalcoupling import run_renal_therapy_step

BASE=dict(map_mmhg=52,cvp_mmhg=4,systemic_flow_ml_min=836)

def test_diuretic_increases_urine():
    b=run_renal_therapy_step(**BASE,therapy=RenalTherapyInputs())
    d=run_renal_therapy_step(**BASE,therapy=RenalTherapyInputs(diuretic_multiplier=2.0))
    assert d.urine_ml_min > b.urine_ml_min

def test_fluid_input_positive_balance():
    r=run_renal_therapy_step(**BASE,therapy=RenalTherapyInputs(fluid_in_ml_min=5.0),dt_min=10)
    assert r.cumulative_net_ml > 0

def test_external_fluid_removal_negative_balance():
    r=run_renal_therapy_step(**BASE,therapy=RenalTherapyInputs(external_fluid_out_ml_min=2.0),dt_min=10)
    assert r.cumulative_net_ml < 0

def test_vasoconstriction_reduces_rbf():
    b=run_renal_therapy_step(**BASE,therapy=RenalTherapyInputs())
    c=run_renal_therapy_step(**BASE,therapy=RenalTherapyInputs(renal_vaso_tone=1.7))
    assert c.renal_flow_ml_min < b.renal_flow_ml_min

def test_reduced_function_reduces_urine():
    b=run_renal_therapy_step(**BASE,therapy=RenalTherapyInputs())
    f=run_renal_therapy_step(**BASE,therapy=RenalTherapyInputs(function_fraction=0.4))
    assert f.urine_ml_min < b.urine_ml_min
