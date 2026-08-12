from neoventilator import PressureControlSettings

# Historical bench name retained for compatibility. The production settings
# object now owns the deterministic pressure waveform.
PressureControlVentilator = PressureControlSettings

__all__ = ["PressureControlVentilator"]
