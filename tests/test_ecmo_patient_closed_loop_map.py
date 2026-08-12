from neoecmo import EcmoConsoleControls
from neoecmocoupling import PatientToEcmoState, solve_closed_loop_va_ecmo


def patient(*, map_mmhg=42.0, cvp_mmhg=5.0, native_output=300.0):
    return PatientToEcmoState(
        weight_kg=3.0,
        venous_pressure_mmhg=cvp_mmhg,
        arterial_pressure_mmhg=map_mmhg,
        blood_volume_fraction=1.0,
        native_cardiac_output_ml_min=native_output,
        native_venous_oxygen_saturation=0.65,
        native_venous_paco2_mmhg=55.0,
    )


def controls(rpm, *, bridge=0.0):
    return EcmoConsoleControls(
        rpm=rpm,
        bridge_clamp_position=bridge,
        sweep_gas_flow_ml_min=600.0,
        fdo2=1.0,
    )


def test_increasing_va_patient_flow_increases_settled_map():
    low = solve_closed_loop_va_ecmo(controls(2200.0), patient())
    high = solve_closed_loop_va_ecmo(controls(3400.0), patient())
    assert high.ecmo_state.circuit.solved_patient_flow_ml_min > low.ecmo_state.circuit.solved_patient_flow_ml_min
    assert high.settled_map_mmhg > low.settled_map_mmhg


def test_stopping_ecmo_returns_map_to_patient_baseline():
    stopped = solve_closed_loop_va_ecmo(controls(0.0), patient(map_mmhg=44.0))
    assert abs(stopped.settled_map_mmhg - 44.0) < 0.05
    assert abs(stopped.map_support_mmhg) < 0.05


def test_bridge_recirculation_does_not_count_as_map_support():
    closed = solve_closed_loop_va_ecmo(controls(3000.0, bridge=0.0), patient())
    open_bridge = solve_closed_loop_va_ecmo(controls(3000.0, bridge=1.0), patient())
    assert open_bridge.ecmo_state.circuit.solved_bridge_flow_ml_min > closed.ecmo_state.circuit.solved_bridge_flow_ml_min
    assert open_bridge.ecmo_state.circuit.solved_patient_flow_ml_min < closed.ecmo_state.circuit.solved_patient_flow_ml_min
    assert open_bridge.settled_map_mmhg < closed.settled_map_mmhg


def test_increased_map_feeds_back_and_limits_flow_relative_to_fixed_baseline_map():
    from neoecmocoupling import solve_ecmo_against_patient
    p = patient(map_mmhg=42.0)
    fixed = solve_ecmo_against_patient(controls(3200.0), p)
    closed = solve_closed_loop_va_ecmo(controls(3200.0), p)
    assert closed.settled_map_mmhg > p.arterial_pressure_mmhg
    assert closed.ecmo_state.circuit.solved_patient_flow_ml_min < fixed.ecmo_state.circuit.solved_patient_flow_ml_min


def test_pulse_pressure_can_fall_while_map_rises():
    low = solve_closed_loop_va_ecmo(controls(1800.0), patient())
    high = solve_closed_loop_va_ecmo(controls(3800.0), patient())
    assert high.settled_map_mmhg > low.settled_map_mmhg
    assert high.estimated_pulse_pressure_mmhg < low.estimated_pulse_pressure_mmhg


def test_closed_loop_converges_and_preserves_branch_conservation():
    result = solve_closed_loop_va_ecmo(controls(3000.0), patient())
    c = result.ecmo_state.circuit
    assert result.converged
    assert abs(c.solved_total_flow_ml_min - (c.solved_patient_flow_ml_min + c.solved_shunt_flow_ml_min + c.solved_bridge_flow_ml_min)) < 0.1
