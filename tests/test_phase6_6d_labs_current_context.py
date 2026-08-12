from neogui.ecmo_workspace import EcmoWorkspace


def test_phase6_6d_live_tk_labs_current_context_is_live_distinct_and_in_view():
    app = EcmoWorkspace()
    try:
        app._show_page("LABS")
        app.root.geometry("1360x820")
        app.root.update_idletasks()

        assert set(app.lab_context_labels) == {"map", "spo2", "flow", "pao2", "paco2"}
        assert "--" not in {label.cget("text") for label in app.lab_context_labels.values()}
        assert app.lab_context_frame is not app.lab_results_text.master
        page_bottom = app.page_frames["LABS"].winfo_rooty() + app.page_frames["LABS"].winfo_height()
        for widget in (app.patient_lab_order_frame, app.postoxy_lab_order_frame, app.lab_context_frame):
            assert widget.winfo_rooty() + widget.winfo_height() <= page_bottom
    finally:
        app._close()
