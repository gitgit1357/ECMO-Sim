import json

import pytest

from neoecmo import EcmoConsoleControls
from neoecmocoupling import CoupledVaEcmoPatient, DynamicCoupledVaEcmoPatient
from neopatient import UnifiedNeonatalPatient
from neoscenarios import (
    ObservationDefinition,
    ObservationRegistry,
    PreloadLowFlowScenarioConfig,
    ScenarioDefinition,
    ScenarioEngine,
    build_lowflow_hypovolemia_scenario,
    build_supported_mechanism_registry,
    learner_event_view,
    register_ready_state_observations,
    validate_scenario_definition,
)


def make_dynamic(rpm=2500.0, sweep=100.0):
    patient = UnifiedNeonatalPatient()
    coupled = CoupledVaEcmoPatient(patient, EcmoConsoleControls(rpm=rpm, sweep_gas_flow_ml_min=sweep))
    return patient, DynamicCoupledVaEcmoPatient(coupled)


def test_supported_registry_contains_only_current_ready_mutations():
    patient, dynamic = make_dynamic()
    registry = build_supported_mechanism_registry(patient=patient, dynamic_patient=dynamic)
    ids = {d.mechanism_id for d in registry.descriptors}
    assert ids == {
        "patient.add_intravascular_input",
        "patient.record_blood_loss",
        "patient.set_myocardial_function",
        "ecmo.set_rpm",
        "ecmo.set_sweep",
    }


def test_ready_observation_registry_registers_six_matrix_approved_providers():
    patient, dynamic = make_dynamic()
    observations = ObservationRegistry()
    register_ready_state_observations(observations, patient=patient, dynamic_patient=dynamic)
    assert {d.provider_id for d in observations.descriptors} == {
        "assess-hemodynamics",
        "assess-pump-function",
        "assess-oxygenator",
        "verify-sweep-gas",
        "assess-gas-exchange",
        "assess-renal-fluid",
    }


def test_observation_is_frozen_and_does_not_change_after_patient_mutates():
    patient = UnifiedNeonatalPatient()
    observations = ObservationRegistry()
    register_ready_state_observations(observations, patient=patient)
    first = observations.sample("assess-hemodynamics", simulation_time_s=3.0)
    before = dict(first.values)
    patient.record_blood_loss(5.0)
    assert dict(first.values) == before


def test_dynamic_ready_observations_expose_authoritative_state_without_diagnosis_inference():
    patient, dynamic = make_dynamic()
    observations = ObservationRegistry()
    register_ready_state_observations(observations, patient=patient, dynamic_patient=dynamic)
    hemo = observations.sample("assess-hemodynamics", simulation_time_s=0.0)
    pump = observations.sample("assess-pump-function", simulation_time_s=0.0)
    oxy = observations.sample("assess-oxygenator", simulation_time_s=0.0)
    sweep = observations.sample("verify-sweep-gas", simulation_time_s=0.0)
    gas = observations.sample("assess-gas-exchange", simulation_time_s=0.0)
    renal = observations.sample("assess-renal-fluid", simulation_time_s=0.0)
    assert "map_mmhg" in hemo.values and "drainage_pressure_mmhg" in hemo.values
    assert pump.values["rpm"] == pytest.approx(2500.0)
    assert "delta_p_mmhg" in oxy.values
    assert sweep.values["sweep_gas_flow_ml_min"] == pytest.approx(100.0)
    assert "patient_paco2_mmhg" in gas.values
    assert "urine_ml_kg_hr" in renal.values
    serialized = json.dumps([o.to_dict() for o in (hemo, pump, oxy, sweep, gas, renal)])
    assert "hypovolemia" not in serialized.lower()


