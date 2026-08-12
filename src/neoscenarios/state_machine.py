from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Tuple

from neoevents import EventRecord

from .models import TriggerDefinition
from .triggers import trigger_matches


@dataclass(frozen=True)
class EventTransitionDefinition:
    transition_id: str
    from_state: str
    to_state: str
    trigger: TriggerDefinition


@dataclass(frozen=True)
class EventMachineDefinition:
    event_id: str
    initial_state: str
    transitions: Tuple[EventTransitionDefinition, ...] = ()
    hidden_metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "transitions", tuple(self.transitions))
        object.__setattr__(self, "hidden_metadata", MappingProxyType(dict(self.hidden_metadata)))


@dataclass
class EventMachineRuntime:
    definition: EventMachineDefinition
    state: str
    entered_at_s: float

    @classmethod
    def start(cls, definition: EventMachineDefinition, simulation_time_s: float) -> "EventMachineRuntime":
        return cls(definition=definition, state=definition.initial_state, entered_at_s=float(simulation_time_s))

    @property
    def time_in_state_s(self) -> float:
        return self._last_time_s - self.entered_at_s if hasattr(self, "_last_time_s") else 0.0

    def evaluate(self, simulation_time_s: float, records: Tuple[EventRecord, ...]) -> EventTransitionDefinition | None:
        now = float(simulation_time_s)
        self._last_time_s = now
        for transition in self.definition.transitions:
            if transition.from_state != self.state:
                continue
            if trigger_matches(
                transition.trigger,
                simulation_time_s=now,
                records=records,
                time_in_state_s=now - self.entered_at_s,
            ):
                self.state = transition.to_state
                self.entered_at_s = now
                return transition
        return None

    def snapshot(self) -> dict:
        return {"event_id": self.definition.event_id, "state": self.state, "entered_at_s": self.entered_at_s}

    def restore(self, payload: Mapping[str, object]) -> None:
        if payload.get("event_id") != self.definition.event_id:
            raise ValueError("event machine snapshot does not match definition")
        self.state = str(payload["state"])
        self.entered_at_s = float(payload["entered_at_s"])
