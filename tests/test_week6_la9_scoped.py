import numpy as np
from sklearn.base import clone

from runners.drive.cards import week6_la9_scoped_v1 as study
from tests.test_week6_la9_pooled_fit import A, B, population


def test_whole_meeting_allocation_uses_only_the_original_corpus_metadata():
    metadata={str(i):{"corpus":"AMI" if i<24 else "ICSI"} for i in range(40)}
    first,allocation=study.roster(metadata)
    assert len(first)==len(set(first))==10
    assert allocation=={"AMI":6,"ICSI":4}
    assert study.roster(dict(reversed(list(metadata.items()))))==(first,allocation)


def test_fixed_parent_coding_and_distinct_utterance_support_in_sample():
    rows,support=population()
    chosen={f"{i:02d}" for i in range(8)}
    base=study.original.state_for_fit(rows,support)
    state,counts,unassigned=study.subset_fit(rows,support,chosen)
    keep=np.array([r["meeting"] in chosen for r in rows])
    assert state["meetings"]==8 and sum(state["fold_counts"])==8
    assert state["categories"]==base["categories"]
    assert counts[A]["distinct_utterances"]+counts[B]["distinct_utterances"]+unassigned==len({(r["meeting"],r["id"]) for r in rows if r["meeting"] in chosen})
    for key,(model,x,_) in state["arms"].items():
        np.testing.assert_array_equal(x,base["arms"][key][1][keep])
        direct=clone(model).fit(x,state["y"])
        np.testing.assert_allclose(direct.coef_,model.coef_,atol=1e-7,rtol=0)
    tiny,low_support,_=study.subset_fit(rows,support,{"01"})
    assert not tiny["eligible"] and not any(v["eligible"] for v in low_support.values())
