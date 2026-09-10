"""Fixed saved probabilities test calibration closure without a model or tokenizer."""
from pathlib import Path
from types import SimpleNamespace
import sys
import pytest
from runners.stage9 import closure_calibration as subject,package_calibration as calibration
from runners.stage9 import common,artifact_comparisons
from runners.stage9.common import closure,digest,file_hash,read,write


def saved(tmp_path,monkeypatch,failed=False,version='actual-package-precision-v2'):
    for module in (subject,calibration,common,artifact_comparisons):monkeypatch.setattr(module,'REPO',tmp_path)
    monkeypatch.setattr(calibration,'ROOT',tmp_path)
    for module in (subject,calibration):monkeypatch.setattr(module,'inside',lambda p:Path(p).resolve())
    monkeypatch.setattr(subject,'verify_committed',lambda *a:None)
    monkeypatch.setattr(calibration,'training_package',lambda *a:(tmp_path/'adapter',digest('adapter'),digest('fit')))
    monkeypatch.setitem(sys.modules,'transformers',SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=lambda *a,**k:object())))
    evidence={'prefix':'Next action: ','options':{'a':'STOP','b':'STOP'}}
    distinct={'prefix':'Next action: ','options':{'a':'one','b':'two'}}
    monkeypatch.setattr(calibration,'examples',lambda c:[{'name':'identical-stop-2','evidence':c['tie']},
                                                      {'name':'distinct-maximum-support','evidence':c['distinct']}])
    monkeypatch.setattr(calibration,'maker_series_case',lambda tok:(distinct,{'fixture':'bounded synthetic long context'}))
    corpus=tmp_path/'private/pilot/qwen-corpus.json';write(corpus,{'tie':evidence,'distinct':distinct})
    src=tmp_path/'runners/stage9/reader/scorer.py';src.parent.mkdir(parents=True);src.write_text('# fixture\n',encoding='utf-8')
    source=closure([src]);directory=tmp_path/'private/package-calibration-pilots/fixture'
    args=['--output',str(directory),'--family','qwen','--package-kind','fitted','--training',str(tmp_path/'fit'),'--scope','pilot']
    job={'id':'calibrate','module':subject.MODULE,'arguments':args,'produces':str(directory/'COMPLETE.json')}
    plan={'sources':source,'jobs':[job]};cell=digest({'manifest_sha256':digest(plan),'job':job})
    identity,_,inputs=calibration.context(directory,'qwen','fitted',tmp_path/'fit','pilot',cell=cell,source=source,version=version)
    write(directory/'IDENTITY.json',identity);write(directory/'INPUTS.json',inputs)
    packages={};predictions={}
    for precision,device,batch in calibration.VARIANTS:
        key=f'{precision}-{device}-{batch}';base=subject.BASES['qwen']
        package={'model':base['model'],'revision':base['revision'],'adapter_sha256':digest('adapter'),
            'precision':precision,'device':device,'batch_size':batch,'max_context':4096,'max_support':128,'max_new_tokens':32,
            'scorer_sources':source,'scorer_sha256':source['sha256'],'base_files':{'weights':'fixture'},
            'base_files_sha256':digest({'weights':'fixture'}),'generation':{'mode':'greedy'},
            **{k:'fixture' for k in ('renderer','attention_implementation','long_context_batch_rule','torch','transformers','peft')}}
        packages[key]=package;rows={}
        permutation={'prefix':distinct['prefix'],'options':dict(reversed(list(distinct['options'].items())))}
        for name,item in {**inputs,'permutation':permutation}.items():
            probabilities={'a':.52,'b':.48} if failed and precision=='float16' and name in ('distinct-maximum-support','permutation') else {'a':.5,'b':.5}
            task=calibration.call_task(package,item,version);cap=directory/'capsules'/digest([key,name])[:16]
            prediction={'valid':True,'probs':probabilities,'ties':['a','b']};receipt={'loaded_sources':{}};access={'fixture':True}
            for n,value in [('evidence',item),('task',task),('out/prediction',prediction),('out/receipt',receipt),('out/access',access)]:write(cap/(n+'.json'),value)
            result={'accepted':True,'rc':0,'capsule':str(cap),'prediction':prediction,'receipt':receipt,'access':access,
                'copied_sources':{'files':{},'sha256':digest({}),'task_sha256':digest(task),'evidence_sha256':digest(item)}}
            write(directory/'calls'/key/(name+'.json'),{'input_sha256':digest({'evidence':item,'task':task}),'result':result})
            if name!='permutation':rows[name]=probabilities
        predictions[key]=rows
        write(directory/'units'/(digest(key)+'.json'),{'identity':digest(identity),'key':key,'complete':True,
            'row':{'package':package,'probabilities':rows}})
    comparison=calibration.compare(predictions,inputs)
    write(directory/'PACKAGES.json',packages);write(directory/'CALIBRATION.json',comparison)
    write(directory/'INVALIDITY.json',[{'attack':a,'rejected':True} for a in ('support_overflow','empty_continuation','wrong_identity')])
    done={'cell_identity':cell,'identity_sha256':digest(identity),'execution_complete':True,'instrument_only':True,
        'instrument_accepted':comparison['instrument_accepted'],'old_1e_minus6_pass':comparison['old_1e_minus6_pass'],
        'family':'qwen','package_kind':'fitted','adapter_sha256':digest('adapter'),'data_role':'pilot','scientific_admission':False}
    def seal():
        done['outputs']=closure([p for p in directory.iterdir() if p.name!='COMPLETE.json'])
        write(directory/'COMPLETE.json',done)
    seal();return directory,job,plan,done,seal


