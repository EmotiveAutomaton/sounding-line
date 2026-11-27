import pandas as pd
import pytest
from hashlib import sha256

from runners.drive.sealed.week7_lgh2 import projection
from runners.drive.sealed.week7_lgh2_survey import survey_frame, run_from_mount, Unavailable


def fixture():
    frame=pd.DataFrame({'conversation_id':[1,1,2,2],'user_id':[1,2,1,3],
                        'laughter':[9,3,0,9],'pre_affect':[5,1,1,5],'affect':[1,5,1,5]})
    # Constructed codes only. The incoming mood scale deliberately runs backwards.
    legends={'laughter':{9:-1,3:1,0:None},'pre_affect':{5:-2,1:2},'affect':{1:-2,5:2}}
    return frame,legends


def test_orientation_and_complete_dyads():
    frame,legends=fixture()
    out=projection(survey_frame(frame,legends),False)
    assert out.conversation.tolist()==[1,1]
    assert out.measure.tolist()==[-1,1]
    assert out.pre_affect.tolist()==[-2,2] and out.affect.tolist()==[-2,2]


def test_unbound_code_and_missing_legend():
    frame,legends=fixture()
    frame.loc[0,'laughter']=17
    with pytest.raises(ValueError,match='Unbound'):
        survey_frame(frame,legends)
    del legends['affect']
    with pytest.raises(ValueError,match='three'):
        survey_frame(frame,legends)


def test_pinned_file_to_aggregate_writer(tmp_path):
    original, legends = fixture()
    chunks = []
    for i in range(24):
        frame = original.iloc[:2].copy()
        frame['conversation_id'] = i
        frame['user_id'] = [2*i, 2*i+1]
        frame['affect'] = [5,1] if i%2 else [1,5]
        frame['laughter'] = [3,9] if i%3 else [9,3]
        chunks.append(frame)
    path = tmp_path/'survey.parquet'
    pd.concat(chunks).to_parquet(path,index=False)
    digest = sha256(path.read_bytes()).hexdigest()
    pin = (path.name, path.stat().st_size, digest)
    out = tmp_path/'out'
    out.mkdir()
    run_from_mount(tmp_path, out, legends, survey_pin=pin, draws=32)
    support = pd.read_csv(out/'support.csv')
    assert support.iloc[0]['n']==48
    assert len(pd.read_csv(out/'mood.csv'))==2
    with pytest.raises(Unavailable):
        run_from_mount(tmp_path, out, legends, survey_pin=(pin[0],pin[1],'0'*64))

