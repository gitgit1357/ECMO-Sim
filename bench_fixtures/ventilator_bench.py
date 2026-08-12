from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from neolung import NeonatalLungModel, LungSimulationResult
from .ventilator import PressureControlVentilator


@dataclass(frozen=True)
class VentilatorBenchMetrics:
    name: str
    pip_cmh2o: float
    peep_cmh2o: float
    rate_bpm: float
    inspiratory_time_s: float
    tidal_volume_ml: float
    tidal_volume_ml_per_kg: float
    minute_ventilation_ml_min: float
    peak_inspiratory_flow_ml_s: float
    peak_expiratory_flow_ml_s: float
    mean_airway_pressure_cmh2o: float
    end_expiratory_volume_ml: float
    intrinsic_peep_proxy_cmh2o: float


def run_ventilator_case(
    name: str,
    ventilator: PressureControlVentilator,
    *,
    lung_changes: dict | None = None,
    duration_s: float = 30.0,
    dt_s: float = 0.002,
) -> VentilatorBenchMetrics:
    # External ventilation bench suppresses spontaneous effort unless a test explicitly overrides it.
    changes = {"inspiratory_muscle_swing_cmh2o": 0.0, "peep_cmh2o": 0.0}
    if lung_changes:
        changes.update(lung_changes)
    model = NeonatalLungModel().copy_with(**changes)

    samples = []
    pressures = []
    n = int(duration_s / dt_s)
    for _ in range(n):
        pao = ventilator.airway_pressure(model.state.time_s)
        pressures.append(pao)
        samples.append(model.step(dt_s, airway_opening_pressure_cmh2o=pao))

    result = LungSimulationResult(samples=samples, parameters=model.params)
    end = samples[-1].time_s
    window_start = max(0.0, end - 15.0)
    selected = [(s, p) for s, p in zip(samples, pressures) if s.time_s >= window_start]
    vols = [s.lung_volume_ml for s, _ in selected]
    flows = [s.flow_ml_s for s, _ in selected]
    paos = [p for _, p in selected]
    vt = max(vols) - min(vols)

    # Proxy for dynamic intrinsic PEEP: alveolar pressure above set PEEP immediately before
    # the next mandatory inspiration. This is a bench diagnostic, not a clinical measurement.
    cycle = ventilator.cycle_s
    preinsp = []
    for s, _ in selected:
        phase = s.time_s % cycle
        if cycle - phase <= max(dt_s * 2, 0.006):
            preinsp.append(s.alveolar_pressure_cmh2o - ventilator.peep_cmh2o)
    auto_peep = max(0.0, sum(preinsp) / len(preinsp)) if preinsp else 0.0

    return VentilatorBenchMetrics(
        name=name,
        pip_cmh2o=ventilator.pip_cmh2o,
        peep_cmh2o=ventilator.peep_cmh2o,
        rate_bpm=ventilator.rate_bpm,
        inspiratory_time_s=ventilator.inspiratory_time_s,
        tidal_volume_ml=vt,
        tidal_volume_ml_per_kg=vt / model.params.weight_kg,
        minute_ventilation_ml_min=vt * ventilator.rate_bpm,
        peak_inspiratory_flow_ml_s=max(flows),
        peak_expiratory_flow_ml_s=min(flows),
        mean_airway_pressure_cmh2o=sum(paos) / len(paos),
        end_expiratory_volume_ml=min(vols),
        intrinsic_peep_proxy_cmh2o=auto_peep,
    )


def ventilator_northstar_matrix() -> Iterable[tuple[str, PressureControlVentilator, dict]]:
    normal = {}
    stiff = {"compliance_ml_per_cmh2o": 3.5}
    resistive = {"airway_resistance_cmh2o_s_per_l": 90.0}
    cases = [
        ("pc_baseline", PressureControlVentilator(10, 5, 40, 0.35), normal),
        ("pc_low_drive", PressureControlVentilator(8, 5, 40, 0.35), normal),
        ("pc_high_drive", PressureControlVentilator(18, 5, 40, 0.35), normal),
        ("pc_high_peep", PressureControlVentilator(13, 8, 40, 0.35), normal),
        ("pc_low_rate", PressureControlVentilator(10, 5, 25, 0.35), normal),
        ("pc_high_rate", PressureControlVentilator(10, 5, 60, 0.30), normal),
        ("pc_long_ti", PressureControlVentilator(10, 5, 40, 0.50), normal),
        ("pc_stiff_lung", PressureControlVentilator(10, 5, 40, 0.35), stiff),
        ("pc_high_resistance", PressureControlVentilator(10, 5, 40, 0.35), resistive),
    ]
    return cases
