import time

import pytest

from neogui import EcmoWorkspaceModel, WorkspaceInputs
from neolabs import LabQueue


def _wait_current(model: EcmoWorkspaceModel, timeout_s: float = 8.0):
    deadline = time.perf_counter() + timeout_s
    model.solve()
    while model.native_physiology_update_pending and time.perf_counter() < deadline:
        time.sleep(0.02)
        model.advance(0.0)
    assert not model.native_physiology_update_pending
    return model.solve()


def _events(model, event_type):
    return [record for record in model.event_records if record.event_type == event_type]


def test_lab_queue_freezes_nested_values_and_uses_deterministic_ids():
    queue = LabQueue()
    source = {"po2": 80.0, "nested": {"flags": ["a"]}}
    first = queue.order(
        panel_id="gas", panel_name="Gas", sample_site="arterial",
        sample_time_s=10.0, turnaround_s=20.0, values=source,
    )
    source["po2"] = 500.0
    source["nested"]["flags"].append("b")
    second = queue.order(
        panel_id="gas", panel_name="Gas", sample_site="arterial",
        sample_time_s=11.0, turnaround_s=0.0, values={"po2": 90.0},
    )
    assert first.result_id == "lab-0001"
    assert second.result_id == "lab-0002"
    assert first.values["po2"] == pytest.approx(80.0)
    assert tuple(first.values["nested"]["flags"]) == ("a",)
    assert not first.is_available(29.9)
    assert first.is_available(30.0)


def test_patient_gas_is_frozen_at_sample_time_and_rejects_pending_native_state():
    model = EcmoWorkspaceModel()
    try:
        model.solve()
        if model.native_physiology_update_pending:
            with pytest.raises(RuntimeError):
                model.order_diagnostic("patient_arterial_gas", turnaround_s=5.0)
        snap = _wait_current(model)
        result = model.order_diagnostic("patient_arterial_gas", turnaround_s=5.0)
        assert result.sample_time_s == pytest.approx(snap.dynamic.elapsed_s)
        assert result.values["pao2_mmhg"] == pytest.approx(snap.dynamic.true.patient.pao2_mmhg)
        assert result.values["paco2_mmhg"] == pytest.approx(snap.dynamic.true.patient.paco2_mmhg)
        assert result.values["sao2_pct"] == pytest.approx(snap.dynamic.true.patient.sao2_pct)
        assert "pH" in result.metadata["missing_analytes"]

        frozen = dict(result.values)
        model.update(fdo2=0.21)
        model.advance(5.0)
        assert dict(result.values) == frozen
    finally:
        model.close()


def test_post_oxygenator_gas_freezes_collection_value_not_future_console_value():
    model = EcmoWorkspaceModel(WorkspaceInputs(pump_running=True, commanded_rpm=2400.0, fdo2=1.0))
    try:
        _wait_current(model)
        result = model.order_diagnostic("post_oxygenator_gas", turnaround_s=10.0)
        collected_pco2 = result.values["pco2_mmhg"]
        assert collected_pco2 == pytest.approx(model.solve().coupled_state.post_oxygenator_paco2_mmhg)

        changed = model.update(sweep_gas_flow_ml_min=0.0)
        assert changed.coupled_state.post_oxygenator_paco2_mmhg != pytest.approx(collected_pco2)
        model.advance(10.0)
        assert result.values["pco2_mmhg"] == pytest.approx(collected_pco2)
    finally:
        model.close()


def test_lab_order_and_result_available_events_are_separate_and_result_event_emits_once():
    model = EcmoWorkspaceModel()
    try:
        _wait_current(model)
        result = model.order_diagnostic("patient_arterial_gas", turnaround_s=2.0)
        ordered = _events(model, "diagnostic.ordered")
        assert ordered[-1].new_value["result_id"] == result.result_id
        assert not _events(model, "diagnostic.result_available")

        model.advance(1.0)
        assert not _events(model, "diagnostic.result_available")
        model.advance(1.0)
        available = _events(model, "diagnostic.result_available")
        assert len(available) == 1
        assert available[0].new_value["result_id"] == result.result_id
        model.advance(1.0)
        assert len(_events(model, "diagnostic.result_available")) == 1
    finally:
        model.close()


def test_zero_turnaround_still_preserves_distinct_order_and_availability_events():
    model = EcmoWorkspaceModel()
    try:
        _wait_current(model)
        result = model.order_diagnostic("post_oxygenator_gas", turnaround_s=0.0)
        assert result.is_available(result.sample_time_s)
        assert _events(model, "diagnostic.ordered")[-1].new_value["result_id"] == result.result_id
        assert _events(model, "diagnostic.result_available")[-1].new_value["result_id"] == result.result_id
    finally:
        model.close()


def test_unsupported_or_invalid_lab_orders_are_rejected_without_events():
    model = EcmoWorkspaceModel()
    try:
        _wait_current(model)
        before = len(model.event_records)
        with pytest.raises(KeyError):
            model.order_diagnostic("cbc_panel")
        with pytest.raises(ValueError):
            model.order_diagnostic("patient_arterial_gas", turnaround_s=-1.0)
        with pytest.raises(ValueError):
            model.order_diagnostic("patient_arterial_gas", turnaround_s=float("nan"))
        assert len(model.event_records) == before
    finally:
        model.close()
