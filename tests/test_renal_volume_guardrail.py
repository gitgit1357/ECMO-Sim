from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from neokidney import KidneyParameters,KidneyState,calculate_kidney_state

def calc(vf,diuretic=1.0,mapv=52,flow=836,cvp=4):
    return calculate_kidney_state(
        KidneyParameters(),KidneyState(),
        map_mmhg=mapv,cvp_mmhg=cvp,systemic_flow_ml_min=flow,
        diuretic_multiplier=diuretic,circulating_volume_fraction=vf
    )

def test_volume_depletion_progressively_suppresses_urine():
    vals=[calc(v).urine_ml_kg_hr for v in [1.0,0.8,0.7,0.6,0.5]]
    assert all(a>b for a,b in zip(vals,vals[1:]))

def test_diuretic_cannot_override_severe_volume_depletion():
    normal=calc(1.0,2.0).urine_ml_kg_hr
    depleted=calc(0.5,2.0,mapv=28,flow=350,cvp=2).urine_ml_kg_hr
    assert depleted < normal*0.15

def test_near_anuria_at_critical_depletion():
    r=calc(0.4,1.0,mapv=22,flow=250,cvp=1)
    assert r.urine_ml_kg_hr < 0.2

def test_recovery_restores_urine():
    low=calc(0.5,1.0,mapv=28,flow=350,cvp=2).urine_ml_kg_hr
    rec=calc(0.9,1.0,mapv=50,flow=780,cvp=3.5).urine_ml_kg_hr
    assert rec > low*4
