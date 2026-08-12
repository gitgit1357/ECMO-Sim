from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from threading import RLock
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Optional, Tuple


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze_json(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(v) for v in value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"event payload value is not JSON-compatible: {type(value).__name__}")


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _thaw_json(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(v) for v in value]
    return value


@dataclass(frozen=True)
class EventRecord:
    """Immutable machine-readable event emitted by learner/system actions.

    ``timestamp`` records wall-clock occurrence time. Simulation time belongs in
    ``metadata['simulation_time_s']`` so the stable Phase 1d schema does not
    conflate wall time with the simulator clock.
    """

    timestamp: datetime
    event_type: str
    source: str
    target: str
    action: str
    old_value: Any = None
    new_value: Any = None
    revision: Optional[int] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None:
            raise ValueError("EventRecord.timestamp must be timezone-aware")
        for name in ("event_type", "source", "target", "action"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"EventRecord.{name} must be a non-empty string")
        object.__setattr__(self, "old_value", _freeze_json(self.old_value))
        object.__setattr__(self, "new_value", _freeze_json(self.new_value))
        object.__setattr__(self, "metadata", _freeze_json(dict(self.metadata)))

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "timestamp": self.timestamp.astimezone(timezone.utc).isoformat(),
            "event_type": self.event_type,
            "source": self.source,
            "target": self.target,
            "action": self.action,
            "old_value": _thaw_json(self.old_value),
            "new_value": _thaw_json(self.new_value),
            "revision": self.revision,
            "metadata": _thaw_json(self.metadata),
        }
        # Fail early if a future event tries to smuggle non-portable state into
        # the durable record contract.
        json.dumps(payload, sort_keys=True)
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "EventRecord":
        return cls(
            timestamp=datetime.fromisoformat(str(payload["timestamp"])),
            event_type=str(payload["event_type"]),
            source=str(payload["source"]),
            target=str(payload["target"]),
            action=str(payload["action"]),
            old_value=payload.get("old_value"),
            new_value=payload.get("new_value"),
            revision=payload.get("revision"),
            metadata=dict(payload.get("metadata", {})),
        )


class EventStream:
    """Small append-only in-memory event stream.

    The stream is thread-safe so future educator/network/scenario surfaces can
    emit safely, but it deliberately owns no scenario progression or scoring.
    """

    def __init__(self, records: Iterable[EventRecord] = ()) -> None:
        self._lock = RLock()
        self._records: list[EventRecord] = list(records)

    def emit(
        self,
        *,
        event_type: str,
        source: str,
        target: str,
        action: str,
        old_value: Any = None,
        new_value: Any = None,
        revision: Optional[int] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> EventRecord:
        record = EventRecord(
            timestamp=timestamp or _utc_now(),
            event_type=event_type,
            source=source,
            target=target,
            action=action,
            old_value=old_value,
            new_value=new_value,
            revision=revision,
            metadata=dict(metadata or {}),
        )
        return self.append(record)

    def append(self, record: EventRecord) -> EventRecord:
        if not isinstance(record, EventRecord):
            raise TypeError("EventStream only accepts EventRecord instances")
        # Serialization is part of the contract; validate before accepting.
        record.to_dict()
        with self._lock:
            self._records.append(record)
        return record

    @property
    def records(self) -> Tuple[EventRecord, ...]:
        with self._lock:
            return tuple(self._records)

    @property
    def latest(self) -> Optional[EventRecord]:
        with self._lock:
            return self._records[-1] if self._records else None

    def to_json_lines(self) -> str:
        with self._lock:
            return "\n".join(json.dumps(record.to_dict(), sort_keys=True) for record in self._records)
