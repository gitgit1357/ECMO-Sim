import pytest

from neoecmo import EcmoConsoleControls
from neoecmocoupling import (
    CoupledVaEcmoPatient,
    DynamicCoupledVaEcmoPatient,
    DynamicResponseConfig,
)
from neopatient import UnifiedNeonatalPatient, UnifiedPatientConfig


def make_dynamic(*, rpm=0, config=DynamicResponseConfig()):
    patient = UnifiedNeonatalPatient(
        UnifiedPatientConfig(weight_kg=3.0, lung_run_s=1.0, circulation_run_s=1.0)
    )
    coupled = CoupledVaEcmoPatient(
        patient,
        EcmoConsoleControls(rpm=rpm, sweep_gas_flow_ml_min=600),
    )
    return DynamicCoupledVaEcmoPatient(coupled, config=config)


def test_flow_display_lags_true_flow_after_rpm_step():
    system = make_dynamic(rpm=0)
    baseline = system.snapshot()
    system.set_controls(EcmoConsoleControls(rpm=3000, sweep_gas_flow_ml_min=600))
    after_one_second = system.advance(1.0)

    assert after_one_second.true.delivery.ecmo_return_flow_ml_min > 0.0
    assert after_one_second.displayed.patient_flow_ml_min > baseline.displayed.patient_flow_ml_min
    assert after_one_second.displayed.patient_flow_ml_min < after_one_second.true.delivery.ecmo_return_flow_ml_min


def test_display_converges_toward_true_state_over_time():
    system = make_dynamic(rpm=0)
    system.set_controls(EcmoConsoleControls(rpm=3000, sweep_gas_flow_ml_min=600))
    early = system.advance(1.0)
    late = system.advance(60.0)

    early_error = abs(early.true.delivery.ecmo_return_flow_ml_min - early.displayed.patient_flow_ml_min)
    late_error = abs(late.true.delivery.ecmo_return_flow_ml_min - late.displayed.patient_flow_ml_min)
    assert late_error < early_error


def test_co2_display_changes_more_slowly_than_true_value_after_sweep_step():
    system = make_dynamic(rpm=3000)
    baseline = system.snapshot()
    system.set_controls(EcmoConsoleControls(rpm=3000, sweep_gas_flow_ml_min=2000))
    changed = system.advance(1.0)

    assert changed.true.patient.paco2_mmhg < baseline.true.patient.paco2_mmhg
    assert changed.displayed.paco2_mmhg > changed.true.patient.paco2_mmhg


def test_true_chatter_is_immediate_but_display_latches_after_delay():
    config = DynamicResponseConfig(chatter_activation_delay_s=2.0, chatter_clear_delay_s=3.0)
    system = make_dynamic(rpm=3800, config=config)
    # Produce a severe effective-volume deficit without creating a detailed fluid model.
    system.coupled.patient.record_blood_loss(95.0)
    first = system.advance(0.5)
    assert first.true.volume_limited_ecmo.chatter_active
    assert not first.chatter_display_active

    latched = system.advance(2.0)
    assert latched.chatter_display_active
    assert "DRAINAGE CHATTER" in latched.advisories


def test_low_volume_and_negative_p1_advisories_use_true_state():
    system = make_dynamic(rpm=3800)
    system.coupled.patient.record_blood_loss(110.0)
    snap = system.advance(1.0)

    assert "LOW EFFECTIVE VENOUS VOLUME" in snap.advisories
    assert snap.true.volume_limited_ecmo.preload_fraction < 0.75


def test_negative_time_rejected():
    system = make_dynamic()
    with pytest.raises(ValueError):
        system.advance(-1.0)
