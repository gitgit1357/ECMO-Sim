from dataclasses import replace

from neoecmo import EcmoConsoleControls
from neoecmocoupling import PatientToEcmoState, solve_volume_limited_va_ecmo


def patient(**changes):
    base = PatientToEcmoState(
        weight_kg=3.0,
        venous_pressure_mmhg=5.0,
        arterial_pressure_mmhg=42.0,
        blood_volume_fraction=1.0,
        native_cardiac_output_ml_min=300.0,
        native_venous_oxygen_saturation=0.65,
        native_venous_paco2_mmhg=55.0,
    )
    return replace(base, **changes)


def test_lower_blood_volume_reduces_sustainable_drainage_and_patient_flow():
    controls = EcmoConsoleControls(rpm=3200, sweep_gas_flow_ml_min=600)
    normal = solve_volume_limited_va_ecmo(controls, patient(blood_volume_fraction=1.0))
    low = solve_volume_limited_va_ecmo(controls, patient(blood_volume_fraction=0.65))
    assert low.sustainable_drainage_flow_ml_min < normal.sustainable_drainage_flow_ml_min
    assert low.delivered_patient_flow_ml_min < normal.delivered_patient_flow_ml_min


def test_hypovolemia_makes_effective_drainage_pressure_more_negative():
    controls = EcmoConsoleControls(rpm=3200, sweep_gas_flow_ml_min=600)
    normal = solve_volume_limited_va_ecmo(controls, patient(blood_volume_fraction=1.0))
    low = solve_volume_limited_va_ecmo(controls, patient(blood_volume_fraction=0.60))
    assert low.effective_venous_pressure_mmhg < normal.effective_venous_pressure_mmhg
    assert low.closed_loop.ecmo_state.circuit.p1_mmhg < normal.closed_loop.ecmo_state.circuit.p1_mmhg


def test_excessive_rpm_with_low_volume_produces_chatter():
    result = solve_volume_limited_va_ecmo(
        EcmoConsoleControls(rpm=4000, sweep_gas_flow_ml_min=600),
        patient(blood_volume_fraction=0.55),
    )
    assert result.chatter_active
    assert result.chatter_severity > 0
    assert result.chatter_low_flow_ml_min < result.chatter_high_flow_ml_min


def test_lowering_rpm_can_reduce_or_clear_chatter():
    low_volume = patient(blood_volume_fraction=0.55)
    high = solve_volume_limited_va_ecmo(EcmoConsoleControls(rpm=4000), low_volume)
    lower = solve_volume_limited_va_ecmo(EcmoConsoleControls(rpm=1800), low_volume)
    assert high.chatter_active
    assert lower.drainage_demand_ratio < high.drainage_demand_ratio
    assert lower.chatter_severity <= high.chatter_severity


def test_bridge_flow_does_not_expand_patient_drainage_capacity():
    p = patient(blood_volume_fraction=0.70)
    closed = solve_volume_limited_va_ecmo(EcmoConsoleControls(rpm=3300, bridge_clamp_position=0.0), p)
    open_bridge = solve_volume_limited_va_ecmo(EcmoConsoleControls(rpm=3300, bridge_clamp_position=1.0), p)
    assert open_bridge.sustainable_drainage_flow_ml_min == closed.sustainable_drainage_flow_ml_min
    assert open_bridge.closed_loop.ecmo_state.circuit.solved_bridge_flow_ml_min > 0


def test_normal_volume_at_moderate_rpm_does_not_chatter():
    result = solve_volume_limited_va_ecmo(EcmoConsoleControls(rpm=2200), patient())
    assert not result.chatter_active
