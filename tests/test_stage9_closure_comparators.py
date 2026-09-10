"""Known constructed requests and saved outcomes; no reader execution or fit."""
from pathlib import Path
import copy
import shutil
import pytest
from runners.stage9 import closure_comparators as subject, closure_purpose, common
from runners.stage9 import artifact_comparisons, baseline_predictions, baseline_controls
from runners.stage9 import baseline_matrix_runtime, comparison_runtime
from runners.stage9.common import closure,digest,file_hash,read,write
from runners.stage9.saved_replay import active,replaying
from runners.stage9.matched_controls import construct
from tests.test_stage9_artifact_comparisons import actual_case
from tests.test_stage9_comparison_runtime import bundle

ORIGINAL=common.REPO
RUNTIMES=(baseline_matrix_runtime,comparison_runtime)


@pytest.fixture(scope='module')
def known_case():
    case=actual_case();return case,construct(case['source_worlds'][1:],'pilot','closure-comparator-control')


def saved(tmp_path,monkeypatch,known_case,kind='plain',invalid=False):
    case,control=copy.deepcopy(known_case);data=bundle()
    models={'models':{v:{'model':data['population']} for v in ('artifact','process_record')},
        'types':{v:data['population_types'] for v in ('artifact','process_record')},
        'library':{k:data[k] for k in ('candidates','prior','shared_groups')},'completion_sha256':digest('synthetic-fit')}
    for module in (subject,closure_purpose,common,artifact_comparisons,baseline_predictions,baseline_controls):
        monkeypatch.setattr(module,'REPO',tmp_path)
    for module in (artifact_comparisons,baseline_predictions,baseline_controls):
        if module is not artifact_comparisons:monkeypatch.setattr(module,'ROOT',tmp_path)
        monkeypatch.setattr(module,'inside',lambda p:Path(p).resolve())
        monkeypatch.setattr(module,'model_inputs',lambda *a:models)
    monkeypatch.setattr(subject,'inside',lambda p:Path(p).resolve())
    monkeypatch.setattr(subject,'verify_committed',lambda *a:None)
    origins={'runners/stage7/runtime.py'}|{p for r in RUNTIMES for p in r.SOURCES.values()}
    for name in origins:
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ORIGINAL/name,p)
    source=closure([tmp_path/p for p in sorted(origins)])
    cases_path=tmp_path/'cases';write(cases_path/'CASES.json',[case])
    write(cases_path/'COMPLETE.json',{'accepted':True,'role':'pilot','outputs':closure([cases_path/'CASES.json'])})
    case_sha=file_hash(cases_path/'COMPLETE.json')
    for module in (baseline_predictions,baseline_controls):
        monkeypatch.setattr(module,'case_inputs',lambda *a:([case],'pilot',case_sha))
    fit=tmp_path/'fit';write(fit/'artifact-PREPARED.json',{'units':[]})
    controls_path=tmp_path/'controls'
    ci={'case_completion_sha256':case_sha,'case_sha256':file_hash(cases_path/'CASES.json')}
    write(controls_path/'IDENTITY.json',ci);write(controls_path/'CONTROLS.json',[{'unit':case['unit'],'control':control}])
    write(controls_path/'COMPLETE.json',{'accepted':True,'execution_complete':True,'role':'pilot',
        'identity_sha256':digest(ci),'outputs':closure([controls_path/'IDENTITY.json',controls_path/'CONTROLS.json'])})
    module={'plain':baseline_predictions,'control':baseline_controls,'artifact':artifact_comparisons}[kind]
    directory=tmp_path/'private'/({'plain':'baseline-prediction-pilots','control':'baseline-control-pilots','artifact':'comparison-pilots'}[kind])/'fixture'
    args=['--root' if kind=='artifact' else '--output',str(directory),'--cases',str(cases_path/'CASES.json' if kind=='artifact' else cases_path),
        '--models',str(fit),'--role' if kind=='artifact' else '--scope','pilot','--doses','0','1']
    if kind=='control':args+=['--controls',str(controls_path)]
    if kind=='artifact':args+=['--views','process_record']
    job={'id':'fixture','module':module.__name__,'arguments':args,'produces':str(directory/'COMPLETE.json')}
    plan={'sources':source,'jobs':[job]}
    module,parsed,directory,identity,cases,package,controls=subject.inputs(job,plan)
    write(directory/'IDENTITY.json',identity)
    class Recorder:
        count=0
        def checkpoint(self,path,inputs,invoke,*,resume_only=False):
            result=invoke();write(path,{'input_sha256':digest(inputs),'result':result});return result
        def request(self,evidence,task,root,sources,*,runtime):
            self.count+=1;cap=root/digest(self.count)[:16]
            for name,origin in sources.items():
                p=cap/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(tmp_path/origin,p)
            (cap/'reader/__init__.py').write_text('',encoding='utf-8')
            (cap/'bootstrap.py').write_text(closure_purpose.BOOTSTRAP,encoding='utf-8',newline='\n')
            files={p.relative_to(cap).as_posix():file_hash(p) for p in cap.rglob('*.py')}
            copied={'files':files,'sha256':digest(files),'evidence_sha256':digest(evidence),'task_sha256':digest(task),
                'bootstrap_owner_sha256':source['files']['runners/stage7/runtime.py']}
            accepted=not invalid;prediction={'valid':accepted,'predictions':{}}
            for name,query in evidence['evidences'].items():
                uniform={k:1/len(query['support']) for k in query['support']}
                if task['operation']=='baseline_matrix':
                    prediction['predictions'][name]={m+'|'+r:uniform for m in evidence['models']
                        for r in ('population','brief','cheap-8.0','cheap-16.0','cheap-32.0')}
                else:
                    assert task['operation']=='comparison_matrix'
                    prediction['predictions'][name]={r:{'prediction':uniform,'exact_within_declared_model':True}
                        for r in ('program_mixture','differentiated_maker')}
            receipt={'loaded_sources':{('reader' if p=='reader/__init__.py' else p[:-3].replace('/','.')):sha
                for p,sha in files.items() if p.startswith('reader/')}};access={'synthetic_fixture':True}
            for name,value in [('evidence',evidence),('task',task),('out/prediction',prediction),('out/receipt',receipt),('out/access',access)]:write(cap/(name+'.json'),value)
            write(root/'closures'/(cap.name+'.json'),copied)
            return {'accepted':accepted,'rc':0 if accepted else 1,'prediction':prediction,'receipt':receipt,'access':access,
                'capsule':str(cap),'copied_sources':copied,'inputs_and_sources_unchanged':True,'wall_s':.1}
    with replaying(Recorder()):rebuilt=subject.reconstruct(module,parsed,directory,cases,package,controls)
    for key,row in rebuilt:write(directory/'units'/(digest(key)+'.json'),{'identity':digest(identity),'key':key,'complete':True,'row':row})
    rows=[row for key,row in rebuilt];write(directory/'PREDICTIONS.json',rows)
    if kind=='plain':write(directory/'FORECASTS.json',baseline_predictions.discovery_forecasts(cases,rows,models,(0,1)))
    done={'cell_identity':identity['cell_identity'],'identity_sha256':digest(identity),'role':'pilot','execution_complete':True,
        'assigned_units':1,'completed_units':1,'scores_computed':False}
    if kind=='artifact':done.update(source=identity['source'],launch_accepted=False,gpu_seconds=0,cpu_scope='parent excludes reader capsules')
    else:
        done['scientific_admission']=False
        if kind=='plain':done.update(source=identity['source'],cpu_scope='parent only; each child capsule has a separate wall receipt')
    names=['PREDICTIONS.json','units','calls']+([] if kind=='artifact' else ['IDENTITY.json','capsules'])+(['FORECASTS.json'] if kind=='plain' else [])
    def seal():
        done['outputs']=closure([directory/n for n in names]);write(directory/'COMPLETE.json',done)
    seal();return directory,job,plan,done,seal


