from __future__ import annotations

import pytest

from neoevents import EventStream
from neoscenarios import (
    ActionDefinition,
    FaultDefinition,
    MechanismAvailability,
    MechanismDescriptor,
    MechanismNotAvailableError,
    MechanismRegistry,
    MechanismResult,
    ScenarioDefinition,
    ScenarioEngine,
    ScenarioRng,
    ScenarioStepDefinition,
    TriggerDefinition,
)
from neopatient import UnifiedNeonatalPatient
from neoscenarios import register_unified_patient_volume_mechanism


def test_seeded_rng_is_reproducible():
    a = ScenarioRng(8127)
    b = ScenarioRng(8127)
    assert [a.randint(1, 100) for _ in range(8)] == [b.randint(1, 100) for _ in range(8)]
    assert a.draw_count == b.draw_count == 8


def test_scenario_definition_rejects_duplicate_action_ids():
    action = ActionDefinition("x", "m")
    with pytest.raises(ValueError):
        ScenarioDefinition("s", "1", "S", learner_actions=(action, action))


def test_unavailable_mechanism_is_explicit_and_does_not_call_handler():
    registry = MechanismRegistry()
    registry.register(MechanismDescriptor("fault.tamponade", MechanismAvailability.NOT_IMPLEMENTED))
    events = EventStream()
    scenario = ScenarioDefinition(
        "test", "1", "Test", learner_actions=(ActionDefinition("decompress", "fault.tamponade"),)
    )
    engine = ScenarioEngine(scenario, seed=1, mechanisms=registry, events=events)
    engine.start()
    with pytest.raises(MechanismNotAvailableError):
        engine.perform_learner_action("decompress")
    assert events.latest.event_type == "scenario.action_unavailable"
    assert not any(r.event_type == "scenario.action_applied" for r in events.records)


def test_elapsed_step_calls_registered_mechanism_once():
    calls = []
    registry = MechanismRegistry()

    def handler(invocation):
        calls.append(invocation)
        return MechanismResult(old_value=0, new_value=1)

    registry.register(MechanismDescriptor("fault.activate", MechanismAvailability.AVAILABLE), handler)
    scenario = ScenarioDefinition(
        "s", "1", "Scenario",
        steps=(ScenarioStepDefinition(
            "onset",
            TriggerDefinition("elapsed_time", {"at_s": 10}),
            actions=(ActionDefinition("activate", "fault.activate"),),
        ),),
    )
    engine = ScenarioEngine(scenario, seed=2, mechanisms=registry)
    engine.start()
    engine.advance_to(9.9)
    assert calls == []
    engine.advance_to(10)
    engine.advance_to(20)
    assert len(calls) == 1
    assert calls[0].simulation_time_s == 10


def test_event_trigger_can_chain_deterministically():
    registry = MechanismRegistry()
    seen = []

    def handler(invocation):
        seen.append(invocation.action_id)
        return MechanismResult()

    registry.register(MechanismDescriptor("m", MechanismAvailability.AVAILABLE), handler)
    first = ScenarioStepDefinition(
        "first", TriggerDefinition("elapsed_time", {"at_s": 1}),
        actions=(ActionDefinition("a1", "m"),),
    )
    second = ScenarioStepDefinition(
        "second", TriggerDefinition("event", {"event_type": "scenario.action_applied", "action": "a1"}),
        actions=(ActionDefinition("a2", "m"),),
    )
    engine = ScenarioEngine(ScenarioDefinition("s", "1", "S", steps=(first, second)), seed=9, mechanisms=registry)
    engine.start()
    engine.advance_to(1)
    assert seen == ["a1", "a2"]


def test_manual_step_does_not_autofire():
    registry = MechanismRegistry()
    calls = []
    registry.register(
        MechanismDescriptor("m", MechanismAvailability.AVAILABLE),
        lambda inv: calls.append(inv.action_id) or MechanismResult(),
    )
    step = ScenarioStepDefinition("educator", TriggerDefinition("manual"), actions=(ActionDefinition("x", "m"),))
    engine = ScenarioEngine(ScenarioDefinition("s", "1", "S", steps=(step,)), seed=4, mechanisms=registry)
    engine.start()
    engine.advance_to(999)
    assert calls == []
    engine.fire_step("educator")
    assert calls == ["x"]


def test_real_volume_mechanism_uses_patient_volume_ledger():
    patient = UnifiedNeonatalPatient()
    registry = MechanismRegistry()
    register_unified_patient_volume_mechanism(registry, patient)
    action = ActionDefinition("volume-bolus", "patient.add_intravascular_input", {"volume_ml": 20.0})
    engine = ScenarioEngine(
        ScenarioDefinition("s", "1", "S", learner_actions=(action,)), seed=3, mechanisms=registry
    )
    engine.start()
    before = patient.state.blood_volume_delta_ml
    engine.perform_learner_action("volume-bolus")
    assert patient.state.blood_volume_delta_ml == before + 20.0
    assert engine.events.latest.event_type == "scenario.action_applied"


def test_fault_activation_still_crosses_mechanism_registry():
    registry = MechanismRegistry()
    registry.register(MechanismDescriptor("fault.kink", MechanismAvailability.NOT_IMPLEMENTED))
    fault = FaultDefinition("drainage-kink", ActionDefinition("activate-kink", "fault.kink"), legacy_id="drainage-cannula-kink")
    step = ScenarioStepDefinition("fault-onset", TriggerDefinition("elapsed_time", {"at_s": 5}), faults=(fault,))
    engine = ScenarioEngine(ScenarioDefinition("s", "1", "S", steps=(step,)), seed=1, mechanisms=registry)
    engine.start()
    with pytest.raises(MechanismNotAvailableError):
        engine.advance_to(5)
    assert any(r.event_type == "scenario.fault_requested" for r in engine.events.records)
    assert engine.events.latest.event_type == "scenario.action_unavailable"


