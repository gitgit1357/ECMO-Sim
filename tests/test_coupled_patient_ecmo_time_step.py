import pytest

from neoecmo import EcmoConsoleControls, ShuntLineConfiguration
from neoecmocoupling import CoupledVaEcmoPatient
from neopatient import UnifiedNeonatalPatient, UnifiedPatientConfig


def make_patient():
    # Short internal solve durations keep this behavioral integration test fast.
    return UnifiedNeonatalPatient(
        UnifiedPatientConfig(weight_kg=3.0, lung_run_s=2.0, circulation_run_s=2.0)
    )


def test_va_support_raises_map_and_reduces_native_contribution():
    patient = make_patient()
    system = CoupledVaEcmoPatient(patient, EcmoConsoleControls(rpm=0, sweep_gas_flow_ml_min=600))
    native = system.snapshot()

    system.set_controls(EcmoConsoleControls(rpm=3000, sweep_gas_flow_ml_min=600))
    supported = system.snapshot()

    assert supported.delivery.ecmo_return_flow_ml_min > 0.0
    assert supported.patient.map_mmhg > native.patient.map_mmhg
    assert supported.patient.native_cardiac_output_ml_min < native.patient.native_cardiac_output_ml_min
    assert supported.effective_systemic_flow_ml_min > supported.patient.native_cardiac_output_ml_min


def test_stopping_ecmo_restores_native_output_multiplier():
    patient = make_patient()
    system = CoupledVaEcmoPatient(patient, EcmoConsoleControls(rpm=3000, sweep_gas_flow_ml_min=600))
    running = system.snapshot()
    assert running.native_output_multiplier < 1.0

    system.set_controls(EcmoConsoleControls(rpm=0, sweep_gas_flow_ml_min=600))
    stopped = system.snapshot()
    assert stopped.native_output_multiplier == pytest.approx(1.0)
    assert stopped.delivery.ecmo_return_flow_ml_min == pytest.approx(0.0)
    assert stopped.patient.vascular_support_enabled is False


def test_ckrt_and_urine_reduce_volume_available_to_next_solve():
    patient = make_patient()
    controls = EcmoConsoleControls(
        rpm=3300,
        sweep_gas_flow_ml_min=600,
        shunt_configuration=ShuntLineConfiguration.CKRT,
        shunt_ckrt_blood_flow_ml_min=40.0,
        shunt_ckrt_net_ultrafiltration_rate_ml_min=0.40,
    )
    system = CoupledVaEcmoPatient(patient, controls)
    before = system.snapshot()
    after = system.advance(20.0)

    assert after.patient.elapsed_min == pytest.approx(20.0)
    assert after.patient.total_blood_volume_ml < before.patient.total_blood_volume_ml
    assert after.patient.cumulative_urine_ml > before.patient.cumulative_urine_ml
    assert after.volume_limited_ecmo.preload_fraction < before.volume_limited_ecmo.preload_fraction
    assert after.volume_limited_ecmo.drainage_demand_ratio > before.volume_limited_ecmo.drainage_demand_ratio


def test_bridge_flow_is_not_counted_as_systemic_support():
    closed_patient = make_patient()
    closed = CoupledVaEcmoPatient(
        closed_patient,
        EcmoConsoleControls(rpm=3000, bridge_clamp_position=0.0, sweep_gas_flow_ml_min=600),
    ).snapshot()

    open_patient = make_patient()
    open_bridge = CoupledVaEcmoPatient(
        open_patient,
        EcmoConsoleControls(rpm=3000, bridge_clamp_position=1.0, sweep_gas_flow_ml_min=600),
    ).snapshot()

    assert open_bridge.delivery.bridge_flow_ml_min > closed.delivery.bridge_flow_ml_min
    assert open_bridge.delivery.ecmo_return_flow_ml_min < closed.delivery.ecmo_return_flow_ml_min
    assert open_bridge.patient.map_mmhg < closed.patient.map_mmhg
