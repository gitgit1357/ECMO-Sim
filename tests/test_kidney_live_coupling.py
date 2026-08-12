from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from neokidney import KidneyParameters,KidneyState,calculate_kidney_state
from neorenalcoupling import run_cv_kidney,run_cvlung_kidney
from neolung import LungParameters
from neolung.gas_exchange import GasExchangeParameters

def test_standalone_normal_urine():
    r=calculate_kidney_state(KidneyParameters(),KidneyState(),map_mmhg=52,cvp_mmhg=4,systemic_flow_ml_min=800)
    assert 1.5 < r.urine_ml_kg_hr < 2.5

def test_live_cv_drives_kidney():
    r=run_cv_kidney()
    assert r.circulation_metrics.mean_aortic_mmhg > 35
    assert r.kidney.renal_flow_ml_min > 30
    assert r.kidney.urine_ml_kg_hr > 1.0

def test_renal_vasoconstriction_reduces_rbf():
    b=run_cv_kidney(1.0)
    c=run_cv_kidney(1.7)
    assert c.kidney.renal_flow_ml_min < b.kidney.renal_flow_ml_min

def test_live_cvlung_normal_is_stable():
    r=run_cvlung_kidney()
    assert 35 < r.circulation_metrics.mean_aortic_mmhg < 70
    assert r.gas_pao2_mmhg > 70
    assert r.kidney.urine_ml_kg_hr > 1.0

def test_peep_can_reduce_renal_perfusion():
    b=run_cvlung_kidney()
    p=run_cvlung_kidney(lung_params=LungParameters(peep_cmh2o=8.0))
    assert p.circulation_metrics.native_output_ml_min < b.circulation_metrics.native_output_ml_min
    assert p.kidney.renal_flow_ml_min <= b.kidney.renal_flow_ml_min + 1e-6

def test_hypoxia_does_not_directly_fake_renal_failure():
    b=run_cvlung_kidney()
    h=run_cvlung_kidney(gas_params=GasExchangeParameters(fio2=0.12))
    assert h.gas_pao2_mmhg < b.gas_pao2_mmhg
    assert h.kidney.urine_ml_kg_hr >= 0
