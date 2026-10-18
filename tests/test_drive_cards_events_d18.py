import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest
from runners.drive.cards import events_d18 as card
from runners.drive.cards import events_d18_spans as spans
from runners.drive.timeline import rebuild
from runners.stage9.coauthor import units, text_of, apply_delta


def event(i, name='text-insert', source='user', **kw):
    return dict(eventNum=i, eventTimestamp=1000+i*100, eventName=name, eventSource=source, **kw)


class Stream:
    def __init__(self, prompt='AAAA\n'):
        self.events=[event(0,'system-initialize','api',currentDoc=prompt)]; self.doc=units(prompt)
    def add(self, ops=None, name='text-insert', source='user'):
        kw={} if ops is None else {'textDelta':{'ops':ops}}
        self.events.append(event(len(self.events),name,source,**kw))
        if ops is not None:self.doc,_,_=apply_delta(self.doc,[None]*len(self.doc),{'ops':ops})
    def insert(self,text,delete=False):
        at=len(self.doc)-1
        self.add([{'retain':at},{'insert':text}])
        if delete:self.add([{'retain':at},{'delete':len(units(text))}],name='text-delete')
        else:self.add(name='cursor-forward')
    def result(self):return self.events,rebuild(self.events,[])


def test_original_atoms_distinguish_retyping_and_surrogate_survival():
    s=Stream();s.insert('\U0001f600AB',True);s.insert('\U0001f600AB')
    data=spans.extract(*s.result());a,b=data['spans']
    assert [(r['status'],r['codepoints']) for r in (a,b)]==[('deleted',3),('retained',3)]
    assert a['surviving_codepoints']==0 and b['surviving_codepoints']==3
    assert spans.match(data['spans'])[0]==[dict(origin='typed',deleted='0',retained='1',deleted_codepoints=3,retained_codepoints=3)]
    s=Stream();s.insert('\U0001f600AB');s.events.append(event(len(s.events),'text-delete',textDelta={'ops':[{'retain':5},{'delete':1}]}))
    with pytest.raises(UnicodeError):spans.extract(s.events,dict(initial_document='AAAA\n',final_document=''))


def test_partial_deletion_and_internal_insertion_are_not_intact():
    s=Stream();s.insert('ABCD');s.add([{'retain':5},{'delete':1}],name='text-delete')
    data=spans.extract(*s.result());row=data['spans'][0]
    assert row['status']=='partial' and row['surviving_codepoints']==3
    assert data['support']['all_partial_original_codepoints']==4
    assert data['support']['all_partial_surviving_codepoints']==3
    s=Stream();s.insert('ABCD');s.add([{'retain':6},{'insert':'X'}])
    data=spans.extract(*s.result())
    assert data['spans'][0]['status']=='partial' and data['spans'][0]['surviving_codepoints']==4
    assert not data['spans'][0]['original_contiguous_at_end']


def test_contiguous_runs_break_on_other_event_and_replacements_stay_separate():
    s=Stream();s.add([{'retain':4},{'insert':'a'}]);s.add([{'retain':5},{'insert':'b'}])
    s.add(name='cursor-forward');s.add([{'retain':6},{'insert':'c'}])
    s.add([{'retain':6},{'delete':1},{'insert':'d'}])
    data=spans.extract(*s.result())
    assert [(r['text'],r['insertions'],r['status']) for r in data['spans']]==[('ab',2,'retained'),('c',1,'deleted'),('d',1,'retained')]


def test_accepted_canonical_terminal_newline_and_system_deletion():
    s=Stream();s.add(name='suggestion-open');s.add(name='suggestion-select')
    # API inserts after Quill's existing newline; canonical append owns the
    # shifted newline and the actual new text, preserving the old terminal.
    s.add([{'retain':5},{'insert':'\U0001f600AB\n'}],source='api')
    data=spans.extract(*s.result())
    assert data['spans'][0]['text']=='\n\U0001f600AB'
    assert data['spans'][0]['origin']=='accepted'
    assert data['spans'][0]['status']=='retained'
    s.add([{'retain':4},{'delete':5}],source='api',name='text-delete')
    data=spans.extract(*s.result());row=data['spans'][0]
    assert row['status']=='deleted' and row['system_deleted_codepoints']==4
    pairs,excluded=spans.match(data['spans'])
    assert not pairs and excluded[0]['reason']=='system deletion involved'


def stub(key,length,status='retained',origin='typed',ordinal=None):
    return dict(key=str(key),codepoints=length,status=status,origin=origin,ordinal=int(key) if ordinal is None else ordinal,
                lexical=True,system_deleted_codepoints=0)


