from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List
import numpy as np
from scipy.integrate import solve_ivp

from neocirculation import TARGETS
from neocirculation.metrics import calculate_baseline_metrics
from neolung import NeonatalLungModel, LungSimulationResult, derive_lung_metrics
from neolung.gas_exchange import GasExchangeParameters, calculate_gas_exchange
from bench_fixtures.ventilator import PressureControlVentilator

from .core import CouplingConfig, _coupled_circulation_model, CMH2O_TO_MMHG


@dataclass(frozen=True)
class CombinedEquipmentPoint:
    scenario_id: str
    pip_cmh2o: float
    peep_cmh2o: float
    vent_rate_bpm: float
    pump_flow_ml_kg_min: float
    pump_flow_ml_min: float
    tidal_volume_ml_kg: float
    pao2_mmhg: float
    paco2_mmhg: float
    native_lv_output_ml_min: float
    native_rv_output_ml_min: float
    total_aortic_inflow_ml_min: float
    circuit_fraction: float
    mean_aortic_mmhg: float
    pulse_pressure_mmhg: float
    mean_pa_mmhg: float
    mean_ra_mmhg: float
    pvr_multiplier: float
    effective_systemic_sao2_pct: float
    oxygen_delivery_index_proxy: float
    volume_conservation_error_ml: float


def _run_ventilator(vent: PressureControlVentilator, duration_s: float = 20.0, dt_s: float = 0.002):
    lung = NeonatalLungModel().copy_with(inspiratory_muscle_swing_cmh2o=0.0, peep_cmh2o=0.0)
    samples = []
    for _ in range(int(duration_s / dt_s)):
        pao = vent.airway_pressure(lung.state.time_s)
        samples.append(lung.step(dt_s, airway_opening_pressure_cmh2o=pao))
    result = LungSimulationResult(samples=samples, parameters=lung.params)
    return derive_lung_metrics(result), result


def _mean_pleural(result: LungSimulationResult, tail_s: float = 10.0) -> float:
    end = result.samples[-1].time_s
    vals = [s.pleural_pressure_cmh2o for s in result.samples if s.time_s >= end-tail_s]
    return float(np.mean(vals))


def _run_circulation_with_va(pvr_mult: float, pleural_delta_mmhg: float, pump_flow_ml_min: float,
                             stabilization_s: float = 12.0, support_s: float = 6.0, sample_hz: float = 50.0):
    base = _coupled_circulation_model(pvr_mult, pleural_delta_mmhg)
    stable = base.simulate(stabilization_s, sample_hz=sample_hz)
    y0 = stable.volumes_ml[:, -1].copy()
    idx = base.index
    initial_total = float(np.sum(y0))
    requested_q = pump_flow_ml_min / 60.0

    def pump_flow(patient):
        ra_v = max(float(patient[idx['RA']]), 0.0)
        factor = min(1.0, ra_v/0.5) if ra_v < 0.5 else 1.0
        return requested_q * factor

    def deriv(t, y):
        dv = base.derivative(t + stabilization_s, y)
        q = pump_flow(y)
        dv[idx['RA']] -= q
        dv[idx['AORTIC_ROOT']] += q
        return dv

    t_eval = np.linspace(0.0, support_s, int(round(support_s*sample_hz))+1)
    sol = solve_ivp(deriv, (0.0, support_s), y0, method='LSODA', t_eval=t_eval,
                    rtol=1e-7, atol=1e-9, max_step=min(0.01, 1.0/sample_hz))
    if not sol.success:
        raise RuntimeError(sol.message)
    window = min(4.0*60.0/TARGETS.heart_rate_bpm, support_s)
    mask = sol.t >= support_s-window
    times = sol.t[mask] + stabilization_s
    states = sol.y[:, mask]
    pressures = np.column_stack([base.pressures(t, states[:,i]) for i,t in enumerate(times)])
    qao=[]; qpv=[]; qp=[]
    for i,t in enumerate(times):
        flows=base.edge_flows(t, states[:,i])
        qao.append(max(0.0, flows['aortic_valve']))
        qpv.append(max(0.0, flows['pulmonary_valve']))
        qp.append(pump_flow(states[:,i]))
    native_lv=float(np.mean(qao))*60.0
    native_rv=float(np.mean(qpv))*60.0
    pump=float(np.mean(qp))*60.0
    aorta=pressures[idx['AORTIC_ROOT']]
    return {
        'native_lv':native_lv,'native_rv':native_rv,'pump':pump,
        'total':native_lv+pump,'map':float(np.mean(aorta)),
        'pp':float(np.max(aorta)-np.min(aorta)),
        'pa':float(np.mean(pressures[idx['MPA']])),
        'ra':float(np.mean(pressures[idx['RA']])),
        'conservation':float(np.sum(sol.y[:,-1])-initial_total),
    }


