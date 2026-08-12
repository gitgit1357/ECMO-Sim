import time

from neogui.ecmo_workspace import EcmoWorkspace


def _wait_current(app: EcmoWorkspace, timeout_s: float = 10.0):
    deadline = time.perf_counter() + timeout_s
    while app.model.native_physiology_update_pending and time.perf_counter() < deadline:
        time.sleep(0.02)
        app.model.advance(0.0)
    assert not app.model.native_physiology_update_pending
    return app.model.solve()


def test_phase6_6e_live_tk_multiple_lab_results_stay_unread_until_all_render_on_labs():
    app = EcmoWorkspace()
    try:
        app._show_page("ECMO")
        _wait_current(app)
        first = app.model.order_diagnostic("patient_arterial_gas", turnaround_s=0.0)
        second = app.model.order_diagnostic("post_oxygenator_gas", turnaround_s=0.0)
        snapshot = app.model.advance(0.0)
        app._apply_snapshot(snapshot)
        app.root.update_idletasks()

        assert app._unread_lab_result_ids == {first.result_id, second.result_id}
        assert "RESULT READY" in app.nav_buttons["LABS"].cget("text")

        app._show_page("LABS")
        app.root.update_idletasks()
        assert app._unread_lab_result_ids == set()
        assert "RESULT READY" not in app.nav_buttons["LABS"].cget("text")
        text = app.lab_results_text.get("1.0", "end")
        assert first.result_id in text and second.result_id in text
    finally:
        app._close()


def test_phase6_6e_ckrt_attention_is_state_based_and_causation_neutral():
    app = EcmoWorkspace()
    try:
        snapshot = app.model.apply_ckrt_prescription(
            blood_flow_ml_min=30.0,
            net_ultrafiltration_rate_ml_min=0.4,
            event_source="scenario",
        )
        app._apply_snapshot(snapshot)
        app.root.update_idletasks()
        assert "CHECK CKRT" in app.nav_buttons["ACT"].cget("text")

        app._show_page("ACT")
        assert "CHECK CKRT" in app.nav_buttons["ACT"].cget("text")
    finally:
        app._close()
