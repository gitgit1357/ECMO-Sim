import pytest

from neoecmo import EcmoConsoleControls, run_ecmo_console
from neoecmocoupling import mix_native_and_ecmo_arterial_blood
from neopatient import UnifiedNeonatalPatient, VascularSupportPort


def _patient_mix(flow_ml_min: float, return_po2: float, return_pco2: float):
    return mix_native_and_ecmo_arterial_blood(
        native_flow_ml_min=500.0,
        native_pao2_mmhg=45.0,
        native_paco2_mmhg=58.0,
        ecmo_flow_ml_min=flow_ml_min,
        ecmo_return_po2_mmhg=return_po2,
        ecmo_return_paco2_mmhg=return_pco2,
        hemoglobin_g_dl=16.5,
    )


def test_increasing_patient_directed_ecmo_flow_raises_patient_pao2_and_oxygen_delivery():
    low = _patient_mix(100.0, 400.0, 30.0)
    high = _patient_mix(400.0, 400.0, 30.0)
    assert high.pao2_mmhg > low.pao2_mmhg
    assert high.oxygen_delivery_ml_min > low.oxygen_delivery_ml_min
    assert high.ecmo_flow_fraction > low.ecmo_flow_fraction


def test_sweep_is_dominant_control_of_patient_co2_at_fixed_blood_flow():
    low_sweep = run_ecmo_console(
        EcmoConsoleControls(rpm=3000, fdo2=1.0, sweep_gas_flow_ml_min=100),
        native_venous_saturation=0.65,
        native_venous_paco2_mmhg=58.0,
    )
    high_sweep = run_ecmo_console(
        EcmoConsoleControls(rpm=3000, fdo2=1.0, sweep_gas_flow_ml_min=1000),
        native_venous_saturation=0.65,
        native_venous_paco2_mmhg=58.0,
    )
    low = _patient_mix(
        low_sweep.circuit.solved_patient_flow_ml_min,
        low_sweep.post_oxygenator_po2_mmhg,
        low_sweep.post_oxygenator_paco2_mmhg,
    )
    high = _patient_mix(
        high_sweep.circuit.solved_patient_flow_ml_min,
        high_sweep.post_oxygenator_po2_mmhg,
        high_sweep.post_oxygenator_paco2_mmhg,
    )
    assert high.paco2_mmhg < low.paco2_mmhg - 5.0
    assert high.pao2_mmhg == pytest.approx(low.pao2_mmhg, abs=0.5)


def test_flow_has_smaller_secondary_co2_effect_than_sweep_change():
    low_flow = _patient_mix(150.0, 400.0, 25.0)
    high_flow = _patient_mix(400.0, 400.0, 25.0)
    flow_co2_change = abs(high_flow.paco2_mmhg - low_flow.paco2_mmhg)

    low_sweep = _patient_mix(300.0, 400.0, 50.0)
    high_sweep = _patient_mix(300.0, 400.0, 25.0)
    sweep_co2_change = abs(high_sweep.paco2_mmhg - low_sweep.paco2_mmhg)
    assert sweep_co2_change > flow_co2_change


def test_unified_patient_consumes_return_po2_and_pco2_not_just_saturation():
    patient = UnifiedNeonatalPatient()
    baseline = patient.snapshot()
    patient.set_vascular_support(
        VascularSupportPort(
            enabled=True,
            support_flow_ml_min=350.0,
            return_oxygen_saturation_pct=100.0,
            return_po2_mmhg=400.0,
            return_paco2_mmhg=22.0,
        )
    )
    supported = patient.snapshot()
    assert supported.pao2_mmhg > baseline.pao2_mmhg
    assert supported.paco2_mmhg < baseline.paco2_mmhg


def test_solved_ecmo_delivery_can_drive_unified_patient_port():
    from neoecmocoupling import ecmo_delivery_from_console_state, vascular_support_port_from_delivery

    ecmo = run_ecmo_console(
        EcmoConsoleControls(rpm=3000, fdo2=1.0, sweep_gas_flow_ml_min=1000),
        native_venous_saturation=0.65,
        native_venous_paco2_mmhg=58.0,
    )
    delivery = ecmo_delivery_from_console_state(ecmo)
    patient = UnifiedNeonatalPatient()
    baseline = patient.snapshot()
    patient.set_vascular_support(vascular_support_port_from_delivery(delivery))
    supported = patient.snapshot()
    assert supported.pao2_mmhg > baseline.pao2_mmhg
    assert supported.paco2_mmhg < baseline.paco2_mmhg
