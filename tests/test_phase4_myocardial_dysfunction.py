import pytest

from neopatient import UnifiedNeonatalPatient, MyocardialFunctionPort
from neoscenarios.mechanisms import build_supported_mechanism_registry
from neoscenarios.models import MechanismInvocation


def test_lv_dysfunction_is_graded_and_statefully_reversible_in_unified_patient():
    patient = UnifiedNeonatalPatient()
    base = patient.snapshot(include_vascular_support=False)
    patient.set_myocardial_function(MyocardialFunctionPort(lv_contractility_scale=0.30, rv_contractility_scale=1.0))
    impaired = patient.snapshot(include_vascular_support=False)
    assert impaired.native_cardiac_output_ml_min < base.native_cardiac_output_ml_min
    assert impaired.map_mmhg < base.map_mmhg
    patient.set_myocardial_function(MyocardialFunctionPort())
    recovered = patient.snapshot(include_vascular_support=False)
    assert recovered.native_cardiac_output_ml_min == pytest.approx(base.native_cardiac_output_ml_min, rel=1e-6)
    assert recovered.map_mmhg == pytest.approx(base.map_mmhg, rel=1e-6)


def test_rv_dysfunction_reduces_forward_flow_and_raises_cvp():
    patient = UnifiedNeonatalPatient()
    base = patient.snapshot(include_vascular_support=False)
    patient.set_myocardial_function(MyocardialFunctionPort(lv_contractility_scale=1.0, rv_contractility_scale=0.30))
    impaired = patient.snapshot(include_vascular_support=False)
    assert impaired.native_cardiac_output_ml_min < base.native_cardiac_output_ml_min
    assert impaired.pulmonary_flow_ml_min < base.pulmonary_flow_ml_min
    assert impaired.map_mmhg < base.map_mmhg
    assert impaired.cvp_mmhg > base.cvp_mmhg


def test_severe_dysfunction_has_larger_effect_than_mild_reduction():
    patient = UnifiedNeonatalPatient()
    patient.set_myocardial_function(MyocardialFunctionPort(lv_contractility_scale=0.70, rv_contractility_scale=1.0))
    mild = patient.snapshot(include_vascular_support=False)
    patient.set_myocardial_function(MyocardialFunctionPort(lv_contractility_scale=0.30, rv_contractility_scale=1.0))
    severe = patient.snapshot(include_vascular_support=False)
    assert severe.native_cardiac_output_ml_min < mild.native_cardiac_output_ml_min
    assert severe.map_mmhg < mild.map_mmhg


def test_myocardial_function_is_a_registered_scenario_mechanism():
    patient = UnifiedNeonatalPatient()
    registry = build_supported_mechanism_registry(patient=patient)
    result = registry.invoke(MechanismInvocation(
        mechanism_id="patient.set_myocardial_function",
        parameters={"lv_contractility_scale": 0.30},
        source="test", action_id="set-lv-function", scenario_id="phase4-myocardial", simulation_time_s=0.0,
    ))
    assert result.old_value["lv_contractility_scale"] == 1.0
    assert result.new_value["lv_contractility_scale"] == 0.30
    assert patient.myocardial_function.lv_contractility_scale == 0.30


def test_invalid_contractility_scale_is_rejected():
    with pytest.raises(ValueError):
        MyocardialFunctionPort(lv_contractility_scale=0.0)


def test_native_worker_reconstructs_nondefault_myocardial_function():
    from neopatient.async_native import NativeSolveRequest, solve_native_request
    patient = UnifiedNeonatalPatient()
    base = patient.snapshot(include_vascular_support=False)
    patient.set_myocardial_function(MyocardialFunctionPort(lv_contractility_scale=0.30, rv_contractility_scale=1.0))
    request = NativeSolveRequest(revision=1, cache_key=patient._native_cache_key(), blood_volume_delta_ml=0.0)
    result = solve_native_request(request)
    assert result.physiology.circulation_metrics.native_output_ml_min < base.native_cardiac_output_ml_min
    assert result.physiology.circulation_metrics.mean_aortic_mmhg < base.map_mmhg
