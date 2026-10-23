import copy
import numpy as np
import pytest

from runners.drive.cards import week_directed_reading as base
from runners.drive.cards import week_directed_style_parity as fast
from tests.test_drive_week_directed_reading import population, DICTIONARY, fixture
from runners.drive.cards.menus_io import write, sha256


@pytest.mark.parametrize("signal", ["always", "early", "late"])
def test_all_known_answer_orders_have_exact_original_curves(signal):
    rows = population(signal)
    primary, ledger = base.study(rows, DICTIONARY)
    result, timing = fast.audit(rows, DICTIONARY, primary, ledger)
    assert result["orders"] == 3*203
    assert result["prefixes"] == 3*203*12
    assert result["exact_all_style_flags_and_endpoints"]
    assert not result["empirical_controls_run"]
    assert timing["wall_seconds"] > 0


def test_empty_prefix_missing_features_ties_and_unlisted_denominator():
    rows = population()[:12]
    rows[0]["word_counts"] = {}
    rows[1]["word_counts"] = {"unlisted": 17, "w0": 3}
    dictionary = {**DICTIONARY, "words": DICTIONARY["words"]+["absent"]}
    indices = list(reversed(range(12)))
    actual = fast.style_prefixes(rows, dictionary, indices)
    expected = [base.profile([rows[j] for j in indices[:i+1]], dictionary)["style"] for i in range(12)]
    np.testing.assert_array_equal(actual, np.asarray(expected, float))
    gallery = base.gallery_model([expected[-1]]*3)
    result = fast.evaluate(rows, dictionary, indices, gallery, 0)
    assert result["identification"] == {"sessions":13,"censored":True}
    assert not any(result["identification_curve"])
    empty = fast.style_prefixes(rows, dictionary, list(range(12)))
    assert np.isnan(empty[0]).all()


@pytest.mark.parametrize("mutation", ["duplicate", "negative", "overflow"])
def test_invalid_count_or_order_refuses(mutation):
    rows = population()[:12]; indices=list(range(12))
    if mutation == "duplicate": indices[-1] = 0
    elif mutation == "negative": rows[0]["word_counts"]={"w0":-1}
    else: rows[0]["word_counts"]={"w0":2**53+1}
    with pytest.raises(ValueError): fast.style_prefixes(rows, DICTIONARY, indices)


def test_missing_order_and_changed_original_curve_refuse():
    rows=population();primary,ledger=base.study(rows, DICTIONARY)
    with pytest.raises(ValueError,match="Incomplete"):
        fast.audit(rows,DICTIONARY,primary,ledger[:-1])
    altered=copy.deepcopy(ledger)
    altered[0]["recovery"]["style"]["identification_curve"][0]=False
    with pytest.raises(ValueError,match="parity"):
        fast.audit(rows,DICTIONARY,primary,altered)


def test_full_handler_binding_fresh_replay_and_mutation_refusal(tmp_path):
    inputs=fixture(tmp_path/"source")
    root=tmp_path/"original";root.mkdir()
    write(root/"PLAN.json",dict(inputs=inputs,config=base.CONFIG))
    base.execute(root/"output",inputs,base.CONFIG)
    write(root/"COMPLETE.json",dict(status="COMPLETE",fresh_process_verified=True,
        outputs={p.relative_to(root).as_posix():sha256(p) for p in root.rglob("*") if p.is_file()}))
    bound=dict(dr1_completion=str(root/"COMPLETE.json"));out=tmp_path/"parity"
    assert fast.execute(out,bound,fast.CONFIG)["status"]=="complete"
    assert fast.verify(out,bound,fast.CONFIG)["verified"]
    import json
    result=json.loads((out/"PARITY.json").read_text());result["orders"]-=1
    (out/"PARITY.json").write_text(json.dumps(result))
    with pytest.raises(ValueError,match="reconstruction"):
        fast.verify(out,bound,fast.CONFIG)
    with pytest.raises(ValueError,match="Frozen"):
        fast.execute(tmp_path/"bad",bound,{**fast.CONFIG,"margin":1})
