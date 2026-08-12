from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src')); sys.path.insert(0,str(ROOT))
from bench_fixtures.ventilator import PressureControlVentilator
from bench_fixtures.ventilator_bench import run_ventilator_case


def test_lung_does_not_import_ventilator_fixture():
    for p in (ROOT/'src'/'neolung').glob('*.py'):
        text=p.read_text()
        assert 'bench_fixtures' not in text
        assert 'PressureControlVentilator' not in text


def test_pressure_control_changes_tidal_volume_with_drive_pressure():
    low=run_ventilator_case('low',PressureControlVentilator(8,5,40,0.35))
    high=run_ventilator_case('high',PressureControlVentilator(18,5,40,0.35))
    assert high.tidal_volume_ml > low.tidal_volume_ml


def test_stiff_lung_gets_less_tidal_volume_at_same_ventilator_settings():
    vent=PressureControlVentilator(10,5,40,0.35)
    normal=run_ventilator_case('normal',vent)
    stiff=run_ventilator_case('stiff',vent,lung_changes={'compliance_ml_per_cmh2o':3.5})
    assert stiff.tidal_volume_ml < normal.tidal_volume_ml


def test_high_resistance_reduces_delivered_tidal_volume():
    vent=PressureControlVentilator(10,5,40,0.35)
    normal=run_ventilator_case('normal',vent)
    resistive=run_ventilator_case('resistive',vent,lung_changes={'airway_resistance_cmh2o_s_per_l':90.0})
    assert resistive.tidal_volume_ml < normal.tidal_volume_ml
