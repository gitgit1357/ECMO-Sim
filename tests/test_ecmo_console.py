from pathlib import Path

import pytest

from neoecmo import (
    EcmoConsoleControls,
    ShuntLineConfiguration,
    run_ecmo_console,
)

ROOT = Path(__file__).resolve().parents[1]

NATIVE_SAT = 0.65
NATIVE_PACO2 = 55.0


def _run(**control_kwargs):
    controls = EcmoConsoleControls(**control_kwargs)
    return run_ecmo_console(controls, NATIVE_SAT, NATIVE_PACO2)


# --- basic operation, bridge closed by default -----------------------------


def test_basic_console_run_produces_consistent_bridge_closed_state():
    state = _run(rpm=3000.0, sweep_gas_flow_ml_min=600.0)
    assert state.circuit.solved_bridge_flow_ml_min == 0.0
    assert state.cdi.mixed_saturation == NATIVE_SAT
    assert state.cdi.recirculation_fraction == 0.0


def test_zero_rpm_gives_zero_flow():
    state = _run(rpm=0.0, sweep_gas_flow_ml_min=600.0)
    assert state.circuit.solved_total_flow_ml_min == pytest.approx(0.0, abs=1e-6)


# --- bridge titration by target flow (the realistic control action) -------


def test_bridge_target_flow_actually_achieves_target():
    state = _run(rpm=3000.0, sweep_gas_flow_ml_min=600.0, bridge_target_flow_ml_min=100.0)
    assert state.circuit.solved_bridge_flow_ml_min == pytest.approx(100.0, rel=1e-4)
    assert state.resolved_bridge_clamp_position > 0.0


def test_bridge_target_flow_shows_recirculation_at_cdi():
    state = _run(rpm=3000.0, sweep_gas_flow_ml_min=600.0, bridge_target_flow_ml_min=100.0)
    assert state.cdi.recirculation_fraction > 0.0
    assert state.cdi.mixed_saturation > NATIVE_SAT


def test_direct_clamp_position_ignored_when_target_flow_given():
    with_target = _run(
        rpm=3000.0,
        sweep_gas_flow_ml_min=600.0,
        bridge_clamp_position=0.9,  # should be ignored
        bridge_target_flow_ml_min=50.0,
    )
    assert with_target.circuit.solved_bridge_flow_ml_min == pytest.approx(50.0, rel=1e-4)


def test_direct_clamp_position_used_when_no_target_given():
    state = _run(rpm=3000.0, sweep_gas_flow_ml_min=600.0, bridge_clamp_position=0.5)
    assert state.resolved_bridge_clamp_position == 0.5
    assert state.circuit.solved_bridge_flow_ml_min > 0.0


# --- shunt configuration control --------------------------------------------


def test_hemofilter_configuration_reduces_shunt_flow_vs_open():
    open_state = _run(rpm=3000.0, sweep_gas_flow_ml_min=600.0)
    hemofilter_state = _run(
        rpm=3000.0,
        sweep_gas_flow_ml_min=600.0,
        shunt_configuration=ShuntLineConfiguration.HEMOFILTER,
    )
    assert hemofilter_state.circuit.solved_shunt_flow_ml_min < open_state.circuit.solved_shunt_flow_ml_min


def test_ckrt_configuration_matches_open_shunt_flow():
    open_state = _run(rpm=3000.0, sweep_gas_flow_ml_min=600.0)
    ckrt_state = _run(
        rpm=3000.0,
        sweep_gas_flow_ml_min=600.0,
        shunt_configuration=ShuntLineConfiguration.CKRT,
        shunt_ckrt_blood_flow_ml_min=30.0,
        shunt_ckrt_net_ultrafiltration_rate_ml_min=2.0,
    )
    assert ckrt_state.circuit.solved_shunt_flow_ml_min == pytest.approx(
        open_state.circuit.solved_shunt_flow_ml_min
    )


# --- sweep gas controls ------------------------------------------------------


def test_fdo2_is_rounded_to_real_blender_step():
    state = _run(rpm=3000.0, sweep_gas_flow_ml_min=600.0, fdo2=0.657)
    assert state.resolved_fdo2 == pytest.approx(0.66)


def test_lower_fdo2_reduces_post_oxygenator_saturation():
    full = _run(rpm=3000.0, sweep_gas_flow_ml_min=600.0, fdo2=1.0)
    half = _run(rpm=3000.0, sweep_gas_flow_ml_min=600.0, fdo2=0.5)
    assert half.post_oxygenator_saturation < full.post_oxygenator_saturation


def test_higher_sweep_gas_flow_improves_co2_clearance():
    low_sweep = _run(rpm=3000.0, sweep_gas_flow_ml_min=50.0)
    high_sweep = _run(rpm=3000.0, sweep_gas_flow_ml_min=1000.0)
    assert high_sweep.post_oxygenator_paco2_mmhg < low_sweep.post_oxygenator_paco2_mmhg


# --- pathology pass-through (not learner controls) doesn't break the console -


def test_shunt_and_bridge_clot_fraction_pass_through_without_error():
    state = _run(rpm=3000.0, sweep_gas_flow_ml_min=600.0)
    controls = EcmoConsoleControls(rpm=3000.0, sweep_gas_flow_ml_min=600.0)
    clotted_state = run_ecmo_console(
        controls,
        NATIVE_SAT,
        NATIVE_PACO2,
        shunt_clot_fraction=0.5,
        bridge_clot_fraction=0.5,
    )
    assert clotted_state.circuit.solved_shunt_flow_ml_min < state.circuit.solved_shunt_flow_ml_min


# --- module boundary ---------------------------------------------------------


def test_ecmo_console_does_not_import_patient_physiology_modules():
    forbidden = ("neocirculation", "neolung", "neokidney", "neocoupling", "neopatient")
    text = (ROOT / "src" / "neoecmo" / "ecmo_console.py").read_text(encoding="utf-8")
    for name in forbidden:
        assert f"import {name}" not in text
        assert f"from {name}" not in text
