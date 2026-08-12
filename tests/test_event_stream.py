from datetime import datetime, timezone
import json

import pytest

from neoevents import EventRecord, EventStream


def test_event_record_requires_machine_readable_identity_and_aware_timestamp():
    with pytest.raises(ValueError):
        EventRecord(
            timestamp=datetime.now(), event_type="control.changed", source="learner",
            target="ecmo_console", action="set_rpm"
        )
    with pytest.raises(ValueError):
        EventRecord(
            timestamp=datetime.now(timezone.utc), event_type="", source="learner",
            target="ecmo_console", action="set_rpm"
        )


def test_event_record_round_trips_through_stable_dictionary_schema():
    record = EventRecord(
        timestamp=datetime(2026, 8, 10, 18, 0, tzinfo=timezone.utc),
        event_type="control.changed",
        source="learner",
        target="ecmo_console",
        action="set_commanded_rpm",
        old_value=2800.0,
        new_value=3000.0,
        revision=7,
        metadata={"simulation_time_s": 12.0, "units": "rpm"},
    )
    payload = record.to_dict()
    assert list(payload) == [
        "timestamp", "event_type", "source", "target", "action",
        "old_value", "new_value", "revision", "metadata",
    ]
    assert EventRecord.from_dict(payload).to_dict() == payload


def test_event_stream_is_append_only_and_serializes_json_lines():
    stream = EventStream()
    first = stream.emit(event_type="system.lifecycle", source="system", target="workspace", action="initialized")
    second = stream.emit(event_type="control.changed", source="learner", target="ecmo_console", action="set_pump_running", old_value=False, new_value=True)
    assert stream.records == (first, second)
    assert stream.latest is second
    lines = stream.to_json_lines().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[1])["new_value"] is True


def test_event_stream_rejects_non_serializable_payloads():
    stream = EventStream()
    with pytest.raises(TypeError):
        stream.emit(event_type="bad", source="test", target="test", action="bad", metadata={"x": object()})