def test_repeatable_automatic_step_is_rejected_until_recurrence_semantics_exist():
    with pytest.raises(ValueError, match="repeatable steps"):
        ScenarioStepDefinition("repeat", TriggerDefinition("elapsed_time", {"at_s": 1}), once=False)


def test_repeatable_manual_step_can_be_fired_more_than_once():
    registry = MechanismRegistry()
    calls = []
    registry.register(
        MechanismDescriptor("m", MechanismAvailability.AVAILABLE),
        lambda inv: calls.append(inv.action_id) or MechanismResult(),
    )
    step = ScenarioStepDefinition(
        "repeat", TriggerDefinition("manual"), actions=(ActionDefinition("x", "m"),), once=False
    )
    engine = ScenarioEngine(ScenarioDefinition("s", "1", "S", steps=(step,)), seed=4, mechanisms=registry)
    engine.start()
    engine.fire_step("repeat")
    engine.fire_step("repeat")
    assert calls == ["x", "x"]


def test_definition_validation_reports_partial_and_missing_mechanisms():
    from neoscenarios import validate_scenario_definition

    registry = MechanismRegistry()
    registry.register(MechanismDescriptor("fault.kink", MechanismAvailability.PARTIAL))
    scenario = ScenarioDefinition(
        "s", "1", "S",
        learner_actions=(ActionDefinition("inspect", "diagnostic.inspect"),),
        steps=(ScenarioStepDefinition(
            "onset", TriggerDefinition("manual"),
            faults=(FaultDefinition("kink", ActionDefinition("activate-kink", "fault.kink")),),
        ),),
    )
    issues = validate_scenario_definition(scenario, registry)
    assert {i.code for i in issues} == {"mechanism_unregistered", "mechanism_partial"}
    assert {i.mechanism_id for i in issues} == {"diagnostic.inspect", "fault.kink"}


def test_scenario_engine_exposes_definition_validation_issues():
    registry = MechanismRegistry()
    scenario = ScenarioDefinition("s", "1", "S", learner_actions=(ActionDefinition("x", "missing"),))
    engine = ScenarioEngine(scenario, seed=1, mechanisms=registry)
    assert engine.validation_issues[0].mechanism_id == "missing"


def test_real_ecmo_control_mechanisms_set_rpm_and_sweep_without_setting_flow():
    from neoecmo import EcmoConsoleControls
    from neoecmocoupling import CoupledVaEcmoPatient, DynamicCoupledVaEcmoPatient
    from neoscenarios import register_dynamic_va_ecmo_control_mechanisms

    patient = UnifiedNeonatalPatient()
    coupled = CoupledVaEcmoPatient(patient, EcmoConsoleControls(rpm=2500.0, sweep_gas_flow_ml_min=200.0))
    dynamic = DynamicCoupledVaEcmoPatient(coupled)
    registry = MechanismRegistry()
    register_dynamic_va_ecmo_control_mechanisms(registry, dynamic)
    scenario = ScenarioDefinition(
        "s", "1", "S",
        learner_actions=(
            ActionDefinition("increase-rpm", "ecmo.set_rpm", {"rpm": 3000.0}),
            ActionDefinition("increase-sweep", "ecmo.set_sweep", {"sweep_gas_flow_ml_min": 500.0}),
        ),
    )
    engine = ScenarioEngine(scenario, seed=8, mechanisms=registry)
    engine.start()
    engine.perform_learner_action("increase-rpm")
    engine.perform_learner_action("increase-sweep")
    assert dynamic.coupled.controls.rpm == 3000.0
    assert dynamic.coupled.controls.sweep_gas_flow_ml_min == 500.0
    assert not hasattr(dynamic.coupled.controls, "flow_ml_min")


def test_action_definitions_reject_executable_or_nonportable_parameters():
    with pytest.raises(TypeError, match="JSON-compatible"):
        ActionDefinition("bad", "m", {"callback": lambda: None})


def test_action_definition_parameters_are_deeply_immutable_data():
    action = ActionDefinition("x", "m", {"nested": {"values": [1, 2, 3]}})
    with pytest.raises(TypeError):
        action.parameters["nested"]["new"] = 4
    assert action.parameters["nested"]["values"] == (1, 2, 3)


def test_event_trigger_ignores_matching_history_from_before_scenario_start():
    events = EventStream()
    events.emit(event_type="external.done", source="old", target="x", action="ready")
    registry = MechanismRegistry()
    calls = []
    registry.register(
        MechanismDescriptor("m", MechanismAvailability.AVAILABLE),
        lambda inv: calls.append(inv.action_id) or MechanismResult(),
    )
    step = ScenarioStepDefinition(
        "after-ready",
        TriggerDefinition("event", {"event_type": "external.done", "action": "ready"}),
        actions=(ActionDefinition("run", "m"),),
    )
    engine = ScenarioEngine(ScenarioDefinition("s", "1", "S", steps=(step,)), seed=1, mechanisms=registry, events=events)
    engine.start()
    assert calls == []
    events.emit(event_type="external.done", source="new", target="x", action="ready")
    engine.advance_to(0)
    assert calls == ["run"]
