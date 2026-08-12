from pathlib import Path
import ast
from neolung import NeonatalLungModel, derive_lung_metrics
from neolung.engineering import LungBenchCase, run_case


def test_normal_lung_produces_neonatal_scale_tidal_volume():
    m = derive_lung_metrics(NeonatalLungModel().run(30.0))
    assert 4.0 <= m.tidal_volume_ml_per_kg <= 8.0
    assert 500 <= m.minute_ventilation_ml_min <= 1300


def test_low_compliance_reduces_tidal_volume_at_same_effort():
    base = run_case(LungBenchCase("base", {}))
    low = run_case(LungBenchCase("low", {"compliance_ml_per_cmh2o": 3.5}))
    assert low.tidal_volume_ml < base.tidal_volume_ml


def test_high_airway_resistance_reduces_tidal_volume_at_same_rate_effort():
    base = run_case(LungBenchCase("base", {}))
    high = run_case(LungBenchCase("high", {"airway_resistance_cmh2o_s_per_l": 90.0}))
    assert high.tidal_volume_ml < base.tidal_volume_ml


def test_peep_raises_end_expiratory_volume():
    base = run_case(LungBenchCase("base", {}))
    peep = run_case(LungBenchCase("peep", {"peep_cmh2o": 5.0}))
    assert peep.end_expiratory_volume_ml > base.end_expiratory_volume_ml


def test_neolung_does_not_import_neocirculation():
    root = Path(__file__).resolve().parents[1] / "src" / "neolung"
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(not a.name.startswith("neocirculation") for a in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("neocirculation")
