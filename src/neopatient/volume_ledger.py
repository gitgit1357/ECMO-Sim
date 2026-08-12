from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VolumeLedgerConfig:
    """Reduced-order patient volume settings.

    Defaults preserve the existing 3.5-kg baseline (about 301 mL) while
    allowing weight-based initialization and scenario-specific overrides.
    """

    blood_volume_ml_per_kg: float = 86.0
    minimum_intravascular_fraction: float = 0.35
    default_input_intravascular_fraction: float = 0.25
    third_space_effect_on_venous_availability: float = 1.0

    def baseline_blood_volume_ml(self, weight_kg: float) -> float:
        if weight_kg <= 0.0:
            raise ValueError("weight_kg must be greater than zero")
        if self.blood_volume_ml_per_kg <= 0.0:
            raise ValueError("blood_volume_ml_per_kg must be greater than zero")
        return weight_kg * self.blood_volume_ml_per_kg


@dataclass
class VolumeLedgerState:
    cumulative_input_ml: float = 0.0
    cumulative_urine_ml: float = 0.0
    cumulative_ckrt_removal_ml: float = 0.0
    cumulative_blood_loss_ml: float = 0.0
    cumulative_sampling_loss_ml: float = 0.0
    third_space_volume_ml: float = 0.0
    intravascular_delta_ml: float = 0.0


@dataclass(frozen=True)
class VolumeLedgerSnapshot:
    baseline_blood_volume_ml: float
    current_intravascular_volume_ml: float
    blood_volume_fraction: float
    effective_venous_volume_ml: float
    effective_venous_volume_fraction: float
    cumulative_input_ml: float
    cumulative_urine_ml: float
    cumulative_ckrt_removal_ml: float
    cumulative_blood_loss_ml: float
    cumulative_sampling_loss_ml: float
    third_space_volume_ml: float


def snapshot_volume_ledger(
    *,
    weight_kg: float,
    config: VolumeLedgerConfig,
    state: VolumeLedgerState,
) -> VolumeLedgerSnapshot:
    baseline = config.baseline_blood_volume_ml(weight_kg)
    minimum = baseline * config.minimum_intravascular_fraction
    current = max(minimum, baseline + state.intravascular_delta_ml)
    effective = max(
        minimum,
        current - state.third_space_volume_ml * config.third_space_effect_on_venous_availability,
    )
    return VolumeLedgerSnapshot(
        baseline_blood_volume_ml=baseline,
        current_intravascular_volume_ml=current,
        blood_volume_fraction=current / baseline,
        effective_venous_volume_ml=effective,
        effective_venous_volume_fraction=effective / baseline,
        cumulative_input_ml=state.cumulative_input_ml,
        cumulative_urine_ml=state.cumulative_urine_ml,
        cumulative_ckrt_removal_ml=state.cumulative_ckrt_removal_ml,
        cumulative_blood_loss_ml=state.cumulative_blood_loss_ml,
        cumulative_sampling_loss_ml=state.cumulative_sampling_loss_ml,
        third_space_volume_ml=state.third_space_volume_ml,
    )
