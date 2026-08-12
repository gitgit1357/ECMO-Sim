from neogui import EcmoWorkspaceModel, WorkspaceInputs
from neoecmo import ShuntLineConfiguration


def test_workspace_emits_structured_control_change_events():
    model = EcmoWorkspaceModel(WorkspaceInputs(pump_running=False, commanded_rpm=3000.0))
    try:
        initial_count = len(model.event_records)
        model.update(pump_running=True)
        model.update(commanded_rpm=3150.0)
        model.update(sweep_gas_flow_ml_min=850.0)
        model.update(fdo2=0.8)
        model.update(bridge_clamp_position=0.4)
        model.update(shunt_configuration=ShuntLineConfiguration.HEMOFILTER)
        records = model.event_records[initial_count:]
        assert [r.action for r in records] == [
            "set_pump_running", "set_commanded_rpm", "set_sweep_gas_flow_ml_min",
            "set_fdo2", "set_bridge_clamp_position", "set_shunt_configuration",
        ]
        assert all(r.event_type == "control.changed" for r in records)
        assert all(r.source == "learner" for r in records)
        assert all("simulation_time_s" in r.metadata for r in records)
        assert records[-1].new_value == ShuntLineConfiguration.HEMOFILTER.value
    finally:
        model.close()


def test_workspace_does_not_emit_duplicate_event_for_noop_update():
    model = EcmoWorkspaceModel(WorkspaceInputs(commanded_rpm=3000.0))
    try:
        before = len(model.event_records)
        model.update(commanded_rpm=3000.0)
        assert len(model.event_records) == before
    finally:
        model.close()


def test_workspace_generic_event_hook_supports_future_interventions_without_scenario_engine():
    model = EcmoWorkspaceModel()
    try:
        record = model.record_event(
            event_type="observation.performed",
            source="learner",
            target="patient",
            action="assess_hemodynamics",
            metadata={"observation": "bedside_assessment"},
        )
        assert record.metadata["simulation_time_s"] == model.dynamic.elapsed_s
        assert model.event_records[-1] is record
    finally:
        model.close()
