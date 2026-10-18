import copy
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest
from runners.drive.cards import events_d38 as card


def vectors():
    e=np.zeros((3,384)); e[0,0]=1; e[1,1]=1; e[2,0]=-1
    return e


def menus(before=0,after=0):
    return [dict(key=f'm{i}',session='s',ordinal=i*10,end_ordinal=i*10+8,options=[0,1,2],chosen=before if i<13 else after) for i in range(24)]


def test_exact_windows_exclude_origin_overlap_and_need_five():
    event=dict(source_span_ordinal=0,ordinal=125)
    window,excluded=card.event_window(event,menus(),card.CONFIG)
    assert excluded is None
    assert [m['ordinal'] for m in window['before']]==list(range(20,120,10))
    assert [m['ordinal'] for m in window['after']]==list(range(130,230,10))
    assert window['overlapping_keys']==['m12']
    assert all(m['ordinal']!=0 for phase in ('before','after') for m in window[phase])
    assert card.event_window(dict(event,ordinal=35),menus(),card.CONFIG)[0] is None


@pytest.mark.parametrize('after,expected',[(0,0.),(2,2.)])
def test_known_event_gradient(after,expected):
    window,_=card.event_window(dict(source_span_ordinal=0,ordinal=125),menus(after=after),card.CONFIG)
    result=card.gradient(window,vectors()[0],vectors())
    assert result['eligible'] and result['gradient']==pytest.approx(expected)
    if after==2:
        assert result['drops']==dict(near=1.,middle=0.,far=-1.)
    tied=card.gradient(window,vectors()[1],np.tile(vectors()[1],(3,1)))
    assert not tied['eligible'] and tied['reason']=='distance tercile boundaries coincide'


@pytest.mark.parametrize('sign,state',[(0,'null'),(1,'positive'),(-1,'negative')])
def test_population_null_positive_reverse(sign,state):
    units=[]
    for wi in range(8):
        events=[]
        for phase in ('early','late'):
            gradient=2. if (sign==1 and phase=='late') or (sign==-1 and phase=='early') else 0.
            events.append(dict(key=phase,phase=phase,session=phase,primary=dict(eligible=True,gradient=gradient),
                outcome_shuffle=dict(eligible=True,gradient=0.),token_scope=dict(truncated=False)))
        units.append(dict(writer=str(wi),events=events,exclusions=[],menu_exclusions=[],model_failures=2,own_failures=0))
    result=card.summarize(units,card.CONFIG)
    assert result['primary']['state']==state
    assert result['primary']['effect']==sign*2
    assert result['outcome_shuffle']['state']=='null'


def test_choice_shuffle_preserves_offers_and_ignored_outcomes():
    rows=menus(before=0,after=-1)
    shuffled=card.shuffle_choices(rows,'w',20261017)
    assert sorted(shuffled.values())==sorted(r['chosen'] for r in rows)
    assert shuffled==card.shuffle_choices(rows,'w',20261017)
    assert any(shuffled[r['key']]!=r['chosen'] for r in rows)


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value),encoding='utf8')