@pytest.mark.parametrize('failed',[False,True])
@pytest.mark.parametrize('version',['actual-package-precision-v1','actual-package-precision-v2'])
def test_reconstructs_complete_saved_grid_and_preserves_failed_threshold(tmp_path,monkeypatch,failed,version):
    directory,job,plan,done,seal=saved(tmp_path,monkeypatch,failed,version)
    def forbidden(*a,**k):raise AssertionError('read-only checker attempted writer/model execution')
    for name in ('Units','resident','execute','writer'):monkeypatch.setattr(calibration,name,forbidden)
    before=closure([tmp_path]);result=subject.inspect_completed(job,plan,tmp_path)
    assert closure([tmp_path])==before
    assert result['variants']==3 and result['calls']==12
    assert result['instrument_accepted'] is (not failed)
    assert result['new_reader_calls']==result['new_reserve_openings']==0
    assert not result['scientific_admission']


@pytest.mark.parametrize('fault',['corpus','inputs','package','scorer','variant','signature','capsule_task','capsule_access',
    'missing_prediction','missing_receipt','invalid_call','extra_call','missing_call','extra_unit','missing_unit','unit_boolean',
    'unit_values','comparison','invalidity','tolerance','counts_boolean','decision_boolean','transport'])
def test_rehashed_semantic_changes_refuse(tmp_path,monkeypatch,fault):
    directory,job,plan,done,seal=saved(tmp_path,monkeypatch)
    path=directory/'calls/float16-cuda-4/distinct-maximum-support.json';cached=read(path);cap=Path(cached['result']['capsule'])
    if fault=='corpus':write(tmp_path/'private/pilot/qwen-corpus.json',{'tie':{},'distinct':{}})
    elif fault=='inputs':write(directory/'INPUTS.json',{})
    elif fault in ('package','scorer','variant'):
        value=read(directory/'PACKAGES.json')
        if fault=='variant':del value['float32-cpu-4']
        else:value['float16-cuda-4']['model' if fault=='package' else 'scorer_sha256']='changed'
        write(directory/'PACKAGES.json',value)
    elif fault=='signature':cached['input_sha256']=digest('changed');write(path,cached)
    elif fault in ('capsule_task','capsule_access'):write(cap/('task.json' if fault=='capsule_task' else 'out/access.json'),{})
    elif fault in ('missing_prediction','missing_receipt'):(cap/'out'/(fault.removeprefix('missing_')+'.json')).unlink()
    elif fault=='invalid_call':cached['result']['accepted']=False;write(path,cached)
    elif fault=='extra_call':write(directory/'calls/extra.json',cached)
    elif fault=='missing_call':path.unlink()
    elif fault=='extra_unit':write(directory/'units/extra.json',{})
    elif fault=='missing_unit':next((directory/'units').glob('*.json')).unlink()
    elif fault in ('unit_boolean','unit_values'):
        p=next((directory/'units').glob('*.json'));value=read(p)
        if fault=='unit_boolean':value['complete']=1
        else:value['row']['probabilities']={}
        write(p,value)
    elif fault=='comparison':write(directory/'CALIBRATION.json',{})
    elif fault=='invalidity':write(directory/'INVALIDITY.json',[])
    elif fault in ('tolerance','transport'):
        value=read(directory/'IDENTITY.json');value['amended_tolerance' if fault=='tolerance' else 'transport_seconds']=99;write(directory/'IDENTITY.json',value)
    elif fault=='counts_boolean':done['instrument_only']=1
    elif fault=='decision_boolean':done['instrument_accepted']=1
    seal()
    with pytest.raises((ValueError,FileNotFoundError,KeyError)):
        subject.inspect_completed(job,plan,tmp_path)


