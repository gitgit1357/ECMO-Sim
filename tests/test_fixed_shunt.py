from pathlib import Path

import pytest

from neoecmo import (
    FixedShuntParameters,
    ScuffingFiltrationState,
    ShuntLineConfiguration,
    fixed_shunt_flow_ml_min,
    run_fixed_shunt_bench,
    step_filtrate_removal,
)

ROOT = Path(__file__).resolve().parents[1]


# --- basic hydraulics (OPEN configuration) ---------------------------------


def test_zero_pressure_difference_gives_zero_flow():
    assert fixed_shunt_flow_ml_min(100.0, 100.0) == 0.0


def test_flow_runs_from_high_to_low_pressure():
    forward = fixed_shunt_flow_ml_min(150.0, 50.0)
    assert forward > 0.0


def test_reversed_pressure_gradient_gives_negative_flow_not_an_error():
    reversed_flow = fixed_shunt_flow_ml_min(50.0, 150.0)
    assert reversed_flow < 0.0


def test_larger_pressure_difference_increases_flow_magnitude():
    small = fixed_shunt_flow_ml_min(120.0, 100.0)
    large = fixed_shunt_flow_ml_min(300.0, 100.0)
    assert large > small > 0.0


# --- HEMOFILTER: installed vs active are independent axes ------------------


def test_hemofilter_installed_but_inactive_still_adds_resistance():
    no_filter = FixedShuntParameters(configuration=ShuntLineConfiguration.OPEN)
    filter_inactive = FixedShuntParameters(
        configuration=ShuntLineConfiguration.HEMOFILTER, scuffing_active=False
    )
    flow_no_filter = fixed_shunt_flow_ml_min(150.0, 50.0, no_filter)
    flow_with_filter = fixed_shunt_flow_ml_min(150.0, 50.0, filter_inactive)
    assert flow_with_filter < flow_no_filter


def test_scuffing_active_state_does_not_change_hydraulic_resistance():
    inactive = FixedShuntParameters(
        configuration=ShuntLineConfiguration.HEMOFILTER, scuffing_active=False
    )
    active = FixedShuntParameters(
        configuration=ShuntLineConfiguration.HEMOFILTER, scuffing_active=True
    )
    flow_inactive = fixed_shunt_flow_ml_min(150.0, 50.0, inactive)
    flow_active = fixed_shunt_flow_ml_min(150.0, 50.0, active)
    assert flow_inactive == pytest.approx(flow_active)


def test_removing_filter_lowers_resistance_raises_flow():
    installed = FixedShuntParameters(configuration=ShuntLineConfiguration.HEMOFILTER)
    removed = FixedShuntParameters(configuration=ShuntLineConfiguration.OPEN)
    assert fixed_shunt_flow_ml_min(150.0, 50.0, removed) > fixed_shunt_flow_ml_min(
        150.0, 50.0, installed
    )


# --- CKRT: 3-way stopcock means shunt flow passes through unaffected ------


def test_ckrt_configuration_behaves_identically_to_open_hydraulically():
    open_params = FixedShuntParameters(configuration=ShuntLineConfiguration.OPEN)
    ckrt_params = FixedShuntParameters(configuration=ShuntLineConfiguration.CKRT)
    for upstream, downstream in [(150.0, 50.0), (500.0, -200.0), (0.0, 0.0), (50.0, 150.0)]:
        assert fixed_shunt_flow_ml_min(upstream, downstream, ckrt_params) == pytest.approx(
            fixed_shunt_flow_ml_min(upstream, downstream, open_params)
        )


def test_ckrt_shunt_flow_still_responds_to_clot_fraction():
    # CKRT doesn't bypass the tubing itself -- clot in the shunt tubing
    # still raises resistance the same way it would in OPEN.
    clean = FixedShuntParameters(configuration=ShuntLineConfiguration.CKRT, clot_fraction=0.0)
    clotted = FixedShuntParameters(configuration=ShuntLineConfiguration.CKRT, clot_fraction=0.7)
    assert fixed_shunt_flow_ml_min(150.0, 50.0, clotted) < fixed_shunt_flow_ml_min(
        150.0, 50.0, clean
    )


def test_ckrt_blood_flow_field_does_not_affect_shunt_hydraulics():
    # ckrt_blood_flow_ml_min is informational only -- the CKRT machine's
    # own independent pump flow never enters the shunt's own calculation.
    low = FixedShuntParameters(configuration=ShuntLineConfiguration.CKRT, ckrt_blood_flow_ml_min=20.0)
    high = FixedShuntParameters(configuration=ShuntLineConfiguration.CKRT, ckrt_blood_flow_ml_min=40.0)
    assert fixed_shunt_flow_ml_min(150.0, 50.0, low) == pytest.approx(
        fixed_shunt_flow_ml_min(150.0, 50.0, high)
    )


def test_ckrt_gives_more_shunt_flow_than_hemofilter():
    # CKRT doesn't add the built-in filter's resistance (its pigtails tap
    # a side port rather than occupying the inline path), so shunt flow
    # under CKRT should be higher than under HEMOFILTER, matching OPEN.
    ckrt_flow = fixed_shunt_flow_ml_min(150.0, 50.0, FixedShuntParameters(configuration=ShuntLineConfiguration.CKRT))
    hemofilter_flow = fixed_shunt_flow_ml_min(150.0, 50.0, FixedShuntParameters(configuration=ShuntLineConfiguration.HEMOFILTER))
    assert ckrt_flow > hemofilter_flow


