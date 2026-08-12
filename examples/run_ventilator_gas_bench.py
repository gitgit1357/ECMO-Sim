from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / 'src'):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from bench_fixtures.ventilator_bench import ventilator_northstar_matrix, run_ventilator_case
from neolung import LungMetrics, calculate_gas_exchange

print('External Ventilator + Standalone Gas Exchange Bench')
print('=' * 105)
print(f"{'Case':24} {'VT/kg':>7} {'VE':>8} {'VA':>8} {'PaCO2':>8} {'PaO2':>8} {'SaO2%':>8}")
for name, vent, changes in ventilator_northstar_matrix():
    m = run_ventilator_case(name, vent, lung_changes=changes)
    lm = LungMetrics(
        respiratory_rate_bpm=m.rate_bpm,
        tidal_volume_ml=m.tidal_volume_ml,
        tidal_volume_ml_per_kg=m.tidal_volume_ml_per_kg,
        minute_ventilation_ml_min=m.minute_ventilation_ml_min,
        peak_inspiratory_flow_ml_s=m.peak_inspiratory_flow_ml_s,
        peak_expiratory_flow_ml_s=m.peak_expiratory_flow_ml_s,
        min_pleural_pressure_cmh2o=-5.0,
        mean_lung_volume_ml=m.end_expiratory_volume_ml + m.tidal_volume_ml/2,
        end_expiratory_volume_ml=m.end_expiratory_volume_ml,
    )
    g = calculate_gas_exchange(lm)
    print(f"{name:24} {m.tidal_volume_ml_per_kg:7.2f} {m.minute_ventilation_ml_min:8.1f} {g.alveolar_ventilation_ml_min:8.1f} {g.arterial_pco2_mmhg:8.1f} {g.arterial_po2_mmhg:8.1f} {g.arterial_saturation_pct:8.2f}")
