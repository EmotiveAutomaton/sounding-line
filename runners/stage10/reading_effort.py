"""Reserved-budget R5 over the existing native Ghost reconstruction reader.

DESIGN CHECK: LESSONS3-5, Stage10 central effort freeze. NULL or unsupported
development gains stop; useful stable gains can buy a declared route. Only the
request token cap changes, BEFORE request binding and persistence. Historical
reader source files and all native execution semantics remain unchanged.
"""
import argparse
from contextlib import contextmanager
from pathlib import Path
from . import ollama,reading_routes,reading_source,effort
from .contracts import digest
from .ghost import task_from,envelopes
from .queue import read,status
from .revision_bank import checked,finish,device,sha

PUBLIC=Path('results/phase_2_4_stage_10/raw/interface-v3/ghost-public')
EXPORT=Path('../../AI and Intentionality/Ghost Scale Simulation/ghost-scale-sim/results/v16/transfer-fixture-2')


@contextmanager
def token_budget(per_call):
    original=ollama.request_for
    def bounded(*a,**k):
        k['generated_tokens']=per_call
        return original(*a,**k)
    ollama.request_for=bounded
    try:yield
    finally:ollama.request_for=original


class Readers:
    def __init__(self,prepared):
        self.prepared=prepared;self.frozen=read(prepared/'FROZEN.json')
        train=read(prepared/'train-public.json');answers=read(prepared/'train-evaluator.json')
        if digest(train)!=self.frozen['public_sha256']['train'] or digest(answers)!=self.frozen['evaluator_sha256']['train']:raise ValueError('native reading training changed')
        self.training,self.answers=train['tasks'],answers['targets']
        allocation=read(prepared/'ALLOCATION.json')
        if digest(allocation)!=self.frozen['allocation_sha256']:raise ValueError('reading allocation differs')
        self.members={r['task_id']:r['case_id'] for r in allocation['tasks']}
        all_envelopes,_=envelopes(PUBLIC)
        self.frames={r['envelope']['task_id']:r['envelope'] for r in all_envelopes}
        self.pilot=min((r['envelope'] for r in all_envelopes if r['case_id']==reading_source.PILOT_CASE),key=lambda e:e['task_id'])
        self.sources={**reading_routes.identity(PUBLIC),'runners/stage10/reading_effort.py':sha(Path(__file__)),
            'runners/stage10/effort.py':sha(Path(effort.__file__)),'prepared':digest(self.frozen),
            'model-profile':digest([ollama.MODEL,ollama.MODEL_DIGEST])}

    def tasks(self,phase):
        if phase=='pilot':return [task_from(self.pilot)]
        public=read(self.prepared/(phase+'-public.json'))
        if digest(public)!=self.frozen['public_sha256'][phase]:raise ValueError('reading public tasks changed')
        tasks=[task_from(self.frames[r['task_id']]) for r in public['tasks']]
        from dataclasses import asdict
        if digest({'tasks':[asdict(t) for t in tasks]})!=digest(public):raise ValueError('task/envelope projection differs')
        return tasks

    def route(self,task,output,arm,allowance):
        if arm not in {'R0','R1','R3'} or allowance!=(256 if arm=='R0' else 512):raise ValueError('undeclared reading effort budget')
        binding=digest([self.sources,task.public(),arm,allowance]);terminal=output/'COMPLETE.json'
        replay=terminal.exists()
        if replay:
            if checked(output)['binding']!=binding:raise ValueError('budget binding differs')
        output.mkdir(parents=True,exist_ok=True)
        with token_budget(allowance//2 if arm=='R3' else allowance):
            result=reading_routes.route(PUBLIC,self.frames.get(task.task_id,self.pilot),output/'native-route',self.training,self.answers,arm,
                self.members.get(task.task_id,reading_source.PILOT_CASE))
        normalized={'status':result['status'],'forecast':result['forecast'],'evidence_sha256':digest(task.public()),'maximum_generated_tokens':allowance,
            'cost':{'model_calls':result['model_calls'],'input_tokens':result['input_tokens'],'output_tokens':result['generated_tokens'],
                    'wall_seconds':result['wall_seconds'],'executor_evaluations':result['executor_evaluations'],
                    'reasoning_tokens':None,'reasoning_tokens_status':'not separately exposed'}}
        effort.check_attempt(task,normalized,allowance)
        for p in (output/'native-route').rglob('REQUEST.json'):
            request=read(p)
            if request['request']['options']['num_predict']!=(allowance//2 if arm=='R3' else allowance):raise ValueError('literal token cap was not applied before transport')
            if request['binding']!=digest({'request':request['request'],'model_digest':ollama.MODEL_DIGEST}):raise ValueError('saved request binding differs')
        if (output/'RESULT.json').exists():
            if read(output/'RESULT.json')!=normalized:raise ValueError('reserved reading result differs')
        else:ollama.write_new(output/'RESULT.json',normalized)
        finish(output,binding)
        return normalized

    def initial(self,t,o,b):return self.route(t,o,'R0',b)
    def retrieval(self,t,o,b):return self.route(t,o,'R1',b)
    def structured(self,t,o,b):return self.route(t,o,'R3',b)


def predict(prepared,output,phase,admission=None,policy=None):
    readers=Readers(prepared);binding=digest([readers.sources,phase]);tasks=readers.tasks(phase)
    if phase!='pilot':
        a=checked(admission)
        if not a['admitted'] or a['reader_sources']!=readers.sources:raise ValueError('literal reserved reading admission required')
    if phase=='evaluation':
        checked(policy);frozen=read(policy/'POLICY.json');effort.verify_policy(frozen)
        if frozen['policy']['producer_hashes']['reader-sources']!=digest(readers.sources):raise ValueError('reading policy source differs')
        binding=digest([binding,frozen])
    rows=[];replay=(output/'COMPLETE.json').exists()
    if replay:
        if checked(output)['binding']!=binding:raise ValueError('reading bank changed')
    with device(output,replay):
        for task in tasks:
            if phase=='evaluation':
                for mode in ['fixed','confidence-only','benefit-cost']:
                    if not replay:status(output/'STATUS.json',{'at':ollama.now(),'completed_routes':len(rows),'task':task.task_id,'arm':mode})
                    result=effort.run(task,output/'routes'/task.task_id/mode,frozen,readers.initial,{'R1':readers.retrieval,'R3':readers.structured},
                        mode=mode,group=readers.members[task.task_id],reader_sources=readers.sources)
                    rows.append({'task_id':task.task_id,'arm':'R5-'+mode,'result':result})
            else:
                for arm,budget in [('R0',256),('R1',512),('R3',512)]:
                    if not replay:status(output/'STATUS.json',{'at':ollama.now(),'completed_routes':len(rows),'task':task.task_id,'arm':arm})
                    result=readers.route(task,output/'routes'/task.task_id/arm,arm,budget);rows.append({'task_id':task.task_id,'arm':arm,'result':result})
    roster={'phase':phase,'rows':rows,'reader_sources':readers.sources}
    if (output/'ROSTER.json').exists():
        if read(output/'ROSTER.json')!=roster:raise ValueError('reading effort roster changed')
    else:ollama.write_new(output/'ROSTER.json',roster)
    extra={'reader_sources':readers.sources}
    if phase=='pilot':
        # A legal parsed hypothesis can correctly report model mismatch. That
        # is a behavior result, not transport failure, and is not auto-repaired.
        attempts=[read(p) for p in output.rglob('ATTEMPT.json')]
        extra['admitted']=len(attempts)==4 and all(a['status']=='VALID' for a in attempts)
    return finish(output,binding,extra)


def truths(prepared,phase,tasks,evidence=None):
    readers=Readers(prepared);manifest=read(PUBLIC/'PUBLIC_MANIFEST.json');raw=read(EXPORT/'RAW_MANIFEST.json')
    if phase not in {'development','evaluation'} or {t.task_id for t in tasks}!={t.task_id for t in readers.tasks(phase)}:raise ValueError('outcome join requires the exact frozen phase population')
    if read(EXPORT/'PUBLIC_MANIFEST.json')!=manifest:raise ValueError('native export is not the reviewed public packet')
    members={c['case_id']:set(c['tasks_in_recorded_order']) for c in manifest['cases']};world=reading_source.native_world(PUBLIC);labels={}
    for task in tasks:
        case=readers.members[task.task_id];p=EXPORT/'private'/(case+'-evaluation.json')
        if sha(p)!=raw['files']['private/'+case+'-evaluation.json']:raise ValueError('native recorded outcome changed')
        data=read(p);truth=reading_source.target_from_record(data,case,task,members[case],world)
        labels[task.task_id]={'correct_choice':truth,'writer_component':case,'prompt_component':case,'source_event':task.task_id}
        if evidence is not None:evidence.sources[p.as_posix()]=sha(p)
    return labels


def fit(prepared,development,admission,output):
    checked(development);readers=Readers(prepared)
    # Complete immutable callback replay happens before development outcome access.
    predict(prepared,development,'development',admission)
    tasks=readers.tasks('development');labels=truths(prepared,'development',tasks)
    rows=read(development/'ROSTER.json')['rows'];routes={(r['task_id'],r['arm']):r['result'] for r in rows}
    from dataclasses import asdict
    bundle={'schema':'stage10.effort-development.1','phase':'development','complete':True,
        'producers':{'development':sha(development/'COMPLETE.json'),'reader-sources':digest(readers.sources)},
        'rows':[{'task':asdict(t),'group':readers.members[t.task_id],'truth':labels[t.task_id]['correct_choice'],
                 'routes':{a:routes[t.task_id,a] for a in ['R0','R1','R3']}} for t in tasks]}
    output.mkdir(parents=True,exist_ok=False);ollama.write_new(output/'POLICY.json',effort.fit(bundle));ollama.write_new(output/'BUNDLE.json',bundle)
    return finish(output,digest(bundle))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['pilot','development','fit','evaluation']);p.add_argument('--output',type=Path,required=True)
    for n in ['prepared','admission','development','policy']:p.add_argument('--'+n,type=Path)
    a=p.parse_args()
    try:
        if a.action=='fit':fit(a.prepared,a.development,a.admission,a.output)
        else:predict(a.prepared,a.output,a.action,a.admission,a.policy)
    except Exception as exc:
        if not (a.output/'FAILED.json').exists():ollama.write_new(a.output/'FAILED.json',{'at':ollama.now(),'error':repr(exc)})
        raise
