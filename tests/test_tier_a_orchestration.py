from neoevents import EventStream
from neoscenarios import (
    ActionDefinition, DisclosurePolicy, EventMachineDefinition, EventMachineRuntime,
    EventTransitionDefinition, FaultDefinition, FrozenObservation, MechanismDescriptor,
    MechanismAvailability, MechanismRegistry, MechanismResult, ScenarioDefinition,
    ScenarioDirectorPolicy, ScenarioEngine, ScenarioStepDefinition, TriggerDefinition,
    instructor_event_view, learner_event_view,
)


def _registry():
    reg = MechanismRegistry()
    reg.register(MechanismDescriptor("noop", MechanismAvailability.AVAILABLE), lambda i: MechanismResult())
    return reg


def test_snapshot_restore_preserves_fired_trigger_and_prevents_duplicate_release():
    definition = ScenarioDefinition(
        "restore", "1", "restore",
        steps=(ScenarioStepDefinition("once", TriggerDefinition("at_start"), actions=(ActionDefinition("a", "noop"),)),),
    )
    events = EventStream()
    e1 = ScenarioEngine(definition, seed=7, mechanisms=_registry(), events=events)
    e1.start()
    snap = e1.snapshot()
    assert len([r for r in events.records if r.event_type == "scenario.step_released"]) == 1
    e2 = ScenarioEngine(definition, seed=7, mechanisms=_registry(), events=events)
    e2.restore(snap)
    e2.advance_to(1)
    assert len([r for r in events.records if r.event_type == "scenario.step_released"]) == 1


def test_director_separates_eligibility_from_release_and_respects_concurrency():
    definition = ScenarioDefinition(
        "director", "1", "director",
        director_policy=ScenarioDirectorPolicy(max_concurrent_unresolved=1),
        steps=(
            ScenarioStepDefinition("first", TriggerDefinition("at_start"), priority=1,
                resolution_trigger=TriggerDefinition("event", {"event_type":"test.resolve", "action":"first"})),
            ScenarioStepDefinition("second", TriggerDefinition("at_start"), priority=2),
        ),
    )
    events = EventStream(); engine = ScenarioEngine(definition, seed=1, mechanisms=_registry(), events=events)
    engine.start()
    assert engine.state.active_steps == {"first"}
    assert engine.state.eligible_steps == {"second"}
    events.emit(event_type="test.resolve", source="test", target="director", action="first")
    engine.advance_to(1)
    assert "first" in engine.state.resolved_steps and "second" in engine.state.fired_steps


def test_time_in_state_uses_state_entry_not_event_creation_time():
    definition = EventMachineDefinition("evt", "suspected", transitions=(
        EventTransitionDefinition("diagnose", "suspected", "diagnosed", TriggerDefinition("time_in_state", {"at_s": 5})),
        EventTransitionDefinition("resolve", "diagnosed", "resolved", TriggerDefinition("time_in_state", {"at_s": 3})),
    ))
    runtime = EventMachineRuntime.start(definition, 100)
    assert runtime.evaluate(104.9, ()) is None
    assert runtime.evaluate(105, ()).transition_id == "diagnose"
    assert runtime.evaluate(107.9, ()) is None
    assert runtime.evaluate(108, ()).transition_id == "resolve"


def test_learner_disclosure_hides_internal_diagnosis_but_instructor_retains_it():
    events = EventStream()
    events.emit(event_type="scenario.fault_requested", source="scenario-engine", target="tamponade",
                action="activate", metadata={"fault_id":"tamponade", "hidden_state":"active", "rationale":"secret"})
    events.emit(event_type="observation.available", source="system", target="patient", action="inspect",
                new_value={"finding":"low flow"}, metadata={"fault_id":"tamponade"})
    learner = learner_event_view(events.records)
    instructor = instructor_event_view(events.records)
    assert len(learner) == 1
    assert "fault_id" not in learner[0]["metadata"]
    assert instructor[0]["metadata"]["fault_id"] == "tamponade"


def test_learner_disclosure_normalizes_internal_scenario_engine_source_tag():
    events = EventStream()
    events.emit(event_type="scenario.observation_sampled", source="scenario-engine", target="assess-hemodynamics",
                action="inspect", new_value={"map_mmhg": 48.0})
    learner = learner_event_view(events.records)
    instructor = instructor_event_view(events.records)
    assert learner[0]["source"] == "system"
    assert instructor[0]["source"] == "scenario-engine"


def test_frozen_observation_does_not_change_after_hidden_state_changes():
    hidden = {"pao2": 48.0}
    obs = FrozenObservation("abg-1", sample_time_s=10, available_time_s=13, values=hidden)
    hidden["pao2"] = 90.0
    assert obs.values["pao2"] == 48.0
    assert not obs.is_available(12.9) and obs.is_available(13)


def test_rng_snapshot_restore_replays_same_next_draw():
    definition = ScenarioDefinition("rng", "1", "rng")
    a = ScenarioEngine(definition, seed=42, mechanisms=_registry())
    a.rng.random(); snap = a.snapshot(); expected = a.rng.random()
    b = ScenarioEngine(definition, seed=42, mechanisms=_registry()); b.restore(snap)
    assert b.rng.random() == expected


def test_generic_time_window_context_and_action_count_triggers_are_data_driven():
    from neoscenarios import trigger_matches
    assert trigger_matches(TriggerDefinition("time_window", {"start_s": 5, "end_s": 10}), simulation_time_s=7, records=())
    assert not trigger_matches(TriggerDefinition("time_window", {"start_s": 5, "end_s": 10}), simulation_time_s=11, records=())
    assert trigger_matches(TriggerDefinition("context", {"ecmo_mode": "VA"}), simulation_time_s=0, records=(), context={"ecmo_mode":"VA"})
    assert trigger_matches(TriggerDefinition("action_count", {"action_id":"inspect", "at_least":2}), simulation_time_s=0, records=(), action_counts={"inspect":2})


def test_director_minimum_spacing_keeps_second_event_eligible_until_time_advances():
    definition = ScenarioDefinition(
        "spacing", "1", "spacing", director_policy=ScenarioDirectorPolicy(max_concurrent_unresolved=2, min_release_spacing_s=5),
        steps=(ScenarioStepDefinition("a", TriggerDefinition("at_start"), priority=1),
               ScenarioStepDefinition("b", TriggerDefinition("at_start"), priority=2)),
    )
    engine = ScenarioEngine(definition, seed=1, mechanisms=_registry())
    engine.start()
    assert "a" in engine.state.fired_steps and "b" in engine.state.eligible_steps
    engine.advance_to(4.9); assert "b" not in engine.state.fired_steps
    engine.advance_to(5); assert "b" in engine.state.fired_steps


def test_event_machine_snapshot_restore_preserves_state_entry_timer():
    definition = EventMachineDefinition("evt", "active", transitions=(
        EventTransitionDefinition("worsen", "active", "worse", TriggerDefinition("time_in_state", {"at_s": 10})),
    ))
    first = EventMachineRuntime.start(definition, 20)
    assert first.evaluate(26, ()) is None
    snap = first.snapshot()
    second = EventMachineRuntime.start(definition, 0); second.restore(snap)
    assert second.evaluate(29.9, ()) is None
    assert second.evaluate(30, ()).to_state == "worse"
