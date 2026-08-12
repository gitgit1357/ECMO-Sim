from neogui.ux_policy import (
    PHYSIOLOGY_PENDING_TEXT,
    SIMULATOR_ADVISORY_LABEL,
    DEVICE_ALARM_DISCLOSURE,
    ecmo_shortcut_allowed,
    physiology_latency_text,
)


def test_ecmo_shortcuts_are_only_active_on_ecmo_page():
    assert ecmo_shortcut_allowed(active_page_key="ECMO", focus_widget_class="Frame")
    for page in ("MON", "VENT", "LABS", "ACT", "LOG"):
        assert not ecmo_shortcut_allowed(active_page_key=page, focus_widget_class="Frame")


def test_ecmo_shortcuts_are_suppressed_while_editing():
    for widget_class in ("Entry", "TEntry", "TCombobox", "Spinbox", "TSpinbox", "Text"):
        assert not ecmo_shortcut_allowed(active_page_key="ECMO", focus_widget_class=widget_class)


def test_latency_banner_is_explicit_about_simulation_time_pause():
    assert physiology_latency_text(pending=True) == PHYSIOLOGY_PENDING_TEXT
    assert "SIM TIME PAUSED" in PHYSIOLOGY_PENDING_TEXT
    assert physiology_latency_text(pending=False) == ""


def test_current_alarm_boundary_is_disclosed_as_simulator_advisories():
    assert SIMULATOR_ADVISORY_LABEL.startswith("SIMULATOR ADVISORIES")
    assert "NOT DEVICE-VALIDATED" in SIMULATOR_ADVISORY_LABEL
    assert "not yet validated" in DEVICE_ALARM_DISCLOSURE
