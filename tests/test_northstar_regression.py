from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bench_fixtures.pumps import NORTHSTAR_TEST_PUMP_V1


def test_synthetic_pump_fixture_affinity_behavior():
    assert NORTHSTAR_TEST_PUMP_V1.head_mmhg(4000, 0) == 320.0
    assert abs(NORTHSTAR_TEST_PUMP_V1.head_mmhg(4000, 2.0)) < 1e-9
    assert NORTHSTAR_TEST_PUMP_V1.free_flow_l_min(2000) == 1.0


def test_accepted_northstar_snapshot_is_versioned_and_frozen():
    root = Path(__file__).resolve().parents[1]
    path = root / "regression_bench" / "reference_snapshots" / "northstar_v1_accepted.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["manifest"]["bench_id"] == "neonatal-circulation-northstar-v1"
    assert data["manifest"]["pump_fixture_id"] == "northstar-synthetic-centrifugal-v1"
    assert data["manifest"]["fixed_flow_steps_ml_kg_min"] == [0, 50, 100, 150, 200]