def run_combined_equipment_bench() -> List[CombinedEquipmentPoint]:
    """Frozen cross-system equipment bench.

    Ventilator and VA support are external fixtures. The oxygenator return is represented
    only by a fixed fully saturated return-blood assumption for the teaching-level mixing
    calculation; it does not belong to the patient physiology.
    """
    cfg=CouplingConfig()
    cases = [
        ('vent_ref_ecmo_0', PressureControlVentilator(10,5,40,0.35), 0.0),
        ('vent_ref_ecmo_100', PressureControlVentilator(10,5,40,0.35), 100.0),
        ('vent_ref_ecmo_200', PressureControlVentilator(10,5,40,0.35), 200.0),
        ('high_peep_ecmo_0', PressureControlVentilator(13,8,40,0.35), 0.0),
        ('high_peep_ecmo_100', PressureControlVentilator(13,8,40,0.35), 100.0),
        ('high_peep_ecmo_200', PressureControlVentilator(13,8,40,0.35), 200.0),
        ('low_vent_ecmo_0', PressureControlVentilator(8,5,40,0.35), 0.0),
        ('low_vent_ecmo_100', PressureControlVentilator(8,5,40,0.35), 100.0),
        ('low_vent_ecmo_200', PressureControlVentilator(8,5,40,0.35), 200.0),
    ]
    out=[]
    for sid,vent,indexed in cases:
        lm,lr=_run_ventilator(vent)
        gas=calculate_gas_exchange(lm, GasExchangeParameters(weight_kg=3.5))
        mean_ppl=_mean_pleural(lr)
        transmitted=max(0.0, vent.peep_cmh2o)*cfg.airway_to_pleural_transmission
        pleural_delta=((mean_ppl-cfg.reference_mean_pleural_cmh2o)+transmitted)*CMH2O_TO_MMHG*cfg.thoracic_pressure_gain
        hypoxic=max(0.0,(cfg.hypoxic_threshold_pao2_mmhg-gas.arterial_po2_mmhg)/cfg.hypoxic_threshold_pao2_mmhg)
        volume_ratio=(lm.mean_lung_volume_ml-cfg.reference_mean_lung_volume_ml)/cfg.reference_mean_lung_volume_ml
        pvr=min(cfg.max_pvr_multiplier,max(0.5,(1.0+cfg.lung_volume_pvr_gain*volume_ratio**2)*(1.0+cfg.hypoxic_pvr_gain*hypoxic)))
        pump=indexed*TARGETS.weight_kg
        circ=_run_circulation_with_va(pvr,pleural_delta,pump)
        total=max(1e-6,circ['total'])
        native_frac=circ['native_lv']/total
        circuit_frac=circ['pump']/total
        # Teaching-level arterial mixing proxy: native output carries lung SaO2;
        # circuit return is an external idealized oxygenator fixture at 100% saturation.
        effective_sat=native_frac*gas.arterial_saturation_pct+circuit_frac*100.0
        do2_proxy=total*(effective_sat/100.0)
        out.append(CombinedEquipmentPoint(
            scenario_id=sid,pip_cmh2o=vent.pip_cmh2o,peep_cmh2o=vent.peep_cmh2o,
            vent_rate_bpm=vent.rate_bpm,pump_flow_ml_kg_min=indexed,pump_flow_ml_min=circ['pump'],
            tidal_volume_ml_kg=lm.tidal_volume_ml/3.5,pao2_mmhg=gas.arterial_po2_mmhg,
            paco2_mmhg=gas.arterial_pco2_mmhg,native_lv_output_ml_min=circ['native_lv'],
            native_rv_output_ml_min=circ['native_rv'],total_aortic_inflow_ml_min=circ['total'],
            circuit_fraction=circuit_frac,mean_aortic_mmhg=circ['map'],pulse_pressure_mmhg=circ['pp'],
            mean_pa_mmhg=circ['pa'],mean_ra_mmhg=circ['ra'],pvr_multiplier=pvr,
            effective_systemic_sao2_pct=effective_sat,oxygen_delivery_index_proxy=do2_proxy,
            volume_conservation_error_ml=circ['conservation']))
    return out


def format_combined_equipment_report(points: Iterable[CombinedEquipmentPoint]) -> str:
    lines=[
      'COMBINED HEART-LUNG + EXTERNAL VENTILATOR/VA SUPPORT BENCH',
      'External fixtures only. Idealized oxygenator return saturation=100% for mixing proxy.',
      '',
      'Scenario              PIP/PEEP  ECMO   VT/kg  PaO2 PaCO2  NativeLV NativeRV Circuit% MAP  PP  PA  EffSaO2',
      '                               mL/kg/m mL/kg  mmHg mmHg    mL/min   mL/min      %    mmHg mmHg mmHg   %'
    ]
    for p in points:
        lines.append(f'{p.scenario_id:21s} {p.pip_cmh2o:2.0f}/{p.peep_cmh2o:<2.0f}    {p.pump_flow_ml_kg_min:4.0f}   '
                     f'{p.tidal_volume_ml_kg:5.2f} {p.pao2_mmhg:5.0f} {p.paco2_mmhg:5.0f}  '
                     f'{p.native_lv_output_ml_min:8.0f} {p.native_rv_output_ml_min:8.0f} '
                     f'{p.circuit_fraction*100:7.1f} {p.mean_aortic_mmhg:4.0f} {p.pulse_pressure_mmhg:3.0f} '
                     f'{p.mean_pa_mmhg:3.0f} {p.effective_systemic_sao2_pct:7.1f}')
    return '\n'.join(lines)
