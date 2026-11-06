import pytest
from runners.drive.cards import week4_pieces_profile as p
from tests.test_week4_pieces_windows_h1 import canonical_fixture,config


def test_prefix_is_order_and_outcome_independent():
    rows=[dict(session=str(i),outcome=i) for i in range(40)]
    a=p.selection(rows,10)
    assert len(a)==3 and a<=p.original.selection(rows,10)
    assert a==p.selection([dict(r,outcome=0) for r in rows[::-1]],10)
    with pytest.raises(ValueError,match='Three'):p.selection(rows[:2],10)


def test_complete_profile_replay_and_tamper(tmp_path):
    inputs=canonical_fixture(tmp_path/'fixture');cfg=config()
    result=p.execute(tmp_path/'profile',inputs,cfg)
    assert result['work']['sample_sessions']==3 and not result['work']['full_first_tenth_probe']
    assert p.verify(tmp_path/'profile',inputs,cfg)['full_profile_replay']
    (tmp_path/'profile/PROFILE_RESULT.json').write_text('{"work":{}}')
    with pytest.raises(ValueError,match='replay differs'):p.verify(tmp_path/'profile',inputs,cfg)
