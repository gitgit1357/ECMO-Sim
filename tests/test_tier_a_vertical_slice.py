from neopatient import UnifiedNeonatalPatient
from neoscenarios import (
    ActionDefinition, FaultDefinition, MechanismRegistry, ScenarioDefinition, ScenarioEngine,
    ScenarioStepDefinition, TriggerDefinition, learner_event_view,
    register_unified_patient_blood_loss_mechanism, register_unified_patient_volume_mechanism,
)


def test_hypovolemia_vertical_slice_trigger_fault_action_resolution_and_disclosure():
    patient = UnifiedNeonatalPatient()
    registry = MechanismRegistry()
    register_unified_patient_blood_loss_mechanism(registry, patient)
    register_unified_patient_volume_mechanism(registry, patient)

    definition = ScenarioDefinition(
        scenario_id="tier-a-hypovolemia-slice", version="1", title="Hypovolemia vertical slice",
        learner_actions=(ActionDefinition("volume-bolus", "patient.add_intravascular_input", {"volume_ml": 10}),),
        steps=(ScenarioStepDefinition(
            "hidden-volume-loss", TriggerDefinition("at_start"),
            faults=(FaultDefinition("hidden-hypovolemia", ActionDefinition("remove-volume", "patient.record_blood_loss", {"volume_ml": 10}), legacy_id="low-flow-hypovolemia"),),
            resolution_trigger=TriggerDefinition("event", {"event_type":"scenario.action_applied", "source":"learner", "action":"volume-bolus"}),
        ),),
    )
    engine = ScenarioEngine(definition, seed=123, mechanisms=registry)
    engine.start()
    assert patient.state.blood_volume_delta_ml == -10
    engine.perform_learner_action("volume-bolus")
    assert patient.state.blood_volume_delta_ml == 0
    assert "hidden-volume-loss" in engine.state.resolved_steps
    visible = learner_event_view(engine.events.records)
    assert all("hidden-hypovolemia" not in str(record) for record in visible)
