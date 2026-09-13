from dataclasses import asdict, replace
import copy
import json
import pytest

from runners.stage10 import revision_source as source, revision_programs as programs
from runners.stage10 import revision_readers as readers, revision_memory as memory, ollama
from runners.stage10.contracts import digest


def record(i=0, group='project-a', truth='PLANNING', kind='schola_category'):
    current=('word '*(5+i))+'\\cite{x}'
    before='earlier '+('word '*max(1,i))
    return {'key':digest([group,i,kind]),'source_key':digest([group,i]),'source_ordinal':2*i,
        'target_source_ordinal':2*i+1,'unit':group,'kind':kind,'truth':truth,
        'views':{'artifact':{'document':current},'record':{'document':current,'previous_document':before,
                 'previous_category':'PLANNING','previous_location':'first_quarter'}}}


def training_bank():
    training,answers=[],[]
    for g in ['project-a','project-b','project-c']:
        for i in [0,20]:
            row=record(i,g,truth='PLANNING' if i==0 else 'REVISION')
            for view in ['artifact','earlier-artifacts','process-record']:
                task=source.task_from(row,view);training.append(asdict(task))
                correct=next(k for k,v in task.choices if v==source.DESCRIPTIONS[row['kind']][row['truth']])
                answers.append({'task_id':task.task_id,'correct_choice':correct,'writer_component':g,'source_event':row['key']})
    return training,answers


def fake_model(monkeypatch, calls):
    monkeypatch.setattr(ollama,'identity',lambda:{'model':ollama.MODEL,'digest':ollama.MODEL_DIGEST})
    def api(path,request=None,**kwargs):
        assert path=='/api/chat';calls.append(request)
        schema=request['format']['properties'];choice=schema['choice']['enum'][0]
        if 'candidates' in schema:
            actions=schema['candidates']['items']['properties']['program']['properties']['below']['enum']
            result={'candidates':[{'goal_hypothesis':'test conjecture','program':{'feature':'constant','threshold':1,'below':actions[0],'otherwise':actions[-1]}}],
                    'choice':choice,'insufficient_support':False}
        else:
            keys=schema['choice']['enum']
            result={'probabilities':{k:1/len(keys) for k in keys},'choice':choice,'insufficient_evidence':True,'explanation':'constructed known forecast'}
        return {'done':True,'done_reason':'stop','message':{'content':json.dumps(result)},'eval_count':12,
            'prompt_eval_count':20,'total_duration':10,'load_duration':1,'prompt_eval_duration':2,'eval_duration':7}
    monkeypatch.setattr(ollama,'api',api)


def test_chronology_evidence_and_source_native_targets_are_distinct():
    row=record();a=source.task_from(row,'artifact');h=source.task_from(row,'earlier-artifacts');p=source.task_from(row,'process-record')
    assert set(a.evidence)=={'document'} and set(h.evidence)=={'document','earlier_drafts'}
    assert 'previous_category' not in h.evidence and p.evidence['previous_category']=='PLANNING'
    changed=copy.deepcopy(row);changed['truth']='REVISION'
    assert source.task_from(changed,'artifact').public()==a.public()
    changed['target_source_ordinal']=changed['source_ordinal']
    with pytest.raises(ValueError,match='later'):source.task_from(changed,'artifact')
    with pytest.raises(ValueError,match='unexpected'):programs.features(replace(a,evidence={**a.evidence,'future_truth':'REVISION'}))
    location=source.task_from(record(kind='schola_location',truth='first_quarter'),'artifact')
    assert len(location.choices)==5 and len(a.choices)==3


def test_known_rules_and_training_compression():
    training,answers=training_bank();library=memory.induce(training,answers)
    assert any(library['libraries'].values())
    task=source.task_from(record(5,'held-out'),'artifact');observed=programs.features(task)
    rule={'feature':'draft_words','threshold':15,'below':'PLANNING','otherwise':'REVISION'}
    assert programs.execute(rule,observed,task)['action']=='PLANNING'
    assert programs.execute(rule,{**observed,'draft_words':30},task)['action']=='REVISION'
    candidates=[{'goal_hypothesis':'not a ground truth','program':rule}]
    result=programs.evaluate(task,candidates)
    assert sum(result['probabilities'].values())==pytest.approx(1)
    with pytest.raises(ValueError,match='duplicate'):programs.evaluate(task,candidates*2)
    with pytest.raises(ValueError,match='outside'):programs.validate({**rule,'below':'no_change'},task)


def test_all_routes_actual_execution_cost_and_immutable_replay(tmp_path,monkeypatch):
    training,answers=training_bank();runner=readers.Readers(training,answers);calls=[];fake_model(monkeypatch,calls)
    task=source.task_from(record(5,'held-out'),'process-record');assert runner.preflight(task)
    original={}
    for arm,n in [('R0',1),('R1',1),('R2',2),('R3',2),('R4-grounded',2),('R4-opaque',2)]:
        value=runner.route(task,tmp_path/arm,arm);original[arm]=value
        assert value['status']=='VALID' and value['cost']['model_calls']==n
        assert value['cost']['output_tokens']==12*n
        if arm.startswith(('R3','R4')):assert value['cost']['executor_evaluations']==2
    grounded=json.loads((tmp_path/'R4-grounded/REPRESENTATION.json').read_text())
    opaque=json.loads((tmp_path/'R4-opaque/REPRESENTATION.json').read_text())
    assert grounded['selection']['selected_training_ids']==opaque['selection']['selected_training_ids']
    monkeypatch.setattr(ollama,'api',lambda *a,**k:pytest.fail('replay called model'))
    for arm,value in original.items():assert runner.route(task,tmp_path/arm,arm)==value
    target=tmp_path/'R3/RESULT.json';value=json.loads(target.read_text());value['forecast']['choice']='o_00000000';target.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='retained file'):runner.route(task,tmp_path/'R3','R3')


def test_reserved_budget_callbacks_and_truncation(tmp_path,monkeypatch):
    training,answers=training_bank();runner=readers.Readers(training,answers);calls=[];fake_model(monkeypatch,calls)
    task=source.task_from(record(5,'held-out'),'artifact')
    assert runner.initial(task,tmp_path/'initial',256)['maximum_generated_tokens']==256
    assert runner.retrieval(task,tmp_path/'retrieval',512)['maximum_generated_tokens']==512
    assert runner.structured(task,tmp_path/'structured',512)['maximum_generated_tokens']==512
    actual=ollama.api
    def truncated(*a,**k):
        result=actual(*a,**k);result['done_reason']='length';return result
    monkeypatch.setattr(ollama,'api',truncated)
    value=runner.route(task,tmp_path/'invalid','R3')
    assert value['status']=='INVALID' and value['forecast'] is None
    assert value['cost']['model_calls']==1 and value['cost']['output_tokens']==12
