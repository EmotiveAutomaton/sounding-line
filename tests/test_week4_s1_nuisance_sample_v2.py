import pytest
from runners.drive.cards import week4_s1_nuisance_sample_v2 as sample

def test_producer_schema_and_full_selection_replay():
    assert all(sample.known_checks().values())
    records=[dict(session='s',writer='w')]
    windows=[dict(session='s',writer='w',genre='creative')]
    assert sample.checked_frame(records,windows)==[dict(writer='w',genre='creative')]
    with pytest.raises(ValueError,match='source join'):
        sample.checked_frame(records,[dict(session='s',writer='other',genre='creative')])
    with pytest.raises(ValueError,match='source join'):sample.checked_frame(records,windows*2)

def test_native_replay_and_scope_mutation(tmp_path):
    config=sample.configuration('constructed');sample.execute(tmp_path,{},config)
    assert sample.verify(tmp_path,{},config)['complete_source_replay']
    (tmp_path/'SAMPLE_SCOPE.json').write_text('{}')
    with pytest.raises(ValueError,match='scope replay'):sample.verify(tmp_path,{},config)

def test_actual_window_metadata_refuses_wrong_genre():
    records=[dict(session='s',writer='w')];windows=[dict(session='s',writer='w',genre='creative')]
    manifest=dict(seed=20261102,sample_size=1,selected_writers=['w'],frame=[dict(writer='w',genre='argumentative')])
    with pytest.raises(ValueError,match='genre frame'):sample.sampled_view((records,windows,{},{},{}),manifest)
