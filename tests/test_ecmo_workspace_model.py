import pytest

from neogui import EcmoWorkspaceModel, WorkspaceInputs
from neoecmo import ShuntLineConfiguration


def test_stopped_pump_applies_zero_rpm_and_flow():
    snapshot = EcmoWorkspaceModel(WorkspaceInputs(pump_running=False, commanded_rpm=3000.0)).solve()
    assert snapshot.applied_rpm == 0.0
    assert snapshot.state.circuit.solved_total_flow_ml_min == pytest.approx(0.0, abs=1e-6)
    assert snapshot.status_text == "STOPPED"


def test_starting_pump_uses_commanded_rpm_and_produces_flow():
    model = EcmoWorkspaceModel(WorkspaceInputs(commanded_rpm=3000.0))
    snapshot = model.update(pump_running=True)
    assert snapshot.applied_rpm == pytest.approx(3000.0)
    assert snapshot.state.circuit.solved_total_flow_ml_min > 0.0
    assert snapshot.status_text == "RUNNING"


def test_bridge_opening_redistributes_flow_without_setting_total_flow_directly():
    model = EcmoWorkspaceModel(WorkspaceInputs(pump_running=True, commanded_rpm=3000.0))
    closed = model.solve()
    opened = model.update(bridge_clamp_position=0.5)
    assert closed.state.circuit.solved_bridge_flow_ml_min == 0.0
    assert opened.state.circuit.solved_bridge_flow_ml_min > 0.0
    assert opened.state.circuit.solved_patient_flow_ml_min < closed.state.circuit.solved_patient_flow_ml_min


def test_fdo2_and_sweep_controls_reach_console_solver():
    model = EcmoWorkspaceModel(WorkspaceInputs(pump_running=True, commanded_rpm=3000.0))
    low = model.update(fdo2=0.5, sweep_gas_flow_ml_min=50.0)
    high = model.update(fdo2=1.0, sweep_gas_flow_ml_min=1000.0)
    assert high.state.post_oxygenator_saturation > low.state.post_oxygenator_saturation
    assert high.state.post_oxygenator_paco2_mmhg < low.state.post_oxygenator_paco2_mmhg


def test_shunt_configuration_is_supported_by_workspace_model():
    model = EcmoWorkspaceModel(WorkspaceInputs(pump_running=True, commanded_rpm=3000.0))
    open_state = model.solve()
    filtered = model.update(shunt_configuration=ShuntLineConfiguration.HEMOFILTER)
    assert filtered.state.circuit.solved_shunt_flow_ml_min < open_state.state.circuit.solved_shunt_flow_ml_min
