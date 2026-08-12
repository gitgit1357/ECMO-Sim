import pytest

from neogui import EcmoWorkspaceModel, WorkspaceInputs, patient_monitor_reading


def test_patient_monitor_projection_is_read_only_view_of_workspace_snapshot():
    model = EcmoWorkspaceModel(WorkspaceInputs(pump_running=True, commanded_rpm=2300.0))
    snap = model.solve()
    before_events = model.event_records
    reading = patient_monitor_reading(snap, physiology_updating=model.native_physiology_update_pending)

    assert reading.map_mmhg == pytest.approx(snap.dynamic.displayed.map_mmhg)
    assert reading.spo2_pct == pytest.approx(snap.dynamic.displayed.sao2_pct)
    assert reading.pao2_mmhg == pytest.approx(snap.dynamic.displayed.pao2_mmhg)
    assert reading.paco2_mmhg == pytest.approx(snap.dynamic.displayed.paco2_mmhg)
    assert reading.cvp_mmhg == pytest.approx(snap.dynamic.true.patient.cvp_mmhg)
    assert reading.systolic_mmhg == pytest.approx(snap.dynamic.true.patient.systolic_mmhg)
    assert reading.diastolic_mmhg == pytest.approx(snap.dynamic.true.patient.diastolic_mmhg)
    assert reading.ecmo_patient_flow_ml_min == pytest.approx(snap.dynamic.displayed.patient_flow_ml_min)
    assert model.event_records == before_events
    model.close()


def test_patient_monitor_does_not_invent_unintegrated_hr_or_temperature():
    model = EcmoWorkspaceModel()
    reading = patient_monitor_reading(model.solve())
    assert reading.heart_rate_bpm is None
    assert reading.temperature_c is None
    model.close()


def test_patient_monitor_updates_from_same_dynamic_display_path():
    model = EcmoWorkspaceModel(WorkspaceInputs(pump_running=False, commanded_rpm=2300.0))
    baseline = patient_monitor_reading(model.solve())
    model.update(pump_running=True)
    changed_snapshot = model.advance(1.0)
    changed = patient_monitor_reading(changed_snapshot)

    assert changed.ecmo_patient_flow_ml_min > baseline.ecmo_patient_flow_ml_min
    assert changed.ecmo_patient_flow_ml_min < changed_snapshot.dynamic.true.delivery.ecmo_return_flow_ml_min
    assert changed.map_mmhg == pytest.approx(changed_snapshot.dynamic.displayed.map_mmhg)
    model.close()


def test_patient_monitor_exposes_fluid_and_renal_state_without_deriving_treatment_logic():
    model = EcmoWorkspaceModel()
    snap = model.solve()
    reading = patient_monitor_reading(snap)
    patient = snap.dynamic.true.patient

    assert reading.urine_ml_kg_hr == pytest.approx(patient.urine_ml_kg_hr)
    assert reading.cumulative_urine_ml == pytest.approx(patient.cumulative_urine_ml)
    assert reading.net_body_fluid_ml == pytest.approx(patient.cumulative_net_body_fluid_ml)
    assert reading.blood_volume_fraction == pytest.approx(patient.blood_volume_fraction)
    model.close()