@pytest.mark.parametrize('kind',['plain','control','artifact'])
@pytest.mark.parametrize('invalid',[False,True])
def test_original_forecasts_and_runtime_requests_reproduce_read_only(tmp_path,monkeypatch,known_case,kind,invalid):
    directory,job,plan,_,_=saved(tmp_path,monkeypatch,known_case,kind,invalid)
    def forbidden(*a,**k):raise AssertionError('reader or writer executed')
    for runtime in RUNTIMES:
        monkeypatch.setattr(runtime,'run_capsule',forbidden);monkeypatch.setattr(runtime,'write',forbidden)
    for module in (artifact_comparisons,baseline_predictions,baseline_controls):
        monkeypatch.setattr(module,'writer',forbidden);monkeypatch.setattr(module,'Units',forbidden)
    before=closure([tmp_path]);result=subject.inspect_completed(job,plan,tmp_path)
    assert result['units']==1 and bool(result['invalid_calls_retained'])==invalid
    assert result['calls']==(4 if kind=='control' else 2)
    assert not result['scientific_admission'] and result['new_reader_calls']==0
    assert closure([tmp_path])==before and active() is None


@pytest.mark.parametrize('fault',['identity','signature','task','access','source','missing_prediction','missing_receipt',
    'unit_boolean','unit_row','extra_unit','extra_call','missing_call','extra_capsule','extra_closure','closure',
    'predictions','forecasts','assigned','complete_boolean','admission','cases','models','control_identity'])
