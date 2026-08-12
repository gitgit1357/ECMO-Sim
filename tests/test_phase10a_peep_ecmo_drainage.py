from dataclasses import replace

import pytest

from neoecmo import EcmoConsoleControls
from neoecmocoupling import CoupledVaEcmoPatient, patient_boundary_from_snapshot
from neopatient import AirwayPort, UnifiedNeonatalPatient, UnifiedPatientConfig


def _system(peep_cmh2o: float, *, rpm: float = 3000.0):
    patient = UnifiedNeonatalPatient(
        UnifiedPatientConfig(weight_kg=3.0, lung_run_s=1.0, circulation_run_s=1.0)
    )
    patient.set_airway(AirwayPort(peep_cmh2o=peep_cmh2o))
    coupled = CoupledVaEcmoPatient(
        patient,
        EcmoConsoleControls(rpm=rpm, sweep_gas_flow_ml_min=600.0),
    )
    return patient, coupled


def test_phase10a_ecmo_boundary_uses_intrathoracic_relative_preload_not_measured_cvp():
    patient, _ = _system(8.0)
    try:
        snapshot = patient.snapshot(include_vascular_support=False)
        boundary = patient_boundary_from_snapshot(snapshot, weight_kg=patient.config.weight_kg)
        assert snapshot.cvp_mmhg > snapshot.venous.preload.intrathoracic_relative_preload_proxy_mmhg
        assert boundary.venous_pressure_mmhg == pytest.approx(
            snapshot.venous.preload.intrathoracic_relative_preload_proxy_mmhg
        )
        assert boundary.venous_pressure_mmhg != pytest.approx(snapshot.cvp_mmhg)
    finally:
        patient.shutdown()


def test_phase10a_graded_peep_raises_measured_cvp_but_lowers_drainage_preload_and_ecmo_flow():
    rows = []
    for peep in (0.0, 5.0, 8.0, 12.0):
        patient, coupled = _system(peep)
        try:
            snap = coupled.snapshot()
            rows.append((
                snap.native_patient.cvp_mmhg,
                snap.native_patient.venous.preload.intrathoracic_relative_preload_proxy_mmhg,
                snap.delivery.ecmo_return_flow_ml_min,
            ))
        finally:
            patient.shutdown()

    cvp = [r[0] for r in rows]
    preload = [r[1] for r in rows]
    flow = [r[2] for r in rows]
    assert cvp == sorted(cvp)
    assert preload == sorted(preload, reverse=True)
    assert flow == sorted(flow, reverse=True)


def test_phase10a_peep_drainage_effect_is_bounded_and_does_not_change_blood_volume():
    baseline_patient, baseline_coupled = _system(0.0)
    elevated_patient, elevated_coupled = _system(8.0)
    try:
        baseline = baseline_coupled.snapshot()
        elevated = elevated_coupled.snapshot()
        assert elevated.native_patient.total_blood_volume_ml == pytest.approx(
            baseline.native_patient.total_blood_volume_ml
        )
        assert elevated.native_patient.blood_volume_fraction == pytest.approx(
            baseline.native_patient.blood_volume_fraction
        )
        # Regression guard only: prevent the educational coupling from becoming
        # a catastrophic step response at the canonical probe.
        assert elevated.delivery.ecmo_return_flow_ml_min > baseline.delivery.ecmo_return_flow_ml_min * 0.80
        assert elevated.delivery.ecmo_return_flow_ml_min < baseline.delivery.ecmo_return_flow_ml_min
    finally:
        baseline_patient.shutdown()
        elevated_patient.shutdown()


def test_phase10a_same_patient_peep_reversal_restores_ecmo_drainage():
    patient, coupled = _system(0.0)
    try:
        baseline = coupled.snapshot()
        patient.set_airway(AirwayPort(peep_cmh2o=8.0))
        elevated = coupled.snapshot()
        assert elevated.delivery.ecmo_return_flow_ml_min < baseline.delivery.ecmo_return_flow_ml_min

        patient.set_airway(AirwayPort(peep_cmh2o=0.0))
        restored = coupled.snapshot()
        assert restored.delivery.ecmo_return_flow_ml_min == pytest.approx(
            baseline.delivery.ecmo_return_flow_ml_min, rel=1e-9, abs=1e-9
        )
        assert restored.volume_limited_ecmo.effective_venous_pressure_mmhg == pytest.approx(
            baseline.volume_limited_ecmo.effective_venous_pressure_mmhg, rel=1e-9, abs=1e-9
        )
    finally:
        patient.shutdown()


def test_phase10a_measured_cvp_cannot_override_canonical_drainage_preload_proxy():
    patient, _ = _system(8.0)
    try:
        snapshot = patient.snapshot(include_vascular_support=False)
        altered = replace(snapshot, cvp_mmhg=99.0)
        boundary = patient_boundary_from_snapshot(altered, weight_kg=patient.config.weight_kg)
        assert boundary.venous_pressure_mmhg == pytest.approx(
            snapshot.venous.preload.intrathoracic_relative_preload_proxy_mmhg
        )
    finally:
        patient.shutdown()
