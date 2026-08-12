from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .mechanisms import MechanismRegistry
from .models import MechanismAvailability, ScenarioDefinition
from .observations import ObservationRegistry


@dataclass(frozen=True)
class ScenarioValidationIssue:
    code: str
    reference_id: str
    mechanism_id: str
    message: str


def validate_scenario_definition(
    definition: ScenarioDefinition,
    registry: MechanismRegistry,
    observations: ObservationRegistry | None = None,
) -> Tuple[ScenarioValidationIssue, ...]:
    """Check a scenario against the current mechanism capability surface.

    This is deliberately not clinical validation. It only answers whether the
    definition asks the runtime to invoke mechanisms that are actually
    registered and available today.
    """

    issues: list[ScenarioValidationIssue] = []

    def check(reference_id: str, mechanism_id: str) -> None:
        descriptor = registry.descriptor(mechanism_id)
        if descriptor is None:
            issues.append(ScenarioValidationIssue(
                code="mechanism_unregistered",
                reference_id=reference_id,
                mechanism_id=mechanism_id,
                message=f"{reference_id} requires unregistered mechanism {mechanism_id}",
            ))
            return
        if descriptor.availability != MechanismAvailability.AVAILABLE:
            issues.append(ScenarioValidationIssue(
                code=f"mechanism_{descriptor.availability.value}",
                reference_id=reference_id,
                mechanism_id=mechanism_id,
                message=(
                    f"{reference_id} requires mechanism {mechanism_id}, currently "
                    f"{descriptor.availability.value}"
                ),
            ))

    for observation in definition.learner_observations:
        if observations is None or observations.descriptor(observation.provider_id) is None:
            issues.append(ScenarioValidationIssue(
                code="observation_unregistered", reference_id=f"learner_observation:{observation.observation_id}",
                mechanism_id=observation.provider_id,
                message=f"learner_observation:{observation.observation_id} requires unregistered observation provider {observation.provider_id}",
            ))

    for action in definition.learner_actions:
        check(f"learner_action:{action.action_id}", action.mechanism_id)
    for step in definition.steps:
        for action in step.actions:
            check(f"step:{step.step_id}/action:{action.action_id}", action.mechanism_id)
        for fault in step.faults:
            check(f"step:{step.step_id}/fault:{fault.fault_id}", fault.activation_action.mechanism_id)

    return tuple(issues)
