from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from neocoupling import run_coupled_neonate
from neolung import LungParameters
from neolung.gas_exchange import GasExchangeParameters


def show(name, result):
    c = result.circulation_metrics
    g = result.gas
    print(f"\n{name}")
    print(f"  MAP: {c.mean_aortic_mmhg:.1f} mmHg")
    print(f"  Native output: {c.native_output_ml_min:.0f} mL/min")
    print(f"  Pulmonary flow: {result.pulmonary_flow_ml_min:.0f} mL/min")
    print(f"  Mean PA: {c.mean_pa_mmhg:.1f} mmHg")
    print(f"  PVR multiplier: {result.pvr_multiplier:.2f}x")
    print(f"  PaO2/SaO2: {g.arterial_po2_mmhg:.0f} mmHg / {g.arterial_saturation_pct:.1f}%")
    print(f"  PaCO2: {g.arterial_pco2_mmhg:.1f} mmHg")
    print(f"  Mixed venous: {result.mixed_venous_po2_mmhg:.1f} mmHg / {result.mixed_venous_saturation_pct:.1f}%")


show("Neutral spontaneous coupling", run_coupled_neonate())
show("Hypoxic lung", run_coupled_neonate(gas_params=GasExchangeParameters(fio2=0.12)))
show("Low compliance", run_coupled_neonate(lung_params=LungParameters(compliance_ml_per_cmh2o=2.6)))
show("PEEP 8", run_coupled_neonate(lung_params=LungParameters(peep_cmh2o=8.0, airway_opening_pressure_cmh2o=0.0)))
