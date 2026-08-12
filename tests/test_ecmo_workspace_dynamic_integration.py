from neogui import EcmoWorkspaceModel, WorkspaceInputs


def test_workspace_exposes_coupled_patient_state():
    model = EcmoWorkspaceModel(WorkspaceInputs(pump_running=True, commanded_rpm=3000.0))
    snap = model.solve()
    assert snap.dynamic.true.delivery.ecmo_return_flow_ml_min > 0.0
    assert snap.dynamic.true.patient.map_mmhg > snap.dynamic.true.native_patient.map_mmhg
    assert snap.coupled_state.circuit.solved_patient_flow_ml_min > 0.0


def test_workspace_advance_uses_delayed_display_flow():
    model = EcmoWorkspaceModel(WorkspaceInputs(pump_running=False, commanded_rpm=3000.0))
    baseline = model.solve()
    model.update(pump_running=True)
    after_one_second = model.advance(1.0)
    true_flow = after_one_second.dynamic.true.delivery.ecmo_return_flow_ml_min
    displayed_flow = after_one_second.dynamic.displayed.patient_flow_ml_min
    assert true_flow > 0.0
    assert baseline.dynamic.displayed.patient_flow_ml_min < displayed_flow < true_flow


def test_workspace_sweep_change_reaches_patient_co2_with_display_lag():
    model = EcmoWorkspaceModel(WorkspaceInputs(pump_running=True, commanded_rpm=3000.0, sweep_gas_flow_ml_min=200.0))
    baseline = model.solve()
    model.update(sweep_gas_flow_ml_min=2000.0)
    changed = model.advance(1.0)
    assert changed.dynamic.true.patient.paco2_mmhg < baseline.dynamic.true.patient.paco2_mmhg
    assert changed.dynamic.displayed.paco2_mmhg > changed.dynamic.true.patient.paco2_mmhg
