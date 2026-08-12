from neoecmo import EcmoConsoleControls
from neoecmocoupling import PatientToEcmoState, solve_ecmo_against_patient


def patient(*, map_mmhg=45.0, cvp_mmhg=5.0):
    return PatientToEcmoState(
        weight_kg=3.0,
        venous_pressure_mmhg=cvp_mmhg,
        arterial_pressure_mmhg=map_mmhg,
        blood_volume_fraction=1.0,
        native_cardiac_output_ml_min=300.0,
        native_venous_oxygen_saturation=0.65,
        native_venous_paco2_mmhg=55.0,
    )


def controls():
    return EcmoConsoleControls(rpm=3000.0, sweep_gas_flow_ml_min=600.0, fdo2=1.0)


def test_higher_map_reduces_patient_directed_flow_at_same_rpm():
    low_afterload = solve_ecmo_against_patient(controls(), patient(map_mmhg=35.0))
    high_afterload = solve_ecmo_against_patient(controls(), patient(map_mmhg=65.0))
    assert high_afterload.ecmo_state.circuit.solved_patient_flow_ml_min < low_afterload.ecmo_state.circuit.solved_patient_flow_ml_min


def test_higher_cvp_increases_patient_directed_flow_at_same_rpm_and_map():
    low_cvp = solve_ecmo_against_patient(controls(), patient(cvp_mmhg=2.0))
    high_cvp = solve_ecmo_against_patient(controls(), patient(cvp_mmhg=10.0))
    assert high_cvp.ecmo_state.circuit.solved_patient_flow_ml_min > low_cvp.ecmo_state.circuit.solved_patient_flow_ml_min


def test_higher_cvp_makes_p1_less_negative():
    low_cvp = solve_ecmo_against_patient(controls(), patient(cvp_mmhg=2.0))
    high_cvp = solve_ecmo_against_patient(controls(), patient(cvp_mmhg=10.0))
    assert high_cvp.ecmo_state.circuit.p1_mmhg > low_cvp.ecmo_state.circuit.p1_mmhg


def test_branch_flow_conservation_is_preserved_with_live_patient_pressures():
    result = solve_ecmo_against_patient(controls(), patient())
    c = result.ecmo_state.circuit
    assert abs(c.solved_total_flow_ml_min - (c.solved_patient_flow_ml_min + c.solved_shunt_flow_ml_min + c.solved_bridge_flow_ml_min)) < 0.1


def test_legacy_uncoupled_console_behavior_remains_available():
    from neoecmo import run_ecmo_console
    state = run_ecmo_console(controls(), 0.65, 55.0)
    assert state.circuit.solved_patient_flow_ml_min > 0.0
