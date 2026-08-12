from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"lab value is not JSON-compatible: {type(value).__name__}")


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _thaw(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_thaw(v) for v in value]
    return value


@dataclass(frozen=True)
class LabResult:
    result_id: str
    panel_id: str
    panel_name: str
    sample_site: str
    sample_time_s: float
    available_time_s: float
    values: Mapping[str, Any]
    units: Mapping[str, str] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("result_id", "panel_id", "panel_name", "sample_site"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} must be non-empty")
        sample = float(self.sample_time_s)
        available = float(self.available_time_s)
        if available < sample:
            raise ValueError("available_time_s cannot precede sample_time_s")
        object.__setattr__(self, "sample_time_s", sample)
        object.__setattr__(self, "available_time_s", available)
        object.__setattr__(self, "values", _freeze(dict(self.values)))
        object.__setattr__(self, "units", _freeze(dict(self.units)))
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata)))

    def is_available(self, simulation_time_s: float) -> bool:
        return float(simulation_time_s) >= self.available_time_s

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_id": self.result_id,
            "panel_id": self.panel_id,
            "panel_name": self.panel_name,
            "sample_site": self.sample_site,
            "sample_time_s": self.sample_time_s,
            "available_time_s": self.available_time_s,
            "values": _thaw(self.values),
            "units": _thaw(self.units),
            "metadata": _thaw(self.metadata),
        }


class LabQueue:
    """Deterministic ordered-test queue with frozen values at sample time."""

    def __init__(self) -> None:
        self._next_id = 1
        self._results: list[LabResult] = []

    def order(
        self,
        *,
        panel_id: str,
        panel_name: str,
        sample_site: str,
        sample_time_s: float,
        turnaround_s: float,
        values: Mapping[str, Any],
        units: Mapping[str, str] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> LabResult:
        turnaround = float(turnaround_s)
        if turnaround < 0.0:
            raise ValueError("turnaround_s must be non-negative")
        result = LabResult(
            result_id=f"lab-{self._next_id:04d}",
            panel_id=panel_id,
            panel_name=panel_name,
            sample_site=sample_site,
            sample_time_s=float(sample_time_s),
            available_time_s=float(sample_time_s) + turnaround,
            values=values,
            units=units or {},
            metadata=metadata or {},
        )
        self._next_id += 1
        self._results.append(result)
        return result

    @property
    def results(self) -> tuple[LabResult, ...]:
        return tuple(self._results)

    def pending(self, simulation_time_s: float) -> tuple[LabResult, ...]:
        return tuple(r for r in self._results if not r.is_available(simulation_time_s))

    def available(self, simulation_time_s: float) -> tuple[LabResult, ...]:
        return tuple(r for r in self._results if r.is_available(simulation_time_s))