def test_rehashed_changed_evidence_and_omissions_refuse(tmp_path,monkeypatch,known_case,fault):
    kind='control' if fault=='control_identity' else 'plain'
    directory,job,plan,done,seal=saved(tmp_path,monkeypatch,known_case,kind)
    path=next((directory/'calls').rglob('*.json'));value=read(path);cap=Path(value['result']['capsule'])
    if fault=='identity':
        p=directory/'IDENTITY.json';v=read(p);v['doses']=[0];write(p,v)
    elif fault=='signature':value['input_sha256']=digest('changed');write(path,value)
    elif fault in ('task','access'):write(cap/('task.json' if fault=='task' else 'out/access.json'),{})
    elif fault=='source':(cap/'reader/worker.py').write_text('# changed\n',encoding='utf-8')
    elif fault in ('missing_prediction','missing_receipt'):(cap/'out'/(fault.removeprefix('missing_')+'.json')).unlink()
    elif fault in ('unit_boolean','unit_row'):
        p=next((directory/'units').glob('*.json'));v=read(p)
        if fault=='unit_boolean':v['complete']=1
        else:v['row']['truth']='changed'
        write(p,v)
    elif fault=='extra_unit':write(directory/'units/extra.json',{})
    elif fault=='extra_call':write(directory/'calls/extra.json',{})
    elif fault=='missing_call':path.unlink()
    elif fault=='extra_capsule':(directory/'capsules/extra').mkdir()
    elif fault=='extra_closure':write(directory/'capsules/closures/extra.json',{})
    elif fault=='closure':write(directory/'capsules/closures'/(cap.name+'.json'),{})
    elif fault in ('predictions','forecasts'):write(directory/(fault.upper()+'.json'),[])
    elif fault=='assigned':done['assigned_units']=2
    elif fault=='complete_boolean':done['execution_complete']=1
    elif fault=='admission':done['scientific_admission']=True
    elif fault=='cases':
        j=copy.deepcopy(job);j['arguments'][j['arguments'].index('--doses')+2]='0';job=j
    elif fault=='models':
        monkeypatch.setattr(baseline_predictions,'model_inputs',lambda *a:{'completion_sha256':digest('substitute')})
    elif fault=='control_identity':
        p=tmp_path/'controls/IDENTITY.json';v=read(p);v['case_sha256']=digest('changed');write(p,v)
    seal()
    with pytest.raises((ValueError,KeyError,FileNotFoundError)):subject.inspect_completed(job,plan,tmp_path)


def test_failed_unrun_and_unfinished_dispatch(tmp_path,monkeypatch):
    def forbidden(*a):raise AssertionError('uncompleted input opened')
    monkeypatch.setattr(subject,'inspect_completed',forbidden)
    monkeypatch.setattr(subject,'verify_disposition',lambda *a:None)
    prior={k:{'module':m} for k,m in zip(('failed','blocked'),list(subject.MODULES)[:2])}
    states={k:{'status':s,'reason':'original refusal','disposition_sha256':digest(s)} for k,s in [('failed','FAILED'),('blocked','NOT_RUN')]}
    write(tmp_path/'STATUS.json',{'jobs':states});assert subject.queue_audits({},tmp_path,prior)['jobs']==states
    states['failed']['status']='RUNNING';write(tmp_path/'STATUS.json',{'jobs':states})
    with pytest.raises(ValueError):subject.queue_audits({},tmp_path,prior)
