import numpy as np
import pytest
from runners.drive.cards import week5_bk_pp3_tree as card
from runners.drive.cards.week5_bk_pp3_fixture import known_checks


def test_original_sample_models_and_exact_null():
    assert all(known_checks().values())


def test_frozen_card_and_input_refuse(tmp_path):
    with pytest.raises(ValueError):card.execute(tmp_path,{},dict(card='BK-PP3.p1',mode='constructed',max_new_draws=0))
    with pytest.raises(ValueError):card.execute(tmp_path,{'cost_complete':'human'},dict(card='BK-PP3.p1',mode='constructed',max_new_draws=1))


def test_one_fit_checkpoint_has_no_scientific_summary(tmp_path):
    r=card.execute(tmp_path,{},dict(card='BK-PP3.p1',mode='constructed',max_new_draws=1))
    assert r['status']=='yielded' and r['new_fits']==1
    assert (tmp_path/'fits/real.json.gz').exists() and not (tmp_path/'SUMMARY.json').exists()


def test_changed_saved_contract_refuses(tmp_path):
    config=dict(card='BK-PP3.p1',mode='constructed',max_new_draws=1)
    card.execute(tmp_path,{},config)
    data=card.read(tmp_path/'BINDING.json');data['seed']+=1
    (tmp_path/'BINDING.json').write_text(__import__('json').dumps(data))
    with pytest.raises(ValueError,match='contract changed'):card.execute(tmp_path,{},config)
