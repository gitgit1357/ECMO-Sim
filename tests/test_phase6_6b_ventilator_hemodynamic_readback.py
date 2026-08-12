from neogui.ecmo_workspace import EcmoWorkspace


def test_phase6_6b_live_tk_ventilator_has_hemodynamic_readback_and_disclosure_in_view():
    app = EcmoWorkspace()
    try:
        app._show_page("VENT")
        app.root.geometry("1360x820")
        app.root.update_idletasks()

        assert {"map", "cvp", "native_co"}.issubset(app.ventilator_readback_labels)
        assert "ecmo_flow" not in app.ventilator_readback_labels
        disclosure = app.ventilator_cbc07_disclosure.cget("text")
        assert "intrathoracic-relative preload proxy" in disclosure
        assert "not a validated quantitative PEEP-to-ECMO drainage prediction" in disclosure

        page_bottom = app.page_frames["VENT"].winfo_rooty() + app.page_frames["VENT"].winfo_height()
        assert app.ventilator_controls_frame.winfo_rooty() + app.ventilator_controls_frame.winfo_height() <= page_bottom
        assert app.ventilator_readback_frame.winfo_rooty() + app.ventilator_readback_frame.winfo_height() <= page_bottom
        assert app.ventilator_cbc07_disclosure.winfo_rooty() + app.ventilator_cbc07_disclosure.winfo_height() <= page_bottom
    finally:
        app._close()
