"""External bench fixtures for testing the circulation engine.

This package is intentionally outside ``neocirculation``. Nothing in the patient
engine imports these fixtures. They may be removed without changing physiology.
"""

from .cannulas import CannulaCurve, CannulaRecord, load_medtronic_life_support_mini

__all__ = ["CannulaCurve", "CannulaRecord", "load_medtronic_life_support_mini"]
