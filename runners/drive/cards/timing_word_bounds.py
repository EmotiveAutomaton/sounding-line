"""Probability enclosures for the next casefolded TOKEN, not a corpus scorer.

DESIGN CHECK: LESSONS 3-5 reread for this design, 2026-10-19. Under both
NULL and ALTERNATIVE scientific effects, the same finite probability-tree
answers must be enclosed. Missing branches, aliases, separators, UTF-8 tails
and context overflow remain unresolved mass, never zero or an imputed score.
An empty conditioning event refuses. A wide log-probability interval refuses
point-score admission. No outcome selects paths or tolerance. Native use and
scientific admission require separate validation and cost accounting.

The oracle supplies nonnegative finite weights for EVERY token, including EOS.
Its normalized weights define the numerical reference distribution. Outward
rounding encloses arithmetic on that distribution, not neural-model error.
Each frontier node is a disjoint token cylinder; no hidden states are merged.
"""
from __future__ import annotations

import codecs
import heapq
import math

from .timing_text import TOKEN, WORD

REJECT, PENDING, ACCEPT = -1, 0, 1


def down(value):
    return max(0., math.nextafter(value, -math.inf))


def up(value):
    return math.nextafter(value, math.inf)


def prefix_state(data, required, final=False):
    """An exact observed byte prefix is a conditioning event, not new text."""
    size = min(len(data), len(required))
    if data[:size] != required[:size]:
        return REJECT
    if len(data) >= len(required):
        return ACCEPT
    return REJECT if final else PENDING


def word_state(data, required, folded, final=False):
    """Joint event: required bytes, then the first original TOKEN == folded.

    Incremental UTF-8 decoding retains incomplete bytes. Invalid sequences use
    GPT-2's replacement decoding. Whitespace/underscores precede the next TOKEN;
    apostrophes after a word need lookahead, including across native tokens.
    """
    before = prefix_state(data, required, final)
    if before != ACCEPT:
        return before
    decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
    text = decoder.decode(data[len(required):], final=final)
    match = TOKEN.search(text)
    if match is None:
        return REJECT if final else PENDING
    value = match.group().casefold()
    if not WORD.fullmatch(match.group()):
        return ACCEPT if value == folded else REJECT
    if not folded.startswith(value):
        return REJECT
    suffix = text[match.end():]
    complete = final or bool(suffix and suffix not in ("'", '\u2019'))
    if complete:
        return ACCEPT if value == folded else REJECT
    # A single trailing apostrophe may join the next alphanumeric character.
    # It may instead become a separate punctuation TOKEN, so keep both paths.
    return PENDING


def _bounds(accepted, frontier, blocked):
    lower = down(math.fsum(accepted)) if accepted else 0.
    upper = min(1., up(math.fsum(frontier + blocked))) if frontier or blocked else 0.
    return lower, upper


