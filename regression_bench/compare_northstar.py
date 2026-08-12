from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from regression_bench.harness import compare, run_northstar_bench

ref_path = ROOT / "regression_bench" / "reference_snapshots" / "northstar_v1_accepted.json"
if not ref_path.exists():
    raise SystemExit(f"Missing accepted reference: {ref_path}")
reference = json.loads(ref_path.read_text(encoding="utf-8"))
current = run_northstar_bench()
report = compare(reference, current)
print("PASS" if report["passed"] else "FAIL", f"({report['failure_count']} differences outside tolerance)")
for item in report["failures"][:50]:
    print(f"- {item['path']}: ref={item['reference']:.6g} current={item['current']:.6g} diff={item['abs_diff']:.6g} tol={item['tolerance']}")
raise SystemExit(0 if report["passed"] else 1)
