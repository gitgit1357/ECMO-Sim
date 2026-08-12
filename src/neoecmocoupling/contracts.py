from __future__ import annotations

from dataclasses import dataclass
import math


def _finite(name: str, value: float) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite; got {value!r}")


@dataclass(frozen=True)
class PatientToEcmoState:
    """Patient-owned boundary values supplied to the ECMO coupling layer.

    This object deliberately contains no pump controls and no circuit-derived
    values.  Stage 1 is a contract only; it does not alter either solver.
    """

    weight_kg: float
    venous_pressure_mmhg: float
    arterial_pressure_mmhg: float
    blood_volume_fraction: float
    native_cardiac_output_ml_min: float
    native_venous_oxygen_saturation: float
    native_venous_paco2_mmhg: float

    def validate(self) -> None:
        for name, value in self.__dict__.items():
            _finite(name, float(value))
        if self.weight_kg <= 0.0:
            raise ValueError("weight_kg must be greater than zero")
        if self.blood_volume_fraction <= 0.0:
            raise ValueError("blood_volume_fraction must be greater than zero")
        if self.native_cardiac_output_ml_min < 0.0:
            raise ValueError("native_cardiac_output_ml_min cannot be negative")
        if not 0.0 <= self.native_venous_oxygen_saturation <= 1.0:
            raise ValueError("native_venous_oxygen_saturation must be between 0 and 1")
        if self.native_venous_paco2_mmhg < 0.0:
            raise ValueError("native_venous_paco2_mmhg cannot be negative")


@dataclass(frozen=True)
class EcmoToPatientState:
    """Circuit-owned support delivered back toward the patient.

    `ecmo_return_flow_ml_min` is true patient-directed ECMO flow, excluding
    shunt and bridge flow.  This is not total circuit flow.
    """

    enabled: bool
    ecmo_drainage_flow_ml_min: float
    ecmo_return_flow_ml_min: float
    return_oxygen_saturation: float
    return_po2_mmhg: float
    return_paco2_mmhg: float
    return_pressure_mmhg: float
    external_fluid_removal_ml_min: float
    total_circuit_flow_ml_min: float
    shunt_flow_ml_min: float
    bridge_flow_ml_min: float
    p1_mmhg: float
    p2_mmhg: float
    p3_mmhg: float

    def validate(self, *, conservation_tolerance_ml_min: float = 0.1) -> None:
        for name, value in self.__dict__.items():
            if name != "enabled":
                _finite(name, float(value))
        for name in (
            "ecmo_drainage_flow_ml_min",
            "ecmo_return_flow_ml_min",
            "external_fluid_removal_ml_min",
            "total_circuit_flow_ml_min",
            "shunt_flow_ml_min",
            "bridge_flow_ml_min",
        ):
            if getattr(self, name) < 0.0:
                raise ValueError(f"{name} cannot be negative")
        if not 0.0 <= self.return_oxygen_saturation <= 1.0:
            raise ValueError("return_oxygen_saturation must be between 0 and 1")
        if self.return_po2_mmhg < 0.0:
            raise ValueError("return_po2_mmhg cannot be negative")
        if self.return_paco2_mmhg < 0.0:
            raise ValueError("return_paco2_mmhg cannot be negative")

        branch_sum = (
            self.ecmo_return_flow_ml_min
            + self.shunt_flow_ml_min
            + self.bridge_flow_ml_min
        )
        if abs(self.total_circuit_flow_ml_min - branch_sum) > conservation_tolerance_ml_min:
            raise ValueError(
                "ECMO branch flows do not conserve total circuit flow: "
                f"total={self.total_circuit_flow_ml_min:.3f}, "
                f"patient+shunt+bridge={branch_sum:.3f} mL/min"
            )
        if abs(self.ecmo_drainage_flow_ml_min - self.ecmo_return_flow_ml_min) > conservation_tolerance_ml_min:
            raise ValueError(
                "Stage-1 VA contract requires matched patient drainage and return flow"
            )


@dataclass(frozen=True)
class EcmoPatientCouplingContract:
    """One validated exchange across the future closed-loop boundary."""

    patient: PatientToEcmoState
    ecmo: EcmoToPatientState

    def validate(self) -> None:
        self.patient.validate()
        self.ecmo.validate()
