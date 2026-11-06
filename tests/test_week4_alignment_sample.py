import pytest
from runners.drive.cards import week4_alignment_sample as m


def test_known_complete_units():
    assert m.known_answers()['verified']


def test_missing_or_duplicate_mandatory_refused():
    with pytest.raises(ValueError,match='absent'):
        m.select(['a','b'],['missing'],1)
    with pytest.raises(ValueError,match='Duplicate'):
        m.select(['a','b'],['a','a'],1)


def test_disjoint_random_group():
    value=m.select([str(i) for i in range(30)],['1','4','7'],10)
    assert len(value['selected'])==13 and not set(value['mandatory'])&set(value['random'])


def test_no_source_row_or_split_changes():
    rows=[dict(writer=w,conversation=w,turn=t,candidates=[1,2],choice=t,half=t,prompt='p')
          for w in ('a','b','c') for t in (0,1)]
    splits=dict(writer_splits={w:{'unchanged':w} for w in ('a','b','c')},prompt_text_indices={'p':3,'global':7})
    selected=m.select(['a','b','c'],['a'],1)
    result,small,ids,indices=m.subset(rows,splits,selected)
    assert ids==[1,2,3,7] and small['prompt_text_indices']==splits['prompt_text_indices']
    for r,i in zip(result,indices):
        assert {k:v for k,v in r.items() if k!='original_comparison_index'}==rows[i]


def test_native_handler_replay_and_tamper(tmp_path):
    config=m.configuration('constructed');m.execute(tmp_path,{},config)
    assert m.verify(tmp_path,{},config)['full_fresh_source_replay']
    (tmp_path/'SUMMARY.json').write_text('{}',encoding='utf8')
    with pytest.raises(ValueError,match='replay differs'):
        m.verify(tmp_path,{},config)