# --- clot fraction raises resistance (OPEN/HEMOFILTER only) ----------------


def test_clot_fraction_raises_resistance_lowers_flow():
    clean = FixedShuntParameters(clot_fraction=0.0)
    clotted = FixedShuntParameters(clot_fraction=0.7)
    assert fixed_shunt_flow_ml_min(150.0, 50.0, clotted) < fixed_shunt_flow_ml_min(
        150.0, 50.0, clean
    )


# --- filtrate removal tracking (HEMOFILTER only) ---------------------------


def test_filtrate_accumulates_only_with_hemofilter_and_active():
    params = FixedShuntParameters(
        configuration=ShuntLineConfiguration.HEMOFILTER,
        scuffing_active=True,
        ultrafiltration_rate_ml_min=10.0,
    )
    state = ScuffingFiltrationState()
    state = step_filtrate_removal(state, dt_s=60.0, params=params)
    assert state.cumulative_filtrate_volume_ml == pytest.approx(10.0)


def test_filtrate_does_not_accumulate_if_hemofilter_but_inactive():
    params = FixedShuntParameters(configuration=ShuntLineConfiguration.HEMOFILTER, scuffing_active=False)
    state = ScuffingFiltrationState()
    state = step_filtrate_removal(state, dt_s=60.0, params=params)
    assert state.cumulative_filtrate_volume_ml == 0.0


def test_filtrate_does_not_accumulate_if_active_but_not_hemofilter():
    params = FixedShuntParameters(configuration=ShuntLineConfiguration.OPEN, scuffing_active=True)
    state = ScuffingFiltrationState()
    state = step_filtrate_removal(state, dt_s=60.0, params=params)
    assert state.cumulative_filtrate_volume_ml == 0.0


def test_filtrate_does_not_accumulate_during_ckrt_even_if_active_flag_set():
    # scuffing_active is a hemofilter-specific flag; it should have no
    # effect while the line is actually configured for CKRT.
    params = FixedShuntParameters(configuration=ShuntLineConfiguration.CKRT, scuffing_active=True)
    state = ScuffingFiltrationState()
    state = step_filtrate_removal(state, dt_s=60.0, params=params)
    assert state.cumulative_filtrate_volume_ml == 0.0


def test_ckrt_net_ultrafiltration_accumulates_while_machine_is_running():
    params = FixedShuntParameters(
        configuration=ShuntLineConfiguration.CKRT,
        ckrt_blood_flow_ml_min=30.0,
        ckrt_net_ultrafiltration_rate_ml_min=2.0,
    )
    state = ScuffingFiltrationState()
    state = step_filtrate_removal(state, dt_s=60.0, params=params)
    assert state.cumulative_filtrate_volume_ml == pytest.approx(2.0)


def test_ckrt_net_ultrafiltration_does_not_accumulate_if_machine_not_running():
    # ckrt_blood_flow_ml_min == 0 means the machine isn't actually
    # connected/running, even if a net UF rate is configured.
    params = FixedShuntParameters(
        configuration=ShuntLineConfiguration.CKRT,
        ckrt_blood_flow_ml_min=0.0,
        ckrt_net_ultrafiltration_rate_ml_min=2.0,
    )
    state = ScuffingFiltrationState()
    state = step_filtrate_removal(state, dt_s=60.0, params=params)
    assert state.cumulative_filtrate_volume_ml == 0.0


def test_ckrt_net_ultrafiltration_is_much_smaller_than_ckrt_blood_flow():
    # Sanity check on the clinical description: CKRT returns nearly all
    # of what it draws, minus only the small intentionally-removed amount.
    params = FixedShuntParameters(
        configuration=ShuntLineConfiguration.CKRT,
        ckrt_blood_flow_ml_min=30.0,
        ckrt_net_ultrafiltration_rate_ml_min=2.0,
    )
    assert params.ckrt_net_ultrafiltration_rate_ml_min < params.ckrt_blood_flow_ml_min


def test_filtrate_removal_rejects_negative_dt():
    params = FixedShuntParameters(configuration=ShuntLineConfiguration.HEMOFILTER, scuffing_active=True)
    state = ScuffingFiltrationState()
    with pytest.raises(ValueError):
        step_filtrate_removal(state, dt_s=-1.0, params=params)


# --- bench sanity -----------------------------------------------------------


def test_bench_sweep_returns_one_point_per_downstream_step():
    steps = (-50, 0, 100, 200)
    points = run_fixed_shunt_bench(downstream_pressure_steps_mmhg=steps, upstream_pressure_mmhg=150.0)
    assert [p.downstream_pressure_mmhg for p in points] == [float(s) for s in steps]
    # Higher downstream pressure (closer to/exceeding upstream) lowers/reverses flow.
    flows = [p.solved_flow_ml_min for p in points]
    assert flows == sorted(flows, reverse=True)


# --- module boundary ---------------------------------------------------------


def test_fixed_shunt_module_does_not_import_patient_physiology_modules():
    forbidden = ("neocirculation", "neolung", "neokidney", "neocoupling", "neopatient")
    for filename in ("fixed_shunt.py", "fixed_shunt_bench.py"):
        text = (ROOT / "src" / "neoecmo" / filename).read_text(encoding="utf-8")
        for name in forbidden:
            assert f"import {name}" not in text
            assert f"from {name}" not in text
