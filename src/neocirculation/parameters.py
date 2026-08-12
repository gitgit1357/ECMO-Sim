from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Dict, Iterable, Mapping


class ParameterClass(str, Enum):
    OBSERVED_TARGET = "observed_target"
    DERIVED = "derived"
    CALIBRATED = "calibrated"
    PROVISIONAL = "provisional"


class Confidence(str, Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


@dataclass(frozen=True)
class ParameterRecord:
    name: str
    value: float
    units: str
    classification: ParameterClass
    confidence: Confidence
    rationale: str
    source_note: str

    def as_dict(self) -> Dict[str, object]:
        data = asdict(self)
        data["classification"] = self.classification.value
        data["confidence"] = self.confidence.value
        return data


class ParameterRegistry:
    """Documented register; it never writes values back into the solver."""

    def __init__(self, records: Iterable[ParameterRecord]) -> None:
        self._records = {record.name: record for record in records}
        if not self._records:
            raise ValueError("ParameterRegistry requires at least one record")

    def get(self, name: str) -> ParameterRecord:
        return self._records[name]

    def records(self) -> Mapping[str, ParameterRecord]:
        return dict(self._records)

    def as_dict(self) -> Dict[str, Dict[str, object]]:
        return {name: record.as_dict() for name, record in self._records.items()}


BASELINE_PARAMETER_REGISTRY = ParameterRegistry(
    [
        ParameterRecord("weight_kg", 3.5, "kg", ParameterClass.OBSERVED_TARGET, Confidence.HIGH,
                        "Reference term neonate size.", "Reference-patient definition; source synthesis pending formal bibliography."),
        ParameterRecord("postnatal_age_hours", 72.0, "h", ParameterClass.OBSERVED_TARGET, Confidence.HIGH,
                        "Avoids immediate transitional circulation while remaining neonatal.", "Reference-patient definition."),
        ParameterRecord("heart_rate_bpm", 130.0, "beats/min", ParameterClass.OBSERVED_TARGET, Confidence.HIGH,
                        "Central resting target for a stable term neonate.", "Clinical target to be source-weighted in the evidence register."),
        ParameterRecord("total_blood_volume_ml", 301.0, "mL", ParameterClass.DERIVED, Confidence.MODERATE,
                        "3.5 kg multiplied by approximately 86 mL/kg.", "Derived from commonly used term-neonate blood-volume range."),
        ParameterRecord("systemic_flow_ml_s", 13.125, "mL/s", ParameterClass.DERIVED, Confidence.MODERATE,
                        "225 mL/kg/min for a 3.5 kg reference patient.", "Derived calibration target."),
        ParameterRecord("systemic_arterial_compliance_scale", 1.0, "multiplier", ParameterClass.CALIBRATED, Confidence.MODERATE,
                        "Produces the selected pulse pressure with conserved volume.", "Hidden reduced-order calibration parameter."),
        ParameterRecord("systemic_resistance_scale", 1.0, "multiplier", ParameterClass.CALIBRATED, Confidence.MODERATE,
                        "Produces the selected MAP at baseline flow.", "Hidden reduced-order calibration parameter."),
        ParameterRecord("pulmonary_resistance_scale", 1.0, "multiplier", ParameterClass.CALIBRATED, Confidence.MODERATE,
                        "Produces the selected mean pulmonary pressure.", "Hidden reduced-order calibration parameter."),
        ParameterRecord("lv_contractility_scale", 1.0, "multiplier", ParameterClass.CALIBRATED, Confidence.MODERATE,
                        "Scales LV maximum elastance without pinning output.", "Hidden reduced-order calibration parameter."),
        ParameterRecord("rv_contractility_scale", 1.0, "multiplier", ParameterClass.CALIBRATED, Confidence.MODERATE,
                        "Scales RV maximum elastance without pinning output.", "Hidden reduced-order calibration parameter."),
    ]
)
