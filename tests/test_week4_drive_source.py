import copy
import pytest
from runners.drive.cards import week4_drive_source as d


def test_unicode_context_and_exclusions():
    first,second,empty=d.fixtures()
    rows=d.project(first)
    assert [r['writer_typed'] for r in rows]==[False,True,True]
    assert rows[1]['sentence']=='I care \U0001f600. '
    assert rows[1]['preceding_sentence']=='Prompt. '
    assert rows[2]['preceding_sentence']=='I care \U0001f600. '
    assert d.project(second)[1]['preceding_sentence']=='Mine and model. '
    assert not d.project(second)[0]['writer_typed']
    assert d.project(empty)==[]
    for fixture in d.fixtures():assert d.project(fixture)==d.project(fixture,True)


def test_broken_provenance_refused():
    t=d.fixtures()[0];t['final_spans'][1]['start_utf16']+=1
    for mode in (False,True):
        with pytest.raises(ValueError):d.project(t,mode)
    t=d.fixtures()[0];t['final_document']+='missing'
    with pytest.raises(ValueError):d.project(t)


def test_payload_projection_excludes_identity():
    row=dict(d.project(d.fixtures()[0])[1],writer='secret',session='private',chosen=True)
    assert set(d.payload(row))=={'sentence','preceding_sentence'}


def test_support_boundary_order_and_duplicates():
    rows=[dict(writer=str(w),genre='g',session=f'{w}-{s}',eligible=200) for w in range(25) for s in range(2)]
    result,private=d.support(rows)
    assert result['pooled']['writers_with_200_each_half']==25
    assert d.support(list(reversed(rows)))==(result,private)
    rows[0]['eligible']=199
    assert d.support(rows)[0]['pooled']['writers_with_200_each_half']==24
    # Repeated text does not collapse actual sentence opportunities across sessions.
    assert d.support([dict(writer='w',genre='g',session=str(s),eligible=200) for s in range(2)])[0]['pooled']['writers_with_200_each_half']==1


def test_complete_handlers_reentry_and_mutation(tmp_path):
    c=d.configuration('constructed')
    d.execute(tmp_path,{},c);assert d.verify(tmp_path,{},c)['verified']
    before={p.name:p.read_bytes() for p in tmp_path.iterdir() if p.name!='PROGRESS.json' and p.is_file()}
    d.verify(tmp_path,{},c)
    assert before=={p.name:p.read_bytes() for p in tmp_path.iterdir() if p.name!='PROGRESS.json' and p.is_file()}
    path=tmp_path/'SUMMARY.json';path.write_text('{}',encoding='utf8')
    with pytest.raises(ValueError):d.verify(tmp_path,{},c)


def test_foreign_config_refused(tmp_path):
    c=d.configuration('constructed');c['expected_sessions']=2
    with pytest.raises(ValueError):d.execute(tmp_path,{},c)
