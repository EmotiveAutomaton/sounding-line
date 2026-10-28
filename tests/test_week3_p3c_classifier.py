import gzip
import json
from pathlib import Path
import pytest
from runners.stage14.common import freeze,filehash,read
from runners.drive.cards import week3_p3c_classifier as c


def test_kappa_known_tables_and_unchanged_boundary():
    labels=['fluency']*100+['meaning-changed']*100
    assert c.kappa(labels,labels)['kappa']==1
    chance=['fluency']*50+['meaning-changed']*50
    assert c.kappa(labels,chance*2)['kappa']==0
    reverse=['meaning-changed']*100+['fluency']*100
    assert c.kappa(labels,reverse)['kappa']==-1
    boundary=['fluency']*80+['meaning-changed']*20+['fluency']*20+['meaning-changed']*80
    assert c.kappa(labels,boundary)['gate_passed']
    boundary[0]='meaning-changed'
    assert not c.kappa(labels,boundary)['gate_passed']


def test_constant_missing_unknown_reference_refuses():
    assert c.kappa(['fluency']*200,['fluency']*200)['kappa'] is None
    assert not c.kappa(['fluency']*200,['meaning-changed']*200)['gate_passed']
    with pytest.raises(ValueError): c.kappa(['fluency'],['fluency'])
    with pytest.raises(ValueError): c.kappa(['unknown']*200,['fluency']*200)


def test_parity_checks_identity_direction_and_numeric_values():
    row=dict(key='a',tokens=8,label='fluency',logits=[0,1,0,0,0],probabilities=[.1,.6,.1,.1,.1])
    c.parity(row,dict(row))
    for changes in [dict(key='b'),dict(tokens=9),dict(label='clarity'),dict(logits=[0,1.01,0,0,0]),dict(probabilities=[float('nan')]*5)]:
        with pytest.raises(ValueError): c.parity(row,dict(row,**changes))


class FakeModel:
    environment={'fake':'unit-check'}
    def __init__(self,path): pass
    def token_count(self,row): return len(row['before'].split())+len(row['after'].split())+4
    def predict(self,row):
        n=self.token_count(row)
        if n>512: raise ValueError('unclipped input exceeds model support')
        index=4 if row['before'].startswith('meaning') else 1
        logits=[0.]*5; logits[index]=1.
        probs=[.1]*5; probs[index]=.6
        return dict(key=row['key'],tokens=n,label=c.LABELS[index],logits=logits,probabilities=probs)


def fixture(tmp_path,monkeypatch,selected_long=False,tail_long=False):
    monkeypatch.setattr(c,'LocalModel',FakeModel); monkeypatch.setattr(c,'model_inputs',lambda _:None)
    root=tmp_path/'source'; out=root/'output'; out.mkdir(parents=True)
    rows=[]
    for i in range(1001):
        before=('meaning' if i%2 else 'surface')+' sentence '+str(i); after='changed sentence '+str(i)
        if (selected_long and i==0) or (tail_long and i==1000): before='word '*600
        rows.append(dict(key=f'key-{i}',before=before,after=after,pair_content_sha256=c.digest([before,after])))
    path=out/'pairs.json.gz'; path.write_bytes(gzip.compress(json.dumps(dict(session='s',rows=rows)).encode(),mtime=0))
    mapping=[dict(pair_id=f'pair-{i+1:03d}',key=r['key'],pair_content_sha256=r['pair_content_sha256']) for i,r in enumerate(rows[:200])]
    blind=[dict(pair_id=m['pair_id'],before=r['before'],after=r['after']) for r,m in zip(rows,mapping)]
    for name,value in {'SESSION_INDEX.json':[dict(session='s',file='pairs.json.gz',sha256=filehash(path),pairs=len(rows))],
        'SUMMARY.json':dict(constructed=False,counts=dict(pairs=len(rows))),
        'CALIBRATION_MAP.json':mapping,'BLIND_CALIBRATION.json':blind,'TIMING_ORDER.json':[r['key'] for r in rows[:1000]]}.items(): freeze(out/name,value)
    complete=root/'COMPLETE.json'; freeze(complete,dict(status='COMPLETE',fresh_process_verified=True,outputs={'output/'+p.name:filehash(p) for p in out.iterdir()}))
    criteria=tmp_path/'criteria.md';criteria.write_text('frozen criteria')
    labels=tmp_path/'labels.json'; freeze(labels,dict(agent_made=True,predictions_seen=False,reviewed_pairs=200,blind_sha256=filehash(out/'BLIND_CALIBRATION.json'),criteria_sha256=filehash(criteria),rows=[dict(pair_id=m['pair_id'],label='meaning-changed' if i%2 else 'fluency',meaning_changed=bool(i%2)) for i,m in enumerate(mapping)]))
    gate=tmp_path/'source_gate.json'; freeze(gate,dict(full_write_through=True,completion_sha256=filehash(complete)))
    native=tmp_path/'native.json';freeze(native,dict(status='COMPLETE',fresh_process_verified=True))
    native_gate=tmp_path/'native_gate.json';freeze(native_gate,dict(full_write_through=True,native_model_validated=True,completion_sha256=filehash(native)))
    inputs={k:str(native) for k in ('model_completion','model_gate','metadata')}
    inputs.update(source_completion=str(complete),source_gate=str(gate),agent_labels=str(labels),criteria=str(criteria),native_completion=str(native),native_gate=str(native_gate))
    return inputs,out


