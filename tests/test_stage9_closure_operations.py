"""Known constructed cases and saved reader outcomes; no models or reserves."""
from pathlib import Path
import pytest
from runners.stage9 import closure_operations as subject, neural_operations as operations
from runners.stage9 import common, artifact_comparisons
from runners.stage9.common import closure,digest,file_hash,read,write
from runners.stage9.series_cases import COHORTS,construct_attempt


@pytest.fixture(scope='module')
def case():
    for i in range(20):
        row=construct_attempt(key='closure-operation-'+str(i),cohort=COHORTS[0],role='pilot',dose=0)
        if row['realized']:return row
    raise AssertionError('known construction fixture unavailable')


def saved(tmp_path,monkeypatch,case,operation='genuine_choice',accepted=True):
    for module in (subject,operations,common,artifact_comparisons):
        monkeypatch.setattr(module,'REPO',tmp_path)
    monkeypatch.setattr(operations,'ROOT',tmp_path)
    for module in (subject,operations):monkeypatch.setattr(module,'inside',lambda p:Path(p).resolve())
    monkeypatch.setattr(subject,'verify_committed',lambda *a:None)
    monkeypatch.setattr(operations,'training_package',lambda *a:(tmp_path/'adapter',digest('adapter'),digest('fit')))
    monkeypatch.setattr(operations,'case_inputs',lambda *a:([case],'pilot',digest('cases')))
    source_path=tmp_path/'runners/stage9/runtime.py';source_path.parent.mkdir(parents=True)
    source_path.write_text('# synthetic package source\n',encoding='utf-8')
    source=closure([source_path]);directory=tmp_path/'private/neural-operation-pilots/fixture'
    args=['--output',str(directory),'--operation',operation,'--family','qwen','--training',str(tmp_path/'fit'),
          '--cases',str(tmp_path/'cases'),'--scope','pilot','--limit','2']
    job={'id':'fixture','module':subject.MODULE,'arguments':args,'produces':str(directory/'COMPLETE.json')}
    plan={'sources':source,'jobs':[job]};a=vars(operations.argument_parser().parse_args(args));a.pop('output')
    identity,_,_,_=operations.context(directory,cell=digest({'manifest_sha256':digest(plan),'job':job}),source=source,**a)
    write(directory/'IDENTITY.json',identity)
    family=operations.BASES['qwen']
    package={k:identity[k] for k in ('adapter_sha256','precision','max_context','max_support','max_new_tokens')}
    package.update(model=family['model'],revision=family['revision'],batch_size=4,device='cuda',
                   generation={'requested':identity['generation']},scorer_sources=source,scorer_sha256=source['sha256'])
    write(directory/'PACKAGE.json',package)
    def call(evidence,arguments,index):
        task=operations.request_task(evidence,arguments,package);cap=directory/'capsules'/digest(index)[:16]
        prediction={'valid':accepted,'probs':{k:1/len(evidence['options']) for k in evidence['options']}}
        receipt={'loaded_sources':{}};access={'fixture':True}
        for name,value in [('evidence',evidence),('task',task),('out/prediction',prediction),('out/receipt',receipt),('out/access',access)]:
            write(cap/(name+'.json'),value)
        result={'accepted':accepted,'rc':0 if accepted else 1,'capsule':str(cap),'prediction':prediction,
                'receipt':receipt,'access':access,'copied_sources':{'files':{},'sha256':digest({}),
                'task_sha256':digest(task),'evidence_sha256':digest(evidence)}}
        write(directory/'calls'/case['unit'][:16]/('call-'+digest(index)[:16]+'.json'),
              {'input_sha256':digest({'evidence':evidence,'task':task}),'result':result})
        return result
    row=operations.unit_result(case,operation,call)
    write(directory/'units'/(digest(case['unit'])+'.json'),{'identity':digest(identity),'key':case['unit'],'complete':True,'row':row})
    if operation in ('artifact_choice','process_choice'):
        from runners.stage9.confirmation_neural import discovery_forecasts
        write(directory/'FORECASTS.json',discovery_forecasts([case],[row],operation))
    done={'identity_sha256':digest(identity),'cell_identity':identity['cell_identity'],'execution_complete':True,
          'expected_units':1,'completed_units':1,'reader_calls':1,'operation':operation,'scope':'pilot',
          'all_reader_calls_valid':accepted}
    def seal():
        done['outputs']=closure([p for p in directory.iterdir() if p.name!='COMPLETE.json'])
        write(directory/'COMPLETE.json',done)
    seal();return directory,job,plan,done,seal


