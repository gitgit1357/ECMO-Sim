from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Iterable, Mapping, Tuple

from neoevents import EventRecord
from neoscenarios import learner_event_view


@dataclass(frozen=True)
class ScenarioLogEntry:
    """Learner-safe, read-only projection of one canonical event record."""

    simulation_time_s: float | None
    event_type: str
    source: str
    target: str
    action: str
    detail: str

    @property
    def simulation_time_text(self) -> str:
        if self.simulation_time_s is None:
            return "--:--"
        total_seconds = max(0, int(round(self.simulation_time_s)))
        return f"{total_seconds // 60:02d}:{total_seconds % 60:02d}"


def _compact(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, Mapping):
        if not value:
            return ""
        return json.dumps(dict(value), sort_keys=True, separators=(",", ":"))
    if isinstance(value, list):
        return json.dumps(value, separators=(",", ":"))
    return str(value)


def _detail(payload: Mapping[str, object]) -> str:
    old_value = payload.get("old_value")
    new_value = payload.get("new_value")
    if old_value is not None and new_value is not None:
        return f"{_compact(old_value)} → {_compact(new_value)}"
    if new_value is not None:
        return _compact(new_value)
    if old_value is not None:
        return _compact(old_value)
    return ""


def scenario_log_entries(records: Iterable[EventRecord]) -> Tuple[ScenarioLogEntry, ...]:
    """Project canonical events into the learner-visible Scenario Log timeline.

    Disclosure is delegated to the Tier-A learner projection so the GUI cannot
    accidentally bypass diagnosis/internal-engine sanitization.  The function
    does not mutate or copy back into the authoritative EventStream.
    """

    entries: list[ScenarioLogEntry] = []
    for payload in learner_event_view(records):
        metadata = payload.get("metadata", {})
        simulation_time_s = None
        if isinstance(metadata, Mapping) and metadata.get("simulation_time_s") is not None:
            simulation_time_s = float(metadata["simulation_time_s"])
        entries.append(
            ScenarioLogEntry(
                simulation_time_s=simulation_time_s,
                event_type=str(payload["event_type"]),
                source=str(payload["source"]),
                target=str(payload["target"]),
                action=str(payload["action"]),
                detail=_detail(payload),
            )
        )
    return tuple(entries)


def debrief_entries(records: Iterable[EventRecord]) -> Tuple[ScenarioLogEntry, ...]:
    """Phase-7 read-only debrief projection.

    This intentionally reuses the learner-safe Scenario Log projection.  A
    debrief entry is evidence of what the event stream recorded; it does not
    score, diagnose, interpret, mutate, or reconstruct historical physiology.
    """

    return scenario_log_entries(records)
