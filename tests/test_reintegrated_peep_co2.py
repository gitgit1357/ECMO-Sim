from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from neocoupling import run_coupled_neonate
from neolung import LungParameters

def test_reintegrated_peep_co2_stays_plausible():
    b=run_coupled_neonate()
    p=run_coupled_neonate(lung_params=LungParameters(peep_cmh2o=8))
    assert 25 < p.gas.arterial_pco2_mmhg < 65
    assert p.circulation_metrics.native_output_ml_min < b.circulation_metrics.native_output_ml_min

def test_reintegrated_lower_flow_does_not_improve_co2_clearance_artificially():
    b=run_coupled_neonate()
    p=run_coupled_neonate(lung_params=LungParameters(peep_cmh2o=12))
    assert p.pulmonary_flow_ml_min < b.pulmonary_flow_ml_min
    assert p.gas.arterial_pco2_mmhg > 25
