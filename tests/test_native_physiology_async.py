import time

from neopatient import UnifiedNeonatalPatient, UnifiedPatientConfig
from neogui import EcmoWorkspaceModel


def _wait_for_native_commit(patient, timeout_s=8.0):
    deadline = time.perf_counter() + timeout_s
    while time.perf_counter() < deadline:
        patient.snapshot()
        runner = patient._native_async_runner
        if (
            runner.active_revision is None
            and runner.pending_revision is None
            and not patient.native_physiology_update_pending
        ):
            return
        time.sleep(0.005)
    raise AssertionError("native physiology worker did not settle before timeout")


def test_async_normal_completion_commits_once():
    patient = UnifiedNeonatalPatient(
        UnifiedPatientConfig(
            weight_kg=3.0,
            lung_run_s=0.3,
            circulation_run_s=0.3,
            native_physiology_async=True,
            native_physiology_executor="process",
        )
    )
    patient.snapshot()  # initial synchronous cache fill
    patient.record_blood_loss(1.0)
    stale = patient.snapshot()  # schedules revision 1, returns last-known-good
    assert patient.native_physiology_update_pending
    _wait_for_native_commit(patient)
    events = patient.native_physiology_debug_events
    commits = [e for e in events if e["event_type"] == "native_physiology_result" and e["status"] == "committed"]
    assert [e["revision"] for e in commits] == [1]
    assert patient._native_async_runner.started_revisions == (1,)
    assert patient._physiology_cache_blood_volume_delta_ml == patient.state.blood_volume_delta_ml
    patient._native_async_runner.shutdown()


def test_async_rapid_supersession_executes_only_active_and_latest_pending():
    patient = UnifiedNeonatalPatient(
        UnifiedPatientConfig(
            weight_kg=3.0,
            lung_run_s=1.0,
            circulation_run_s=1.0,
            native_physiology_async=True,
            native_physiology_executor="process",
        )
    )
    patient.snapshot()  # initial synchronous cache fill

    for _ in range(4):
        patient.record_blood_loss(1.0)
        patient.snapshot()

    assert patient._native_async_latest_requested_revision == 4
    assert patient._native_async_runner.active_revision == 1
    assert patient._native_async_runner.pending_revision == 4

    _wait_for_native_commit(patient)

    # Revision 1 was already running and cannot be cancelled. Revisions 2/3
    # never run; the latest pending request (4) replaces them.
    assert patient._native_async_runner.started_revisions == (1, 4)
    results = [e for e in patient.native_physiology_debug_events if e["event_type"] == "native_physiology_result"]
    assert [(e["revision"], e["status"]) for e in results] == [
        (1, "discarded_stale"),
        (4, "committed"),
    ]
    assert patient._physiology_cache_blood_volume_delta_ml == patient.state.blood_volume_delta_ml
    patient._native_async_runner.shutdown()


def test_workspace_freezes_simulation_time_while_native_equilibrium_updates():
    model = EcmoWorkspaceModel()
    patient = model.dynamic.coupled.patient
    initial = model.advance(1.0)
    elapsed_before = initial.dynamic.elapsed_s

    patient.record_blood_loss(20.0)
    t0 = time.perf_counter()
    pending = model.advance(1.0)
    callback_s = time.perf_counter() - t0

    assert callback_s < 0.250
    assert pending.dynamic.elapsed_s == elapsed_before
    assert model.native_physiology_update_pending

    deadline = time.perf_counter() + 8.0
    while time.perf_counter() < deadline and model.native_physiology_update_pending:
        model.advance(1.0)
        time.sleep(0.005)

    assert not model.native_physiology_update_pending
    resumed = model.advance(1.0)
    assert resumed.dynamic.elapsed_s == elapsed_before + 1.0
    patient._native_async_runner.shutdown()
