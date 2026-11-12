import copy
import pytest
from runners.drive.cards import week5_ex3 as ex
from runners.drive.cards import week5_ex23_fixture as fixture


def test_actual_exporter_full_reentry_and_fresh_verify(tmp_path):
    assert fixture.execute(tmp_path,{},dict(card='EX3'))['queries']==50
    assert fixture.verify(tmp_path,{},dict(card='EX3'))['verified']
    task=ex.common.read(tmp_path/'consumer/bundle/TASK.json')
    assert len(task['documents'])==50 and all(len(q['distractor_ids'])==49 for q in task['queries'])
    assert 'Fixture Author' not in (tmp_path/'consumer/bundle/TASK.json').read_text()
    assert 'Goal 0' not in (tmp_path/'consumer/bundle/TASK.json').read_text()
    for document in task['documents']:
        motivation=next(p for p in document['sections'] if p['role']=='motivation')
        nested=[p for p in document['sections'] if motivation['start_line']<p['start_line']<motivation['subtree_end_line']]
        assert nested and all(not p['retained_in_query'] for p in nested)


def test_changed_source_document_refuses(tmp_path):
    args=fixture.ex3_source(tmp_path/'constructed');p=tmp_path/'constructed/public/pep-0000.rst'
    p.write_text(p.read_text()+'changed',encoding='utf8')
    with fixture.alias(ex.core,'git',fixture.git_metadata):
        with pytest.raises(ValueError,match='source file'):ex.execute(tmp_path/'out',args,{})


def test_frozen_allocation_required():
    rows=[{'document':str(i),'author':'a'} for i in range(50)]
    proper=[dict(query=0,candidates=list(range(50)),truth_position=0,other_stratum=0)]
    assert len(ex.task_rows(rows,proper)[0]['distractor_ids'])==49
    changed=copy.deepcopy(proper);changed[0]['candidates'][-1]=0
    with pytest.raises(ValueError,match='roster'):ex.task_rows(rows,changed)


def test_changed_prepared_binding_refuses(tmp_path):
    args=fixture.ex3_source(tmp_path/'constructed');p=tmp_path/'constructed/prepare/output/PREPARED.json'
    value=ex.common.read(p);value['rows_binding']='bad';ex.common.io.write_json(p,value)
    with pytest.raises(ValueError,match='changed'):ex.execute(tmp_path/'out',args,{})


@pytest.mark.parametrize('config',[{'distractors':9},{'max_new_documents':0},{'max_wall_seconds':-1}])
def test_invalid_semantic_or_operational_configuration_refuses(tmp_path,config):
    with pytest.raises(ValueError):ex.execute(tmp_path,{'go1_prepare':'absent'},config)


def test_materializer_never_accepts_external_target(tmp_path):
    with pytest.raises(ValueError,match='named local'):ex.export_local(tmp_path,tmp_path/'external')
