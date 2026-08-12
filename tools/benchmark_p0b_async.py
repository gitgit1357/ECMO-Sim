from __future__ import annotations

from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from neogui.ecmo_workspace import EcmoWorkspaceModel


def main() -> None:
    model = EcmoWorkspaceModel()
    patient = model.dynamic.coupled.patient
    routine = []
    for _ in range(10):
        start = time.perf_counter()
        model.advance(1.0)
        routine.append(time.perf_counter() - start)

    patient.record_blood_loss(20.0)
    start = time.perf_counter()
    model.advance(1.0)
    invalidation_callback = time.perf_counter() - start

    refresh_callbacks = []
    started = time.perf_counter()
    next_refresh = started + 1.0
    while model.native_physiology_update_pending and time.perf_counter() - started < 10.0:
        time.sleep(0.005)
        now = time.perf_counter()
        if now >= next_refresh:
            callback_start = time.perf_counter()
            model.advance(1.0)
            refresh_callbacks.append(time.perf_counter() - callback_start)
            next_refresh += 1.0

    if model.native_physiology_update_pending:
        model.advance(0.0)

    print(f"routine mean: {statistics.mean(routine) * 1000:.2f} ms")
    print(f"routine max: {max(routine) * 1000:.2f} ms")
    print(f"forced-invalidation callback: {invalidation_callback * 1000:.2f} ms")
    print(f"native settle: {(time.perf_counter() - started) * 1000:.2f} ms")
    if refresh_callbacks:
        print(f"refresh callback max while solving: {max(refresh_callbacks) * 1000:.2f} ms")
    print(f"pending after benchmark: {model.native_physiology_update_pending}")
    model.close()


if __name__ == "__main__":
    main()
