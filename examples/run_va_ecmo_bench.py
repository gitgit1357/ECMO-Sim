from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from neocirculation.va_ecmo_bench import (
    format_closed_loop_va_ecmo_report,
    run_closed_loop_va_ecmo_bench,
)

points = run_closed_loop_va_ecmo_bench()
print(format_closed_loop_va_ecmo_report(points))
