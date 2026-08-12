from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from neoecmocoupling.adapters import patient_boundary_from_snapshot
from neopatient import (
    UnifiedNeonatalPatient,
    VenousOxygenState,
    VenousPreloadState,
    VenousState,
)


COMPUTATION_SOURCES = (
    "src/neopatient/core.py",
    "src/neocoupling/core.py",
    "src/neoecmocoupling/adapters.py",
)
PROJECTION_TOKENS = (
    "learner_patient_reading",
    "patient_monitor_reading",
    "neogui.patient_monitor",
)


def _projection_dependency_violations(source_text: str) -> tuple[str, ...]:
    lowered = source_text.lower()
    return tuple(token for token in PROJECTION_TOKENS if token.lower() in lowered)


def test_phase9a_structural_guard_no_projection_feedback_into_venous_state():
    project_root = Path(__file__).resolve().parents[1]
    violations = {}
    for relative in COMPUTATION_SOURCES:
        text = (project_root / relative).read_text()
        found = _projection_dependency_violations(text)
        if found:
            violations[relative] = found
    assert violations == {}


def test_phase9a_structural_guard_demonstrably_rejects_projection_dependency():
    deliberately_broken_source = (
        "from neogui.patient_monitor import learner_patient_reading\n"
        "venous = learner_patient_reading(snapshot)\n"
    )
    assert _projection_dependency_violations(deliberately_broken_source) == (
        "learner_patient_reading",
        "neogui.patient_monitor",
    )


def test_phase9a_venous_state_is_immutable_and_preserves_existing_authorities():
    patient = UnifiedNeonatalPatient()
    try:
        coupled = patient._solve()
        snapshot = patient.snapshot()

        assert snapshot.venous.preload.cvp_mmhg == pytest.approx(
            coupled.circulation_metrics.mean_ra_mmhg
        )
        assert snapshot.cvp_mmhg == pytest.approx(snapshot.venous.preload.cvp_mmhg)
        assert snapshot.venous.preload.effective_venous_volume_ml == pytest.approx(
            snapshot.effective_venous_volume_ml
        )
        assert snapshot.venous.preload.effective_venous_volume_fraction == pytest.approx(
            snapshot.effective_venous_volume_fraction
        )

        assert snapshot.venous.oxygen.native_mixed_venous_po2_mmhg == pytest.approx(
            coupled.mixed_venous_po2_mmhg
        )
        assert snapshot.venous.oxygen.native_mixed_venous_saturation_pct == pytest.approx(
            coupled.mixed_venous_saturation_pct
        )
        assert snapshot.venous.oxygen.native_mixed_venous_oxygen_content_ml_dl == pytest.approx(
            coupled.mixed_venous_oxygen_content_ml_dl
        )

        with pytest.raises(FrozenInstanceError):
            snapshot.venous.preload.cvp_mmhg = 999.0
    finally:
        patient.shutdown()


def test_phase9a_preload_proxy_is_explicitly_derived_from_current_native_step():
    patient = UnifiedNeonatalPatient()
    try:
        coupled = patient._solve()
        snapshot = patient.snapshot()
        preload = snapshot.venous.preload

        assert preload.pleural_delta_mmhg == pytest.approx(coupled.pleural_delta_mmhg)
        assert preload.intrathoracic_relative_preload_proxy_mmhg == pytest.approx(
            coupled.circulation_metrics.mean_ra_mmhg - coupled.pleural_delta_mmhg
        )
    finally:
        patient.shutdown()


def test_phase9a_venous_state_uses_current_volume_ledger_after_update():
    patient = UnifiedNeonatalPatient()
    try:
        before = patient.snapshot()
        patient.add_intravascular_input(10.0)
        after = patient.snapshot()

        assert after.venous.preload.effective_venous_volume_ml > before.venous.preload.effective_venous_volume_ml
        assert after.venous.preload.effective_venous_volume_fraction == pytest.approx(
            after.effective_venous_volume_fraction
        )
    finally:
        patient.shutdown()


def test_phase9a_existing_ecmo_boundary_consumes_only_canonical_venous_api():
    patient = UnifiedNeonatalPatient()
    try:
        snapshot = patient.snapshot()
        substituted = VenousState(
            preload=VenousPreloadState(
                cvp_mmhg=7.25,
                pleural_delta_mmhg=1.5,
                intrathoracic_relative_preload_proxy_mmhg=5.75,
                effective_venous_volume_ml=222.0,
                effective_venous_volume_fraction=0.73,
            ),
            oxygen=VenousOxygenState(
                native_mixed_venous_po2_mmhg=31.0,
                native_mixed_venous_saturation_pct=61.0,
                native_mixed_venous_oxygen_content_ml_dl=13.5,
            ),
        )
        snapshot = replace(
            snapshot,
            venous=substituted,
            cvp_mmhg=99.0,
            effective_venous_volume_fraction=0.99,
            sao2_pct=99.0,
        )

        boundary = patient_boundary_from_snapshot(snapshot, weight_kg=3.5)

        # Phase 10a intentionally migrates the ECMO drainage boundary from
        # measured CVP to the canonical intrathoracic-relative preload proxy.
        assert boundary.venous_pressure_mmhg == pytest.approx(5.75)
        assert boundary.blood_volume_fraction == pytest.approx(0.73)
        assert boundary.native_venous_oxygen_saturation == pytest.approx(0.61)
    finally:
        patient.shutdown()
