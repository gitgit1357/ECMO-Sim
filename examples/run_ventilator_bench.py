from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT))

from bench_fixtures.ventilator_bench import run_ventilator_case, ventilator_northstar_matrix

print('Ventilator NorthStar v1 — external pressure-control fixture')
print('name                 PIP PEEP RR  Ti    VTml  ml/kg  MVml/min  MAPaw  autoPEEP')
for name, vent, changes in ventilator_northstar_matrix():
    m = run_ventilator_case(name, vent, lung_changes=changes)
    print(f'{name:20s} {m.pip_cmh2o:3.0f} {m.peep_cmh2o:4.0f} {m.rate_bpm:3.0f} {m.inspiratory_time_s:4.2f} '
          f'{m.tidal_volume_ml:6.1f} {m.tidal_volume_ml_per_kg:6.2f} {m.minute_ventilation_ml_min:8.0f} '
          f'{m.mean_airway_pressure_cmh2o:6.2f} {m.intrinsic_peep_proxy_cmh2o:8.2f}')
