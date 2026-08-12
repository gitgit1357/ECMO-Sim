from __future__ import annotations

from concurrent.futures import Future, ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
import multiprocessing
from typing import Optional, Tuple

from neocoupling import run_coupled_neonate
from neolung import LungParameters
from neolung.gas_exchange import GasExchangeParameters
from neoventilator import PressureControlSettings


NativeCacheKey = Tuple[object, ...]


@dataclass(frozen=True)
class NativeSolveRequest:
    revision: int
    cache_key: NativeCacheKey
    blood_volume_delta_ml: float


@dataclass(frozen=True)
class NativeSolveResult:
    revision: int
    cache_key: NativeCacheKey
    blood_volume_delta_ml: float
    physiology: object


def solve_native_request(request: NativeSolveRequest) -> NativeSolveResult:
    """Pure worker entry point: only immutable primitives enter the solver."""
    (
        weight_kg,
        lung_run_s,
        circulation_run_s,
        peep_cmh2o,
        airway_opening_pressure_cmh2o,
        fio2,
        pc_pip,
        pc_peep,
        pc_rate,
        pc_ti,
        pc_fio2,
        pc_rise,
        pc_fall,
        lv_contractility_scale,
        rv_contractility_scale,
    ) = request.cache_key
    lp = LungParameters(
        weight_kg=weight_kg,
        peep_cmh2o=peep_cmh2o,
        airway_opening_pressure_cmh2o=airway_opening_pressure_cmh2o,
    )
    gp = GasExchangeParameters(weight_kg=weight_kg, fio2=fio2)
    pressure_control = None
    if pc_pip is not None:
        pressure_control = PressureControlSettings(
            pip_cmh2o=float(pc_pip),
            peep_cmh2o=float(pc_peep),
            rate_bpm=float(pc_rate),
            inspiratory_time_s=float(pc_ti),
            fio2=float(pc_fio2),
            rise_time_s=float(pc_rise),
            fall_time_s=float(pc_fall),
        )
    physiology = run_coupled_neonate(
        lung_params=lp,
        gas_params=gp,
        duration_lung_s=lung_run_s,
        duration_circulation_s=circulation_run_s,
        blood_volume_delta_ml=request.blood_volume_delta_ml,
        pressure_control=pressure_control,
        lv_contractility_scale=float(lv_contractility_scale),
        rv_contractility_scale=float(rv_contractility_scale),
    )
    return NativeSolveResult(
        revision=request.revision,
        cache_key=request.cache_key,
        blood_volume_delta_ml=request.blood_volume_delta_ml,
        physiology=physiology,
    )


class NativePhysiologyAsyncRunner:
    """Single active solve plus one trailing-edge latest-pending request."""

    def __init__(self, executor_kind: str = "thread") -> None:
        if executor_kind not in {"thread", "process"}:
            raise ValueError("executor_kind must be 'thread' or 'process'")
        self.executor_kind = executor_kind
        self._executor = None
        self._active_request: Optional[NativeSolveRequest] = None
        self._active_future: Optional[Future] = None
        self._pending_request: Optional[NativeSolveRequest] = None
        self._started_revisions: list[int] = []

    @property
    def active_revision(self) -> Optional[int]:
        return self._active_request.revision if self._active_request is not None else None

    @property
    def pending_revision(self) -> Optional[int]:
        return self._pending_request.revision if self._pending_request is not None else None

    @property
    def started_revisions(self) -> Tuple[int, ...]:
        return tuple(self._started_revisions)

    def submit_latest(self, request: NativeSolveRequest) -> None:
        if self._active_future is None:
            self._start(request)
            return
        # Never queue intermediate work. The newest request replaces the one
        # pending behind the uncancelable active solve.
        self._pending_request = request

    def poll_completed(self) -> Optional[NativeSolveResult]:
        future = self._active_future
        if future is None or not future.done():
            return None
        result = future.result()
        self._active_future = None
        self._active_request = None
        pending = self._pending_request
        self._pending_request = None
        if pending is not None:
            self._start(pending)
        return result

    def _ensure_executor(self):
        if self._executor is None:
            if self.executor_kind == "process":
                self._executor = ProcessPoolExecutor(max_workers=1, mp_context=multiprocessing.get_context("spawn"))
            else:
                self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="native-physiology")
        return self._executor

    def _start(self, request: NativeSolveRequest) -> None:
        self._started_revisions.append(request.revision)
        self._active_request = request
        self._active_future = self._ensure_executor().submit(solve_native_request, request)

    def shutdown(self) -> None:
        if self._executor is not None:
            self._executor.shutdown(wait=False, cancel_futures=True)
