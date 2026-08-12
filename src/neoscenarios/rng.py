from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Mapping, Sequence, TypeVar

T = TypeVar("T")


def _to_list(value):
    if isinstance(value, tuple):
        return [_to_list(v) for v in value]
    return value


def _to_tuple(value):
    if isinstance(value, list):
        return tuple(_to_tuple(v) for v in value)
    return value


@dataclass
class ScenarioRng:
    seed: int
    _draw_count: int = 0
    _random: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.seed = int(self.seed)
        self._random = random.Random(self.seed)

    @property
    def draw_count(self) -> int:
        return self._draw_count

    def _drawn(self, value: T) -> T:
        self._draw_count += 1
        return value

    def random(self) -> float: return self._drawn(self._random.random())
    def uniform(self, a: float, b: float) -> float: return self._drawn(self._random.uniform(a, b))
    def randint(self, a: int, b: int) -> int: return self._drawn(self._random.randint(a, b))
    def choice(self, values: Sequence[T]) -> T:
        if not values: raise ValueError("ScenarioRng.choice requires a non-empty sequence")
        return self._drawn(self._random.choice(values))

    def snapshot(self) -> dict:
        return {"seed": self.seed, "draw_count": self._draw_count, "state": _to_list(self._random.getstate())}

    def restore(self, payload: Mapping[str, object]) -> None:
        if int(payload["seed"]) != self.seed:
            raise ValueError("RNG snapshot seed does not match scenario seed")
        self._draw_count = int(payload["draw_count"])
        self._random.setstate(_to_tuple(payload["state"]))
