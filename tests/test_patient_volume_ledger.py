import pytest
from neopatient import UnifiedNeonatalPatient, UnifiedPatientConfig


def test_weight_based_baseline_preserves_default_patient():
    p=UnifiedNeonatalPatient(UnifiedPatientConfig(weight_kg=3.5))
    s=p.snapshot()
    assert s.total_blood_volume_ml == pytest.approx(301.0, abs=0.01)


def test_weight_based_baseline_scales_with_weight():
    p=UnifiedNeonatalPatient(UnifiedPatientConfig(weight_kg=3.0))
    assert p.snapshot().total_blood_volume_ml == pytest.approx(258.0, abs=0.01)


def test_blood_input_and_loss_change_intravascular_volume():
    p=UnifiedNeonatalPatient(UnifiedPatientConfig(weight_kg=3.0))
    baseline=p.snapshot().total_blood_volume_ml
    p.add_intravascular_input(10)
    assert p.snapshot().total_blood_volume_ml == pytest.approx(baseline+10)
    p.record_blood_loss(6)
    assert p.snapshot().total_blood_volume_ml == pytest.approx(baseline+4)


def test_third_spacing_reduces_effective_venous_volume_not_measured_blood_volume():
    p=UnifiedNeonatalPatient(UnifiedPatientConfig(weight_kg=3.0))
    before=p.snapshot()
    p.move_to_third_space(12)
    after=p.snapshot()
    assert after.total_blood_volume_ml == pytest.approx(before.total_blood_volume_ml)
    assert after.effective_venous_volume_ml == pytest.approx(before.effective_venous_volume_ml-12)
    assert after.effective_venous_volume_fraction < after.blood_volume_fraction


def test_sampling_loss_is_tracked_separately():
    p=UnifiedNeonatalPatient(UnifiedPatientConfig(weight_kg=3.0))
    p.record_sampling_loss(2.5)
    assert p.state.volume_ledger.cumulative_sampling_loss_ml == pytest.approx(2.5)
