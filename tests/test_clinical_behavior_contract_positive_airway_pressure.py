from __future__ import annotations

import pytest

from neopatient import AirwayPort, UnifiedNeonatalPatient, UnifiedPatientConfig


def _patient(weight_kg: float = 3.0) -> UnifiedNeonatalPatient:
    return UnifiedNeonatalPatient(UnifiedPatientConfig(weight_kg=weight_kg))


def _snapshot_at_peep(peep_cmh2o: float):
    patient = _patient()
    patient.set_airway(AirwayPort(peep_cmh2o=peep_cmh2o))
    return patient.snapshot(include_vascular_support=False)


@pytest.fixture(scope="module")
def graded_peep():
    return {peep: _snapshot_at_peep(peep) for peep in (0.0, 5.0, 8.0, 12.0)}


def test_cbc07_higher_peep_reduces_native_output_and_map_while_measured_cvp_rises(graded_peep):
    baseline = graded_peep[0.0]
    elevated = graded_peep[8.0]

    assert elevated.native_cardiac_output_ml_min < baseline.native_cardiac_output_ml_min
    assert elevated.map_mmhg < baseline.map_mmhg
    assert elevated.cvp_mmhg > baseline.cvp_mmhg

    # Positive airway pressure must not masquerade as a blood-volume intervention.
    assert elevated.total_blood_volume_ml == pytest.approx(baseline.total_blood_volume_ml)
    assert elevated.blood_volume_fraction == pytest.approx(baseline.blood_volume_fraction)


def test_cbc07_canonical_peep_sweep_is_directionally_graded(graded_peep):
    ordered = [graded_peep[p] for p in (0.0, 5.0, 8.0, 12.0)]
    outputs = [s.native_cardiac_output_ml_min for s in ordered]
    maps = [s.map_mmhg for s in ordered]
    cvps = [s.cvp_mmhg for s in ordered]

    assert outputs == sorted(outputs, reverse=True)
    assert maps == sorted(maps, reverse=True)
    assert cvps == sorted(cvps)


def test_cbc07_static_peep_does_not_create_a_large_co2_artifact(graded_peep):
    baseline = graded_peep[0.0]
    elevated = graded_peep[8.0]

    # PEEP is allowed to change gas exchange through the coupled model, but static
    # PEEP alone must not behave like an invented hyperventilation mechanism.
    assert 20.0 <= elevated.paco2_mmhg <= 60.0
    assert elevated.paco2_mmhg > baseline.paco2_mmhg * 0.70


def test_cbc07_reversing_peep_recomputes_the_same_patient_to_baseline():
    patient = _patient()
    baseline = patient.snapshot(include_vascular_support=False)

    patient.set_airway(AirwayPort(peep_cmh2o=8.0))
    elevated = patient.snapshot(include_vascular_support=False)
    assert elevated.native_cardiac_output_ml_min < baseline.native_cardiac_output_ml_min

    patient.set_airway(AirwayPort(peep_cmh2o=0.0))
    restored = patient.snapshot(include_vascular_support=False)

    for field in (
        "native_cardiac_output_ml_min",
        "map_mmhg",
        "cvp_mmhg",
        "pao2_mmhg",
        "paco2_mmhg",
        "total_blood_volume_ml",
        "blood_volume_fraction",
    ):
        assert getattr(restored, field) == pytest.approx(getattr(baseline, field), rel=1e-9, abs=1e-9)
