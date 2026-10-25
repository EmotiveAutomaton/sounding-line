"""WB1 exact transition-conditional sequence controls and held-writer coverage.

DESIGN CHECK: LESSONS 3-5 and CONTROLS read 2026-10-25. A deterministic
first-order chain has identical real/reference counts and cannot discover a
piece. Planted dependencies above order one may exceed the exact-transition
reference. Fixed first/last state, length and every transition multiplicity
must survive; their failure invalidates the instrument, not the theory.
Future-linked accepted-edit tokens never enter primary pieces. Discovery and
test writers are disjoint. The positive route needs >=20 eligible pieces AND
both coverage intervals strictly above zero; everything else routes to the
separately frozen coarser variant, never to a silently relaxed threshold.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import math

import numpy as np

SEED = 20261026


def transition_counts(sequence):
    return Counter(zip(sequence[:-1], sequence[1:]))


def markov_surrogate(sequence, rng):
    """Uniform Euler trail conditional on exact transitions and initial state.

    Wilson's loop-erased directed walk samples the last-exit tree rooted at the
    fixed final state. At each other state that tree edge is last; all remaining
    outgoing edge occurrences are uniformly permuted. Walking these stacks gives
    a uniform labelled Euler trail; parallel-edge multiplicity is constant across
    unlabelled sequences, so the conditional sequence law is uniform as well.
    Ordinary randomly shuffled Hierholzer output is deliberately not used: exact
    edge preservation by itself would not establish a uniform conditional law.
    """
    sequence = list(sequence)
    if len(sequence) < 3:
        return sequence
    adjacency = defaultdict(list)
    for a, b in zip(sequence[:-1], sequence[1:]):
        adjacency[a].append(b)
    root = sequence[-1]
    in_tree = {root}
    last_exit = {}
    for start in sorted(set(sequence)):
        if start in in_tree:
            continue
        walk = [start]
        positions = {start: 0}
        while walk[-1] not in in_tree:
            here = walk[-1]
            options = adjacency[here]
            if not options:
                raise ValueError("transition graph cannot reach final state")
            nxt = options[int(rng.integers(len(options)))]
            if nxt in positions:
                cut = positions[nxt]
                for removed in walk[cut+1:]:
                    positions.pop(removed)
                walk = walk[:cut+1]
            else:
                positions[nxt] = len(walk)
                walk.append(nxt)
        for a, b in zip(walk[:-1], walk[1:]):
            last_exit[a] = b
            in_tree.add(a)
    stacks = {}
    for node, outgoing in adjacency.items():
        choices = list(outgoing)
        if node != root:
            choices.remove(last_exit[node])
        rng.shuffle(choices)
        if node != root:
            choices.append(last_exit[node])
        stacks[node] = choices
    used = Counter()
    result = [sequence[0]]
    for _ in range(len(sequence)-1):
        here = result[-1]
        if used[here] >= len(stacks.get(here, ())):
            raise ValueError("conditional walk ended before consuming all edges")
        result.append(stacks[here][used[here]])
        used[here] += 1
    if result[0] != sequence[0] or result[-1] != sequence[-1] or transition_counts(result) != transition_counts(sequence):
        raise ValueError("conditional surrogate changed its sufficient statistics")
    return result


def surrogate(sequence, seconds, duration, seed, thirds=False):
    rng = np.random.default_rng(seed)
    if not thirds:
        return markov_surrogate(sequence, rng)
    if len(sequence) != len(seconds) or not math.isfinite(duration) or duration < 0:
        raise ValueError("invalid session-time thirds")
    labels = [min(2, int(3*t/duration)) if duration else 0 for t in seconds]
    if labels != sorted(labels) or any(t < 0 or t > duration+1e-6 for t in seconds):
        raise ValueError("invalid chronological event thirds")
    result = []
    for third in range(3):
        part = [token for token, label in zip(sequence, labels) if label == third]
        result.extend(markov_surrogate(part, rng))
    if transition_counts(result) != transition_counts(sequence):
        raise ValueError("per-third conditioning changed boundary transitions")
    return result


def derived_seed(scope, draw, session):
    payload = json.dumps([SEED, scope, draw, session], separators=(",", ":")).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "little")


def ngrams(sequence):
    for size in range(3, 7):
        for start in range(len(sequence)-size+1):
            yield tuple(sequence[start:start+size])


def candidates(sessions, minimum_occurrences=30, minimum_writers=10):
    counts, writers = Counter(), defaultdict(set)
    for row in sorted(sessions, key=lambda r: r["session"]):
        local = Counter(ngrams(row["symbols"]))
        counts.update(local)
        for piece in local:
            writers[piece].add(row["writer"])
    return {piece: dict(count=counts[piece], writers=len(writers[piece])) for piece in sorted(counts)
            if counts[piece] >= minimum_occurrences and len(writers[piece]) >= minimum_writers}


def discover(candidate_rows, surrogate_counts):
    result = []
    for piece in sorted(candidate_rows):
        counts = np.asarray(surrogate_counts[piece], dtype=float)
        if counts.ndim != 1 or not len(counts) or not np.isfinite(counts).all() or np.any(counts < 0):
            raise ValueError("incomplete or invalid discovery reference")
        real = candidate_rows[piece]["count"]
        mean, maximum = float(counts.mean()), int(counts.max())
        if real >= 2*mean and real > maximum:
            result.append(dict(symbols=list(piece), real_count=real, discovery_writers=candidate_rows[piece]["writers"],
                               reference_mean=mean, reference_max=maximum,
                               primary_eligible="edit_accepted" not in piece))
    return result


def greedy_cover(sequence, pieces):
    """Longest candidate globally first, then earliest position, then lexical id."""
    ordered = sorted(set(tuple(p) for p in pieces), key=lambda p: (-len(p), p))
    by_size = defaultdict(set)
    for piece in ordered:
        if not 3 <= len(piece) <= 6:
            raise ValueError("piece must contain three through six symbols")
        by_size[len(piece)].add(piece)
    occupied = np.zeros(len(sequence), bool)
    matches = []
    for size in sorted(by_size, reverse=True):
        for start in range(len(sequence)-size+1):
            if occupied[start:start+size].any():
                continue
            piece = tuple(sequence[start:start+size])
            if piece in by_size[size]:
                occupied[start:start+size] = True
                matches.append(dict(start=start, stop=start+size, symbols=list(piece)))
    return int(occupied.sum()), sorted(matches, key=lambda r: r["start"])


def coverage_interval(rows, draws=2000, seed=SEED):
    """Event-weighted difference; resample whole real writers with all sessions."""
    groups = defaultdict(lambda: np.zeros(2, float))
    for row in sorted(rows, key=lambda r: r["session"]):
        if row["events"] < 0 or not 0 <= row["real_covered"] <= row["events"] or not 0 <= row["reference_covered"] <= row["events"]:
            raise ValueError("invalid coverage counts")
        groups[row["writer"]] += [row["real_covered"]-row["reference_covered"], row["events"]]
    data = np.asarray([groups[w] for w in sorted(groups) if groups[w][1] > 0])
    if len(data) < 3:
        return dict(state="unsupported", reason="fewer than three supported test writers", writers=len(data))
    estimate = float(data[:,0].sum()/data[:,1].sum())
    rng = np.random.default_rng(seed)
    boot = []
    for _ in range(draws):
        chosen = data[rng.integers(0,len(data),len(data))].sum(0)
        boot.append(float(chosen[0]/chosen[1]))
    low, high = np.quantile(boot,[.025,.975]).tolist()
    return dict(estimate=estimate,ci_low=low,ci_high=high,writers=len(data),events=int(data[:,1].sum()),
                state="positive" if low > 0 else "negative" if high < 0 else "not_detected",
                bootstrap_draws=draws,seed=seed,weighting="event-weighted; whole-writer cluster resampling")


def route(primary, sensitivity, n_eligible, coarse=False):
    passed = n_eligible >= 20 and primary.get("state") == "positive" and sensitivity.get("state") == "positive"
    return dict(coverage_gate_passed=passed, minimum_primary_pieces=20, primary_pieces=n_eligible,
                next="pieces" if passed else "single_events" if coarse else "WB1b",
                full_card_requires="effect vectors, consistency control and discovery-only classes")
