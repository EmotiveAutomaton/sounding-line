from dataclasses import asdict,replace
from pathlib import Path
from copy import deepcopy
import json
import pytest
from runners.stage10 import earlier_artifacts as earlier, ollama
from runners.stage10.human_memory_checks import task as fixture_task
from runners.stage10.contracts import canonical,digest


def source():
    return {'key':'session','events':[{'ordinal':1,'document':'old draft','usable':True,'options':[{'trimmed':'idea'}]},
        {'ordinal':2,'document':'current draft','usable':True,'options':[{'trimmed':'next'}]},
        {'ordinal':3,'document':'FUTURE','usable':True,'options':[{'trimmed':'FUTURE'}]}]}

def test_prior_snapshot_is_strictly_before_current_without_records():
    rows=earlier.index_session(source()); row=rows[digest({'session':'session','event':2})]
    t=replace(fixture_task(10,3,'artifact'),evidence={'document':'current draft','suggestions':['next']})
    got=earlier.extend(t,row)
    assert got.evidence=={**t.evidence,'earlier_drafts':['old draft']}
    assert got.choices==t.choices and got.question==t.question and got.evidence_view=='earlier-artifacts'
    assert 'FUTURE' not in canonical(got.public())

def test_first_and_identical_snapshots_are_retained():
    s=source(); s['events'][1]['document']='old draft'; rows=earlier.index_session(s)
    assert rows[digest({'session':'session','event':1})]['prior'] is None
    assert rows[digest({'session':'session','event':2})]['prior']['document']=='old draft'

@pytest.mark.parametrize('ordinal',[1,0,-1])
def test_reversed_or_duplicate_chronology_refuses(ordinal):
    s=source();s['events'][1]['ordinal']=ordinal
    with pytest.raises(ValueError):earlier.index_session(s)

def test_private_fields_cannot_reach_projection():
    s=source();s['final_document']='SECRET';s['events'][0]['decision']='SECRET'
    assert 'SECRET' not in canonical(earlier.projection(canonical(s)))

def test_changed_menu_or_future_prior_refuses():
    row=earlier.index_session(source())[digest({'session':'session','event':2})]
    t=replace(fixture_task(10,3,'artifact'),evidence={'document':'changed','suggestions':['next']})
    with pytest.raises(ValueError):earlier.extend(t,row)
    t=replace(t,evidence={'document':'current draft','suggestions':['next']}); row['prior']['ordinal']=2
    with pytest.raises(ValueError):earlier.extend(t,row)


def test_whole_preparation_chain_replay_and_corruption(tmp_path,monkeypatch):
    original=tmp_path/'original'; sessions=tmp_path/'sessions'; prepared=tmp_path/'prepared'
    public={}; answers={}; pins={}
    for n,phase in enumerate(('train','development','evaluation')):
        session=source(); session['key']=phase
        p=sessions/(phase+'.json');ollama.write_new(p,session);pins[phase]=earlier.hashlib.sha256(p.read_bytes()).hexdigest()
        tasks=[];targets=[]
        for ordinal in (1,2):
            event=session['events'][ordinal-1]
            t=replace(fixture_task(n*100+ordinal,3,'artifact'),evidence={'document':event['document'],'suggestions':[r['trimmed'] for r in event['options']]})
            tasks.append(asdict(t));targets.append(dict(task_id=t.task_id,source_event=digest({'session':phase,'event':ordinal}),writer_component=phase,prompt_component=phase,correct_choice=t.choices[0][0]))
        public[phase]={'tasks':tasks};answers[phase]={'targets':targets}
        ollama.write_new(original/(phase+'-public.json'),public[phase]);ollama.write_new(original/(phase+'-evaluator.json'),answers[phase])
    src={'source_sessions':pins};ollama.write_new(original/'SOURCE.json',src)
    ollama.write_new(original/'FROZEN.json',dict(source_sha256=digest(src),public_sha256={k:digest(v) for k,v in public.items()},evaluator_sha256={k:digest(v) for k,v in answers.items()}))
    original_text=Path.read_text
    def guarded(p,*a,**k):
        if p.name in ('evaluation-evaluator.json','development-evaluator.json'):raise AssertionError('outcomes opened')
        return original_text(p,*a,**k)
    monkeypatch.setattr(Path,'read_text',guarded)
    frozen=earlier.prepare(original,sessions,prepared)
    assert earlier.prepare(original,sessions,prepared)==frozen
    assert frozen['counts']['evaluation']['tasks']==2 and not frozen['exclusions']
    calls=[]
    def api(path,request):
        choices=json.loads(request['messages'][1]['content'])['task']['choices']
        response=dict(choice=choices[0]['id'],probabilities={c['id']:.25 for c in choices},insufficient_evidence=True,explanation='constructed')
        calls.append(request)
        return dict(done=True,done_reason='stop',message={'content':canonical(response)},eval_count=50,prompt_eval_count=100,total_duration=1,load_duration=0,prompt_eval_duration=0,eval_duration=1)
    monkeypatch.setattr(ollama,'api',api);monkeypatch.setattr(ollama,'identity',lambda:{'fixture':True})
    for module in (earlier.phase_queue,earlier.phase_deliberation):
        monkeypatch.setattr(module,'GPU_LOCK',tmp_path/'unused-lock')
        monkeypatch.setattr(module,'acquire_gpu_lock',lambda *a:None);monkeypatch.setattr(module,'release_gpu_lock',lambda:None)
        monkeypatch.setattr(module,'native_identity',lambda *a:{'fixture':True,'pid':0})
    pilot=tmp_path/'pilot.json';ollama.write_new(pilot,dict(status='PASS',sources=earlier.identity(),prepared_sha256=digest(frozen),fixture=True))
    out=tmp_path/'queue';result=earlier.run(prepared,out,pilot)
    assert result['model_calls']==16 and len(calls)==16 and len(result['jobs'])==4
    before={str(p):p.read_bytes() for p in out.rglob('*') if p.is_file()}
    def forbidden(*a,**k):raise AssertionError('new inference on replay')
    monkeypatch.setattr(ollama,'api',forbidden)
    assert earlier.run(prepared,out,pilot)==result
    assert before=={str(p):p.read_bytes() for p in out.rglob('*') if p.is_file()}
    raw=next(out.rglob('RAW.json'));raw.write_text('{}',encoding='utf8')
    with pytest.raises(ValueError):earlier.run(prepared,out,pilot)
