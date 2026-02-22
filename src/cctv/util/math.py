from __future__ import annotations

import math


def nice_step(rough: float) -> int:
    """Return the smallest 'nice' number (1/2/5 * 10^n) >= rough."""
    if rough <= 0:
        return 1
    exp = math.floor(math.log10(rough))
    base = 10 ** exp
    for m in (1, 2, 5, 10):
        step = m * base
        if step >= rough:
            return int(step)
    return int(base * 10)