def enclose(oracle, pieces, eos, classify, *, max_nodes, max_depth,
            tolerance_nats=1e-4):
    """Best-first exact-event search with an explicit unexpanded-mass bound.

    Each oracle row must contain precisely pieces.keys() plus EOS. Nodes at
    either work or context limits remain in the bound. The returned interval
    can be wide even after a successful execution. No midpoint is produced.
    """
    if (type(max_nodes) is not int or max_nodes < 0 or type(max_depth) is not int
            or max_depth < 0 or not math.isfinite(tolerance_nats)
            or tolerance_nats <= 0 or eos in pieces
            or any(not isinstance(p, bytes) or not p for p in pieces.values())):
        raise ValueError('invalid event search configuration')
    identities = set(pieces) | {eos}
    # Heap entries: highest upper mass first, stable insertion tie break.
    heap = [(-1., 0, (), b'', 1., 1.)]
    accepted_lo, accepted_hi, blocked = [], [], []
    nodes = 0
    sequence = 1
    reason = 'work_limit'
    while heap and nodes < max_nodes:
        lower, upper = _bounds(accepted_lo, accepted_hi + [-r[0] for r in heap], blocked)
        if lower > 0 and math.log(upper / lower) <= tolerance_nats:
            reason = 'precision'
            break
        _, _, path, data, low, high = heapq.heappop(heap)
        state = classify(data, False)
        if state == ACCEPT:
            accepted_lo.append(low)
            accepted_hi.append(high)
            continue
        if state == REJECT:
            continue
        if state != PENDING:
            raise ValueError('invalid event classification')
        if len(path) >= max_depth:
            blocked.append(high)
            continue
        weights = oracle(path)
        if set(weights) != identities or any(not math.isfinite(v) or v < 0 for v in weights.values()):
            raise ValueError('incomplete or invalid next-token distribution')
        total = math.fsum(weights.values())
        if not math.isfinite(total) or total <= 0:
            raise ValueError('empty next-token distribution')
        total_lo, total_hi = down(total), up(total)
        if total_lo <= 0:
            raise ValueError('distribution normalization underflow')
        nodes += 1
        for token in sorted(identities):
            weight = weights[token]
            if weight == 0:
                continue
            child_lo = down(low * down(weight / total_hi))
            child_hi = min(1., up(high * up(weight / total_lo)))
            ended = token == eos
            child_data = data if ended else data + pieces[token]
            disposition = classify(child_data, ended)
            if disposition == ACCEPT:
                accepted_lo.append(child_lo)
                accepted_hi.append(child_hi)
            elif disposition == PENDING and not ended:
                heapq.heappush(heap, (-child_hi, sequence, path + (token,), child_data, child_lo, child_hi))
                sequence += 1
            elif disposition != REJECT:
                raise ValueError('invalid terminal event classification')
    if not heap:
        reason = 'context_limit' if blocked else 'exhausted'
    lower, upper = _bounds(accepted_lo, accepted_hi + [-r[0] for r in heap], blocked)
    return dict(lower=lower, upper=upper, expanded_nodes=nodes,
                frontier_nodes=len(heap), context_limited_nodes=len(blocked),
                unresolved_mass=min(1., up(math.fsum([-r[0] for r in heap] + blocked))) if heap or blocked else 0.,
                stopping_reason=reason,
                tolerance_met=lower > 0 and math.log(upper / lower) <= tolerance_nats)


def conditional_bounds(numerator, denominator, tolerance_nats=1e-4):
    """A/B where A is a subset of B; impossible/wide events give no point."""
    a, b = numerator, denominator
    if not (0 <= a['lower'] <= a['upper'] <= 1 and 0 <= b['lower'] <= b['upper'] <= 1):
        raise ValueError('invalid probability enclosure')
    if b['upper'] == 0:
        raise ValueError('impossible observed conditioning prefix')
    if a['lower'] > b['upper']:
        raise ValueError('joint event is not a subset of conditioning event')
    lower = down(a['lower'] / b['upper'])
    upper = min(1., up(a['upper'] / b['lower'])) if b['lower'] > 0 else 1.
    nll_low = -math.log(upper) if upper > 0 else None
    nll_high = -math.log(lower) if lower > 0 else None
    admitted = nll_low is not None and nll_high is not None and nll_high - nll_low <= tolerance_nats
    return dict(lower=lower, upper=upper, nll_lower=nll_low, nll_upper=nll_high,
                point_score_admitted=admitted, scientific_admission=False)


def next_word_bounds(oracle, pieces, eos, required, folded, **options):
    if not isinstance(required, bytes) or not folded or folded.casefold() != folded:
        raise ValueError('exact prefix bytes and casefolded target required')
    # The same native prefix can be reused, but never combine distinct paths.
    denominator = (dict(lower=1., upper=1., expanded_nodes=0, frontier_nodes=0,
                        context_limited_nodes=0, unresolved_mass=0., stopping_reason='empty_prefix', tolerance_met=True)
                   if not required else enclose(oracle, pieces, eos,
                       lambda data, final: prefix_state(data, required, final), **options))
    numerator = enclose(oracle, pieces, eos,
                        lambda data, final: word_state(data, required, folded, final), **options)
    return dict(numerator=numerator, denominator=denominator,
                conditional=conditional_bounds(numerator, denominator, options.get('tolerance_nats', 1e-4)))
