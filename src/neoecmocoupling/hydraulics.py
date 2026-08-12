from __future__ import annotations

from dataclasses import dataclass

from neoecmo import EcmoConsoleControls, EcmoConsoleState, run_ecmo_console

from .contracts import PatientToEcmoState


@dataclass(frozen=True)
class HydraulicCouplingResult:
    patient_boundary: PatientToEcmoState
    ecmo_state: EcmoConsoleState


def solve_ecmo_against_patient(
    controls: EcmoConsoleControls,
    patient: PatientToEcmoState,
) -> HydraulicCouplingResult:
    """Solve the ECMO circuit against live patient MAP/CVP boundaries.

    This is two-way only at the hydraulic boundary: the patient supplies
    pressures and venous blood state; the circuit returns solved flow and
    pressures. Patient physiology itself is not advanced here.
    """
    patient.validate()
    state = run_ecmo_console(
        controls,
        native_venous_saturation=patient.native_venous_oxygen_saturation,
        native_venous_paco2_mmhg=patient.native_venous_paco2_mmhg,
        patient_arterial_pressure_mmhg=patient.arterial_pressure_mmhg,
        patient_venous_pressure_mmhg=patient.venous_pressure_mmhg,
    )
    return HydraulicCouplingResult(patient_boundary=patient, ecmo_state=state)
