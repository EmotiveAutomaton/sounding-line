"""Known-answer history selection and whole-worker checks.

DESIGN CHECK: LESSONS3-5. Distinct writers and exact history length are required
under both hypotheses; only prior handling changes. Constructed model replies
drive the real request, parse, execution and replay paths without GPU inference.
"""
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import patch
import json

from . import human_history as history, human_memory, human_memory_routes, human_routes
from . import human_memory_checks as fixtures
from .contracts import canonical, digest
from .ollama import write_new, now


def run(output, rival='R3'):
    output.mkdir(parents=True,exist_ok=False); prepared=output/'prepared'
    train, labels=fixtures.rows()
    for row in train:
        row['evidence_view']='process-record'; row['evidence']['earlier_handling']=['edit']
    for row in labels:
        row['prompt_component']='training-prompt'
    def task(i, earlier):
        return replace(fixtures.task(i,3,'process-record'),evidence={'document':'word word word','suggestions':['word idea'],'earlier_handling':earlier})
    dev=[task(100,['accept']),task(101,['edit'])]; evaluation=[task(200,['accept']),task(201,['edit'])]
    def targets(tasks,lane):
        return [dict(task_id=t.task_id,correct_choice=(next(k for k,v in t.choices if v==history.human_routes.programs.DESCRIPTIONS['edit']) if rival=='R4-grounded' else t.choices[0][0]),writer_component=lane+str(i),prompt_component=lane+'-prompt',source_event=t.task_id) for i,t in enumerate(tasks)]
    public={'train':{'tasks':train},'development':{'tasks':[asdict(t) for t in dev]},'evaluation':{'tasks':[asdict(t) for t in evaluation]}}
    answers={'train':{'targets':labels},'development':{'targets':targets(dev,'dev')},'evaluation':{'targets':targets(evaluation,'eval')}}
    frozen=dict(public_sha256={k:digest(v) for k,v in public.items()},evaluator_sha256={k:digest(v) for k,v in answers.items()})
    for phase in public:
        write_new(prepared/(phase+'-public.json'),public[phase]); write_new(prepared/(phase+'-evaluator.json'),answers[phase])
    write_new(prepared/'FROZEN.json',frozen)
    learned=human_memory.fit(prepared,output/'memory'); checks=[]; calls=[]
    def check(name,value):
        if not value: raise AssertionError(name)
        checks.append(name)
    def refuse(name,callback):
        try: callback()
        except ValueError: checks.append(name)
        else: raise AssertionError(name)
    identities={r['task_id']:r for r in answers['evaluation']['targets']}
    pairs,excluded=history.pair_histories(evaluation,identities)
    check('exact-length different-writer histories pair',len(pairs)==2 and not excluded and all(r['history_changed'] for r in pairs))
    same={k:{**v,'writer_component':'one'} for k,v in identities.items()}
    check('same-writer history is not a mismatch control',not history.pair_histories(evaluation,same)[0])
    changed=replace(evaluation[1],evidence={**evaluation[1].evidence,'earlier_handling':['edit','edit']})
    check('unmatched lengths remain excluded',not history.pair_histories([evaluation[0],changed],identities)[0])
    check('empty histories remain explicitly excluded',len(history.pair_histories([replace(t,evidence={**t.evidence,'earlier_handling':[]}) for t in evaluation],identities)[1])==2)
    def api(path,request):
        body=json.loads(request['messages'][1]['content']); choices=body['task']['choices']
        if 'candidates' in request['format']['properties']:
            action='ignore' if rival=='R4-grounded' and 'permitted_training_representation' not in body else 'edit'
            response={'candidates':[{'goal_hypothesis':'constructed','program':{'feature':'history_available','threshold':.5,'below':'ignore','otherwise':action}}],
                      'choice':choices[0]['id'],'insufficient_support':False}
        else:
            response={'choice':choices[0]['id'],'probabilities':{c['id']:.25 for c in choices},'explanation':'constructed','insufficient_evidence':True}
        calls.append(request)
        return dict(fixture='constructed response, no inference',done=True,done_reason='stop',message={'content':canonical(response)},
                    eval_count=100,prompt_eval_count=1000,total_duration=1,load_duration=0,prompt_eval_duration=0,eval_duration=1)
    def forbidden(*args,**kwargs): raise AssertionError('unexpected inference or rule execution')
    with patch.object(history.ollama,'api',api),patch.object(history.ollama,'identity',lambda:{'fixture':True}),\
         patch.object(history,'GPU_LOCK',output/'unused-lock'),patch.object(history,'acquire_gpu_lock',lambda *a:None),\
         patch.object(history,'release_gpu_lock',lambda:None),patch.object(history,'native_identity',lambda *a:{'pid':0,'fixture':True}):
        for t in dev:
            human_routes.route(t,output/'r3/attempts'/t.task_id)
            human_memory_routes.route(t,output/'r4/attempts'/digest(['development',t.task_id,'R4-grounded'])[:32],
                                      'R4-grounded',train,labels,learned)
        for parent in ('r3','r4'):
            write_new(output/parent/'COMPLETE.json',{'status':'COMPLETE','fixture':True})
        original_read=history.read
        def guarded(path):
            if path.name=='evaluation-evaluator.json': raise AssertionError('full evaluation answer read')
            return original_read(path)
        with patch.object(history,'read',guarded),patch.object(history.ollama,'api',forbidden),\
             patch.object(human_routes.programs,'evaluate',forbidden):
            selection=history.prepare(prepared,output/'memory',output/'r3',output/'r4',output/'selection')
            check('preparation reproduces without evaluation answers or callbacks',history.prepare(prepared,output/'memory',output/'r3',output/'r4',output/'selection')==selection)
        check('development rule chooses the constructed rival',selection['fit']['chosen']==rival)
        changed=deepcopy(selection); changed['pairs'][0]['altered']['evidence']['document']='changed'
        refuse('non-history intervention change refused',lambda:history.validate_frozen(changed))
        changed=deepcopy(selection); changed['pairs'][0]['donor_writer']='fabricated'
        refuse('invented donor refused by source reconstruction',lambda:history.validate_frozen(changed))
        before=len(calls); result=history.run(output/'selection/FROZEN.json',output/'queue')
        check('whole history worker runs both intended routes',len(result['rows'])==4 and len(calls)-before==6)
        with patch.object(history.ollama,'api',forbidden),patch.object(human_routes.programs,'evaluate',forbidden):
            check('completed worker replays without calls or execution',history.run(output/'selection/FROZEN.json',output/'queue')==result)
            raw=next((output/'queue').rglob('RAW.json')); saved=raw.read_bytes(); raw.write_text('{}',encoding='utf8')
            try: refuse('corrupt raw evidence refuses replay',lambda:history.run(output/'selection/FROZEN.json',output/'queue'))
            finally: raw.write_bytes(saved)
        retained=[json.loads(r['messages'][1]['content'])['task'] for r in calls[before:]]
        check('actual requests retain original drafts and options',all(r['evidence']['document']=='word word word' and r['evidence']['suggestions']==['word idea'] for r in retained))
    result=dict(at=now(),status='PASS',checks=checks,sources=history.identity(),actual_model_calls=0,
                selected_rival=rival,constructed_responses=len(calls),
                actual_rule_evaluations=sum(history.read(p)['executor_evaluations'] for p in output.rglob('EXECUTION.json')),
                scope='constructed history selection and whole-worker integrity; no scientific effect claim')
    write_new(output/'COMPLETE.json',result)
    return result


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--output',type=Path,required=True); p.add_argument('--rival',choices=['R3','R4-grounded'],default='R3')
    a=p.parse_args(); r=run(a.output,a.rival); print('PASS',len(r['checks']),'history checks; zero model inference')
