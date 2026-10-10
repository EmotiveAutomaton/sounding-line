"""R01 repair 1: one witnessed free quantity per request, deterministic composition.

DESIGN CHECK: LESSONS 2-5; SL4. NULL: constant handling, missing/absent confusion,
fact-insensitive output or malformed probabilities refuse. ALTERNATIVE: every
witnessed field and span survives diverse Unicode and edit controls. This gate
licenses extraction only. Natural inference has an independent downstream screen.
"""
from copy import deepcopy
import json,math
from .common import freeze,digest
from .local import service,call,CONTEXT
from .records import fixtures
from .compact import expand,evaluate
from .statistics import ACTIONS
from runners.stage9.coauthor import units
from runners.stage11.replay import replay
from runners.stage11_1.targets import project,SLOTS

def controls():
    cases=[]
    for i,base in enumerate(fixtures()):
        rows=deepcopy(base['lines']);kind=(i//4)%4;doc=base['event']['end_document']
        if kind==1:
            rows.append(dict(eventName='text-insert',eventSource='user',textDelta={'ops':[{'retain':len(units(doc))-1},{'insert':' More.'}]}))
        elif kind==2:
            rows.append(dict(eventName='text-insert',eventSource='user',textDelta={'ops':[{'insert':'Revised: '}]}))
        elif kind==3 and base['target']['handling'] in ('accept','edit'):
            start=len(units(base['event']['document']))-1
            rows.append(dict(eventName='text-delete',eventSource='user',textDelta={'ops':[{'retain':start},{'delete':len(units(doc))-start-1}]}))
        r=replay(rows);e=r['events'][0]
        if not r['reconstructed'] or not e['usable']:raise ValueError('control source is not exact')
        target=project(e,rows)
        cases.append(dict(key=f'factor-{i:03d}',event=e,target=target,lines=rows))
    return cases

def request(case,field,model):
    if field=='handling':labels=list(ACTIONS);observed=dict(recorded_handling=case['target']['handling']);spans=False
    else:
        f=next(x for x in case['target']['facts'] if x['slot']==field)
        labels={'selection':['absent','select'],'entry':['absent','insert'],'change':['absent','delete','format_edit','content_edit'],
            'continuation':['absent','insert'],'surrounding':['absent','format_edit','content_edit'],'removal':['absent','delete']}[field]
        observed=dict(slot=field,recorded_operation=f['operation'],exact_spans=f['exact_spans']);spans=True
    props={k:dict(type='number',minimum=0,maximum=1) for k in labels}
    if spans:props['spans']=dict(type='array',items=dict(type='array',items=dict(type='integer',minimum=0),minItems=2,maxItems=2))
    schema=dict(type='object',properties=props,required=list(props),additionalProperties=False)
    text='This is an explicit source transcription test. The recorded fact is certain. Give probability 1 to its exact named category and 0 to the other categories. Category probabilities must sum to 1. Copy the supplied exact spans, if requested. Do not infer intention.\nSOURCE: '+json.dumps(observed,ensure_ascii=False)+'\nRESPONSE SCHEMA: '+json.dumps(schema)
    return dict(model=model,stream=False,think=False,keep_alive='10m',format=schema,options=dict(temperature=0,seed=141010,num_ctx=CONTEXT,num_thread=1,num_predict=512),messages=[dict(role='user',content=text)]),labels

def parse(response,labels,length,spans):
    from runners.stage13.scoring import validate_spans
    if response.get('done') is not True or response.get('done_reason')!='stop':raise ValueError('unfinished response')
    b=json.loads(response['message']['content'])
    if set(b)!=set(labels+(['spans'] if spans else [])):raise ValueError('wrong response keys')
    p=[b[k] for k in labels]
    if any(type(x) not in (int,float) or not math.isfinite(x) or not 0<=x<=1 for x in p) or abs(sum(p)-1)>1e-6:raise ValueError('invalid literal probabilities')
    if spans:validate_spans(b['spans'],length)
    return b

def compose(values):
    b=dict(handling=[values['handling'][a] for a in ACTIONS],present=[1-values[s]['absent'] for s in SLOTS],spans=[values[s]['spans'] for s in SLOTS])
    for s,labels in [('change',['delete','format_edit','content_edit']),('surrounding',['format_edit','content_edit'])]:
        total=1-values[s]['absent'];b[s]=[values[s][a]/total for a in labels] if total>0 else [1.]+[0.]*(len(labels)-1)
    return expand(b)

def run(card,out,raw,tick):
    cases=controls()[:card['cases']];results=[]
    freeze(out/'CONTROL_MANIFEST.json',dict(cases=cases,digest=digest(cases),source='new exact replay, independent of model answers',evidence='V4 witnessed extraction'))
    with service(out,card) as state:
        count=0
        for case in cases:
            values={};errors=[];cost=[]
            for field in ['handling',*SLOTS]:
                req,labels=request(case,field,card['model']);response,receipt=call(req,out/'calls'/f"{case['key']}-{field}",state,card);cost.append(receipt)
                try:values[field]=parse(response,labels,len(case['event']['end_document']),field!='handling')
                except (ValueError,TypeError,KeyError) as exc:errors.append(str(exc))
                count+=1;tick(dict(completed_calls=count,planned_calls=len(cases)*7))
            pred=compose(values) if not errors else None
            results.append(dict(key=case['key'],prediction=pred,errors=errors,score=evaluate(pred,case['target']),cost=cost))
    exact=sum(r['score']['exact'] for r in results);valid=sum(r['score']['valid'] for r in results)
    freeze(out/'PREDICTIONS.json',results)
    freeze(out/'SUMMARY.json',dict(attempted=len(results),calls=count,valid=valid,exact=exact,half_brier=sum(r['score']['half_brier'] for r in results)/len(results),scope='explicit-source extraction; copying answers does not demonstrate hidden inference'))
    freeze(out/'ADMISSION.json',dict(admitted=len(results)>=64 and exact==len(results) and all(r['score']['half_brier']==0 for r in results) and valid/len(results)>=.95,extraction_only=True,natural_competence=False,reason='all explicit certain fields require exact mass and spans; natural screen separate'))
