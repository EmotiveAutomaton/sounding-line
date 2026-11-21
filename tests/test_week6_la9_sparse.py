import numpy as np

from runners.drive.cards import week6_la9_sparse_v1 as sparse
from tests.test_week6_la9_pooled_fit import A, B, population


def test_same_coefficients_for_original_draws_in_both_arms():
    rows, support = population()
    state = sparse.original.state_for_fit(rows, support)
    matrices = sparse.prepare(state)
    for ordinal in (0,1,3,11,77):
        dense = sparse.original.coefficients(state, ordinal)
        fast = sparse.draw(state, matrices, ordinal)
        sparse.original.compare.compare_record(dense, fast)


def test_zero_weight_meetings_keep_missing_terms_undefined():
    rows, support = population()
    for row in rows:
        if row["act_type"] == B and row["meeting"] != "00":
            row["act_type"] = A
    state = sparse.original.state_for_fit(rows, support)
    matrices = sparse.prepare(state)
    n = state["meetings"]
    for ordinal in range(100):
        rng=np.random.default_rng(np.random.SeedSequence([sparse.original.model.SEED,ordinal,6]))
        if 0 not in rng.integers(n,size=n):
            fast = sparse.draw(state,matrices,ordinal)
            assert fast["True"][B] is None
            sparse.original.compare.compare_record(sparse.original.coefficients(state,ordinal),fast)
            return
    raise AssertionError("Constructed fixture lacked a meeting omission")