def test_scenario_validation_checks_observation_providers():
    patient = UnifiedNeonatalPatient()
    mechanisms = build_supported_mechanism_registry(patient=patient)
    definition = ScenarioDefinition(
        scenario_id="observation-validation", version="1", title="Observation validation",
        learner_observations=(ObservationDefinition("assess", "missing-provider"),),
    )
    issues = validate_scenario_definition(definition, mechanisms, ObservationRegistry())
    assert len(issues) == 1
    assert issues[0].code == "observation_unregistered"


def test_lowflow_hypovolemia_family_definition_maps_only_to_ready_capabilities():
    patient, dynamic = make_dynamic()
    mechanisms = build_supported_mechanism_registry(patient=patient, dynamic_patient=dynamic)
    observations = ObservationRegistry()
    register_ready_state_observations(observations, patient=patient, dynamic_patient=dynamic)
    definition = build_lowflow_hypovolemia_scenario(
        PreloadLowFlowScenarioConfig(blood_loss_ml=10.0, replacement_ml=10.0)
    )
    assert definition.scenario_id == "lowflow-hypovolemia"
    assert definition.legacy_id == "lf-01-preload"
    assert definition.metadata["clinical_validation_status"] == "behavior-contract-pending"
    assert validate_scenario_definition(definition, mechanisms, observations) == ()


def test_lowflow_hypovolemia_family_end_to_end_observe_treat_resolve_restore():
    patient, dynamic = make_dynamic()
    mechanisms = build_supported_mechanism_registry(patient=patient, dynamic_patient=dynamic)
    observations = ObservationRegistry()
    register_ready_state_observations(observations, patient=patient, dynamic_patient=dynamic)
    definition = build_lowflow_hypovolemia_scenario(
        PreloadLowFlowScenarioConfig(blood_loss_ml=10.0, replacement_ml=10.0)
    )
    engine = ScenarioEngine(definition, seed=44, mechanisms=mechanisms, observations=observations)
    engine.start()
    assert patient.state.blood_volume_delta_ml == pytest.approx(-10.0)
    observed = engine.perform_learner_observation("assess-hemodynamics")
    assert observed.sample_time_s == 0.0
    frozen_map = observed.values["map_mmhg"]
    snap = engine.snapshot()
    engine.perform_learner_action("volume-bolus")
    assert patient.state.blood_volume_delta_ml == pytest.approx(0.0)
    assert "activate-preload-loss" in engine.state.resolved_steps
    assert observed.values["map_mmhg"] == frozen_map
    visible = learner_event_view(engine.events.records)
    assert all("hypovolemia" not in json.dumps(v).lower() for v in visible)
    assert all(v["source"] != "scenario-engine" for v in visible)

    # Restore orchestration/observation history without re-firing the fault.
    restored = ScenarioEngine(definition, seed=44, mechanisms=mechanisms, observations=observations, events=engine.events)
    restored.restore(snap)
    assert len(restored.observation_results) == 1
    assert restored.observation_results[0].to_dict() == observed.to_dict()
    before = patient.state.blood_volume_delta_ml
    restored.advance_to(0.0)
    assert patient.state.blood_volume_delta_ml == before


def test_supported_fault_catalog_contains_only_hypovolemia_core_fault():
    from neoscenarios import build_supported_fault_catalog
    catalog = build_supported_fault_catalog()
    assert [r.fault_id for r in catalog.registrations] == ["hypovolemia"]
    fault = catalog.build("hypovolemia", volume_ml=7.5)
    assert fault.activation_action.mechanism_id == "patient.record_blood_loss"
    assert fault.activation_action.parameters["volume_ml"] == pytest.approx(7.5)


def test_scenario_with_observations_requires_observation_registry_in_preflight():
    patient = UnifiedNeonatalPatient()
    mechanisms = build_supported_mechanism_registry(patient=patient)
    definition = ScenarioDefinition(
        scenario_id="observation-required", version="1", title="Observation required",
        learner_observations=(ObservationDefinition("assess", "assess-hemodynamics"),),
    )
    issues = validate_scenario_definition(definition, mechanisms)
    assert len(issues) == 1
    assert issues[0].code == "observation_unregistered"
