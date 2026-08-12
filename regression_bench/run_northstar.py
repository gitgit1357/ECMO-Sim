from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from regression_bench.harness import save_result

out = ROOT / "regression_bench" / "results" / "northstar_latest.json"
data = save_result(out)
print(f"NorthStar bench: {data['manifest']['bench_id']}")
print(f"Manifest: {data['manifest']['manifest_hash']}")
print(f"Saved: {out}")
print(json.dumps(data['baseline'], indent=2))
