"""Boundary contracts for coupling the modular neonatal patient and ECMO circuit.

Stage 1 intentionally performs translation and validation only.  It does not
modify patient physiology or replace the circuit's placeholder patient path.
"""

from .adapters import (
    build_coupling_contract,
    ecmo_delivery_from_console_state,
    patient_boundary_from_snapshot,
    vascular_support_port_from_delivery,
)
from .mixing import PatientArterialGasState, mix_native_and_ecmo_arterial_blood
from .contracts import (
    EcmoPatientCouplingContract,
    EcmoToPatientState,
    PatientToEcmoState,
)

__all__ = [
    "PatientToEcmoState",
    "EcmoToPatientState",
    "EcmoPatientCouplingContract",
    "patient_boundary_from_snapshot",
    "ecmo_delivery_from_console_state",
    "build_coupling_contract",
    "vascular_support_port_from_delivery",
    "PatientArterialGasState",
    "mix_native_and_ecmo_arterial_blood",
    "ClosedLoopVaResult",
    "VaMapCouplingConfig",
    "solve_closed_loop_va_ecmo",
    "PreloadDrainageConfig",
    "VolumeLimitedVaResult",
    "solve_volume_limited_va_ecmo",
]

from .hydraulics import HydraulicCouplingResult, solve_ecmo_against_patient

from .closed_loop import ClosedLoopVaResult, VaMapCouplingConfig, solve_closed_loop_va_ecmo

from .preload import (
    PreloadDrainageConfig,
    VolumeLimitedVaResult,
    solve_volume_limited_va_ecmo,
)

from .time_step import (
    CoupledPatientEcmoSnapshot,
    CoupledVaEcmoPatient,
    TimeStepCouplingConfig,
)

__all__ += [
    "TimeStepCouplingConfig",
    "CoupledPatientEcmoSnapshot",
    "CoupledVaEcmoPatient",
]

from .dynamics import (
    DisplayedCoupledState,
    DynamicCoupledSnapshot,
    DynamicCoupledVaEcmoPatient,
    DynamicResponseConfig,
)

__all__ += [
    "DynamicResponseConfig",
    "DisplayedCoupledState",
    "DynamicCoupledSnapshot",
    "DynamicCoupledVaEcmoPatient",
]
