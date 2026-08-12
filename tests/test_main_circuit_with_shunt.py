from pathlib import Path

import pytest

from neoecmo import (
    FixedShuntParameters,
    solve_main_circuit_with_shunt_operating_point,
)

ROOT = Path(__file__).resolve().parents[1]


# --- flow conservation and internal consistency ----------------------------


def test_shunt_and_patient_flow_sum_to_total():
    p = solve_main_circuit_with_shunt_operating_point(3000.0)
    assert p.solved_shunt_flow_ml_min + p.solved_patient_flow_ml_min == pytest.approx(
        p.solved_total_flow_ml_min
    )


def test_junction_pressures_are_internally_consistent():
    p = solve_main_circuit_with_shunt_operating_point(3000.0)
    assert p.p3_mmhg - p.p1_mmhg == pytest.approx(p.junction_delta_p_mmhg)
    assert p.p2_mmhg - p.p3_mmhg == pytest.approx(p.oxygenator_delta_p_mmhg)


# --- cross-validation against the clinical author's real numbers ----------


def test_reproduces_reported_shunt_fraction_with_bridge_closed():
    # Real numbers: ~600 mL/min total, bridge closed -> shunt fraction 35-40%.
    p = solve_main_circuit_with_shunt_operating_point(3000.0)
    assert 0.35 <= p.shunt_fraction <= 0.42


def test_shunt_fraction_stays_roughly_constant_across_rpm():
    # Both branches are linear resistances in this stage (shunt quad term
    # is 0, patient-path placeholder is linear), so the split ratio should
    # not depend meaningfully on total flow/RPM.
    fractions = [
        solve_main_circuit_with_shunt_operating_point(rpm).shunt_fraction
        for rpm in (2000.0, 2500.0, 3000.0, 3500.0, 4000.0)
    ]
    assert max(fractions) - min(fractions) < 0.01


# --- shunt obstruction (clot) shifts the split toward the patient ---------


def test_shunt_clot_fraction_reduces_shunt_flow_fraction():
    clean_params = FixedShuntParameters(clot_fraction=0.0)
    clotted_params = FixedShuntParameters(clot_fraction=0.6)

    clean = solve_main_circuit_with_shunt_operating_point(3000.0, shunt_params=clean_params)
    clotted = solve_main_circuit_with_shunt_operating_point(
        3000.0, shunt_params=clotted_params
    )
    assert clotted.shunt_fraction < clean.shunt_fraction


# --- increasing RPM increases total flow -----------------------------------


def test_increasing_rpm_increases_total_flow():
    totals = [
        solve_main_circuit_with_shunt_operating_point(rpm).solved_total_flow_ml_min
        for rpm in (2000.0, 3000.0, 4000.0)
    ]
    assert totals == sorted(totals)
    assert totals[0] < totals[-1]


# --- module boundary ---------------------------------------------------------


def test_main_circuit_with_shunt_does_not_import_patient_physiology_modules():
    forbidden = ("neocirculation", "neolung", "neokidney", "neocoupling", "neopatient")
    text = (ROOT / "src" / "neoecmo" / "main_circuit_with_shunt.py").read_text(
        encoding="utf-8"
    )
    for name in forbidden:
        assert f"import {name}" not in text
        assert f"from {name}" not in text
