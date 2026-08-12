from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Tuple

from neoevents import EventRecord


_DEFAULT_HIDDEN_METADATA = frozenset({
    "complication_id", "fault_id", "hidden_state", "score", "score_delta",
    "rationale", "educator_setup", "knowledge_plan", "trigger_policy",
    "scenario_id", "scenario_version", "mechanism_id",
})
_DEFAULT_INTERNAL_EVENT_TYPES = frozenset({
    "scenario.step_eligible", "scenario.step_released", "scenario.state_transition",
    "scenario.trigger_fired", "scenario.fault_requested", "scenario.started",
    "scenario.completed", "scenario.step_resolved",
})


@dataclass(frozen=True)
class DisclosurePolicy:
    hidden_metadata_keys: frozenset[str] = field(default_factory=lambda: _DEFAULT_HIDDEN_METADATA)
    learner_hidden_event_types: frozenset[str] = field(default_factory=lambda: _DEFAULT_INTERNAL_EVENT_TYPES)
    # Learner views describe bedside provenance, not internal software actors.
    # Preserve the durable instructor/debrief source unchanged and normalize only
    # the projected learner view.
    learner_source_aliases: Mapping[str, str] = field(default_factory=lambda: {"scenario-engine": "system"})


def _sanitize_mapping(value, hidden: frozenset[str]):
    if isinstance(value, Mapping):
        return {str(k): _sanitize_mapping(v, hidden) for k, v in value.items() if str(k) not in hidden}
    if isinstance(value, tuple):
        return [_sanitize_mapping(v, hidden) for v in value]
    return value


def learner_event_view(records: Iterable[EventRecord], policy: DisclosurePolicy = DisclosurePolicy()) -> Tuple[dict, ...]:
    visible = []
    for record in records:
        if record.event_type in policy.learner_hidden_event_types:
            continue
        # Scenario-engine mutation events describe hidden setup/fault mechanics.
        # Learner-originated actions remain visible; engine-originated mechanism
        # calls do not, because they can reveal the diagnosis directly.
        if record.source == "scenario-engine" and record.event_type in {
            "scenario.action_requested", "scenario.action_applied", "scenario.action_unavailable"
        }:
            continue
        payload = record.to_dict()
        payload["source"] = policy.learner_source_aliases.get(payload["source"], payload["source"])
        payload["metadata"] = _sanitize_mapping(payload.get("metadata", {}), policy.hidden_metadata_keys)
        payload["old_value"] = _sanitize_mapping(payload.get("old_value"), policy.hidden_metadata_keys)
        payload["new_value"] = _sanitize_mapping(payload.get("new_value"), policy.hidden_metadata_keys)
        visible.append(payload)
    return tuple(visible)


def instructor_event_view(records: Iterable[EventRecord]) -> Tuple[dict, ...]:
    return tuple(record.to_dict() for record in records)
