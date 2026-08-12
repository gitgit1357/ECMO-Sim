from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze_value(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_value(v) for v in value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"scenario definition value is not JSON-compatible data: {type(value).__name__}")


def _freeze_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    frozen = _freeze_value(dict(value or {}))
    assert isinstance(frozen, Mapping)
    return frozen


class ScenarioStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    STOPPED = "stopped"


class MechanismAvailability(str, Enum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    NOT_IMPLEMENTED = "not_implemented"


@dataclass(frozen=True)
class MechanismDescriptor:
    mechanism_id: str
    availability: MechanismAvailability
    description: str = ""
    capability_ref: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.mechanism_id.strip():
            raise ValueError("mechanism_id must be non-empty")


@dataclass(frozen=True)
class ActionDefinition:
    action_id: str
    mechanism_id: str
    parameters: Mapping[str, Any] = field(default_factory=dict)
    label: str = ""

    def __post_init__(self) -> None:
        if not self.action_id.strip() or not self.mechanism_id.strip():
            raise ValueError("action_id and mechanism_id must be non-empty")
        object.__setattr__(self, "parameters", _freeze_mapping(self.parameters))




@dataclass(frozen=True)
class ObservationDefinition:
    observation_id: str
    provider_id: str
    parameters: Mapping[str, Any] = field(default_factory=dict)
    label: str = ""
    turnaround_s: float = 0.0

    def __post_init__(self) -> None:
        if not self.observation_id.strip() or not self.provider_id.strip():
            raise ValueError("observation_id and provider_id must be non-empty")
        if self.turnaround_s < 0:
            raise ValueError("turnaround_s cannot be negative")
        object.__setattr__(self, "parameters", _freeze_mapping(self.parameters))
        object.__setattr__(self, "turnaround_s", float(self.turnaround_s))


@dataclass(frozen=True)
class FaultDefinition:
    fault_id: str
    activation_action: ActionDefinition
    label: str = ""
    legacy_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.fault_id.strip():
            raise ValueError("fault_id must be non-empty")


@dataclass(frozen=True)
class TriggerDefinition:
    """Serializable trigger primitive.

    Supported kinds in Phase 1e:
    - ``elapsed_time``: simulation time >= ``at_s``
    - ``event``: event stream contains a matching event; optional field filters
    - ``manual``: never auto-fires; educator/host calls ``fire_step`` explicitly
    - ``all`` / ``any``: composition of child triggers
    """

    kind: str
    parameters: Mapping[str, Any] = field(default_factory=dict)
    children: Tuple["TriggerDefinition", ...] = ()

    def __post_init__(self) -> None:
        if self.kind not in {"at_start", "elapsed_time", "time_in_state", "time_window", "event", "action_count", "context", "manual", "all", "any"}:
            raise ValueError(f"unsupported trigger kind: {self.kind}")
        object.__setattr__(self, "parameters", _freeze_mapping(self.parameters))
        object.__setattr__(self, "children", tuple(self.children))
        if self.kind in {"all", "any"} and not self.children:
            raise ValueError(f"{self.kind} trigger requires children")


@dataclass(frozen=True)
class ScenarioStepDefinition:
    step_id: str
    trigger: TriggerDefinition
    actions: Tuple[ActionDefinition, ...] = ()
    faults: Tuple[FaultDefinition, ...] = ()
    once: bool = True
    priority: int = 100
    resolution_trigger: TriggerDefinition | None = None

    def __post_init__(self) -> None:
        if not self.step_id.strip():
            raise ValueError("step_id must be non-empty")
        if not self.once and self.trigger.kind != "manual":
            raise ValueError("Phase 1e repeatable steps must use a manual trigger")
        object.__setattr__(self, "actions", tuple(self.actions))
        object.__setattr__(self, "faults", tuple(self.faults))
        object.__setattr__(self, "priority", int(self.priority))




@dataclass(frozen=True)
class ScenarioDirectorPolicy:
    max_concurrent_unresolved: int = 1
    min_release_spacing_s: float = 0.0

    def __post_init__(self) -> None:
        if self.max_concurrent_unresolved < 1:
            raise ValueError("max_concurrent_unresolved must be >= 1")
        if self.min_release_spacing_s < 0:
            raise ValueError("min_release_spacing_s must be >= 0")


@dataclass(frozen=True)
class ScenarioDefinition:
    scenario_id: str
    version: str
    title: str
    steps: Tuple[ScenarioStepDefinition, ...] = ()
    learner_actions: Tuple[ActionDefinition, ...] = ()
    learner_observations: Tuple[ObservationDefinition, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    legacy_id: Optional[str] = None
    director_policy: ScenarioDirectorPolicy = field(default_factory=ScenarioDirectorPolicy)

    def __post_init__(self) -> None:
        if not self.scenario_id.strip() or not self.version.strip() or not self.title.strip():
            raise ValueError("scenario_id, version, and title must be non-empty")
        object.__setattr__(self, "steps", tuple(self.steps))
        object.__setattr__(self, "learner_actions", tuple(self.learner_actions))
        object.__setattr__(self, "learner_observations", tuple(self.learner_observations))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))
        ids = [step.step_id for step in self.steps]
        if len(ids) != len(set(ids)):
            raise ValueError("scenario step IDs must be unique")
        action_ids = [action.action_id for action in self.learner_actions]
        if len(action_ids) != len(set(action_ids)):
            raise ValueError("learner action IDs must be unique")
        observation_ids = [obs.observation_id for obs in self.learner_observations]
        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError("learner observation IDs must be unique")


@dataclass(frozen=True)
class MechanismInvocation:
    mechanism_id: str
    parameters: Mapping[str, Any]
    source: str
    action_id: str
    scenario_id: str
    simulation_time_s: float


@dataclass(frozen=True)
class MechanismResult:
    applied: bool = True
    old_value: Any = None
    new_value: Any = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))