def test_failed_and_unrun_are_retained_without_fixture_access(tmp_path,monkeypatch):
    def forbidden(*a):raise AssertionError('uncompleted calibration inputs opened')
    monkeypatch.setattr(subject,'inspect_completed',forbidden)
    checked=[];monkeypatch.setattr(subject,'verify_disposition',lambda q,j,s:checked.append(s['status']))
    prior={k:{'module':subject.MODULE} for k in ('failure','blocked')}
    states={k:{'status':v,'reason':'original failure','disposition_sha256':digest(v)} for k,v in [('failure','FAILED'),('blocked','NOT_RUN')]}
    write(tmp_path/'STATUS.json',{'jobs':states})
    assert subject.queue_audits({},tmp_path,prior)['jobs']==states and checked==['FAILED','NOT_RUN']


def saved_consumer(tmp_path,monkeypatch,*,selected=False,failed=False):
    """Literal consumer records over known saved probabilities, no model calls.

    The selected-map resolver's existing fitting-grid tests are separate. This
    fixture substitutes that producer only; map validation and exact-package
    calibration reconstruction run normally.
    """
    from runners.stage9 import calibration_check as consumer,neural_operations,selected_recipe
    from runners.stage9.recipe_selection import PILOT_FITS
    directory,_,original,_,_=saved(tmp_path,monkeypatch,failed)
    for module in (consumer,neural_operations,selected_recipe):monkeypatch.setattr(module,'REPO',tmp_path)
    monkeypatch.setattr(consumer,'ROOT',tmp_path)
    for module in (consumer,selected_recipe):monkeypatch.setattr(module,'inside',lambda p:Path(p).resolve())
    target=tmp_path/'target';package=read(directory/'PACKAGES.json')['float16-cuda-4']
    target_identity={'cell_identity':digest('target'),'scope':'pilot','family':'qwen','package_kind':'fitted'}
    mapping=tmp_path/'CALIBRATIONS.json';provenance=None
    if selected:
        family,recipe,seed=next(row for row in PILOT_FITS if row[0]=='qwen')
        prior={'family':family,'recipe':recipe,'seed':seed,'selection':str(tmp_path/'selection'),
            'fitting_manifest':str(tmp_path/'fit-plan'),'fitting_queue':str(tmp_path/'fit-queue'),
            'adapter_sha256':digest('adapter'),'training_complete_sha256':digest('fit')}
        target_identity.update(recipe_selection=prior,adapter_sha256=digest('adapter'),training_complete_sha256=digest('fit'))
        monkeypatch.setattr(selected_recipe,'resolve',lambda *a:(tmp_path/'fit',dict(prior)))
        rows=[{'family':f,'recipe':r,'seed':s,'calibration':str(directory if f=='qwen' else tmp_path/'other-calibration')}
              for f,r,s in PILOT_FITS]
        write(mapping,{'scope':'pilot','calibrations':rows})
        provenance={'mapping':str(mapping),'mapping_sha256':file_hash(mapping),'recipe_selection':dict(prior)}
    write(target/'IDENTITY.json',target_identity);write(target/'PACKAGE.json',package)
    def seal_target():
        ti=read(target/'IDENTITY.json')
        write(target/'COMPLETE.json',{'execution_complete':True,'cell_identity':ti['cell_identity'],
            'identity_sha256':digest(ti),'outputs':closure([target/'IDENTITY.json',target/'PACKAGE.json'])})
    seal_target()
    output=tmp_path/'private/calibration-check-pilots/consumer'
    args=['--output',str(output),'--target',str(target),'--scope','pilot']
    args+=['--selected-calibrations',str(mapping)] if selected else ['--calibration',str(directory)]
    job={'id':'consume','module':subject.CONSUMER_MODULE,'arguments':args,'produces':str(output/'COMPLETE.json')}
    files={**original['sources']['files'],'runners/run_arg_replication.py':digest('queue-only-helper')}
    plan={'sources':{'files':files,'sha256':digest(files)},'jobs':[job]}
    cell=digest({'manifest_sha256':digest(plan),'job':job})
    # Independent literal identity, rather than the constructor being tested.
    identity={'cell_identity':cell,'operation':'actual-package-calibration-consumer-v1','scope':'pilot',
        'source':original['sources'],'target':str(target),'calibration':str(directory),
        'target_complete_sha256':file_hash(target/'COMPLETE.json'),
        'calibration_complete_sha256':file_hash(directory/'COMPLETE.json'),'package':package}
    if selected:identity['selected_calibration']=provenance
    decision=calibration.checked_calibration(directory,package)
    assert decision['instrument_accepted'] is (not failed)
    write(output/'IDENTITY.json',identity);write(output/'DECISION.json',decision)
    done={'cell_identity':cell,'identity_sha256':digest(identity),'execution_complete':True,
        'instrument_accepted':not failed,'scientific_admission':False,'wall_seconds':1.0,'parent_cpu_seconds':.5}
    def seal():
        done['identity_sha256']=digest(read(output/'IDENTITY.json'))
        done['outputs']=closure([p for p in output.iterdir() if p.name!='COMPLETE.json'])
        write(output/'COMPLETE.json',done)
    seal();return output,target,mapping,job,plan,done,seal,seal_target


