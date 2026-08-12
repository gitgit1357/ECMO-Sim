from pathlib import Path

import pytest

from neoecmo import (
    BridgeParameters,
    solve_main_circuit_with_shunt_and_bridge_operating_point,
    solve_main_circuit_with_shunt_operating_point,
)

ROOT = Path(__file__).resolve().parents[1]


# --- critical regression check: bridge closed by default must exactly ----
# --- reproduce Wiring Stage 2 (shunt-only) behavior ------------------------


def test_bridge_closed_by_default_reproduces_stage2_exactly():
    for rpm in (2000.0, 3000.0, 4000.0):
        stage2 = solve_main_circuit_with_shunt_operating_point(rpm)
        stage3 = solve_main_circuit_with_shunt_and_bridge_operating_point(rpm)
        assert stage3.solved_total_flow_ml_min == pytest.approx(
            stage2.solved_total_flow_ml_min, rel=1e-6
        )
        assert stage3.solved_shunt_flow_ml_min == pytest.approx(
            stage2.solved_shunt_flow_ml_min, rel=1e-6
        )
        assert stage3.solved_patient_flow_ml_min == pytest.approx(
            stage2.solved_patient_flow_ml_min, rel=1e-6
        )


def test_bridge_flow_is_zero_when_closed():
    p = solve_main_circuit_with_shunt_and_bridge_operating_point(3000.0)
    assert p.solved_bridge_flow_ml_min == 0.0
    assert p.bridge_fraction == 0.0


# --- flow conservation ------------------------------------------------------


def test_three_way_flow_sums_to_total():
    p = solve_main_circuit_with_shunt_and_bridge_operating_point(
        3000.0, bridge_params=BridgeParameters(clamp_position=0.3)
    )
    assert (
        p.solved_shunt_flow_ml_min + p.solved_bridge_flow_ml_min + p.solved_patient_flow_ml_min
    ) == pytest.approx(p.solved_total_flow_ml_min)
    assert (p.shunt_fraction + p.bridge_fraction + p.patient_fraction) == pytest.approx(1.0)


# --- opening the bridge progressively increases its share of flow ---------


def test_opening_bridge_increases_bridge_fraction_monotonically():
    fractions = [
        solve_main_circuit_with_shunt_and_bridge_operating_point(
            3000.0, bridge_params=BridgeParameters(clamp_position=c)
        ).bridge_fraction
        for c in (0.0, 0.05, 0.1, 0.3, 0.6, 1.0)
    ]
    assert fractions == sorted(fractions)
    assert fractions[0] == 0.0
    assert fractions[-1] > fractions[0]


def test_opening_bridge_reduces_patient_fraction():
    closed = solve_main_circuit_with_shunt_and_bridge_operating_point(3000.0)
    open_bridge = solve_main_circuit_with_shunt_and_bridge_operating_point(
        3000.0, bridge_params=BridgeParameters(clamp_position=0.3)
    )
    assert open_bridge.patient_fraction < closed.patient_fraction


def test_fully_open_bridge_dominates_flow():
    p = solve_main_circuit_with_shunt_and_bridge_operating_point(
        3000.0, bridge_params=BridgeParameters(clamp_position=1.0)
    )
    assert p.bridge_fraction > 0.9


# --- degenerate rpm=0 case still solves -------------------------------------


def test_zero_rpm_still_solves():
    p = solve_main_circuit_with_shunt_and_bridge_operating_point(0.0)
    assert p.solved_total_flow_ml_min == pytest.approx(0.0, abs=1e-6)


# --- module boundary ---------------------------------------------------------


def test_module_does_not_import_patient_physiology_modules():
    forbidden = ("neocirculation", "neolung", "neokidney", "neocoupling", "neopatient")
    text = (
        ROOT / "src" / "neoecmo" / "main_circuit_with_shunt_and_bridge.py"
    ).read_text(encoding="utf-8")
    for name in forbidden:
        assert f"import {name}" not in text
        assert f"from {name}" not in text
