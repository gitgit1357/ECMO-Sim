import time

from neoecmo import ShuntLineConfiguration
from neogui.ecmo_workspace import EcmoWorkspace


def _wait_current(app: EcmoWorkspace, timeout_s: float = 10.0):
    deadline = time.perf_counter() + timeout_s
    while app.model.native_physiology_update_pending and time.perf_counter() < deadline:
        time.sleep(0.02)
        app.model.advance(0.0)
    assert not app.model.native_physiology_update_pending
    snapshot = app.model.solve()
    app._apply_snapshot(snapshot)
    app.root.update_idletasks()
    return snapshot


def test_phase6_act_observe_console_row():
    app = EcmoWorkspace()
    try:
        app._show_page("ECMO")
        before = app.telemetry_tiles["map"].value.cget("text")
        app._toggle_pump()
        app.root.update_idletasks()
        assert app.telemetry_tiles["map"].value.cget("text") != "--"
        assert app.telemetry_tiles["patient"].value.cget("text") != "--"
        assert app.status_ribbon_labels["map"].cget("text") != "--"
        assert app.status_ribbon_labels["ecmo_flow"].cget("text") != "--"
        assert before != ""
    finally:
        app._close()


def test_phase6_act_observe_ventilator_row():
    app = EcmoWorkspace()
    try:
        app._show_page("VENT")
        _wait_current(app)
        app.vent_pip_var.set("12")
        app.vent_peep_var.set("8")
        app.vent_rate_var.set("40")
        app.vent_ti_var.set("0.35")
        app.vent_fio2_var.set("40")
        app._apply_pressure_control()
        _wait_current(app)
        for key in ("map", "cvp", "native_co", "pao2", "paco2"):
            assert app.ventilator_readback_labels[key].cget("text") != "--"
        assert "ecmo_flow" not in app.ventilator_readback_labels
        assert app.status_ribbon_labels["ecmo_flow"].cget("text") != "--"
    finally:
        app._close()


def test_phase6_act_observe_interventions_volume_row():
    app = EcmoWorkspace()
    try:
        app._show_page("ACT")
        _wait_current(app)
        before = app.intervention_readback_labels["blood"].cget("text")
        app.volume_intervention_var.set("10")
        app._apply_volume_intervention()
        _wait_current(app)
        after = app.intervention_readback_labels["blood"].cget("text")
        assert after != "--"
        assert after != before
        for key in ("map", "cvp", "flow", "fluid"):
            assert app.intervention_readback_labels[key].cget("text") != "--"
    finally:
        app._close()


def test_phase6_act_observe_interventions_ckrt_row():
    app = EcmoWorkspace()
    try:
        app._show_page("ACT")
        snapshot = app.model.update(shunt_configuration=ShuntLineConfiguration.CKRT)
        app._apply_snapshot(snapshot)
        app.ckrt_blood_flow_var.set("30")
        app.ckrt_uf_var.set("0.4")
        app._apply_ckrt_intervention()
        app.root.update_idletasks()
        assert "ACTIVE" in app.ckrt_intervention_status.cget("text")
        for key in ("map", "cvp", "flow", "urine", "fluid"):
            assert app.intervention_readback_labels[key].cget("text") != "--"
    finally:
        app._close()


def test_phase6_act_observe_labs_row():
    app = EcmoWorkspace()
    try:
        app._show_page("LABS")
        _wait_current(app)
        app._order_lab("patient_arterial_gas")
        app.root.update_idletasks()
        assert all(label.cget("text") != "--" for label in app.lab_context_labels.values())
        text = app.lab_results_text.get("1.0", "end")
        assert "PENDING" in text
        assert "CURRENT PATIENT CONTEXT" != "ORDERED RESULTS"
    finally:
        app._close()


def test_phase6_act_observe_monitor_read_only_row_keeps_ribbon_visible():
    app = EcmoWorkspace()
    try:
        app._show_page("MON")
        app.root.update_idletasks()
        assert app.status_ribbon_frame.winfo_ismapped()
        assert app.status_ribbon_labels["map"].cget("text") != "--"
    finally:
        app._close()


def test_phase6_act_observe_scenario_log_read_only_row_keeps_ribbon_visible():
    app = EcmoWorkspace()
    try:
        app._show_page("LOG")
        app.root.update_idletasks()
        assert app.status_ribbon_frame.winfo_ismapped()
        assert app.status_ribbon_labels["map"].cget("text") != "--"
    finally:
        app._close()
