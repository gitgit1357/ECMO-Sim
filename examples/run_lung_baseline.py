from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from neolung import NeonatalLungModel, derive_lung_metrics

m = NeonatalLungModel()
r = m.run(30.0)
x = derive_lung_metrics(r)
print("Standalone neonatal lung baseline")
for k, v in x.__dict__.items():
    print(f"{k:34s} {v:.3f}" if isinstance(v, float) else f"{k:34s} {v}")
