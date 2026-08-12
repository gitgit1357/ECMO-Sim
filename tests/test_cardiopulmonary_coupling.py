from neocoupling import run_coupled_neonate
from neolung import LungParameters
from neolung.gas_exchange import GasExchangeParameters


def test_neutral_coupling_preserves_baseline_reasonably():
    r = run_coupled_neonate(duration_lung_s=12, duration_circulation_s=12)
    assert 45 <= r.circulation_metrics.mean_aortic_mmhg <= 58
    assert 650 <= r.circulation_metrics.native_output_ml_min <= 950
    assert 0.8 <= r.pvr_multiplier <= 1.2


def test_hypoxia_increases_pvr_and_reduces_pulmonary_flow():
    normal = run_coupled_neonate(duration_lung_s=12, duration_circulation_s=12)
    hypoxic = run_coupled_neonate(gas_params=GasExchangeParameters(fio2=0.12), duration_lung_s=12, duration_circulation_s=12)
    assert hypoxic.gas.arterial_po2_mmhg < normal.gas.arterial_po2_mmhg
    assert hypoxic.pvr_multiplier > normal.pvr_multiplier
    assert hypoxic.pulmonary_flow_ml_min < normal.pulmonary_flow_ml_min


def test_positive_pressure_changes_thoracic_boundary_without_cross_imports():
    r = run_coupled_neonate(lung_params=LungParameters(peep_cmh2o=8.0), duration_lung_s=12, duration_circulation_s=12)
    assert r.pleural_delta_mmhg == r.pleural_delta_mmhg


def test_higher_peep_reduces_native_output_via_coupling():
    normal = run_coupled_neonate(duration_lung_s=12, duration_circulation_s=12)
    peep = run_coupled_neonate(lung_params=LungParameters(peep_cmh2o=8.0), duration_lung_s=12, duration_circulation_s=12)
    assert peep.circulation_metrics.native_output_ml_min < normal.circulation_metrics.native_output_ml_min


def test_coupling_is_separate_module_boundary():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / 'src'
    circ_text = '\n'.join(p.read_text() for p in (root/'neocirculation').glob('*.py'))
    lung_text = '\n'.join(p.read_text() for p in (root/'neolung').glob('*.py'))
    assert 'neocoupling' not in circ_text
    assert 'neocoupling' not in lung_text
