from __future__ import annotations

from dataclasses import dataclass

from ..faults import build_supported_fault_catalog
from ..models import (
    ActionDefinition,
    FaultDefinition,
    ObservationDefinition,
    ScenarioDefinition,
    ScenarioDirectorPolicy,
    ScenarioStepDefinition,
    TriggerDefinition,
)


@dataclass(frozen=True)
class PreloadLowFlowScenarioConfig:
    blood_loss_ml: float
    replacement_ml: float
    onset_s: float = 0.0
    observation_turnaround_s: float = 0.0

    def __post_init__(self) -> None:
        if self.blood_loss_ml <= 0 or self.replacement_ml <= 0:
            raise ValueError("blood_loss_ml and replacement_ml must be > 0")
        if self.onset_s < 0 or self.observation_turnaround_s < 0:
            raise ValueError("scenario times cannot be negative")


def build_lowflow_hypovolemia_scenario(config: PreloadLowFlowScenarioConfig) -> ScenarioDefinition:
    """First production-structured scenario family member.

    The orchestration and mechanism mapping are production-shaped; the supplied
    blood-loss/replacement magnitudes remain caller-owned clinical content and
    are not declared validated by this factory.
    """
    trigger = TriggerDefinition("at_start") if config.onset_s == 0 else TriggerDefinition(
        "elapsed_time", {"at_s": config.onset_s}
    )
    replacement = ActionDefinition(
        "volume-bolus", "patient.add_intravascular_input",
        {"volume_ml": config.replacement_ml, "intravascular_fraction": 1.0},
        label="Administer intravascular volume",
    )
    return ScenarioDefinition(
        scenario_id="lowflow-hypovolemia",
        legacy_id="lf-01-preload",
        version="1.0.0",
        title="Low flow: preload limitation / hypovolemia",
        learner_actions=(replacement,),
        learner_observations=(
            ObservationDefinition("assess-hemodynamics", "assess-hemodynamics", label="Assess hemodynamic pattern"),
            ObservationDefinition("assess-pump-function", "assess-pump-function", label="Assess pump and actual output"),
            ObservationDefinition("assess-gas-exchange", "assess-gas-exchange", label="Assess gas exchange"),
            ObservationDefinition("assess-renal-fluid", "assess-renal-fluid", label="Assess renal/fluid status"),
        ),
        steps=(
            ScenarioStepDefinition(
                step_id="activate-preload-loss",
                trigger=trigger,
                faults=(build_supported_fault_catalog().build(
                    "hypovolemia", volume_ml=config.blood_loss_ml
                ),),
                resolution_trigger=TriggerDefinition(
                    "event", {"event_type": "scenario.action_applied", "source": "learner", "action": "volume-bolus"}
                ),
            ),
        ),
        director_policy=ScenarioDirectorPolicy(max_concurrent_unresolved=1),
        metadata={
            "scenario_family": "low-flow",
            "mechanism_family": "preload-volume",
            "clinical_validation_status": "behavior-contract-pending",
            "timing_status": "author-supplied-not-validated-by-engine",
            "diagnosis_hidden_from_learner": True,
        },
    )
