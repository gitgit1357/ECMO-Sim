from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from neocoupling import run_coupled_neonate
from neolung import LungParameters
from neolung.gas_exchange import GasExchangeParameters


def compact(r):
    c, g = r.circulation_metrics, r.gas
    return {
        'map_mmhg': round(c.mean_aortic_mmhg, 3),
        'native_output_ml_min': round(c.native_output_ml_min, 3),
        'pulmonary_flow_ml_min': round(r.pulmonary_flow_ml_min, 3),
        'mean_pa_mmhg': round(c.mean_pa_mmhg, 3),
        'pvr_multiplier': round(r.pvr_multiplier, 4),
        'pao2_mmhg': round(g.arterial_po2_mmhg, 3),
        'paco2_mmhg': round(g.arterial_pco2_mmhg, 3),
        'sao2_pct': round(g.arterial_saturation_pct, 3),
        'mixed_venous_sat_pct': round(r.mixed_venous_saturation_pct, 3),
        'oxygen_delivery_ml_min': round(r.systemic_oxygen_delivery_ml_min, 3),
    }

out = {
    'schema': 'cardiopulmonary-coupling-northstar-v1',
    'scenarios': {
        'neutral': compact(run_coupled_neonate()),
        'hypoxia_fio2_012': compact(run_coupled_neonate(gas_params=GasExchangeParameters(fio2=0.12))),
        'low_compliance': compact(run_coupled_neonate(lung_params=LungParameters(compliance_ml_per_cmh2o=2.6))),
        'peep_8': compact(run_coupled_neonate(lung_params=LungParameters(peep_cmh2o=8.0))),
    }
}
path = Path(__file__).with_name('current_coupling_northstar.json')
path.write_text(json.dumps(out, indent=2) + '\n')
print(path)