@pytest.mark.parametrize('selected',[False,True])
@pytest.mark.parametrize('failed',[False,True])
def test_consumer_reconstructs_fixed_and_selected_decisions(tmp_path,monkeypatch,selected,failed):
    from runners.stage9 import calibration_check as consumer
    output,target,mapping,job,plan,done,seal,seal_target=saved_consumer(tmp_path,monkeypatch,selected=selected,failed=failed)
    # Exercise the actual Windows writer lifecycle, including its persistent
    # empty lock file, before disabling all writer entrypoints for inspection.
    from runners.stage9.queue import writer
    with writer(output):pass
    def forbidden(*a,**k):raise AssertionError('consumer audit attempted writer/model execution')
    for module,names in [(consumer,('run','Units','writer')), (calibration,('resident','execute','writer','Units','post'))]:
        for name in names:monkeypatch.setattr(module,name,forbidden)
    before=closure([tmp_path]);result=subject.inspect_consumer(job,plan,tmp_path)
    assert result['instrument_accepted'] is (not failed) and result['selected_calibration'] is selected
    assert result['new_reader_calls']==result['new_reserve_openings']==0
    assert result['scientific_admission'] is False and closure([tmp_path])==before
    write(tmp_path/'STATUS.json',{'jobs':{'consume':{'status':'COMPLETE'}}})
    assert subject.queue_audits(plan,tmp_path,{'consume':job})['jobs']=={'consume':result}


@pytest.mark.parametrize('fault',['identity','source','decision','decision_boolean','decision_scope',
    'acceptance','acceptance_boolean','execution_boolean','admission','cell','extra_output','missing_output',
    'unlisted_output','writer_payload','target_scope','target_package','target_identity','calibration_path','produce','dispatcher','uncommitted'])
