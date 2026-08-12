from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional, Set

from neoevents import EventRecord, EventStream

from .actions import ActionExecutor
from .mechanisms import MechanismRegistry
from .models import ScenarioDefinition, ScenarioStatus
from .observations import FrozenObservation, ObservationRegistry
from .rng import ScenarioRng
from .triggers import trigger_matches
from .validation import validate_scenario_definition


@dataclass
class ScenarioRuntimeState:
    status: ScenarioStatus = ScenarioStatus.CREATED
    simulation_time_s: float = 0.0
    fired_steps: Set[str] = field(default_factory=set)
    eligible_steps: Set[str] = field(default_factory=set)
    active_steps: Set[str] = field(default_factory=set)
    resolved_steps: Set[str] = field(default_factory=set)
    action_counts: dict[str, int] = field(default_factory=dict)
    last_release_time_s: float | None = None


class ScenarioEngine:
    """Deterministic scenario director over registered simulator mechanisms.

    Eligibility and release are distinct.  The engine owns orchestration only;
    every simulator mutation crosses the MechanismRegistry boundary.
    """

    def __init__(self, definition: ScenarioDefinition, *, seed: int, mechanisms: MechanismRegistry,
                 events: Optional[EventStream] = None, context: Optional[Mapping[str, object]] = None,
                 observations: Optional[ObservationRegistry] = None) -> None:
        self.definition = definition
        self.seed = int(seed)
        self.rng = ScenarioRng(self.seed)
        self.mechanisms = mechanisms
        self.events = events or EventStream()
        self.actions = ActionExecutor(mechanisms, self.events)
        self.observations = observations
        self.observation_results: list[FrozenObservation] = []
        self.state = ScenarioRuntimeState()
        self.context = dict(context or {})
        self._learner_actions = {a.action_id: a for a in definition.learner_actions}
        self._learner_observations = {o.observation_id: o for o in definition.learner_observations}
        self._steps = {s.step_id: s for s in definition.steps}
        self._event_start_index = len(self.events.records)

    @property
    def validation_issues(self):
        return validate_scenario_definition(self.definition, self.mechanisms, self.observations)

    def start(self) -> None:
        if self.state.status != ScenarioStatus.CREATED:
            raise RuntimeError("scenario can only be started once")
        self.state.status = ScenarioStatus.RUNNING
        self._event_start_index = len(self.events.records)
        self.events.emit(event_type="scenario.started", source="scenario-engine", target=self.definition.scenario_id,
                         action="start", metadata={"scenario_id": self.definition.scenario_id,
                         "scenario_version": self.definition.version, "seed": self.seed, "simulation_time_s": 0.0})
        self._evaluate()

    def advance_to(self, simulation_time_s: float) -> None:
        self._require_running()
        new_time = float(simulation_time_s)
        if new_time < self.state.simulation_time_s:
            raise ValueError("scenario simulation time cannot move backward")
        self.state.simulation_time_s = new_time
        self._evaluate()

    def perform_learner_action(self, action_id: str) -> None:
        self._require_running()
        try:
            definition = self._learner_actions[action_id]
        except KeyError as exc:
            raise KeyError(f"unknown learner action: {action_id}") from exc
        self.actions.execute(definition, scenario_id=self.definition.scenario_id,
                             simulation_time_s=self.state.simulation_time_s, source="learner")
        self.state.action_counts[action_id] = self.state.action_counts.get(action_id, 0) + 1
        self._evaluate()

    def perform_learner_observation(self, observation_id: str) -> FrozenObservation:
        self._require_running()
        if self.observations is None:
            raise RuntimeError("scenario has no observation registry")
        try:
            definition = self._learner_observations[observation_id]
        except KeyError as exc:
            raise KeyError(f"unknown learner observation: {observation_id}") from exc
        self.events.emit(
            event_type="scenario.observation_requested", source="learner", target=definition.provider_id,
            action=definition.observation_id, metadata={"scenario_id": self.definition.scenario_id,
            "simulation_time_s": self.state.simulation_time_s},
        )
        sampled = self.observations.sample(
            definition.provider_id, simulation_time_s=self.state.simulation_time_s, parameters=definition.parameters
        )
        available_time_s = self.state.simulation_time_s + definition.turnaround_s
        observation = FrozenObservation(
            observation_id=definition.observation_id, sample_time_s=sampled.sample_time_s,
            available_time_s=available_time_s, values=sampled.values,
            metadata={**dict(sampled.metadata), "provider_id": definition.provider_id,
                      "scenario_id": self.definition.scenario_id},
        )
        self.observation_results.append(observation)
        self.events.emit(
            event_type="scenario.observation_sampled", source="scenario-engine", target=definition.provider_id,
            action=definition.observation_id, new_value=dict(observation.values),
            metadata={"scenario_id": self.definition.scenario_id, "simulation_time_s": self.state.simulation_time_s,
                      "sample_time_s": observation.sample_time_s, "available_time_s": observation.available_time_s},
        )
        return observation

    def available_observations(self) -> tuple[FrozenObservation, ...]:
        return tuple(o for o in self.observation_results if o.is_available(self.state.simulation_time_s))

    def fire_step(self, step_id: str, *, source: str = "educator") -> None:
        self._require_running()
        step = self._steps.get(step_id)
        if step is None:
            raise KeyError(f"unknown scenario step: {step_id}")
        self.state.eligible_steps.add(step_id)
        self._release_eligible(source=source, force_step=step_id)

    def complete(self) -> None:
        self._require_running()
        self.state.status = ScenarioStatus.COMPLETED
        self.events.emit(event_type="scenario.completed", source="scenario-engine", target=self.definition.scenario_id,
                         action="complete", metadata={"scenario_id": self.definition.scenario_id,
                         "simulation_time_s": self.state.simulation_time_s})

    def snapshot(self) -> dict:
        return {
            "scenario_id": self.definition.scenario_id, "version": self.definition.version, "seed": self.seed,
            "state": {"status": self.state.status.value, "simulation_time_s": self.state.simulation_time_s,
                      "fired_steps": sorted(self.state.fired_steps), "eligible_steps": sorted(self.state.eligible_steps),
                      "active_steps": sorted(self.state.active_steps), "resolved_steps": sorted(self.state.resolved_steps),
                      "action_counts": dict(self.state.action_counts), "last_release_time_s": self.state.last_release_time_s},
            "rng": self.rng.snapshot(), "event_start_index": self._event_start_index,
            "observations": [o.to_dict() for o in self.observation_results],
        }

    def restore(self, payload: Mapping[str, object]) -> None:
        if payload.get("scenario_id") != self.definition.scenario_id or payload.get("version") != self.definition.version:
            raise ValueError("scenario snapshot does not match definition")
        raw = dict(payload["state"])
        self.state = ScenarioRuntimeState(
            status=ScenarioStatus(str(raw["status"])), simulation_time_s=float(raw["simulation_time_s"]),
            fired_steps=set(raw.get("fired_steps", ())), eligible_steps=set(raw.get("eligible_steps", ())),
            active_steps=set(raw.get("active_steps", ())), resolved_steps=set(raw.get("resolved_steps", ())),
            action_counts={str(k): int(v) for k, v in dict(raw.get("action_counts", {})).items()},
            last_release_time_s=None if raw.get("last_release_time_s") is None else float(raw["last_release_time_s"]),
        )
        self.rng.restore(dict(payload["rng"]))
        self.observation_results = [FrozenObservation.from_dict(o) for o in payload.get("observations", [])]
        self._event_start_index = int(payload.get("event_start_index", len(self.events.records)))

    def _require_running(self) -> None:
        if self.state.status != ScenarioStatus.RUNNING:
            raise RuntimeError("scenario is not running")

    def _records(self) -> tuple[EventRecord, ...]:
        return self.events.records[self._event_start_index:]

    def _matches(self, trigger) -> bool:
        return trigger_matches(trigger, simulation_time_s=self.state.simulation_time_s, records=self._records(),
                               action_counts=self.state.action_counts, context=self.context)

    def _evaluate(self) -> None:
        # Resolve released steps first, then evaluate new eligibility, then release
        # according to director policy. Repeat because released actions can emit
        # events that make later steps eligible.
        for _ in range(max(4, len(self.definition.steps) * 3 + 1)):
            changed = False
            for step_id in tuple(self.state.active_steps):
                step = self._steps[step_id]
                if step.resolution_trigger is not None and self._matches(step.resolution_trigger):
                    self.state.active_steps.remove(step_id)
                    self.state.resolved_steps.add(step_id)
                    self.events.emit(event_type="scenario.step_resolved", source="scenario-engine",
                                     target=self.definition.scenario_id, action=step_id,
                                     metadata={"scenario_id": self.definition.scenario_id,
                                               "simulation_time_s": self.state.simulation_time_s})
                    changed = True
            for step in self.definition.steps:
                if step.step_id in self.state.fired_steps or step.step_id in self.state.eligible_steps:
                    continue
                if step.trigger.kind == "manual":
                    continue
                if self._matches(step.trigger):
                    self.state.eligible_steps.add(step.step_id)
                    self.events.emit(event_type="scenario.step_eligible", source="scenario-engine",
                                     target=self.definition.scenario_id, action=step.step_id,
                                     metadata={"scenario_id": self.definition.scenario_id,
                                               "simulation_time_s": self.state.simulation_time_s,
                                               "priority": step.priority})
                    changed = True
            if self._release_eligible(source="scenario-engine"):
                changed = True
            if not changed:
                return
        raise RuntimeError("scenario evaluation failed to converge")

    def _release_eligible(self, *, source: str, force_step: str | None = None) -> bool:
        policy = self.definition.director_policy
        if len(self.state.active_steps) >= policy.max_concurrent_unresolved:
            return False
        if self.state.last_release_time_s is not None and not force_step:
            if self.state.simulation_time_s - self.state.last_release_time_s < policy.min_release_spacing_s:
                return False
        candidates = [self._steps[sid] for sid in self.state.eligible_steps]
        if force_step:
            candidates = [s for s in candidates if s.step_id == force_step]
        if not candidates:
            return False
        step = sorted(candidates, key=lambda s: (s.priority, s.step_id))[0]
        self.state.eligible_steps.discard(step.step_id)
        self._fire_step(step, source=source)
        return True

    def _fire_step(self, step, *, source: str) -> None:
        if step.once and step.step_id in self.state.fired_steps:
            return
        self.events.emit(event_type="scenario.step_released", source=source, target=self.definition.scenario_id,
                         action=step.step_id, metadata={"scenario_id": self.definition.scenario_id,
                         "simulation_time_s": self.state.simulation_time_s})
        for fault in step.faults:
            self.events.emit(event_type="scenario.fault_requested", source=source, target=fault.fault_id,
                             action="activate", metadata={"scenario_id": self.definition.scenario_id,
                             "legacy_id": fault.legacy_id, "fault_id": fault.fault_id,
                             "simulation_time_s": self.state.simulation_time_s})
            self.actions.execute(fault.activation_action, scenario_id=self.definition.scenario_id,
                                 simulation_time_s=self.state.simulation_time_s, source="scenario-engine")
        for action in step.actions:
            self.actions.execute(action, scenario_id=self.definition.scenario_id,
                                 simulation_time_s=self.state.simulation_time_s, source="scenario-engine")
        if step.once:
            self.state.fired_steps.add(step.step_id)
        if step.resolution_trigger is not None:
            self.state.active_steps.add(step.step_id)
        else:
            self.state.resolved_steps.add(step.step_id)
        self.state.last_release_time_s = self.state.simulation_time_s
