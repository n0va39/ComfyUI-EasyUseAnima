"""Per-request wildcard option selection."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, cast

from .models import WildcardOption
from .seed import normalize_seed

if TYPE_CHECKING:
    import numpy as np  # pyright: ignore[reportMissingImports]

__all__ = ()


class _Selector:
    def __init__(self, seed: int, sequential: bool):
        self.seed = normalize_seed(seed)
        self.sequential = sequential
        self.rng: np.random.Generator | None
        if self.sequential:
            self.rng = None
        else:
            import numpy as np  # pyright: ignore[reportMissingImports]

            self.rng = np.random.Generator(np.random.PCG64(self.seed))

    def count_from_range(self, minimum: int, maximum: int) -> int:
        minimum = max(0, minimum)
        maximum = max(minimum, maximum)
        if minimum == maximum:
            return minimum
        if self.sequential:
            return minimum + (self.seed % (maximum - minimum + 1))
        rng = cast("np.random.Generator", self.rng)
        return int(rng.integers(minimum, maximum + 1))

    def choose_one(self, options: Sequence[WildcardOption]) -> WildcardOption | None:
        selected = self.choose_many(options, 1)
        return selected[0] if selected else None

    def choose_many(
        self,
        options: Sequence[WildcardOption],
        count: int,
    ) -> list[WildcardOption]:
        if not options or count <= 0:
            return []
        if self.sequential:
            count = min(count, len(options))
            start = self.seed % len(options)
            return [options[(start + offset) % len(options)] for offset in range(count)]

        weights = [max(0.0, option.weight) for option in options]
        positive = [
            (option, weight)
            for option, weight in zip(options, weights)
            if weight > 0
        ]
        if positive:
            pool = [option for option, _weight in positive]
            pool_weights = [weight for _option, weight in positive]
        else:
            pool = list(options)
            pool_weights = None

        count = min(count, len(pool))
        probabilities = None
        if pool_weights is not None:
            total = sum(pool_weights)
            probabilities = [weight / total for weight in pool_weights]
        rng = cast("np.random.Generator", self.rng)
        indices = rng.choice(len(pool), size=count, replace=False, p=probabilities)
        return [pool[int(index)] for index in indices]
