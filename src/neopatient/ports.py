from neoventilator import PressureControlSettings
from dataclasses import dataclass

@dataclass(frozen=True)
class AirwayPort:
    peep_cmh2o: float = 0.0
    airway_opening_pressure_cmh2o: float = 0.0
    fio2: float = 0.21
    pressure_control: PressureControlSettings | None = None

@dataclass(frozen=True)
class VascularSupportPort:
    enabled: bool = False
    support_flow_ml_min: float = 0.0
    return_oxygen_saturation_pct: float = 100.0
    return_po2_mmhg: float = 450.0
    return_paco2_mmhg: float = 40.0
    supported_map_mmhg: float | None = None
    estimated_pulse_pressure_mmhg: float | None = None
    native_output_multiplier: float = 1.0

@dataclass(frozen=True)
class RenalTherapyPort:
    fluid_in_ml_min: float = 0.0
    external_fluid_out_ml_min: float = 0.0
    diuretic_multiplier: float = 1.0
    renal_vaso_tone: float = 1.0
    renal_function_fraction: float = 1.0

@dataclass(frozen=True)
class MyocardialFunctionPort:
    lv_contractility_scale: float = 1.0
    rv_contractility_scale: float = 1.0

    def __post_init__(self):
        if not (0.0 < self.lv_contractility_scale <= 2.0):
            raise ValueError("lv_contractility_scale must be > 0 and <= 2")
        if not (0.0 < self.rv_contractility_scale <= 2.0):
            raise ValueError("rv_contractility_scale must be > 0 and <= 2")
