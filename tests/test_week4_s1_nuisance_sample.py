import pytest
from runners.drive.cards import week4_s1_nuisance_sample as sample

def test_stratified_whole_writer_selection():
    assert all(sample.known_checks().values())
    records=[dict(writer=str(i),genre=g) for i in range(10) for g in ('a','b','a')]
    frame=sample.writer_frame(records)
    manifest=dict(seed=sample.SEED,frame=frame,sample_size=5,selected_writers=sample.select_writers(frame,5))
    assert sample.validate_sample(list(reversed(records)),manifest)==manifest['selected_writers']
    assert {r['genre'] for r in frame}=={'a'}
    manifest['selected_writers']=[]
    with pytest.raises(ValueError,match='membership'):sample.validate_sample(records,manifest)

def test_bad_frames_and_sizes_refuse():
    with pytest.raises(ValueError,match='Duplicate'):sample.select_writers([dict(writer='a',genre='x')]*2,1)
    with pytest.raises(ValueError,match='size'):sample.select_writers([dict(writer='a',genre='x')],2)
    with pytest.raises(ValueError,match='frame'):sample.validate_sample([],dict(seed=0))

def test_sample_scope_replayed_and_mutation_refused(tmp_path):
    config=sample.configuration('constructed')
    sample.execute(tmp_path,{},config)
    assert sample.verify(tmp_path,{},config)['complete_source_replay']
    (tmp_path/'SAMPLE_SCOPE.json').write_text('{}')
    with pytest.raises(ValueError,match='scope replay'):sample.verify(tmp_path,{},config)

def test_selected_windows_keep_original_values():
    records=[dict(writer=str(i),genre='a') for i in range(4)]
    windows=[dict(writer=r['writer'],session=f'{r["writer"]}-{j}') for r in records for j in range(3)]
    frame=sample.writer_frame(records);selected=sample.select_writers(frame,2)
    manifest=dict(seed=sample.SEED,frame=frame,sample_size=2,selected_writers=selected)
    intervals={'full_population':True};histories={'all_donors':True};medians={'full_record':True}
    values=(records,windows,intervals,histories,medians)
    view=sample.sampled_view(values,manifest)
    assert len(view[1])==6 and {w['writer'] for w in view[1]}==set(selected)
    assert all(sum(w['writer']==writer for w in view[1])==3 for writer in selected)
    assert all(any(w is original for original in windows) for w in view[1])
    assert all(view[i] is values[i] for i in (0,2,3,4))
