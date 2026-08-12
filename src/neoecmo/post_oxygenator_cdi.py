from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Optional


@dataclass(frozen=True)
class PostOxygenatorBloodState:
    """True blood state immediately after the oxygenator and before patient mixing.

    This is circuit-owned truth. It is not the patient's arterial blood gas and it
    is not itself a sensor reading.
    """

    po2_mmhg: float
    pco2_mmhg: float
    oxygen_saturation: float
    hematocrit_pct: float
    hemoglobin_g_dl: float
    temperature_c: float

    def validate(self) -> None:
        for name, value in self.__dict__.items():
            if not math.isfinite(float(value)):
                raise ValueError(f"{name} must be finite")
        if self.po2_mmhg < 0.0 or self.pco2_mmhg < 0.0:
            raise ValueError("blood-gas partial pressures cannot be negative")
        if not 0.0 <= self.oxygen_saturation <= 1.0:
            raise ValueError("oxygen_saturation must be between 0 and 1")
        if not 0.0 <= self.hematocrit_pct <= 100.0:
            raise ValueError("hematocrit_pct must be between 0 and 100")
        if self.hemoglobin_g_dl < 0.0:
            raise ValueError("hemoglobin_g_dl cannot be negative")


@dataclass(frozen=True)
class PostOxyCdiReading:
    """Displayed post-oxygenator CDI values.

    The sensor layer can later add lag, offset, freeze and invalid-signal behavior
    without changing oxygenator truth or patient arterial mixing.
    """

    valid: bool
    po2_mmhg: Optional[float]
    pco2_mmhg: Optional[float]
    oxygen_saturation: Optional[float]
    hematocrit_pct: Optional[float]
    hemoglobin_g_dl: Optional[float]
    temperature_c: Optional[float]
    status: str = "VALID"


@dataclass(frozen=True)
class PostOxyCdiSensorState:
    valid: bool = True
    po2_offset_mmhg: float = 0.0
    pco2_offset_mmhg: float = 0.0
    saturation_offset: float = 0.0
    hematocrit_offset_pct: float = 0.0
    temperature_offset_c: float = 0.0
    frozen_reading: Optional[PostOxyCdiReading] = None


def measure_post_oxygenator_blood(
    blood: PostOxygenatorBloodState,
    sensor: PostOxyCdiSensorState = PostOxyCdiSensorState(),
) -> PostOxyCdiReading:
    blood.validate()
    if sensor.frozen_reading is not None:
        return PostOxyCdiReading(**{**sensor.frozen_reading.__dict__, "status": "FROZEN"})
    if not sensor.valid:
        return PostOxyCdiReading(
            valid=False,
            po2_mmhg=None,
            pco2_mmhg=None,
            oxygen_saturation=None,
            hematocrit_pct=None,
            hemoglobin_g_dl=None,
            temperature_c=None,
            status="INVALID",
        )

    hct = min(max(blood.hematocrit_pct + sensor.hematocrit_offset_pct, 0.0), 100.0)
    # Hgb remains consistent with displayed Hct using the common reduced-order 3:1 relation.
    displayed_hgb = hct / 3.0
    return PostOxyCdiReading(
        valid=True,
        po2_mmhg=max(0.0, blood.po2_mmhg + sensor.po2_offset_mmhg),
        pco2_mmhg=max(0.0, blood.pco2_mmhg + sensor.pco2_offset_mmhg),
        oxygen_saturation=min(max(blood.oxygen_saturation + sensor.saturation_offset, 0.0), 1.0),
        hematocrit_pct=hct,
        hemoglobin_g_dl=displayed_hgb,
        temperature_c=blood.temperature_c + sensor.temperature_offset_c,
        status="VALID",
    )
