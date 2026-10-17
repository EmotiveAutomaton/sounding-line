"""Shared October 17 descriptive state and family routing contract.

DESIGN CHECK: 2026-10-17, LESSONS sections 3-5 read. NULL: an interval
including zero with a zero/opposite point estimate is null; a same-direction
point is marginal. ALTERNATIVE: an interval excluding zero in the declared
direction is positive, and in the opposite direction negative. Invalid inputs
never become null. Bands are exhaustive, including exact zero boundaries.
These states authorize only the packet's descriptive follow-ups, never admission.
"""
from __future__ import annotations

import math

STATES = frozenset({'positive', 'marginal', 'null', 'negative', 'invalid', 'blind', 'blocked'})


def contrast_state(effect, ci_low, ci_high, expected_direction=1, valid=True):
    if expected_direction not in (-1, 1):
        raise ValueError('Expected direction must be -1 or +1')
    if not valid:
        return 'invalid'
    try:
        values = tuple(float(x) for x in (effect, ci_low, ci_high))
    except (ValueError, TypeError):
        return 'invalid'
    effect, low, high = values
    if not all(math.isfinite(x) for x in values) or not low <= effect <= high:
        return 'invalid'
    if expected_direction == -1:
        effect, low, high = -effect, -high, -low
    if low > 0:
        return 'positive'
    if high < 0:
        return 'negative'
    return 'marginal' if effect > 0 else 'null'


classify = contrast_state


def instrument_state(valid, usable=True):
    return 'positive' if valid and usable else 'invalid'


def family_progress(ladder, landed):
    """Only the resolved prefix counts: completion order cannot stop a family.

    Each entry: state, optional extension_state, extension_pending.
    Invalid/blocked/blind do not increment or reset. Pending gaps stop traversal.
    """
    count = 0
    resolved = []
    for card in ladder:
        if card not in landed:
            break
        row = landed[card]
        state = row['state']
        if state not in STATES:
            raise ValueError(f'Unknown state for {card}')
        if row.get('extension_pending') and state in {'positive', 'marginal'}:
            break
        if state == 'marginal':
            state = 'positive' if row.get('extension_state') == 'positive' else 'null'
        if state in {'positive', 'negative'}:
            count = 0
        elif state == 'null':
            count += 1
        resolved.append(card)
        if count >= 6:
            break
    return {'consecutive_nulls': count, 'stopped': count >= 6, 'resolved_prefix': resolved}


def texture_order(state, *, extension_done=False, blind=False, handling=False):
    if state == 'negative':
        return ['s']
    if state != 'positive' or not extension_done:
        return []
    moves = ['s', 'p', 'r']
    return (['c'] + moves if blind else moves + ['c']) if handling else moves
