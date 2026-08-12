"""Compatibility re-export for the neutral blood-mixing utility.

Patient physiology imports from ``neoblood`` so it does not depend on the
ECMO package or the ECMO coupling package. Existing coupling callers may keep
using this module during the transition.
"""
from neoblood.mixing import PatientArterialGasState, mix_native_and_ecmo_arterial_blood

__all__ = ["PatientArterialGasState", "mix_native_and_ecmo_arterial_blood"]
