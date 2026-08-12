from __future__ import annotations

from dataclasses import dataclass

from .ecmo_workspace import WorkspaceSnapshot


@dataclass(frozen=True)
class PatientMonitorReading:
    """Read-only learner monitor projection of an authoritative workspace snapshot.

    This object contains no physiology and performs no clinical inference. It
    only selects/labels values already owned by the coupled patient/display
    layer. Channels that are not integrated into the unified patient are
    explicitly unavailable rather than synthesized here.
    """

    simulation_time_s: float
    map_mmhg: float
    systolic_mmhg: float
    diastolic_mmhg: float
    cvp_mmhg: float
    spo2_pct: float
    pao2_mmhg: float
    paco2_mmhg: float
    native_cardiac_output_ml_min: float
    ecmo_patient_flow_ml_min: float
    urine_ml_kg_hr: float
    cumulative_urine_ml: float
    net_body_fluid_ml: float
    blood_volume_fraction: float
    physiology_updating: bool
    heart_rate_bpm: float | None = None
    temperature_c: float | None = None


def learner_patient_reading(snapshot: WorkspaceSnapshot, *, physiology_updating: bool = False) -> PatientMonitorReading:
    """Project authoritative patient state for every learner-facing GUI surface.

    Phase 6 establishes this as the single shared projection contract for patient
    values that appear on more than one learner surface.  It contains no
    physiology and performs no clinical inference.
    """

    displayed = snapshot.dynamic.displayed
    patient = snapshot.dynamic.true.patient
    return PatientMonitorReading(
        simulation_time_s=float(snapshot.dynamic.elapsed_s),
        map_mmhg=float(displayed.map_mmhg),
        systolic_mmhg=float(patient.systolic_mmhg),
        diastolic_mmhg=float(patient.diastolic_mmhg),
        cvp_mmhg=float(patient.cvp_mmhg),
        spo2_pct=float(displayed.sao2_pct),
        pao2_mmhg=float(displayed.pao2_mmhg),
        paco2_mmhg=float(displayed.paco2_mmhg),
        native_cardiac_output_ml_min=float(patient.native_cardiac_output_ml_min),
        ecmo_patient_flow_ml_min=float(displayed.patient_flow_ml_min),
        urine_ml_kg_hr=float(patient.urine_ml_kg_hr),
        cumulative_urine_ml=float(patient.cumulative_urine_ml),
        net_body_fluid_ml=float(patient.cumulative_net_body_fluid_ml),
        blood_volume_fraction=float(patient.blood_volume_fraction),
        physiology_updating=bool(physiology_updating),
    )


# Backward-compatible API alias for pre-Phase-6 callers.  New learner GUI surfaces
# must consume learner_patient_reading directly.
patient_monitor_reading = learner_patient_reading