def test_consumer_rehashed_substitutions_refuse(tmp_path,monkeypatch,fault):
    output,target,mapping,job,plan,done,seal,seal_target=saved_consumer(tmp_path,monkeypatch)
    if fault in ('identity','source'):
        value=read(output/'IDENTITY.json');value['operation' if fault=='identity' else 'source']='changed'
        write(output/'IDENTITY.json',value)
    elif fault.startswith('decision'):
        value=read(output/'DECISION.json')
        value['scientific_admission' if fault=='decision_scope' else 'instrument_accepted']=(1 if fault=='decision_boolean' else False if fault=='decision' else True)
        write(output/'DECISION.json',value)
    elif fault in ('acceptance','acceptance_boolean','execution_boolean','admission','cell'):
        key={'acceptance':'instrument_accepted','acceptance_boolean':'instrument_accepted',
            'execution_boolean':'execution_complete','admission':'scientific_admission','cell':'cell_identity'}[fault]
        done[key]={'acceptance':False,'acceptance_boolean':1,'execution_boolean':1,'admission':True,'cell':'other'}[fault]
    elif fault=='extra_output':write(output/'EXTRA.json',{})
    elif fault=='missing_output':(output/'DECISION.json').unlink()
    elif fault in ('target_scope','target_identity'):
        value=read(target/'IDENTITY.json');value['scope' if fault=='target_scope' else 'cell_identity']='changed'
        write(target/'IDENTITY.json',value);seal_target()
    elif fault=='target_package':
        value=read(target/'PACKAGE.json');value['model']='changed';write(target/'PACKAGE.json',value);seal_target()
    elif fault=='calibration_path':job['arguments'][-1]=str(tmp_path/'other-calibration')
    elif fault=='produce':job['produces']=str(tmp_path/'different/COMPLETE.json')
    elif fault=='dispatcher':job['module']=subject.MODULE
    elif fault=='uncommitted':
        def refuse(*a):raise ValueError('original queue commit missing')
        monkeypatch.setattr(subject,'verify_committed',refuse)
    seal()
    if fault=='unlisted_output':write(output/'UNLISTED.json',{})
    if fault=='writer_payload':(output/'WRITER.lock').write_bytes(b'unexpected evidence')
    with pytest.raises((ValueError,KeyError,FileNotFoundError)):
        subject.inspect_consumer(job,plan,tmp_path)


@pytest.mark.parametrize('fault',['map_missing','map_path','map_scope','map_identity','selected_provenance'])
def test_consumer_selected_provenance_is_live(tmp_path,monkeypatch,fault):
    output,target,mapping,job,plan,done,seal,seal_target=saved_consumer(tmp_path,monkeypatch,selected=True)
    if fault=='selected_provenance':
        value=read(output/'IDENTITY.json');value['selected_calibration']['recipe_selection']['seed']=0
        write(output/'IDENTITY.json',value)
    else:
        value=read(mapping)
        if fault=='map_missing':value['calibrations'].pop()
        elif fault=='map_path':value['calibrations'][0]['calibration']=str(tmp_path/'wrong')
        elif fault=='map_scope':value['scope']='scientific'
        else:value['extra']='changed bytes'
        write(mapping,value)
    seal()
    with pytest.raises((ValueError,KeyError,FileNotFoundError)):
        subject.inspect_consumer(job,plan,tmp_path)


def test_consumer_failed_and_unrun_do_not_open_inputs(tmp_path,monkeypatch):
    monkeypatch.setattr(subject,'inspect_consumer',lambda *a:pytest.fail('nonexecuted input opened'))
    checked=[];monkeypatch.setattr(subject,'verify_disposition',lambda q,j,s:checked.append(s['status']))
    prior={k:{'module':subject.CONSUMER_MODULE} for k in ('failed','blocked')}
    states={k:{'status':v,'reason':'original nonexecution','disposition_sha256':digest(v)}
            for k,v in [('failed','FAILED'),('blocked','NOT_RUN')]}
    write(tmp_path/'STATUS.json',{'jobs':states})
    assert subject.queue_audits({},tmp_path,prior)['jobs']==states and checked==['FAILED','NOT_RUN']
    states['failed']['status']='RUNNING';write(tmp_path/'STATUS.json',{'jobs':states})
    with pytest.raises(ValueError,match='terminal'):subject.queue_audits({},tmp_path,prior)
