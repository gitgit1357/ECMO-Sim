from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .core import CirculationModel, EdgeSpec, NodeSpec, periodic_elastance


@dataclass(frozen=True)
class NeonatalBaselineTargets:
    weight_kg: float = 3.5
    postnatal_age_hours: float = 72.0
    heart_rate_bpm: float = 130.0
    total_blood_volume_ml: float = 301.0
    systolic_bp_mmhg: float = 70.0
    diastolic_bp_mmhg: float = 42.0
    map_mmhg: float = 51.0
    cvp_mmhg: float = 4.0
    mean_pa_pressure_mmhg: float = 18.0
    left_atrial_pressure_mmhg: float = 6.0
    systemic_flow_ml_s: float = 13.125  # 0.7875 L/min = 225 mL/kg/min


TARGETS = NeonatalBaselineTargets()


def build_normal_term_neonate() -> CirculationModel:
    """
    Standalone 3.5-kg normal term neonate circulation.

    Anatomy is explicit from caval return through the four chambers, branch
    pulmonary arteries and veins, aortic root/arch, upper and lower systemic
    beds, and coronary return. Distal organ beds remain lumped.
    """

    hr = TARGETS.heart_rate_bpm

    nodes: List[NodeSpec] = [
        NodeSpec("SVC", "systemic_vein", 15.0, 2.0),
        NodeSpec("IVC", "systemic_vein", 40.0, 5.0),
        NodeSpec(
            "RA",
            "atrium",
            2.0,
            pressure_fn=periodic_elastance(hr, 0.18, 0.95, 2.0, 0.78, 0.20, 1.5),
        ),
        NodeSpec(
            "RV",
            "ventricle",
            1.0,
            pressure_fn=periodic_elastance(hr, 0.16, 32.0, 1.0, 0.00, 0.38, 1.5, 0.30, 8.0, 2.0),
        ),
        NodeSpec("MPA", "pulmonary_artery", 5.185, 0.11, 1.5),
        NodeSpec("RPA", "pulmonary_artery", 2.76, 0.08, 1.5),
        NodeSpec("LPA", "pulmonary_artery", 2.76, 0.08, 1.5),
        NodeSpec("RIGHT_LUNG", "pulmonary_bed", 7.8, 1.20, 1.5),
        NodeSpec("LEFT_LUNG", "pulmonary_bed", 7.8, 1.20, 1.5),
        NodeSpec("RPV", "pulmonary_vein", 3.95, 0.90, 1.5),
        NodeSpec("LPV", "pulmonary_vein", 3.95, 0.90, 1.5),
        NodeSpec(
            "LA",
            "atrium",
            2.0,
            pressure_fn=periodic_elastance(hr, 0.20, 1.05, 2.0, 0.78, 0.20, 1.5),
        ),
        NodeSpec(
            "LV",
            "ventricle",
            1.0,
            pressure_fn=periodic_elastance(hr, 0.20, 76.0, 1.0, 0.00, 0.38, 1.5, 0.30, 8.0, 2.0),
        ),
        NodeSpec("AORTIC_ROOT", "systemic_artery", 3.215, 0.034),
        NodeSpec("AORTIC_ARCH", "systemic_artery", 4.25, 0.053),
        NodeSpec("UPPER_ARTERY", "systemic_artery", 2.12, 0.058),
        NodeSpec("LOWER_ARTERY", "systemic_artery", 3.44, 0.092),
        NodeSpec("UPPER_BED", "systemic_bed", 6.75, 0.35),
        NodeSpec("LOWER_BED", "systemic_bed", 13.5, 0.70),
        NodeSpec("UPPER_VEINS", "systemic_vein", 10.5, 2.50),
        NodeSpec("LOWER_VEINS", "systemic_vein", 10.0, 6.00),
        NodeSpec("CORONARY_BED", "coronary_bed", 2.075, 0.05, 1.5),
    ]

    # Resistances are in mmHg*s/mL. Branch values are chosen so the aggregate
    # normal-state circulation settles near 225 mL/kg/min and normal neonatal
    # pressure targets. They are calibration parameters, not claims of direct
    # anatomical measurement.
    edges: List[EdgeSpec] = [
        EdgeSpec("svc_to_ra", "SVC", "RA", 0.055),
        EdgeSpec("ivc_to_ra", "IVC", "RA", 0.050),
        EdgeSpec("tricuspid", "RA", "RV", 0.08, valve=True),
        EdgeSpec("pulmonary_valve", "RV", "MPA", 0.04, valve=True, source_resistance_mmhg_s_per_ml=0.06),
        EdgeSpec("mpa_to_rpa", "MPA", "RPA", 0.045),
        EdgeSpec("mpa_to_lpa", "MPA", "LPA", 0.045),
        EdgeSpec("rpa_to_right_lung", "RPA", "RIGHT_LUNG", 1.32),
        EdgeSpec("lpa_to_left_lung", "LPA", "LEFT_LUNG", 1.32),
        EdgeSpec("right_lung_to_rpv", "RIGHT_LUNG", "RPV", 0.50),
        EdgeSpec("left_lung_to_lpv", "LEFT_LUNG", "LPV", 0.50),
        EdgeSpec("rpv_to_la", "RPV", "LA", 0.060),
        EdgeSpec("lpv_to_la", "LPV", "LA", 0.060),
        EdgeSpec("mitral", "LA", "LV", 0.07, valve=True),
        EdgeSpec("aortic_valve", "LV", "AORTIC_ROOT", 0.04, valve=True, source_resistance_mmhg_s_per_ml=0.06),
        EdgeSpec("root_to_arch", "AORTIC_ROOT", "AORTIC_ARCH", 0.060),
        EdgeSpec("arch_to_upper", "AORTIC_ARCH", "UPPER_ARTERY", 0.090),
        EdgeSpec("arch_to_lower", "AORTIC_ARCH", "LOWER_ARTERY", 0.070),
        EdgeSpec("upper_arterial_bed", "UPPER_ARTERY", "UPPER_BED", 7.5),
        EdgeSpec("lower_arterial_bed", "LOWER_ARTERY", "LOWER_BED", 5.3),
        EdgeSpec("upper_bed_to_veins", "UPPER_BED", "UPPER_VEINS", 2.0),
        EdgeSpec("lower_bed_to_veins", "LOWER_BED", "LOWER_VEINS", 1.5),
        EdgeSpec("upper_veins_to_svc", "UPPER_VEINS", "SVC", 0.35),
        EdgeSpec("lower_veins_to_ivc", "LOWER_VEINS", "IVC", 0.25),
        EdgeSpec("left_coronary_inflow", "AORTIC_ROOT", "CORONARY_BED", 18.0),
        EdgeSpec("coronary_sinus_return", "CORONARY_BED", "RA", 0.60),
    ]

    # Initial volumes sum to 301 mL. They intentionally begin near, rather
    # than exactly on, the periodic steady state so the stabilization test
    # verifies that the loop settles without hidden clamps or controllers.
    initial: Dict[str, float] = {
        "SVC": 23.0,
        "IVC": 60.0,
        "RA": 6.0,
        "RV": 6.0,
        "MPA": 7.0,
        "RPA": 4.0,
        "LPA": 4.0,
        "RIGHT_LUNG": 18.0,
        "LEFT_LUNG": 18.0,
        "RPV": 8.0,
        "LPV": 8.0,
        "LA": 6.0,
        "LV": 6.0,
        "AORTIC_ROOT": 5.0,
        "AORTIC_ARCH": 7.0,
        "UPPER_ARTERY": 5.0,
        "LOWER_ARTERY": 8.0,
        "UPPER_BED": 12.0,
        "LOWER_BED": 24.0,
        "UPPER_VEINS": 23.0,
        "LOWER_VEINS": 40.0,
        "CORONARY_BED": 3.0,
    }

    return CirculationModel(nodes, edges, initial)
