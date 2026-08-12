from dataclasses import dataclass

@dataclass(frozen=True)
class CirculationToKidney:
    map_mmhg: float
    cvp_mmhg: float
    systemic_flow_ml_min: float
    renal_vaso_tone: float = 1.0

@dataclass(frozen=True)
class KidneyToCirculation:
    renal_flow_ml_min: float
    urine_removed_ml_min: float
    renal_resistance_signal: float
