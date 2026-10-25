from collections import Counter
from itertools import product

import numpy as np
import pytest

from runners.drive.cards import week3_pieces_stats as w


def test_exact_transitions_first_last_and_seeded_reproducibility():
    source = list("ABACABAACBCABCA")
    for seed in range(100):
        result=w.markov_surrogate(source,np.random.default_rng(seed))
        assert len(result)==len(source) and result[0]==source[0] and result[-1]==source[-1]
        assert w.transition_counts(result)==w.transition_counts(source)
        assert result==w.markov_surrogate(source,np.random.default_rng(seed))


def test_uniform_conditional_law_against_enumerated_small_graph():
    source="AABABAA"
    valid={"".join(s) for s in product("AB",repeat=len(source)) if s[0]==source[0] and s[-1]==source[-1] and w.transition_counts(s)==w.transition_counts(source)}
    rng=np.random.default_rng(39)
    counts=Counter("".join(w.markov_surrogate(source,rng)) for _ in range(12000))
    assert set(counts)==valid
    expectation=12000/len(valid)
    # Fixed-seed calibration has a deliberately generous six-sigma envelope.
    assert max(abs(n-expectation) for n in counts.values()) < 6*np.sqrt(expectation)


def test_deterministic_chain_cannot_invent_a_piece():
    source=list("ABCABCABCABC")
    candidates=w.candidates([dict(session=str(i),writer=str(i),symbols=source) for i in range(10)],minimum_occurrences=10)
    null={piece:[row["count"]]*200 for piece,row in candidates.items()}
    assert w.discover(candidates,null)==[]


def test_planted_higher_order_piece_excludes_future_edits_from_primary():
    candidate={tuple("ABC"):dict(count=30,writers=10),tuple(["accept","edit_accepted","burst"]):dict(count=30,writers=10)}
    found=w.discover(candidate,{p:[5]*200 for p in candidate})
    assert len(found)==2 and sum(p["primary_eligible"] for p in found)==1
    # Equality with maximum is a fail even when the mean is small.
    assert not w.discover({tuple("ABC"):candidate[tuple("ABC")]},{tuple("ABC"):[0]*199+[30]})


def test_greedy_longest_global_not_left_to_right():
    covered, matches=w.greedy_cover(list("ABCDEF"),[list("ABC"),list("BCDEF")])
    assert covered==5 and matches[0]["start"]==1


def test_per_third_keeps_local_and_boundary_transitions():
    source=list("ABACABACABCABCBCABCABC")
    seconds=list(range(len(source)))
    result=w.surrogate(source,seconds,len(source),81,thirds=True)
    assert w.transition_counts(result)==w.transition_counts(source)
    for lo,hi in ((0,7),(7,14),(14,21)):
        assert w.transition_counts(result[lo:hi])==w.transition_counts(source[lo:hi])


def test_coverage_unit_weighting_and_both_gate_directions():
    rows=[dict(session=str(i),writer=str(i),events=100+i,real_covered=70,reference_covered=20) for i in range(10)]
    positive=w.coverage_interval(rows)
    assert positive["state"]=="positive" and positive["estimate"]==pytest.approx(500/1045)
    assert w.route(positive,positive,20)["next"]=="pieces"
    assert w.route(positive,positive,19)["next"]=="WB1b"
    null=w.coverage_interval([dict(r,real_covered=20) for r in rows])
    assert null["estimate"]==0 and null["state"]=="not_detected"
    assert w.route(positive,null,20,coarse=True)["next"]=="single_events"
    negative=w.coverage_interval([dict(r,real_covered=0) for r in rows])
    assert negative["state"]=="negative"
