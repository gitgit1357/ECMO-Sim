from neogui.ecmo_workspace import EcmoWorkspace


def _relative_luminance(color: str) -> float:
    channels = [int(color[index:index + 2], 16) / 255.0 for index in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(fg: str, bg: str) -> float:
    high, low = sorted((_relative_luminance(fg), _relative_luminance(bg)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def test_phase6_6f_wcag_aa_normal_text_pairs_pass_for_core_workspace_colors():
    pairs = [
        (EcmoWorkspace.MUTED, EcmoWorkspace.SCREEN_2),
        (EcmoWorkspace.YELLOW, EcmoWorkspace.SCREEN_2),
        (EcmoWorkspace.MUTED, "#23303a"),
        ("#3d4a50", EcmoWorkspace.NAV),
        ("#37566b", EcmoWorkspace.NAV),
        ("#506068", EcmoWorkspace.NAV),
        ("#ffffff", EcmoWorkspace.NAV_ACTIVE),
    ]
    for fg, bg in pairs:
        assert _contrast(fg, bg) >= 4.5, (fg, bg, _contrast(fg, bg))


def test_phase6_6f_live_tk_attention_states_have_text_not_color_only():
    app = EcmoWorkspace()
    try:
        snapshot = app.model.apply_ckrt_prescription(blood_flow_ml_min=30.0, net_ultrafiltration_rate_ml_min=0.4)
        app._apply_snapshot(snapshot)
        app.root.update_idletasks()
        assert "CHECK CKRT" in app.nav_buttons["ACT"].cget("text")
        assert "INACTIVE" in app.ckrt_intervention_status.cget("text").upper()
        assert app.ribbon_compute_status.cget("text") in {"CURRENT", "PHYSIOLOGY UPDATING • LAST COMMITTED VALUES"}
    finally:
        app._close()
