import copy
from pathlib import Path
import pytest
from runners.drive.cards import week5_ex2 as ex
from runners.drive.cards import week5_ex23_fixture as fixture


def test_complete_constructed_export_and_independent_reentry(tmp_path):
    result=fixture.execute(tmp_path,{},dict(card='EX2'))
    assert result['rows']==5000 and result['all_categories_1000']
    assert fixture.verify(tmp_path,{},dict(card='EX2'))['verified']
    rows=ex.common.read(tmp_path/'consumer/bundle/EDITS.json')
    assert len(rows)==5000 and all('editor' not in row and 'post' not in row for row in rows)
    assert all(row['post_id'].isdigit() and row['post_id'] in row['attribution_url'] for row in rows)
    assert all(row['classifier_output']==row['reason_category'] for row in rows)


def sample_state():
    return dict(primary_rows=0,counts={k:0 for k in ex.source.PRIMARY},heaps={k:[] for k in ex.source.PRIMARY},editors=[])


def metadata(n=5500):
    return [dict(editor=f'editor-{i%25}',post=f'post-{i}',stamp=str(i),site='writers',type=5,
        reason=ex.source.PRIMARY[i%5],self_edit=False,owner_known=True) for i in range(n)]


def test_selection_is_exact_balanced_and_independent_of_prediction_fields():
    rows=metadata();a=sample_state();b=sample_state();ex.accumulate(rows,'writers',0,a)
    changed=[dict(row,unused_prediction='deliberately changed') for row in rows]
    ex.accumulate(changed,'writers',0,b)
    assert ex.selected(a)==ex.selected(b) and len(ex.selected(a))==5000
    for reason in ex.source.PRIMARY:
        retained=[r for r in ex.selected(a) if r['reason']==reason]
        expected=sorted([dict(row,source_row=i) for i,row in enumerate(rows) if row['reason']==reason],key=ex.rank)[:1000]
        assert {r['source_row'] for r in retained}=={r['source_row'] for r in expected}


def test_below_category_floor_is_not_replaced_by_smaller_export():
    state=sample_state();ex.accumulate(metadata(4999),'writers',0,state)
    assert ex.selected(state) is None


def test_public_post_mapping_and_missing_identity(tmp_path):
    path=tmp_path/'Posts.xml';path.write_text('<posts><row Id="7"/><row Id="9"/></posts>',encoding='utf8')
    salt=b'z'*32;wanted={ex.source.salted(salt,'writers-post','9')};found={}
    ex.recover_public_posts(path,salt,'writers',wanted,found,lambda:False)
    assert list(found.values())==['9']
    with pytest.raises(ValueError,match='no exact'):ex.recover_public_posts(path,salt,'writers',{'absent'},{},lambda:False)


def test_source_row_mismatch_and_private_url_refuse():
    row=metadata(1)[0];meta=dict(row,user_fold=1,classifier_output='grammar')
    record=dict(row,before='before',after='after')
    with pytest.raises(ValueError,match='numeric'):ex.export_row(meta,record,'salted-identity')
    with pytest.raises(ValueError,match='no longer'):ex.export_row(meta,dict(record,reason='grammar'),'1')


def test_unfinished_or_wrong_primary_producer_refuses(tmp_path):
    ex.common.io.write_json(tmp_path/'COMPLETE.json',dict(status='PAUSED',fresh_process_verified=False,outputs={}))
    with pytest.raises(ValueError,match='Complete'):ex.authenticate({'analysis_run':str(tmp_path)},lambda:False)


def test_partial_copy_refuses_before_any_destination_created(tmp_path):
    with pytest.raises(ValueError,match='named local'):ex.export_local(tmp_path,tmp_path/'target')
