import pytest

from neoecmo import ShuntLineConfiguration
from neogui import EcmoWorkspaceModel, WorkspaceInputs


def _events(model, event_type):
    return [record for record in model.event_records if record.event_type == event_type]


def test_volume_intervention_uses_authoritative_patient_volume_mechanism_and_emits_event():
    model = EcmoWorkspaceModel()
    try:
        before = model.dynamic.coupled.patient.snapshot()
        model.apply_intravascular_volume(10.0)
        after = model.dynamic.coupled.patient.snapshot()
        assert after.total_blood_volume_ml == pytest.approx(before.total_blood_volume_ml + 10.0)
        events = _events(model, "intervention.applied")
        assert events[-1].action == "add_intravascular_volume"
        assert events[-1].metadata["mechanism_id"] == "patient.add_intravascular_input"
        assert events[-1].metadata["volume_ml"] == pytest.approx(10.0)
    finally:
        model.close()


def test_volume_intervention_rejects_non_positive_or_nonfinite_values():
    model = EcmoWorkspaceModel()
    try:
        for value in (0.0, -1.0, float("nan"), float("inf")):
            with pytest.raises(ValueError):
                model.apply_intravascular_volume(value)
    finally:
        model.close()


def test_ckrt_prescription_is_stored_but_inactive_when_shunt_is_not_ckrt():
    model = EcmoWorkspaceModel(WorkspaceInputs(shunt_configuration=ShuntLineConfiguration.OPEN))
    try:
        snapshot = model.apply_ckrt_prescription(
            blood_flow_ml_min=30.0,
            net_ultrafiltration_rate_ml_min=0.4,
        )
        assert snapshot.inputs.shunt_ckrt_blood_flow_ml_min == pytest.approx(30.0)
        assert snapshot.inputs.shunt_ckrt_net_ultrafiltration_rate_ml_min == pytest.approx(0.4)
        event = _events(model, "intervention.applied")[-1]
        assert event.action == "set_ckrt_prescription"
        assert event.metadata["active"] is False
        before = model.dynamic.coupled.patient.state.volume_ledger.cumulative_ckrt_removal_ml
        model.advance(60.0)
        after = model.dynamic.coupled.patient.state.volume_ledger.cumulative_ckrt_removal_ml
        assert after == pytest.approx(before)
    finally:
        model.close()


def test_ckrt_prescription_removes_fluid_only_when_ckrt_selected_and_blood_flow_running():
    model = EcmoWorkspaceModel(WorkspaceInputs(shunt_configuration=ShuntLineConfiguration.CKRT))
    try:
        model.apply_ckrt_prescription(
            blood_flow_ml_min=30.0,
            net_ultrafiltration_rate_ml_min=0.4,
        )
        event = _events(model, "intervention.applied")[-1]
        assert event.metadata["active"] is True
        before = model.dynamic.coupled.patient.state.volume_ledger.cumulative_ckrt_removal_ml
        model.advance(60.0)
        after = model.dynamic.coupled.patient.state.volume_ledger.cumulative_ckrt_removal_ml
        assert after - before == pytest.approx(0.4, abs=1e-6)
    finally:
        model.close()


def test_ckrt_zero_blood_flow_gates_net_uf_even_when_ckrt_selected():
    model = EcmoWorkspaceModel(WorkspaceInputs(shunt_configuration=ShuntLineConfiguration.CKRT))
    try:
        model.apply_ckrt_prescription(
            blood_flow_ml_min=0.0,
            net_ultrafiltration_rate_ml_min=0.4,
        )
        before = model.dynamic.coupled.patient.state.volume_ledger.cumulative_ckrt_removal_ml
        model.advance(60.0)
        after = model.dynamic.coupled.patient.state.volume_ledger.cumulative_ckrt_removal_ml
        assert after == pytest.approx(before)
    finally:
        model.close()


def test_ckrt_prescription_rejects_negative_or_nonfinite_values():
    model = EcmoWorkspaceModel()
    try:
        bad_pairs = [(-1.0, 0.0), (10.0, -0.1), (float("nan"), 0.0), (10.0, float("inf"))]
        for blood_flow, uf in bad_pairs:
            with pytest.raises(ValueError):
                model.apply_ckrt_prescription(
                    blood_flow_ml_min=blood_flow,
                    net_ultrafiltration_rate_ml_min=uf,
                )
    finally:
        model.close()
