from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
import json
import pytest
from runners.stage10 import earlier_programs as programs, earlier_memory as memory, earlier_routes as routes, ollama
from runners.stage10 import human_programs, human_memory_checks as fixtures
from runners.stage10.contracts import canonical, digest


def task(i, words=3, prior=None):
    t=fixtures.task(i,words)
    return replace(t,evidence_view='earlier-artifacts',evidence={**t.evidence,'earlier_drafts':[] if prior is None else [prior]})


def training(kind='signal'):
    public,answers=fixtures.rows(kind)
    for r in public:
        r['evidence_view']='earlier-artifacts';r['evidence']['earlier_drafts']=['the earlier draft']
    return public,answers


def test_same_rule_and_current_state_remain_identical_when_prior_changes():
    candidates=[{'goal_hypothesis':'constructed','program':{'feature':'draft_words','threshold':6,'below':'accept','otherwise':'edit'}}]
    for words in (2,10):
        expected=human_programs.evaluate(fixtures.task(100,words),candidates)
        for prior in (None,'word '*words,'earlier text with quite different content'):
            t=task(100,words,prior)
            assert programs.evaluate(t,candidates)==expected
            body=json.loads(routes.proposal.request_for(t)['messages'][1]['content'])
            assert body['task']['evidence']==t.evidence
            assert body['public_features']==expected['features']
            assert body['feature_definitions']==human_programs.FEATURES


@pytest.mark.parametrize('extra',[{'earlier_handling':['accept']},{'private_goal':'secret'},{'future_document':'secret'}])
def test_private_records_refuse(extra):
    t=task(200,prior='past');t=replace(t,evidence={**t.evidence,**extra})
    with pytest.raises(ValueError):routes.proposal.request_for(t)


@pytest.mark.parametrize('prior',[None,'not a list',[1],['one','two']])
def test_bad_prior_shape_refuses(prior):
    t=task(201);t=replace(t,evidence={**t.evidence,'earlier_drafts':prior})
    with pytest.raises(ValueError):programs.features(t)


def test_induction_signal_null_and_support():
    learned=memory.induce(*training())
    rule=learned['libraries']['earlier-artifacts'][0]['program']
    assert programs.execute(rule,programs.features(task(100,2)))['action']=='accept'
    assert programs.execute(rule,programs.features(task(101,10)))['action']=='edit'
    for kind in ('null','constant','one-group'):
        assert not memory.induce(*training(kind))['libraries']['earlier-artifacts']


def test_common_store_and_naming_preserve_same_definitions():
    public,answers=training();learned=memory.induce(public,answers);t=task(100,prior='old')
    got={arm:routes.representation_for(t,public,answers,learned,arm) for arm in routes.ARMS}
    assert got['R3'][0] is None and not got['R1-memory'][0]['procedures']
    opaque,grounded=got['R4-opaque'][0],got['R4-grounded'][0]
    assert [p['program'] for p in opaque['procedures']]==[p['program'] for p in grounded['procedures']]
    assert opaque['examples']==grounded['examples']
    for arm,(rep,receipt) in got.items():
        if rep is not None:
            assert len(canonical(rep).encode('utf8'))<=receipt['effective_store_limit_bytes']<=6000
            assert 'writer_component' not in canonical(rep)
    with pytest.raises(ValueError):routes.representation_for(t,public,answers,learned,'unimplemented')