def test_matching_exact_caliper_source_ties_and_disjoint_origin():
    rows=[stub(0,8,'deleted'),stub(1,10),stub(2,10),stub(3,8,'deleted'),stub(4,8,'deleted'),stub(5,8,origin='accepted')]
    pairs,exclusions=spans.match(rows)
    assert [(p['deleted'],p['retained']) for p in pairs]==[('0','1'),('3','2')]
    assert any(e==dict(key='4',reason='no unused same-origin length match') for e in exclusions)
    assert not spans.match([stub(0,8,'deleted'),stub(1,11)])[0]


@pytest.mark.parametrize('world,state',[('null','null'),('positive','positive'),('reverse','negative')])
def test_known_answer_reliability(world,state):
    x=np.tile([-2.,-1.,1.,2.],10); y=x if world=='positive' else -x if world=='reverse' else np.tile([1.,-1.,-1.,1.],10)
    result=card.reliability(np.column_stack((x,y)),card.CONFIG)
    assert result['state']==state
    assert result['effect']==pytest.approx(0 if world=='null' else 1 if world=='positive' else -1,abs=1e-14)
    assert result['standard_error']>=0 and 'not permutation p' in result['p_method']
    assert card.reliability([[1,1]]*40,card.CONFIG)['state']=='invalid'
    assert card.reliability([[0,0],[1,1],[2,2]],card.CONFIG)['state']=='invalid'


def test_session_chronology_parity_equal_weight_and_ties():
    sessions=[]
    for i,rate in enumerate((0.,1.,1.,0.)):
        pair=dict(origin='typed',sacrifice=int(rate),deleted_prompt_fit=0. if rate else 1.,retained_prompt_fit=1.,tied=not bool(rate))
        sessions.append(dict(writer='w',session=f's{i}',session_order=i,scored_pairs=[pair]*(1 if i<2 else 50),
            support={},token_scopes=[],session_exclusion=None,exclusions=[]))
    result=card.summarize(list(reversed(sessions)),card.CONFIG)
    assert result['per_writer'][0]['halves']['all']==[.5,.5]
    assert result['tied_pairs']==51
    sessions[0]['scored_pairs']=[]
    result=card.summarize(sessions,card.CONFIG)
    assert result['per_writer'][0]['exclusions']['all']['sessions']==[1,2]


def test_undefined_draw_is_not_silently_dropped_and_tie_counts_zero():
    result=card.reliability([[0,0],[1,1],[2,2],[3,3]],card.CONFIG)
    assert result['state']=='invalid' and result['invalid_bootstrap']>0
    unit=dict(text_inputs=['AAAA'],prompt_available=True,pairs=[dict(deleted_vector=0,retained_vector=0)])
    vectors,scopes=FakeEncoder().encode(unit['text_inputs'])
    result=card.score_session(unit,vectors,scopes)
    assert result['scored_pairs'][0]['sacrifice']==0 and result['scored_pairs'][0]['tied']
    unit=dict(text_inputs=[],prompt_available=False,pairs=[{}])
    result=card.score_session(unit,np.empty((0,384)),[])
    assert result['session_exclusion']=='empty supplied prompt/context' and not result['scored_pairs']


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value),encoding='utf8')


def full_fixture(root,writers=12,model_identity_path=None):
    root.mkdir(parents=True,exist_ok=True); p5=root/'p5';content=root/'content';p2=root/'p2'
    inputs=dict(sessions=str(root/'SESSIONS.json'),p2_index=str(p2/'SESSION_INDEX.json'),source_root=str(root),
        source_roster=str(root/'ROSTER.json'),content_model=str(Path(model_identity_path).resolve()) if model_identity_path else str(content/'MODEL.json'),
        content_complete=str(content/'COMPLETE.json'),p5_inputs=str(p5/'output/INPUTS.json'),
        p5_summary=str(p5/'output/SUMMARY.json'),p5_completion=str(p5/'COMPLETE.json'))
    sessions,index,roster=[],[],[]
    for wi in range(writers):
        for si in range(4):
            sid,writer=f'w{wi:02}s{si}',f'w{wi:02}'
            s=Stream()
            for pair in range(writers):
                success=pair<wi
                s.insert('BBBB' if success else 'AAAA',True);s.insert('AAAA' if success else 'BBBB')
            events,timeline=s.result();raw=root/'raw'/f'{sid}.jsonl';raw.parent.mkdir(parents=True,exist_ok=True)
            raw.write_text(''.join(json.dumps(e)+'\n' for e in events),encoding='utf8')
            p2path=p2/f'{sid}.json';write(p2path,timeline)
            sessions.append(dict(session=sid,writer=writer,timestamp=si*10000,rows=[]))
            roster.append(dict(session=sid,writer=writer,path=raw.relative_to(root).as_posix(),source_sha256=card.filehash(raw)))
            index.append(dict(session=sid,writer=writer,file=p2path.name,sha256=card.filehash(p2path)))
    write(Path(inputs['sessions']),sessions);write(Path(inputs['p2_index']),index);write(Path(inputs['source_roster']),roster)
    if model_identity_path is None:
        cache=root/'fake-model/revision';cache.mkdir(parents=True);weight=cache/'fixture';weight.write_bytes(b'not real model')
        write(Path(inputs['content_model']),dict(repo='sentence-transformers/all-MiniLM-L6-v2',path=str(cache),revision='revision',files={weight.name:card.filehash(weight)}))
    write(Path(inputs['content_complete']),dict(status='COMPLETE',outputs={'MODEL.json':card.filehash(inputs['content_model'])}))
    source_keys=('sessions','p2_index','source_root','source_roster','content_model')
    write(Path(inputs['p5_inputs']),dict(paths={k:inputs[k] for k in source_keys},sha256={k:card.filehash(inputs[k]) for k in source_keys if k!='source_root'}))
    write(Path(inputs['p5_summary']),dict(sessions=len(sessions)))
    write(Path(inputs['p5_completion']),dict(status='COMPLETE',fresh_process_verified=True,
        outputs={Path(inputs[k]).relative_to(p5).as_posix():card.filehash(inputs[k]) for k in ('p5_inputs','p5_summary')}))
    return inputs


