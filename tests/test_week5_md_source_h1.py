from types import SimpleNamespace
import numpy as np
import pytest
from runners.drive.cards import week5_md_source_h1 as source


def task():
    p=np.zeros((30,15));p[:,0]=np.arange(1,31);p[:,9]=np.nan
    p[[0,3,5,8,11,13,16,18,21,24,26,29],9]=50
    return p


def subject(ps,cs,days):
    return dict(dataHdr=source.HEADER,data=ps,timesPlayed=cs,dayNumber=days,
                timeOfDay=np.zeros(len(cs)),nPlays=len(cs))


def test_native_support_fixture():
    assert source.fixture()['passed']


def test_conflicting_later_counter_keeps_exact_first():
    p=task();q=p.copy();q[:,1]=1
    ps,cs,ds,eligible,audit=source.resolve(subject([p,p,q],[1,2,2],[0,1,1]))
    assert cs == [1] and not eligible
    assert audit['conflicting_counter_plays_excluded'] == 2
    assert np.array_equal(ps[0],p,equal_nan=True)


def test_noninteger_counter_never_silently_truncated():
    with pytest.raises(ValueError,match='counter value'):
        source.resolve(subject([task()],[1.9],[0]))


def test_independent_projection_checks_every_value_and_exclusion(tmp_path,monkeypatch):
    p=task();q=p.copy();q[:,1]=1
    ss=[subject([p,p],[1,1],[0,1]),subject([p,p,q],[1,2,2],[0,1,1]),subject([p],[3],[np.nan])]
    monkeypatch.setattr(source,'source_subjects',lambda path,independent=False:
                        [SimpleNamespace(**s) for s in ss] if independent else ss)
    source.prepare(tmp_path,tmp_path/'out')
    assert source.verify_projection(tmp_path,tmp_path/'out')['verified']
    with np.load(tmp_path/'out/task.npz') as bundle:
        data={k:bundle[k] for k in bundle.files}
    data['plays'][0,0,8]=99
    np.savez_compressed(tmp_path/'out/task.npz',**data)
    import json
    receipt=json.loads((tmp_path/'out/SOURCE.json').read_text())
    receipt['task_sha256']=source.sha(tmp_path/'out/task.npz')
    source.save_json(tmp_path/'out/SOURCE.json',receipt)
    with pytest.raises(ValueError,match='numeric task mismatch'):
        source.verify_projection(tmp_path,tmp_path/'out')
