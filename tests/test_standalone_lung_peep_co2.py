from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from neolung import run_standalone_peep_gas_point

def test_peep_only_modestly_changes_co2_at_fixed_perfusion():
    b=run_standalone_peep_gas_point(0,pulmonary_perfusion_fraction=1.0)
    p=run_standalone_peep_gas_point(8,pulmonary_perfusion_fraction=1.0)
    assert p.paco2_mmhg > b.paco2_mmhg*0.80
    assert p.paco2_mmhg < b.paco2_mmhg*1.15

def test_lower_pulmonary_perfusion_reduces_co2_clearance():
    good=run_standalone_peep_gas_point(5,pulmonary_perfusion_fraction=1.0)
    low=run_standalone_peep_gas_point(5,pulmonary_perfusion_fraction=0.5)
    assert low.effective_clearance_ventilation_ml_min < good.effective_clearance_ventilation_ml_min
    assert low.paco2_mmhg > good.paco2_mmhg

def test_static_peep_does_not_create_artificial_hyperventilation():
    p=run_standalone_peep_gas_point(12,pulmonary_perfusion_fraction=1.0)
    assert p.paco2_mmhg > 25
