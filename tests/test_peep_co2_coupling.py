from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from neocoupling import run_coupled_neonate
from neolung import LungParameters

def test_peep_does_not_cause_massive_hypocapnia():
    b=run_coupled_neonate()
    p=run_coupled_neonate(lung_params=LungParameters(peep_cmh2o=8.0))
    assert 28 <= p.gas.arterial_pco2_mmhg <= 60
    assert p.gas.arterial_pco2_mmhg > b.gas.arterial_pco2_mmhg * 0.70

def test_peep_hemodynamic_effect_remains():
    b=run_coupled_neonate()
    p=run_coupled_neonate(lung_params=LungParameters(peep_cmh2o=8.0))
    assert p.circulation_metrics.native_output_ml_min < b.circulation_metrics.native_output_ml_min
