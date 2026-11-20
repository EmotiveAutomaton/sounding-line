"""Constructed pooled-class odds, missing nuisance support and replay checks."""
import numpy as np
import pytest

from runners.drive.cards import week6_la9_pooled_fit_v1 as fit


A, B = "AMI/information_exchange", "ICSI/question"


def population():
    rows = []
    for m in range(16):
        for k in range(10):
            for label in (0, 1):
                tag = B if (k + label * 2) % 10 < 4 + 2 * label else A
                rows.append(dict(meeting=f"{m:02d}", id=f"{k}-{label}", pair=k, role=("control","case")[label],
                                 act_type=tag, label=label, numeric=[3+(k % 4), k % 2, *([0]*7)]))
    for label in (0,1):
        rows.append(dict(meeting="00", id=f"rare{label}", pair="z", role=("control","case")[label],
                         act_type="unmapped/z", label=label, numeric=[3,0,*([0]*7)]))
    support = {tag: {"distinct_utterances": sum(row["act_type"]==tag for row in rows), "eligible": True}
               for tag in (A,B)}
    support["AMI/social"] = {"distinct_utterances": 0, "eligible": False}
    return rows, support


def test_point_and_weighted_fit_use_the_original_solver_and_reference():
    rows, support = population()
    state = fit.state_for_fit(rows, support)
    actual = fit.coefficients(state)
    for inc in (True,False):
        model, template = fit.model.fitted(rows, inc)
        index = template[0].index(B)
        assert actual[str(inc)][A] == 0 and actual[str(inc)][B] > 0
        assert np.isclose(actual[str(inc)][B],model.coef_[0][(9 if inc else 8)+index-1])
    for ordinal in range(128):
        rng = np.random.default_rng(np.random.SeedSequence([fit.model.SEED,ordinal,6]))
        weights = np.bincount(rng.integers(16,size=16),minlength=16)[state["group"]]
        if not weights[-1]:
            break
    assert sum(weights[state["term"]==state["categories"].index("unmapped/z")]) == 0
    expected, _ = fit.model.fitted(rows, True, weights)
    scored = fit.coefficients(state,ordinal)
    assert np.isclose(scored["True"][B],expected.coef_[0][9])


def test_missing_target_or_reference_does_not_create_a_zero_coefficient():
    rows, support = population()
    for row in rows:
        if row["act_type"] == B and row["meeting"] != "00":
            row["act_type"] = A
    state = fit.state_for_fit(rows, support)
    for ordinal in range(128):
        values = fit.coefficients(state,ordinal)
        if values["True"][B] is None:
            assert values["True"][A] == 0
            break
    else:
        pytest.fail("Constructed allocation omitted none of the one-meeting class")
    support[A]["eligible"] = False
    state = fit.state_for_fit(rows,support)
    assert fit.coefficients(state)["True"][B] is None


def test_summary_lists_zero_counts_and_only_the_affected_interval_is_unavailable():
    rows,support = population()
    state = fit.state_for_fit(rows,support)
    point = fit.coefficients(state)
    bank = [{arm:dict(values) for arm,values in point.items()} for _ in range(2000)]
    bank[4]["True"][B] = None
    result = fit.assemble(state,support,2,point,bank)
    assert result["arms"]["True"][B]["absent_draws"] == [4]
    assert result["arms"]["False"][B]["status"] == "descriptive"
    assert result["arms"]["False"]["AMI/social"]["status"] == "below class floor"
    assert result["arms"]["True"][A]["status"] == "reference"
    assert sum(result["heldout_meetings_by_fold"]) == 16
    with pytest.raises(ValueError,match="Every registered"):
        fit.assemble(state,support,2,point,bank[:-1])


def test_pooled_fit_checkpoint_and_fresh_replay(tmp_path,monkeypatch):
    rows,support = population()
    monkeypatch.setattr(fit,"load",lambda _: (rows,support,2,{"parent":"constructed"}))
    cfg={"phase":"LA9","draws":2000,"max_new_draws":2}
    assert fit.execute(tmp_path,{},cfg)["completed"] == 2
    assert fit.execute(tmp_path,{},cfg)["completed"] == 4
    assert fit.verify(tmp_path,{},cfg)["completed"] == 2
    for i in range(2):
        p=f"draws/{i:04d}.json"
        fit.compare.compare_record(fit.stored(tmp_path/p),fit.stored(tmp_path/"independent-replay"/p))
    (tmp_path/"draws/0001.json").write_bytes(b"{}")
    with pytest.raises(ValueError,match="checkpoint bytes"):
        fit.execute(tmp_path,{},cfg)
