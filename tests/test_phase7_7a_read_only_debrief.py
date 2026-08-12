from pathlib import Path

from neoevents import EventStream
from neogui.scenario_log import debrief_entries, scenario_log_entries


def test_phase7_debrief_is_read_only_projection_of_canonical_event_stream():
    events = EventStream()
    original = events.emit(
        event_type="control.changed",
        source="learner",
        target="ecmo_console",
        action="set_commanded_rpm",
        old_value=2200,
        new_value=2500,
        metadata={"simulation_time_s": 14.0},
    )
    before = events.records

    entries = debrief_entries(events.records)

    assert events.records == before == (original,)
    assert entries == scenario_log_entries(events.records)
    assert entries[0].simulation_time_text == "00:14"
    assert entries[0].action == "set_commanded_rpm"


def test_phase7_debrief_retains_tier_a_disclosure_and_does_not_expose_hidden_diagnosis():
    events = EventStream()
    events.emit(
        event_type="scenario.fault_requested",
        source="scenario-engine",
        target="tamponade",
        action="activate",
        metadata={"simulation_time_s": 1.0, "fault_id": "tamponade", "scenario_id": "secret"},
    )
    events.emit(
        event_type="scenario.observation_sampled",
        source="scenario-engine",
        target="assess-hemodynamics",
        action="sample",
        new_value={"finding": "low flow"},
        metadata={"simulation_time_s": 2.0, "scenario_id": "secret"},
    )

    entries = debrief_entries(events.records)

    assert len(entries) == 1
    rendered = " ".join(
        (entries[0].event_type, entries[0].source, entries[0].target, entries[0].action, entries[0].detail)
    ).lower()
    assert "tamponade" not in rendered
    assert "secret" not in rendered


def test_phase7_debrief_contract_has_no_score_interpretation_or_replay_fields():
    events = EventStream()
    events.emit(
        event_type="control.changed",
        source="learner",
        target="ventilator",
        action="apply_pressure_control",
        new_value={"pip": 20},
        metadata={"simulation_time_s": 8.0},
    )
    entry = debrief_entries(events.records)[0]

    prohibited = {
        "score", "points", "grade", "correct", "incorrect", "optimal",
        "interpretation", "diagnosis", "replay_snapshot", "snapshot",
    }
    assert prohibited.isdisjoint(vars(entry))


def test_phase7_gui_presents_debrief_without_scoring_or_replay_controls():
    source = (Path(__file__).resolve().parents[1] / "src" / "neogui" / "ecmo_workspace.py").read_text()
    start = source.index("def _build_scenario_log_page")
    end = source.index("def _refresh_scenario_log", start)
    block = source[start:end].lower()

    assert '"debrief"' in source.lower()
    assert "debrief — event timeline" in block
    assert "does not score performance" in block
    assert "replay historical physiology" in block
    for forbidden_control in ("score_button", "replay_button", "grade_button"):
        assert forbidden_control not in block


def test_phase7_live_tk_debrief_renders_event_stream_without_mutation():
    from neogui.ecmo_workspace import EcmoWorkspace

    app = EcmoWorkspace()
    try:
        assert app.nav_buttons["LOG"].cget("text") == "Debrief"
        before = app.model.event_records
        app._refresh_scenario_log()
        after = app.model.event_records

        assert after == before
        assert len(app.scenario_log_tree.get_children()) == len(debrief_entries(before))
        def widget_texts(widget):
            texts = []
            if hasattr(widget, "cget") and "text" in widget.keys():
                texts.append(widget.cget("text"))
            for child in widget.winfo_children():
                texts.extend(widget_texts(child))
            return texts

        assert any("DEBRIEF" in text for text in widget_texts(app.page_frames["LOG"]))
    finally:
        app._close()
