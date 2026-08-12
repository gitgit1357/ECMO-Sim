import pytest

from neoecmo.tubing_geometry import (
    MEASURED_SEGMENTS,
    poiseuille_linear_resistance_mmhg_per_ml_min,
    resistance_for_segment,
    reynolds_number,
)


# --- physical scaling laws, not just fixed numbers -------------------------


def test_resistance_scales_linearly_with_length():
    r_short = poiseuille_linear_resistance_mmhg_per_ml_min(0.375, 1.0)
    r_long = poiseuille_linear_resistance_mmhg_per_ml_min(0.375, 3.0)
    assert r_long == pytest.approx(r_short * 3.0, rel=1e-9)


def test_resistance_scales_as_inverse_fourth_power_of_diameter():
    r_wide = poiseuille_linear_resistance_mmhg_per_ml_min(0.375, 1.0)
    r_half_diameter = poiseuille_linear_resistance_mmhg_per_ml_min(0.1875, 1.0)
    assert r_half_diameter == pytest.approx(r_wide * 16.0, rel=1e-6)


def test_resistance_scales_linearly_with_viscosity():
    r_at_3cp = poiseuille_linear_resistance_mmhg_per_ml_min(0.375, 1.0, viscosity_cp=3.0)
    r_at_6cp = poiseuille_linear_resistance_mmhg_per_ml_min(0.375, 1.0, viscosity_cp=6.0)
    assert r_at_6cp == pytest.approx(r_at_3cp * 2.0, rel=1e-9)


def test_narrower_shunt_tubing_has_much_higher_resistance_than_main_tubing():
    main = MEASURED_SEGMENTS["main_pre_pump"]
    shunt = MEASURED_SEGMENTS["fixed_shunt_tubing"]
    r_main_per_ft = poiseuille_linear_resistance_mmhg_per_ml_min(
        main.inner_diameter_in, 1.0
    )
    r_shunt_per_ft = poiseuille_linear_resistance_mmhg_per_ml_min(
        shunt.inner_diameter_in, 1.0
    )
    # 3/8" vs 1/16" is a 6x diameter ratio -> 6^4 = 1296x resistance per foot.
    assert r_shunt_per_ft == pytest.approx(r_main_per_ft * 1296.0, rel=1e-6)


# --- reynolds number / laminar-flow confirmation ---------------------------


def test_reynolds_number_increases_with_flow():
    re_low = reynolds_number(50.0, 0.375)
    re_high = reynolds_number(500.0, 0.375)
    assert re_high > re_low


def test_main_circuit_stays_laminar_across_realistic_neonatal_flows():
    for flow in (50, 200, 500, 1000):
        assert reynolds_number(flow, 0.375) < 2300.0


def test_bridge_tubing_stays_laminar_across_realistic_neonatal_flows():
    for flow in (50, 200, 500, 1000):
        assert reynolds_number(flow, 0.375) < 2300.0


def test_shunt_tubing_stays_laminar_at_realistic_shunt_flows():
    # The shunt is restrictive by design and should never carry flows
    # anywhere near the main circuit's — confirm laminar at the range it
    # would actually operate in.
    for flow in (10, 30, 50, 100):
        assert reynolds_number(flow, 0.0625) < 2300.0


def test_shunt_tubing_approaches_turbulent_only_at_unrealistically_high_flow():
    # At a flow far beyond what the shunt should ever see, Reynolds number
    # approaches/exceeds the laminar limit — documenting why the narrow
    # bore is an intentional restrictive design choice, not just "small".
    assert reynolds_number(500.0, 0.0625) >= 2300.0


# --- named segment lookup ---------------------------------------------------


def test_resistance_for_segment_matches_direct_calculation():
    segment = MEASURED_SEGMENTS["main_pre_pump"]
    direct = poiseuille_linear_resistance_mmhg_per_ml_min(
        segment.inner_diameter_in, segment.length_ft
    )
    assert resistance_for_segment("main_pre_pump") == pytest.approx(direct)


def test_all_measured_segments_are_resolvable():
    for name in MEASURED_SEGMENTS:
        r = resistance_for_segment(name)
        assert r > 0.0
