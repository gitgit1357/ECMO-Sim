import pytest

from neoecmo import solve_bridge_clamp_position_for_target_flow


def test_zero_target_gives_zero_clamp_position():
    clamp, point = solve_bridge_clamp_position_for_target_flow(0.0, rpm=3000.0)
    assert clamp == 0.0
    assert point.solved_bridge_flow_ml_min == 0.0


def test_negative_target_treated_same_as_zero():
    clamp, point = solve_bridge_clamp_position_for_target_flow(-50.0, rpm=3000.0)
    assert clamp == 0.0
    assert point.solved_bridge_flow_ml_min == 0.0


def test_solved_clamp_position_actually_produces_target_flow():
    for target in (50.0, 100.0, 200.0, 400.0):
        clamp, point = solve_bridge_clamp_position_for_target_flow(target, rpm=3000.0)
        assert point.solved_bridge_flow_ml_min == pytest.approx(target, rel=1e-4)


def test_higher_target_flow_requires_more_open_clamp():
    clamp_low, _ = solve_bridge_clamp_position_for_target_flow(50.0, rpm=3000.0)
    clamp_high, _ = solve_bridge_clamp_position_for_target_flow(200.0, rpm=3000.0)
    assert clamp_high > clamp_low


def test_opening_bridge_for_target_flow_reduces_patient_flow():
    _, closed_point = solve_bridge_clamp_position_for_target_flow(0.0, rpm=3000.0)
    _, opened_point = solve_bridge_clamp_position_for_target_flow(100.0, rpm=3000.0)
    assert opened_point.solved_patient_flow_ml_min < closed_point.solved_patient_flow_ml_min


def test_unachievable_target_raises_clear_error():
    with pytest.raises(RuntimeError):
        solve_bridge_clamp_position_for_target_flow(50000.0, rpm=3000.0)


def test_bridge_clot_fraction_requires_more_opening_for_same_target_flow():
    clean_clamp, _ = solve_bridge_clamp_position_for_target_flow(
        100.0, rpm=3000.0, bridge_clot_fraction=0.0
    )
    clotted_clamp, _ = solve_bridge_clamp_position_for_target_flow(
        100.0, rpm=3000.0, bridge_clot_fraction=0.5
    )
    assert clotted_clamp > clean_clamp


def test_target_flow_is_preserved_when_live_patient_pressure_boundaries_are_supplied():
    target = 100.0
    _, point = solve_bridge_clamp_position_for_target_flow(
        target,
        rpm=3000.0,
        patient_arterial_pressure_mmhg=50.0,
        patient_venous_pressure_mmhg=5.0,
        live_patient_residual_vasculature_resistance_mmhg_per_ml_min=0.03,
    )
    assert point.solved_bridge_flow_ml_min == pytest.approx(target, abs=0.05)
