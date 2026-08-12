from __future__ import annotations

from typing import Iterable

from neoevents import EventRecord

from .models import TriggerDefinition


def _event_matches(record: EventRecord, parameters) -> bool:
    for field in ("event_type", "source", "target", "action"):
        expected = parameters.get(field)
        if expected is not None and getattr(record, field) != expected:
            return False
    metadata = parameters.get("metadata")
    if metadata:
        for key, expected in dict(metadata).items():
            if record.metadata.get(key) != expected:
                return False
    return True


def trigger_matches(
    trigger: TriggerDefinition,
    *,
    simulation_time_s: float,
    records: Iterable[EventRecord],
    time_in_state_s: float | None = None,
    action_counts: dict[str, int] | None = None,
    context: dict[str, object] | None = None,
) -> bool:
    if trigger.kind == "manual":
        return False
    if trigger.kind == "at_start":
        return float(simulation_time_s) <= 0.0
    if trigger.kind == "time_in_state":
        if time_in_state_s is None:
            return False
        return float(time_in_state_s) >= float(trigger.parameters["at_s"])
    if trigger.kind == "time_window":
        start = float(trigger.parameters.get("start_s", 0.0))
        end = float(trigger.parameters["end_s"])
        return start <= float(simulation_time_s) <= end
    if trigger.kind == "action_count":
        if action_counts is None:
            return False
        action_id = str(trigger.parameters["action_id"])
        minimum = int(trigger.parameters.get("at_least", 1))
        return int(action_counts.get(action_id, 0)) >= minimum
    if trigger.kind == "context":
        if context is None:
            return False
        return all(context.get(str(k)) == v for k, v in trigger.parameters.items())
    if trigger.kind == "elapsed_time":
        return float(simulation_time_s) >= float(trigger.parameters["at_s"])
    if trigger.kind == "event":
        return any(_event_matches(record, trigger.parameters) for record in records)
    if trigger.kind == "all":
        return all(trigger_matches(child, simulation_time_s=simulation_time_s, records=records, time_in_state_s=time_in_state_s, action_counts=action_counts, context=context) for child in trigger.children)
    if trigger.kind == "any":
        return any(trigger_matches(child, simulation_time_s=simulation_time_s, records=records, time_in_state_s=time_in_state_s, action_counts=action_counts, context=context) for child in trigger.children)
    raise ValueError(f"unsupported trigger kind: {trigger.kind}")