def test_complete_selected_science_queue_replay_and_failures(tmp_path,monkeypatch):
    source=tmp_path/'source'; fit=tmp_path/'fit';selected=tmp_path/'selected'
    public,answers=training();records={'train-public.json':{'tasks':public},'train-evaluator.json':{'targets':answers}}
    ids={}
    for phase,offset in (('development',100),('evaluation',200)):
        targets=[task(offset,2,'old'),task(offset+1,10,'word '*10),task(offset+2,2,'x'*20000)]
        records[phase+'-public.json']={'tasks':[asdict(t) for t in targets]}
        ids[phase]=[{'task_id':t.task_id,'writer_component':phase,'prompt_component':phase,'original_task_id':t.task_id} for t in targets]
    records['IDENTITIES.json']=ids
    records['FROZEN.json']={'public_sha256':{p:digest(records[p+'-public.json']) for p in ('train','development','evaluation')},
        'evaluator_sha256':{'train':digest(records['train-evaluator.json'])},'identities_sha256':digest(ids),'exclusions':[]}
    for name,value in records.items():ollama.write_new(source/name,value)
    original_read=Path.read_text
    def guarded(p,*a,**k):
        if p.name in ('evaluation-evaluator.json','development-evaluator.json'):raise AssertionError('target outcomes opened')
        return original_read(p,*a,**k)
    monkeypatch.setattr(Path,'read_text',guarded)
    learned=memory.fit(source,fit);frozen=routes.selection(source,source,fit,selected)
    assert [r['tasks'] for r in frozen['counts'].values()]==[2,2]
    assert len(frozen['additional_context_exclusions'])==2
    assert routes.selection(source,source,fit,selected)==frozen
    calls=[]
    def api(path,request):
        body=json.loads(request['messages'][1]['content']); choices=body['task']['choices']
        if 'candidates' in request['format']['properties']:
            response={'candidates':[{'goal_hypothesis':'constructed','program':{'feature':'draft_words','threshold':6,'below':'accept','otherwise':'edit'}}],
                'choice':choices[0]['id'],'insufficient_support':False}
        else:response={'choice':choices[0]['id'],'probabilities':{c['id']:.25 for c in choices},'insufficient_evidence':True,'explanation':'fixture'}
        # One actual malformed first proposal must remain charged and terminate early.
        content='{}' if not calls else canonical(response)
        calls.append(request)
        return {'done':True,'done_reason':'stop','message':{'content':content},'eval_count':100,'prompt_eval_count':1000,
            'total_duration':1,'load_duration':0,'prompt_eval_duration':0,'eval_duration':1}
    monkeypatch.setattr(ollama,'api',api);monkeypatch.setattr(ollama,'identity',lambda:{'fixture':True})
    monkeypatch.setattr(routes,'GPU_LOCK',tmp_path/'unused-lock')
    monkeypatch.setattr(routes,'native_identity',lambda *a:{'pid':0,'fixture':True})
    monkeypatch.setattr(routes,'acquire_gpu_lock',lambda *a:None);monkeypatch.setattr(routes,'release_gpu_lock',lambda:None)
    pilot=tmp_path/'pilot.json';ollama.write_new(pilot,{'status':'PASS','sources':routes.identity(),'memory_sha256':digest(learned)})
    output=tmp_path/'queue';result=routes.run(selected,source,fit,output,('development','evaluation'),pilot)
    assert len(result['rows'])==16 and len(calls)==27 and sum(r['status']=='INVALID' for r in result['rows'])==1
    assert result['model_calls']==27 and result['generated_tokens']==2700
    before={str(p):p.read_bytes() for p in output.rglob('*') if p.is_file()}
    def forbidden(*a,**k):raise AssertionError('unexpected inference or execution in replay')
    monkeypatch.setattr(ollama,'api',forbidden);monkeypatch.setattr(programs,'evaluate',forbidden)
    assert routes.run(selected,source,fit,output,('development','evaluation'),pilot)==result
    assert before=={str(p):p.read_bytes() for p in output.rglob('*') if p.is_file()}
    raw=next(output.rglob('RAW.json')); saved=raw.read_bytes();raw.write_text('{}',encoding='utf8')
    with pytest.raises(ValueError):routes.run(selected,source,fit,output,('development','evaluation'),pilot)
    raw.write_bytes(saved)
    changed=deepcopy(records['train-public.json']);changed['tasks'][0]['evidence']['document']='changed'
    (source/'train-public.json').write_text(canonical(changed),encoding='utf8')
    with pytest.raises(ValueError):routes.run(selected,source,fit,output,('development','evaluation'),pilot)
