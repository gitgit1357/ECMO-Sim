from __future__ import annotations

from neoevents import EventStream

from .mechanisms import MechanismNotAvailableError, MechanismRegistry
from .models import ActionDefinition, MechanismInvocation, MechanismResult


class ActionExecutor:
    def __init__(self, registry: MechanismRegistry, events: EventStream) -> None:
        self.registry = registry
        self.events = events

    def execute(
        self,
        definition: ActionDefinition,
        *,
        scenario_id: str,
        simulation_time_s: float,
        source: str,
    ) -> MechanismResult:
        invocation = MechanismInvocation(
            mechanism_id=definition.mechanism_id,
            parameters=definition.parameters,
            source=source,
            action_id=definition.action_id,
            scenario_id=scenario_id,
            simulation_time_s=float(simulation_time_s),
        )
        common_metadata = {
            "scenario_id": scenario_id,
            "simulation_time_s": float(simulation_time_s),
            "mechanism_id": definition.mechanism_id,
        }
        self.events.emit(
            event_type="scenario.action_requested",
            source=source,
            target=definition.mechanism_id,
            action=definition.action_id,
            new_value=dict(definition.parameters),
            metadata=common_metadata,
        )
        try:
            result = self.registry.invoke(invocation)
        except MechanismNotAvailableError as exc:
            self.events.emit(
                event_type="scenario.action_unavailable",
                source=source,
                target=definition.mechanism_id,
                action=definition.action_id,
                metadata={**common_metadata, "reason": str(exc)},
            )
            raise
        self.events.emit(
            event_type="scenario.action_applied",
            source=source,
            target=definition.mechanism_id,
            action=definition.action_id,
            old_value=result.old_value,
            new_value=result.new_value,
            metadata={**common_metadata, **dict(result.metadata)},
        )
        return result
