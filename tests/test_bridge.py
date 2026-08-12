from pathlib import Path

import pytest

from neoecmo import BridgeParameters, bridge_flow_ml_min, run_bridge_clamp_sweep_bench

ROOT = Path(__file__).resolve().parents[1]


# --- closed clamp: hard zero, not an asymptote -----------------------------


def test_fully_closed_clamp_gives_zero_flow_regardless_of_pressure_gradient():
    closed = BridgeParameters(clamp_position=0.0)
    for upstream, downstream in [(150.0, 50.0), (500.0, -200.0), (0.0, 0.0), (50.0, 150.0)]:
        assert bridge_flow_ml_min(upstream, downstream, closed) == 0.0


def test_near_zero_clamp_position_also_gives_zero_flow():
    nearly_closed = BridgeParameters(clamp_position=1e-9)
    assert bridge_flow_ml_min(150.0, 50.0, nearly_closed) == 0.0


# --- fully open clamp: normal signed-quadratic hydraulics ------------------


def test_fully_open_clamp_produces_forward_flow_with_forward_gradient():
    open_bridge = BridgeParameters(clamp_position=1.0)
    assert bridge_flow_ml_min(150.0, 50.0, open_bridge) > 0.0


def test_fully_open_clamp_produces_reversed_flow_with_reversed_gradient():
    open_bridge = BridgeParameters(clamp_position=1.0)
    assert bridge_flow_ml_min(50.0, 150.0, open_bridge) < 0.0


def test_zero_pressure_difference_gives_zero_flow_when_open():
    open_bridge = BridgeParameters(clamp_position=1.0)
    assert bridge_flow_ml_min(100.0, 100.0, open_bridge) == 0.0


# --- partial clamp: monotonic between closed and open ----------------------


def test_flow_increases_monotonically_with_clamp_position():
    positions = [0.05, 0.25, 0.5, 0.75, 1.0]
    flows = [
        bridge_flow_ml_min(150.0, 50.0, BridgeParameters(clamp_position=p)) for p in positions
    ]
    assert flows == sorted(flows)
    assert flows[0] < flows[-1]


def test_partial_opening_allows_weaning_trial_level_flow_below_fully_open():
    weaning = BridgeParameters(clamp_position=0.3)
    fully_open = BridgeParameters(clamp_position=1.0)
    assert 0.0 < bridge_flow_ml_min(150.0, 50.0, weaning) < bridge_flow_ml_min(
        150.0, 50.0, fully_open
    )


# --- clot fraction raises resistance at fixed clamp position --------------


def test_clot_fraction_raises_resistance_lowers_flow_at_fixed_clamp():
    clean = BridgeParameters(clamp_position=0.5, clot_fraction=0.0)
    clotted = BridgeParameters(clamp_position=0.5, clot_fraction=0.7)
    assert bridge_flow_ml_min(150.0, 50.0, clotted) < bridge_flow_ml_min(150.0, 50.0, clean)


# --- bench sanity -----------------------------------------------------------


def test_bench_sweep_returns_one_point_per_clamp_step():
    steps = (0.0, 0.25, 0.5, 1.0)
    points = run_bridge_clamp_sweep_bench(clamp_position_steps=steps)
    assert [p.clamp_position for p in points] == list(steps)
    assert points[0].solved_flow_ml_min == 0.0
    flows = [p.solved_flow_ml_min for p in points]
    assert flows == sorted(flows)


# --- module boundary ---------------------------------------------------------


def test_bridge_module_does_not_import_patient_physiology_modules():
    forbidden = ("neocirculation", "neolung", "neokidney", "neocoupling", "neopatient")
    for filename in ("bridge.py", "bridge_bench.py"):
        text = (ROOT / "src" / "neoecmo" / filename).read_text(encoding="utf-8")
        for name in forbidden:
            assert f"import {name}" not in text
            assert f"from {name}" not in text
