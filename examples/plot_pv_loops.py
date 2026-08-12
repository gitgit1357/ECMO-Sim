from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import matplotlib.pyplot as plt
from neocirculation import build_normal_term_neonate, TARGETS
from neocirculation.pv import extract_pressure_volume_loop

model = build_normal_term_neonate()
result = model.simulate(20.0, 200.0)
for chamber in ("LV", "RV"):
    loop = extract_pressure_volume_loop(result, chamber, TARGETS.heart_rate_bpm, beats=3)
    plt.figure()
    plt.plot(loop.volume_ml, loop.pressure_mmhg)
    plt.xlabel("Volume (mL)")
    plt.ylabel("Pressure (mmHg)")
    plt.title(f"{chamber} Pressure-Volume Loop (engineering diagnostic)")
    plt.tight_layout()
    plt.show()
