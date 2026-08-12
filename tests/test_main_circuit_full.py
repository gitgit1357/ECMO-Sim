from pathlib import Path

import pytest

from neoecmo import (
    BridgeParameters,
    patient_path_delta_p_mmhg,
    solve_main_circuit_full_operating_point,
    solve_patient_path_flow_ml_min,
)

ROOT = Path(__file__).resolve().parents[1]


# --- patient_path.py: forward/inverse consistency --------------------------


def test_solve_patient_path_flow_inverts_delta_p_function():
    for flow in (100.0, 250.0, 360.0, 500.0):
        dp = patient_path_delta_p_mmhg(flow)
        solved_flow = solve_patient_path_flow_ml_min(dp)
        assert solved_flow == pytest.approx(flow, rel=1e-4)


def test_patient_path_zero_delta_p_gives_zero_flow():
    assert solve_patient_path_flow_ml_min(0.0) == 0.0


def test_patient_path_delta_p_increases_with_flow():
    deltas = [patient_path_delta_p_mmhg(flow) for flow in (0, 200, 400, 600)]
    assert deltas == sorted(deltas)
    assert deltas[0] < deltas[-1]


# --- full circuit: flow conservation and pressure consistency -------------


def test_full_circuit_flow_conservation():
    p = solve_main_circuit_full_operating_point(3000.0)
    assert (
        p.solved_shunt_flow_ml_min + p.solved_bridge_flow_ml_min + p.solved_patient_flow_ml_min
    ) == pytest.approx(p.solved_total_flow_ml_min)


def test_full_circuit_pressure_consistency():
    p = solve_main_circuit_full_operating_point(3000.0)
    assert p.p3_mmhg - p.p1_mmhg == pytest.approx(p.junction_delta_p_mmhg)
    assert p.p2_mmhg - p.p3_mmhg == pytest.approx(p.oxygenator_delta_p_mmhg)


# --- cross-validation against the clinical author's real numbers, now ----
# --- with real cannulas instead of a flat placeholder ----------------------


def test_reproduces_real_numbers_closely_at_3000rpm_bridge_closed():
    # Real numbers: ~600 total / ~240 shunt / ~360 patient.
    p = solve_main_circuit_full_operating_point(3000.0)
    assert p.solved_total_flow_ml_min == pytest.approx(600.0, rel=0.10)
    assert p.solved_shunt_flow_ml_min == pytest.approx(240.0, rel=0.10)
    assert p.solved_patient_flow_ml_min == pytest.approx(360.0, rel=0.10)
    assert 0.35 <= p.shunt_fraction <= 0.42


# --- new emergent behavior: shunt fraction is NO LONGER flat across RPM ---
# --- now that the patient path includes real (quadratic) cannula terms ---


def test_shunt_fraction_now_increases_with_rpm_due_to_quadratic_cannula_terms():
    fractions = [
        solve_main_circuit_full_operating_point(rpm).shunt_fraction
        for rpm in (2000.0, 2500.0, 3000.0, 3500.0, 4000.0)
    ]
    assert fractions == sorted(fractions)
    assert fractions[-1] > fractions[0]


# --- bridge behavior carries over correctly with the real patient path ---


def test_bridge_closed_gives_zero_bridge_flow():
    p = solve_main_circuit_full_operating_point(3000.0)
    assert p.solved_bridge_flow_ml_min == 0.0


def test_bridge_crack_still_diverts_majority_of_flow():
    p = solve_main_circuit_full_operating_point(
        3000.0, bridge_params=BridgeParameters(clamp_position=0.1)
    )
    assert p.bridge_fraction > 0.5


# --- degenerate rpm=0 case still solves -------------------------------------


def test_zero_rpm_still_solves():
    p = solve_main_circuit_full_operating_point(0.0)
    assert p.solved_total_flow_ml_min == pytest.approx(0.0, abs=1e-6)


# --- module boundary ---------------------------------------------------------


def test_patient_path_does_not_import_patient_physiology_modules():
    forbidden = ("neocirculation", "neolung", "neokidney", "neocoupling", "neopatient")
    text = (ROOT / "src" / "neoecmo" / "patient_path.py").read_text(encoding="utf-8")
    for name in forbidden:
        assert f"import {name}" not in text
        assert f"from {name}" not in text


def test_main_circuit_full_does_not_import_patient_physiology_modules():
    forbidden = ("neocirculation", "neolung", "neokidney", "neocoupling", "neopatient")
    text = (ROOT / "src" / "neoecmo" / "main_circuit_full.py").read_text(encoding="utf-8")
    for name in forbidden:
        assert f"import {name}" not in text
        assert f"from {name}" not in text
