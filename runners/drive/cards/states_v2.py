"""Correct percentile-interval validation; original live source stays frozen.

DESIGN CHECK: LESSONS 3-5 read 2026-10-17. NULL: intervals including zero
route by the declared point direction. ALTERNATIVE: same/reverse exclusion is
positive/negative. Bootstrap intervals need not contain the observed point.
Invalid means nonfinite input, reversed bounds or a failed validity check,
never point-estimate exclusion. Exact-zero and reverse-direction bands match
the ratified contract. Family and extension routing are unchanged.
"""
from __future__ import annotations
import math
from .states import STATES, family_progress, texture_order, instrument_state


def contrast_state(effect, ci_low, ci_high, expected_direction=1, valid=True):
    if expected_direction not in (-1, 1):
        raise ValueError('Expected direction must be -1 or +1')
    if not valid:
        return 'invalid'
    try:
        effect, low, high = (float(x) for x in (effect, ci_low, ci_high))
    except (ValueError, TypeError):
        return 'invalid'
    if not all(math.isfinite(x) for x in (effect, low, high)) or low > high:
        return 'invalid'
    if expected_direction == -1:
        effect, low, high = -effect, -high, -low
    if low > 0:
        return 'positive'
    if high < 0:
        return 'negative'
    return 'marginal' if effect > 0 else 'null'


classify = contrast_state
