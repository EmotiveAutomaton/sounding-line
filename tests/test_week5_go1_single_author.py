import pytest
from runners.drive.cards import week5_go1_single_author as cell


def rows():
    return [dict(repository='eips',type='Standards Track',category='Core',author=str(i),document=str(i),
                 motivation='goal',rest='body',multi_author=i>=50) for i in range(55)]


def test_filter_precedes_fixed_49_distractor_roster(tmp_path):
    path=tmp_path/'rows.json';cell.base.core.write(path,dict(documents=rows()))
    data,roster=cell.prepared_rows({'documents':str(path)}, {})
    assert len(data)==len(roster)==50
    assert all(set(a['candidates'])==set(range(50)) for a in roster)
    assert all(not r['multi_author'] for r in data)


@pytest.mark.parametrize('flag',[None,0,'false'])
def test_unknown_flags_refuse(tmp_path,flag):
    data=rows();data[0]['multi_author']=flag
    path=tmp_path/'rows.json';cell.base.core.write(path,dict(documents=data))
    with pytest.raises(ValueError,match='Explicit source'):cell.prepared_rows({'documents':str(path)}, {})
