from neogui.ecmo_workspace import EcmoWorkspace


def test_phase6_6c_live_tk_interventions_controls_and_readback_are_simultaneously_visible():
    app = EcmoWorkspace()
    try:
        app._show_page("ACT")
        app.root.geometry("1360x820")
        app.root.update_idletasks()

        assert set(app.intervention_readback_labels) == {"map", "cvp", "flow", "urine", "fluid", "blood"}
        assert "--" not in {label.cget("text") for label in app.intervention_readback_labels.values()}
        page_bottom = app.page_frames["ACT"].winfo_rooty() + app.page_frames["ACT"].winfo_height()
        for widget in (app.volume_intervention_frame, app.ckrt_intervention_frame, app.intervention_readback_frame):
            assert widget.winfo_rooty() + widget.winfo_height() <= page_bottom
    finally:
        app._close()
