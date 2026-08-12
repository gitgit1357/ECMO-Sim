from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from neolung import default_gas_bench_cases, run_gas_case

print("Standalone Neonatal Gas Exchange Bench")
print("=" * 104)
print(f"{'Case':30} {'VA mL/min':>10} {'PAO2':>8} {'PaO2':>8} {'SaO2%':>8} {'PaCO2':>8} {'Shunt':>8}")
for case in default_gas_bench_cases():
    r = run_gas_case(case)
    print(f"{case.name:30} {r.alveolar_ventilation_ml_min:10.1f} {r.alveolar_po2_mmhg:8.1f} {r.arterial_po2_mmhg:8.1f} {r.arterial_saturation_pct:8.2f} {r.arterial_pco2_mmhg:8.1f} {100*r.shunt_fraction:7.1f}%")