@pytest.mark.parametrize('operation',['genuine_choice','artifact_choice','process_choice'])
@pytest.mark.parametrize('accepted',[True,False])
def test_actual_choice_reconstruction_preserves_failed_calls_read_only(tmp_path,monkeypatch,case,operation,accepted):
    directory,job,plan,_,_=saved(tmp_path,monkeypatch,case,operation,accepted)
    before=closure([tmp_path]);result=subject.inspect_completed(job,plan,tmp_path)
    assert closure([tmp_path])==before
    assert result['units']==result['calls']==1
    assert result['invalid_calls_retained']==int(not accepted)
    assert result['new_reader_calls']==result['new_reserve_openings']==0
    assert result['scientific_admission'] is False


@pytest.mark.parametrize('fault',['identity','package','scorer','call_signature','capsule_task','capsule_access',
    'capsule_prediction','missing_prediction','missing_receipt','nonboolean','missing_call','extra_call',
    'unit','unit_boolean','missing_unit','extra_unit','counts','validity','export'])
def test_rehashed_semantic_fault_refuses(tmp_path,monkeypatch,case,fault):
    directory,job,plan,done,seal=saved(tmp_path,monkeypatch,case,'artifact_choice')
    path=next((directory/'calls').rglob('*.json'));call=read(path);cap=Path(call['result']['capsule'])
    if fault=='identity':value=read(directory/'IDENTITY.json');value['role']='reserve';write(directory/'IDENTITY.json',value)
    elif fault in ('package','scorer'):
        value=read(directory/'PACKAGE.json');value['model' if fault=='package' else 'scorer_sha256']='changed';write(directory/'PACKAGE.json',value)
    elif fault=='call_signature':call['input_sha256']=digest('changed');write(path,call)
    elif fault in ('capsule_task','capsule_access','capsule_prediction'):
        name={'capsule_task':'task','capsule_access':'out/access','capsule_prediction':'out/prediction'}[fault]
        write(cap/(name+'.json'),{'changed':True})
    elif fault=='nonboolean':call['result']['accepted']=1;write(path,call)
    elif fault in ('missing_prediction','missing_receipt'):
        (cap/'out'/(fault.removeprefix('missing_')+'.json')).unlink()
    elif fault=='missing_call':path.unlink()
    elif fault=='extra_call':write(directory/'calls/extra.json',call)
    elif fault=='unit':unit=next((directory/'units').glob('*.json'));value=read(unit);value['row']['target']='changed';write(unit,value)
    elif fault=='unit_boolean':unit=next((directory/'units').glob('*.json'));value=read(unit);value['complete']=1;write(unit,value)
    elif fault=='missing_unit':next((directory/'units').glob('*.json')).unlink()
    elif fault=='extra_unit':write(directory/'units/extra.json',{})
    elif fault=='counts':done['reader_calls']=2
    elif fault=='validity':done['all_reader_calls_valid']=1
    elif fault=='export':write(directory/'FORECASTS.json',[])
    seal()
    with pytest.raises((ValueError,FileNotFoundError)):
        subject.inspect_completed(job,plan,tmp_path)


def test_failed_and_unrun_dispositions_never_open_operation_inputs(tmp_path,monkeypatch):
    def forbidden(*a):raise AssertionError('uncompleted operation opened')
    monkeypatch.setattr(subject,'inspect_completed',forbidden)
    checked=[];monkeypatch.setattr(subject,'verify_disposition',lambda q,j,s:checked.append(s['status']))
    prior={k:{'module':subject.MODULE} for k in ('failure','blocked')}
    states={k:{'status':s,'reason':'original refusal','disposition_sha256':digest(s)}
            for k,s in [('failure','FAILED'),('blocked','NOT_RUN')]}
    write(tmp_path/'STATUS.json',{'jobs':states})
    assert subject.queue_audits({},tmp_path,prior)['jobs']==states
    assert checked==['FAILED','NOT_RUN']


def test_current_inputs_and_original_source_scope_are_shared(tmp_path,monkeypatch,case):
    directory,job,plan,_,_=saved(tmp_path,monkeypatch,case)
    args=vars(operations.argument_parser().parse_args(job['arguments']));args.pop('output')
    original=read(directory/'IDENTITY.json')
    source={'files':{**plan['sources']['files'],'runners/run_arg_replication.py':digest('external')}}
    source['sha256']=digest(source['files'])
    rebuilt,_,_,_=operations.context(directory,cell=original['cell_identity'],source=source,**args)
    assert rebuilt==original
    args['scope']='scientific'
    with pytest.raises(ValueError,match='scientific namespace'):
        operations.context(directory,cell=original['cell_identity'],source=source,**args)
