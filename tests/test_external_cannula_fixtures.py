from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bench_fixtures.cannulas import load_medtronic_life_support_mini


def test_manufacturer_anchor_points_are_reproduced():
    for r in load_medtronic_life_support_mini():
        assert abs(r.estimated_pressure_loss_mmhg(r.flow_l_min_at_minus_40_mmhg) - 40.0) < 1e-9
        assert abs(r.estimated_pressure_loss_mmhg(r.flow_l_min_at_plus_100_mmhg) - 100.0) < 1e-9


def test_larger_cannula_has_lower_loss_at_same_flow():
    records = load_medtronic_life_support_mini()
    losses = [r.estimated_pressure_loss_mmhg(0.5) for r in records]
    assert losses == sorted(losses, reverse=True)


def test_patient_engine_does_not_import_bench_fixtures():
    src = ROOT / "src" / "neocirculation"
    for path in src.glob("*.py"):
        assert "bench_fixtures" not in path.read_text(encoding="utf-8")


def test_overlay_module_is_external_only():
    overlay = ROOT / "bench_fixtures" / "cannula_overlay.py"
    assert overlay.exists()
    assert "neocirculation" not in overlay.read_text(encoding="utf-8")


def test_patient_engine_does_not_import_regression_or_pump_fixtures():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "src" / "neocirculation"
    text = "\n".join(p.read_text(encoding="utf-8") for p in root.glob("*.py"))
    assert "bench_fixtures" not in text
    assert "regression_bench" not in text
