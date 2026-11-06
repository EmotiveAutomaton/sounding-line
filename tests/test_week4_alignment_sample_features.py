from pathlib import Path
import shutil
import numpy as np
import pytest
from runners.drive.cards import week4_alignment_sample_features as card
from runners.drive.cards import week3_alignment_features as original
from runners.drive.cards.menus_io import read,write
from tests.test_week3_alignment_features import fixture as old_fixture,complete


def fixture(root):
    inputs=old_fixture(root)
    path=Path(inputs['prepared_summary']);value=read(path)
    value.update(variant='CA1.s1',sample_scope=True)
    new=Path(root)/'sample';out=new/'output';out.mkdir(parents=True)
    for name in value['output_hashes']:shutil.copyfile(path.parent/name,out/name)
    write(out/'SUMMARY.json',value);complete(new)
    inputs.update(prepared_summary=str(out/'SUMMARY.json'),prepared_complete=str(new/'COMPLETE.json'))
    return inputs


def test_full_global_prompt_pool_and_same_pilot_comparisons():
    rows=[dict(candidates=[i*4+j for j in range(4)],prompt=str(i%3),choice=0) for i in range(100)]
    splits=dict(prompt_text_indices={str(i):400+i for i in range(20)})
    selected,ids,prompts=card.select_ids(rows,splits,'full',original.SEED)
    assert len(selected)==100
    assert set(range(400,420))<=set(ids) and len(prompts)==20
    for r in rows:r['choice']=3
    assert card.select_ids(rows,splits,'full',original.SEED)==(selected,ids,prompts)
    assert card.select_ids(rows,splits,'pilot',original.SEED)==original.select_ids(rows,splits,'pilot',original.SEED)


def test_fixture_handler_replay_reentry_and_scope(tmp_path):
    inputs=fixture(tmp_path/'source');out=tmp_path/'output';config=card.configuration('fixture')
    result=card.execute(out,inputs,config)
    assert card.verify(out,inputs,config)['global_prompt_pool']
    assert card.execute(out,inputs,config)==result
    assert read(out/'SAMPLE_SCOPE.json')['sample_scope']


def test_changed_embedding_refused(tmp_path):
    inputs=fixture(tmp_path/'source');out=tmp_path/'output';config=card.configuration('fixture')
    card.execute(out,inputs,config);path=out/'chunks/00000.npy'
    v=np.load(path);v[0,0]+=.1;np.save(path,v)
    with pytest.raises(ValueError,match='replay differs'):card.verify(out,inputs,config)


def test_unlabelled_population_refused(tmp_path):
    inputs=old_fixture(tmp_path/'source')
    with pytest.raises(ValueError,match='explicit sample'):card.execute(tmp_path/'out',inputs,card.configuration('fixture'))


def test_unfrozen_config_refused(tmp_path):
    with pytest.raises(ValueError,match='Frozen'):card.execute(tmp_path,{},dict(mode='pilot'))
