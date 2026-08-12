from pathlib import Path

import pytest

from neoecmo import (
    DEFAULT_REVOLUTION_CURVE,
    pump_head_mmhg,
    run_pump_head_bench,
    solve_pump_operating_point,
)

ROOT = Path(__file__).resolve().parents[1]


# --- Acceptance criterion 2: zero RPM creates no pump head ------------------


def test_zero_rpm_creates_no_head_at_any_flow():
    for flow in (-500.0, 0.0, 250.0, 1000.0, 5000.0):
        assert pump_head_mmhg(0.0, flow) == 0.0


# --- Acceptance criterion 3: increasing RPM increases available head -------


def test_increasing_rpm_increases_available_head_at_fixed_flow():
    heads = [pump_head_mmhg(rpm, 400.0) for rpm in (1000, 2000, 3000, 4000)]
    assert heads == sorted(heads)
    assert heads[0] < heads[-1]


# --- Acceptance criterion 4: increasing resistance lowers flow -------------


def test_increasing_resistance_lowers_flow():
    low_r = solve_pump_operating_point(3000, 0.0, 0.0, 0.02, 0.05)
    high_r = solve_pump_operating_point(3000, 0.0, 0.0, 0.10, 0.20)
    assert high_r.solved_flow_ml_min < low_r.solved_flow_ml_min


# --- Acceptance criterion 5: higher outlet pressure lowers flow ------------


def test_higher_outlet_pressure_lowers_flow():
    low_outlet = solve_pump_operating_point(3000, 0.0, 0.0, 0.02, 0.05)
    high_outlet = solve_pump_operating_point(3000, 0.0, 200.0, 0.02, 0.05)
    assert high_outlet.solved_flow_ml_min < low_outlet.solved_flow_ml_min


# --- Acceptance criterion 6: lower inlet pressure lowers flow and makes ----
# --- P1 more negative -------------------------------------------------------


def test_lower_inlet_pressure_lowers_flow_and_more_negative_p1():
    normal_inlet = solve_pump_operating_point(3000, 0.0, 0.0, 0.02, 0.05)
    low_inlet = solve_pump_operating_point(3000, -80.0, 0.0, 0.02, 0.05)
    assert low_inlet.solved_flow_ml_min < normal_inlet.solved_flow_ml_min
    assert low_inlet.p1_mmhg < normal_inlet.p1_mmhg


# --- Acceptance criterion 7: same RPM can create multiple flows ------------


def test_same_rpm_can_produce_multiple_flows_under_different_conditions():
    a = solve_pump_operating_point(3000, 0.0, 0.0, 0.02, 0.05)
    b = solve_pump_operating_point(3000, 0.0, 300.0, 0.02, 0.05)
    assert a.solved_flow_ml_min != pytest.approx(b.solved_flow_ml_min)


# --- Acceptance criterion 8: solver remains stable across neonatal --------
# --- low-flow ranges ---------------------------------------------------------


def test_solver_stable_across_neonatal_low_flow_range():
    for rpm in (500, 1000, 1500, 2000, 2500, 3000, 3500, 4000):
        point = solve_pump_operating_point(rpm, 0.0, 0.0, 0.02, 0.05)
        assert point.solved_flow_ml_min == pytest.approx(point.solved_flow_ml_min)
        assert -20000.0 <= point.solved_flow_ml_min <= 20000.0


# --- Acceptance criterion 1: RPM never directly assigns flow ---------------
# (structural — the solver takes a resistance/pressure boundary as a required
# input; there is no code path that returns flow from RPM alone.)


def test_rpm_alone_does_not_determine_flow_without_boundary_conditions():
    same_rpm_different_flow = [
        solve_pump_operating_point(3000, 0.0, outlet, 0.02, 0.05).solved_flow_ml_min
        for outlet in (-100.0, 0.0, 100.0, 300.0)
    ]
    assert len(set(round(f, 3) for f in same_rpm_different_flow)) == len(
        same_rpm_different_flow
    )


# --- Acceptance criterion 9: pump curve implementation is isolated and -----
# --- replaceable -------------------------------------------------------------


def test_pump_curve_is_a_separate_replaceable_parameter_object():
    from neoecmo.pump import PumpHeadCurveParameters

    custom_curve = PumpHeadCurveParameters(
        rpm_ref=3000.0,
        k_shutoff_mmhg=500.0,
        k_droop_linear_mmhg_per_ml_min=0.2,
        k_droop_quad_mmhg_per_ml_min2=0.0001,
    )
    default_head = pump_head_mmhg(3000.0, 300.0, DEFAULT_REVOLUTION_CURVE)
    custom_head = pump_head_mmhg(3000.0, 300.0, custom_curve)
    assert default_head != pytest.approx(custom_head)


# --- Acceptance criterion 10: existing modular-patient tests remain --------
# --- unchanged and passing (enforced by running the full suite, not here) --

# --- Module boundary: neoecmo must not import the native physiology -------
# --- engines, mirroring the existing bench_fixtures boundary tests --------


def test_neoecmo_does_not_import_patient_physiology_modules():
    forbidden = ("neocirculation", "neolung", "neokidney", "neocoupling", "neopatient")
    src = ROOT / "src" / "neoecmo"
    for path in src.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for name in forbidden:
            assert f"import {name}" not in text, f"{path.name} imports {name}"
            assert f"from {name}" not in text, f"{path.name} imports from {name}"


def test_patient_physiology_modules_do_not_import_neoecmo():
    for pkg in ("neocirculation", "neolung", "neokidney", "neocoupling", "neopatient"):
        src = ROOT / "src" / pkg
        if not src.exists():
            continue
        for path in src.glob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert "import neoecmo" not in text
            assert "from neoecmo" not in text


# --- Sanity check on the bench sweep helper itself -------------------------


def test_bench_sweep_returns_one_point_per_rpm_step():
    steps = (0, 1000, 2000, 3000)
    points = run_pump_head_bench(rpm_steps=steps)
    assert [p.rpm for p in points] == list(steps)
    assert points[0].pump_head_mmhg == 0.0
