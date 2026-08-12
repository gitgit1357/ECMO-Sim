from __future__ import annotations

EDITING_WIDGET_CLASSES = frozenset({
    "Entry", "TEntry", "TCombobox", "Spinbox", "TSpinbox", "Text",
})

SIMULATOR_ADVISORY_LABEL = "SIMULATOR ADVISORIES • NOT DEVICE-VALIDATED"
DEVICE_ALARM_DISCLOSURE = "Device alarm priorities / acknowledge / silence are not yet validated"
PHYSIOLOGY_PENDING_TEXT = "PHYSIOLOGY UPDATING • SIM TIME PAUSED"


def ecmo_shortcut_allowed(*, active_page_key: str, focus_widget_class: str | None) -> bool:
    """Return whether a global ECMO keyboard shortcut may mutate a control.

    Shortcuts are intentionally limited to the ECMO page and suppressed while
    the learner is editing text/combobox/spinbox input.  This is a UI safety
    policy only; it does not change any circuit or patient behavior.
    """
    if active_page_key != "ECMO":
        return False
    return (focus_widget_class or "") not in EDITING_WIDGET_CLASSES


def physiology_latency_text(*, pending: bool) -> str:
    """Learner-visible global status for asynchronous native physiology."""
    return PHYSIOLOGY_PENDING_TEXT if pending else ""