def test_actual_serialized_handler_replay_reentry_and_corruption(tmp_path,monkeypatch):
    inputs,source=fixture(tmp_path,monkeypatch,tail_long=True); out=tmp_path/'run'
    c.execute(out,inputs,c.CONFIGS['calibration'])
    assert read(out/'SUMMARY.json')['agreement']['kappa']==1
    assert read(out/'SUMMARY.json')['overlength_population_pairs']==1
    assert read(out/'SUMMARY.json')['scientific_admission'] is False
    before={str(p):filehash(p) for p in out.rglob('*.json') if p.name!='PROGRESS.json'}
    assert c.verify(out,inputs,c.CONFIGS['calibration'])['full_classifier_replay']
    c.execute(out,inputs,c.CONFIGS['calibration'])
    assert before=={str(p):filehash(p) for p in out.rglob('*.json') if p.name!='PROGRESS.json'}
    prediction=out/'calibration/key-0.json'; value=read(prediction);value['label']='style';prediction.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='categorical replay'): c.verify(out,inputs,c.CONFIGS['calibration'])


def test_selected_overlength_preserved_without_scoring(tmp_path,monkeypatch):
    inputs,_=fixture(tmp_path,monkeypatch,selected_long=True);out=tmp_path/'run'
    c.execute(out,inputs,c.CONFIGS['calibration'])
    summary=read(out/'SUMMARY.json')
    assert not summary['calibration_complete'] and not summary['gate_passed']
    assert not (out/'calibration').exists()
    assert len(read(out/'TOKEN_COVERAGE.json')['selected_overlength'])==1
    assert c.verify(out,inputs,c.CONFIGS['calibration'])['verified']


def test_changed_source_bytes_and_unblinded_annotations_refuse(tmp_path,monkeypatch):
    inputs,out=fixture(tmp_path,monkeypatch)
    labels=Path(inputs['agent_labels']);d=read(labels);d['predictions_seen']=True;labels.write_text(json.dumps(d))
    with pytest.raises(ValueError,match='blind agent'):c.corpus(inputs,FakeModel(None))
    d['predictions_seen']=False;labels.write_text(json.dumps(d))
    path=out/'pairs.json.gz';path.write_bytes(path.read_bytes()+b'changed')
    with pytest.raises(ValueError,match='source bytes'):c.corpus(inputs,FakeModel(None))


def test_mismatched_annotations_and_duplicate_selection_refuse(tmp_path,monkeypatch):
    inputs,_=fixture(tmp_path,monkeypatch)
    labels=Path(inputs['agent_labels']);d=read(labels);d['rows'][0]['pair_id']='different';labels.write_text(json.dumps(d))
    with pytest.raises(ValueError,match='annotation identity'):c.corpus(inputs,FakeModel(None))


def test_validation_mode_runs_actual_handler_without_corpus(tmp_path,monkeypatch):
    monkeypatch.setattr(c,'LocalModel',FakeModel);monkeypatch.setattr(c,'model_inputs',lambda _:None)
    dummy=tmp_path/'dummy.json';freeze(dummy,{})
    inputs={k:str(dummy) for k in ('model_completion','model_gate','metadata')};out=tmp_path/'validation'
    c.execute(out,inputs,c.CONFIGS['validation']);assert c.verify(out,inputs,c.CONFIGS['validation'])['verified']
    assert read(out/'SUMMARY.json')['overlength_refused']
    assert not read(out/'SUMMARY.json')['corpus_inference']
