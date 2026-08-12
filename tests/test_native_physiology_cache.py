from neopatient import UnifiedNeonatalPatient, UnifiedPatientConfig


def test_repeated_snapshots_reuse_native_physiology(monkeypatch):
    import neopatient.core as core

    calls = 0
    original = core.run_coupled_neonate

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(core, "run_coupled_neonate", counted)
    patient = UnifiedNeonatalPatient(
        UnifiedPatientConfig(weight_kg=3.0, lung_run_s=0.2, circulation_run_s=0.2)
    )
    patient.snapshot()
    patient.snapshot()
    patient.snapshot()
    assert calls == 1


def test_explicit_blood_loss_invalidates_native_physiology(monkeypatch):
    import neopatient.core as core

    calls = 0
    original = core.run_coupled_neonate

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(core, "run_coupled_neonate", counted)
    patient = UnifiedNeonatalPatient(
        UnifiedPatientConfig(weight_kg=3.0, lung_run_s=0.2, circulation_run_s=0.2)
    )
    patient.snapshot()
    patient.record_blood_loss(1.0)
    patient.snapshot()
    assert calls == 2