def full_fixture(root,writers=3,model_identity_path=None,null_outcomes=False):
    root.mkdir(parents=True,exist_ok=True)
    content=root/'content'; d39=root/'d39'; p5=root/'p5'
    inputs=dict(sessions=str(root/'SESSIONS.json'),content_records=str(content/'RECORDS.json'),
        content_vectors=str(content/'VECTORS.npy'),content_model=str(Path(model_identity_path).resolve()) if model_identity_path else str(content/'MODEL.json'),
        content_complete=str(content/'COMPLETE.json'),d39_failures=str(d39/'output/FAILURES.json'),
        d39_inputs=str(d39/'output/INPUTS.json'),d39_completion=str(d39/'COMPLETE.json'),
        p5_inputs=str(p5/'output/INPUTS.json'),p5_summary=str(p5/'output/SUMMARY.json'),p5_completion=str(p5/'COMPLETE.json'))
    sessions,records,failures=[],[],[]
    for wi in range(writers):
        for si in range(2):
            writer,sid=f'w{wi}',f'w{wi}s{si}'
            rows=[]
            for m in menus(after=2 if si else 0):
                key=sid+m['key']
                rows.append(dict(key=key,writer=writer,session=sid,ordinal=m['ordinal'],end_ordinal=m['end_ordinal'],
                    menu=['near','middle','far'],inserted='' if null_outcomes and m['ordinal'] else ['near','middle','far'][m['chosen']],
                    handling='edit' if m['ordinal']==0 else 'dismiss' if null_outcomes else 'accept'))
                records.append(dict(key=key,writer=writer,session=sid,options=[0,1,2]))
            sessions.append(dict(writer=writer,session=sid,timestamp=si*1000,end_at=si*1000+999,rows=rows))
            text='Original deleted span.'
            failures.append(dict(writer=writer,session=sid,session_index=si,kind='model',source_span_ordinal=0,ordinal=125,
                deleted_text=text,original_codepoints=len(text),deleted_codepoints=math.ceil(.8*len(text))))
    write(Path(inputs['sessions']),sessions);write(Path(inputs['content_records']),records)
    np.save(inputs['content_vectors'],vectors())
    if model_identity_path is None:
        cache=root/'fake-model/revision';cache.mkdir(parents=True)
        weights=cache/'weights.fixture';weights.write_bytes(b'test-only no real model')
        write(Path(inputs['content_model']),dict(repo='sentence-transformers/all-MiniLM-L6-v2',path=str(cache),revision='revision',files={weights.name:card.filehash(weights)}))
    write(Path(inputs['content_complete']),dict(status='COMPLETE',outputs={Path(inputs[k]).name:card.filehash(inputs[k]) for k in ('content_records','content_vectors','content_model')}))
    write(Path(inputs['d39_failures']),failures)
    write(Path(inputs['d39_inputs']),dict(paths={'sessions':inputs['sessions']},pins={inputs['sessions']:card.filehash(inputs['sessions'])}))
    write(Path(inputs['d39_completion']),dict(status='COMPLETE',fresh_process_verified=True,
        outputs={Path(inputs[k]).relative_to(d39).as_posix():card.filehash(inputs[k]) for k in ('d39_failures','d39_inputs')}))
    write(Path(inputs['p5_inputs']),dict(paths={k:inputs[k] for k in ('sessions','content_model')},
        sha256={k:card.filehash(inputs[k]) for k in ('sessions','content_model')}))
    write(Path(inputs['p5_summary']),dict(sessions=len(sessions)))
    write(Path(inputs['p5_completion']),dict(status='COMPLETE',fresh_process_verified=True,
        outputs={Path(inputs[k]).relative_to(p5).as_posix():card.filehash(inputs[k]) for k in ('p5_inputs','p5_summary')}))
    return inputs


class FakeEncoder:
    def __init__(self,*args):pass
    def encode(self,texts):
        return np.tile(vectors()[0],(len(texts),1)),[dict(full_tokens=3,used_tokens=3,truncated=False,codepoint_end=len(t)) for t in texts]


def test_actual_source_handler_yield_fresh_replay_and_mutation(tmp_path,monkeypatch):
    inputs=full_fixture(tmp_path/'source')
    output=tmp_path/'output'
    monkeypatch.setattr(card,'Encoder',FakeEncoder)
    original=card.score_writer;calls=[]
    def score(*args):
        calls.append(args[0]['writer'])
        result=original(*args)
        if len(calls)==1:write(output/'YIELD_REQUEST.json',{})
        return result
    monkeypatch.setattr(card,'score_writer',score)
    assert card.execute(output,inputs,card.CONFIG)['status']=='yielded'
    (output/'YIELD_REQUEST.json').unlink()
    result=card.execute(output,inputs,card.CONFIG)
    assert len(calls)==3 and result['primary']['effect']==2 and result['primary']['state']=='positive'
    assert card.verify(output,inputs,card.CONFIG)['verified']
    args=tmp_path/'args.json';write(args,dict(output=str(output),inputs=inputs,config=card.CONFIG))
    script="import json,sys; from pathlib import Path; from runners.drive.cards.events_d38 import verify; a=json.load(open(sys.argv[1])); print(json.dumps(verify(Path(a['output']),a['inputs'],a['config'])))"
    child=subprocess.run([sys.executable,'-B','-c',script,str(args)],capture_output=True,text=True,env=dict(os.environ,PYTHONHASHSEED='633'),check=True)
    assert json.loads(child.stdout)['verified']
    with pytest.raises(ValueError,match='never rerun'):card.execute(output,inputs,card.CONFIG)
    Path(inputs['d39_failures']).write_text('[]',encoding='utf8')
    with pytest.raises(ValueError,match='input changed'):card.verify(output,inputs,card.CONFIG)


def test_exact_origin_and_ambiguity_exclusions(tmp_path):
    inputs=full_fixture(tmp_path)
    data=card.source(inputs)
    data[0][0]['rows'][0]['handling']='ignore'
    support=card.writer_support('w0',*data,card.CONFIG)
    assert len(support['events'])==1 and support['exclusions'][0]['reason']=='missing exact originating acceptance'
    row=copy.deepcopy(data[0][1]['rows'][1]);row['menu']=['near','near','far']
    result,reason=card.eligible_menu(row,data[1][row['key']],data[2])
    assert result is None and reason=='selected offer missing or ambiguous'