class FakeEncoder:
    def __init__(self,*args):pass
    def encode(self,texts):
        values=np.zeros((len(texts),384),np.float32)
        for i,text in enumerate(texts):values[i,0 if text.strip()=='AAAA' else 1]=1
        return values,[dict(full_tokens=len(t),used_tokens=min(254,len(t)),truncated=len(t)>254,codepoint_end=min(254,len(t))) for t in texts]


def test_actual_handler_yield_resume_and_fresh_source_replay(tmp_path,monkeypatch):
    inputs=full_fixture(tmp_path/'source');output=tmp_path/'output';monkeypatch.setattr(card,'Encoder',FakeEncoder)
    original=card.score_session;calls=[]
    def score(*args):
        calls.append(args[0]['session']);result=original(*args)
        if len(calls)==1:write(output/'YIELD_REQUEST.json',{})
        return result
    monkeypatch.setattr(card,'score_session',score)
    assert card.execute(output,inputs,card.CONFIG)['status']=='yielded'
    (output/'YIELD_REQUEST.json').unlink()
    result=card.execute(output,inputs,card.CONFIG)
    assert len(calls)==48 and result['primary']['state']=='positive' and result['primary']['effect']==pytest.approx(1.)
    assert result['accepted_specification']['state']=='invalid'
    first=card.read(output/'FIRST_TENTH.json')
    assert first['sessions']==5 and first['total_sessions']==48
    request=tmp_path/'VERIFY.json';write(request,dict(inputs=inputs,config=card.CONFIG,output=str(output)))
    code='import json,sys;from pathlib import Path;from runners.drive.cards.events_d18 import verify;r=json.load(open(sys.argv[1]));print(json.dumps(verify(Path(r["output"]),r["inputs"],r["config"])))'
    child=subprocess.run([sys.executable,'-B','-c',code,str(request)],text=True,capture_output=True,env=dict(os.environ,PYTHONHASHSEED='175'))
    assert child.returncode==0,child.stderr
    assert json.loads(child.stdout)['verified']
    with pytest.raises(ValueError,match='never rerun'):card.execute(output,inputs,card.CONFIG)
    raw=Path(inputs['source_root'])/card.read(inputs['source_roster'])[0]['path'];raw.write_text(raw.read_text()+'\n')
    with pytest.raises(ValueError,match='raw/P2 input changed'):card.verify(output,inputs,card.CONFIG)


def test_missing_prompt_no_match_and_output_tampering(tmp_path,monkeypatch):
    s=Stream('\n');s.insert('AAAA',True);s.insert('BBBB')
    data=spans.extract(*s.result());assert not data['prompt'].strip() and spans.match(data['spans'])[0]
    inputs=full_fixture(tmp_path/'source',writers=1);output=tmp_path/'output';monkeypatch.setattr(card,'Encoder',FakeEncoder)
    result=card.execute(output,inputs,card.CONFIG);assert result['primary']['state']=='invalid'
    summary=card.read(output/'SUMMARY.json');summary['matched_pairs']+=1;write(output/'SUMMARY.json',summary)
    with pytest.raises(ValueError,match='output changed'):card.verify(output,inputs,card.CONFIG)


def test_unchanged_prompt_and_final_source_authentication():
    s=Stream();s.insert('ABCD');events,timeline=s.result()
    with pytest.raises(ValueError,match='initial prompt'):spans.extract(events,dict(timeline,initial_document='changed'))
    with pytest.raises(ValueError,match='final replay'):spans.extract(events,dict(timeline,final_document='changed'))
