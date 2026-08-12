from neoevents import EventStream
from neogui.scenario_log import scenario_log_entries


def test_scenario_log_projects_events_in_append_order_with_simulation_time():
    events = EventStream()
    events.emit(event_type="system.lifecycle", source="system", target="workspace", action="initialized", metadata={"simulation_time_s": 0.0})
    events.emit(event_type="control.changed", source="learner", target="ecmo_console", action="set_commanded_rpm", old_value=2200, new_value=2400, metadata={"simulation_time_s": 12.4})
    entries = scenario_log_entries(events.records)
    assert [e.action for e in entries] == ["initialized", "set_commanded_rpm"]
    assert entries[1].simulation_time_s == 12.4
    assert entries[1].simulation_time_text == "00:12"
    assert "2200" in entries[1].detail and "2400" in entries[1].detail


def test_scenario_log_uses_tier_a_disclosure_and_hides_internal_diagnosis_events():
    events = EventStream()
    events.emit(
        event_type="scenario.fault_requested", source="scenario-engine", target="tamponade", action="activate",
        metadata={"simulation_time_s": 3.0, "fault_id": "tamponade", "scenario_id": "hidden-case"},
    )
    events.emit(
        event_type="scenario.observation_sampled", source="scenario-engine", target="assess-hemodynamics", action="sample",
        new_value={"finding": "low flow"}, metadata={"simulation_time_s": 4.0, "scenario_id": "hidden-case"},
    )
    entries = scenario_log_entries(events.records)
    assert len(entries) == 1
    assert entries[0].source == "system"
    text = " ".join((entries[0].event_type, entries[0].source, entries[0].target, entries[0].action, entries[0].detail)).lower()
    assert "tamponade" not in text
    assert "hidden-case" not in text


def test_scenario_log_is_read_only_and_does_not_change_authoritative_stream():
    events = EventStream()
    original = events.emit(event_type="control.changed", source="learner", target="ventilator", action="apply_pressure_control", new_value={"pip": 20}, metadata={"simulation_time_s": 8.0})
    before = events.records
    entries = scenario_log_entries(events.records)
    assert len(entries) == 1
    assert events.records == before == (original,)
