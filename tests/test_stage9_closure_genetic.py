"""Constructed local revisions and saved outcomes; no model or raw-corpus reads."""
from pathlib import Path
import pytest
from runners.stage9 import closure_genetic as subject, genetic_jobs as genetic
from runners.stage9 import common, revision_predictions, artifact_comparisons, runtime
from runners.stage9.common import closure, digest, file_hash, read, write
from runners.stage9.genetic_cases import offered
from runners.stage9.features import copy_probabilities
from runners.readout_repair import readout, digest as text_digest


def saved(tmp_path, monkeypatch, kind='controls', accepted=True):
    original_repo=common.REPO
    for module in (subject, genetic, common, revision_predictions, artifact_comparisons, runtime):
        monkeypatch.setattr(module,'REPO',tmp_path)
    monkeypatch.setattr(genetic,'ROOT',tmp_path)
    for module in (subject,genetic,revision_predictions):
        monkeypatch.setattr(module,'inside',lambda p:Path(p).resolve())
    monkeypatch.setattr(subject,'verify_committed',lambda *a:None)
    source_names=list(subject.COPIES.values())+['runners/stage7/runtime.py']
    for name in source_names:
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((original_repo/name).read_bytes())
    source=closure([tmp_path/n for n in source_names])
    pool=[{'key':str(i),'work':'constructed work','local_before':'old local text',
        'local_after':text,'hands':[],'hand_status':'synthetic unspecified hand'}
        for i,text in enumerate(('new local text','other short words','three different words','another changed phrase'))]
    case=offered(pool[0],pool);cases_path=tmp_path/'private/genetic-case-pilots/fixture'
    case_identity={'operation':'genetic-cases-v1','scope':'pilot','cell_identity':'synthetic-case',
        'rows_sha256':digest([case]),'selected_keys':[case['key']]}
    write(cases_path/'IDENTITY.json',case_identity);write(cases_path/'CASES.json',[case])
    write(cases_path/'COMPLETE.json',{'execution_complete':True,'identity_sha256':digest(case_identity),
        'cell_identity':'synthetic-case','assigned':1,'outputs':closure([cases_path/'IDENTITY.json',cases_path/'CASES.json'])})
    directory=tmp_path/'private/genetic-prediction-pilots/fixture'
    args=[kind,'--output',str(directory),'--cases',str(cases_path),'--scope','pilot']
    if kind=='neural':args+=['--family','qwen','--package-kind','base']
    job={'id':'fixture','module':subject.MODULE,'arguments':args,'produces':str(directory/'COMPLETE.json')}
    plan={'sources':source,'jobs':[job]};cell=digest({'manifest_sha256':digest(plan),'job':job})
    identity,_,_=genetic.prediction_context(directory,cases_path,'pilot',kind,cell=cell,source=source,
        family='qwen' if kind=='neural' else None,package_kind='base' if kind=='neural' else 'fitted')
    write(directory/'IDENTITY.json',identity)
    evidence=case['evidence']
    if kind=='neural':
        base=subject.BASES['qwen']
        package={'model':base['model'],'revision':base['revision'],
            **{k:identity[k] for k in ('adapter_sha256','precision','max_context','max_support','max_new_tokens')},
            'device':'cuda','batch_size':4,'generation':{'requested':identity['generation']},
            'scorer_sources':source,'scorer_sha256':source['sha256']}
        write(directory/'PACKAGE.json',package);(directory/'services').mkdir()
        task={'operation':'choice','identity':package|{'information_sha256':digest(evidence)}}
        components=[{'option_id':key,'logprob':-float(i+1),'valid':True,'identity':task['identity'],
            'prefix_sha256':text_digest(evidence['prefix']),'continuation_sha256':text_digest(text),
            'semantics':'sum_log_probability'} for i,(key,text) in enumerate(sorted(evidence['options'].items()))]
        prediction=readout(evidence['prefix'],evidence['options'],lambda *a:components,task['identity'])
    else:
        task={'operation':'copy_baseline','copy_source':case['case']['local_before']}
        prediction={'valid':True,'probs':copy_probabilities(case['case']['local_before'],evidence['options'])}
    if not accepted:prediction={'valid':False,'reason':'constructed retained failure'}
    cap,copied=runtime.materialize(evidence,task,directory/'capsules')
    loaded={('reader' if p=='reader/__init__.py' else p[:-3].replace('/','.')):sha
            for p,sha in copied['files'].items() if p.startswith('reader/')}
    receipt={'loaded_sources':loaded};access={'fixture':True}
    for name,value in [('prediction',prediction),('receipt',receipt),('access',access)]:write(cap/'out'/(name+'.json'),value)
    result={'accepted':accepted,'rc':0,'capsule':str(cap),'copied_sources':copied,
        'prediction':prediction,'receipt':receipt,'access':access,'inputs_and_sources_unchanged':True}
    write(directory/'calls'/('0.json'),{'input_sha256':digest({'evidence':evidence,'task':task}),'result':result})
    row=genetic.unit(case,result,kind)
    write(directory/'units'/(digest('0')+'.json'),{'identity':digest(identity),'key':'0','complete':True,'row':row})
    write(directory/'PREDICTIONS.json',[row])
    done={'cell_identity':cell,'identity_sha256':digest(identity),'execution_complete':True,'scope':'pilot',
        'assigned':1,'invalid':int(not accepted),'scored':False,'scientific_admission':False}
    def seal():
        done['outputs']=closure([p for p in directory.iterdir() if p.name!='COMPLETE.json'])
        write(directory/'COMPLETE.json',done)
    seal();return directory,job,plan,done,seal


@pytest.mark.parametrize('kind',['controls','neural'])
@pytest.mark.parametrize('accepted',[True,False])
def test_saved_complete_predictions_reconstruct_without_execution(tmp_path,monkeypatch,kind,accepted):
    directory,job,plan,_,_=saved(tmp_path,monkeypatch,kind,accepted)
    def forbidden(*a,**k):raise AssertionError('reader/writer called by saved reconstruction')
    for name in ('writer','Units','execute'):monkeypatch.setattr(genetic,name,forbidden)
    before=closure([tmp_path]);result=subject.inspect_completed(job,plan,tmp_path)
    assert result['calls']==result['units']==1 and result['invalid_calls_retained']==int(not accepted)
    assert result['new_reader_calls']==result['new_reserve_openings']==0 and not result['scientific_admission']
    assert before==closure([tmp_path])


@pytest.mark.parametrize('fault',['identity','cases','signature','task','evidence','source','access','missing_prediction',
    'missing_receipt','validity_boolean','unit_boolean','unit_row','extra_call','missing_call','extra_unit','missing_unit',
    'extra_capsule','extra_closure','closure','export','assigned','invalid','scored','admission','package','components'])
def test_rehashed_semantic_changes_refuse(tmp_path,monkeypatch,fault):
    kind='neural' if fault in ('package','components') else 'controls'
    directory,job,plan,done,seal=saved(tmp_path,monkeypatch,kind)
    path=directory/'calls/0.json';call=read(path);result=call['result'];cap=Path(result['capsule'])
    if fault=='identity':
        p=directory/'IDENTITY.json';v=read(p);v['scope']='scientific';write(p,v)
    elif fault=='cases':
        p=Path(genetic.argument_parser().parse_args(job['arguments']).cases)/'CASES.json';v=read(p);v[0]['truth']='absent';write(p,v)
    elif fault=='signature':call['input_sha256']=digest('changed');write(path,call)
    elif fault in ('task','evidence','access'):write(cap/('out/access.json' if fault=='access' else fault+'.json'),{})
    elif fault=='source':(cap/'reader/worker.py').write_text('# changed\n',encoding='utf-8')
    elif fault in ('missing_prediction','missing_receipt'):(cap/'out'/(fault.removeprefix('missing_')+'.json')).unlink()
    elif fault=='validity_boolean':result['accepted']=1;write(path,call)
    elif fault in ('unit_boolean','unit_row'):
        p=next((directory/'units').glob('*.json'));v=read(p)
        if fault=='unit_boolean':v['complete']=1
        else:v['row']['truth']='absent'
        write(p,v)
    elif fault=='extra_call':write(directory/'calls/extra.json',call)
    elif fault=='missing_call':path.unlink()
    elif fault=='extra_unit':write(directory/'units/extra.json',{})
    elif fault=='missing_unit':next((directory/'units').glob('*.json')).unlink()
    elif fault=='extra_capsule':(directory/'capsules/extra').mkdir()
    elif fault=='extra_closure':write(directory/'capsules/closures/extra.json',{})
    elif fault=='closure':write(directory/'capsules/closures'/(cap.name+'.json'),{})
    elif fault=='export':write(directory/'PREDICTIONS.json',[])
    elif fault in ('assigned','invalid','scored'):done[fault]=2 if fault!='scored' else True
    elif fault=='admission':done['scientific_admission']=True
    elif fault=='package':
        p=directory/'PACKAGE.json';v=read(p);v['model']='changed';write(p,v)
    elif fault=='components':
        result['prediction']['components'][0]['logprob']=-99
        write(cap/'out/prediction.json',result['prediction']);write(path,call)
        predictions=read(directory/'PREDICTIONS.json');predictions[0]['call']=result;write(directory/'PREDICTIONS.json',predictions)
    seal()
    with pytest.raises((ValueError,FileNotFoundError,KeyError)):subject.inspect_completed(job,plan,tmp_path)


def test_terminal_dispositions_and_unfinished_refusal(tmp_path,monkeypatch):
    def forbidden(*a):raise AssertionError('uncompleted input opened')
    monkeypatch.setattr(subject,'inspect_completed',forbidden)
    checks=[];monkeypatch.setattr(subject,'verify_disposition',lambda q,j,s:checks.append(s['status']))
    prior={k:{'module':subject.MODULE,'arguments':[op]} for k,op in [('failed','neural'),('blocked','controls')]}
    states={k:{'status':s,'reason':'original refusal','disposition_sha256':digest(s)} for k,s in [('failed','FAILED'),('blocked','NOT_RUN')]}
    write(tmp_path/'STATUS.json',{'jobs':states})
    assert subject.queue_audits({},tmp_path,prior)['jobs']==states and checks==['FAILED','NOT_RUN']
    states['failed']['status']='RUNNING';write(tmp_path/'STATUS.json',{'jobs':states})
    with pytest.raises(ValueError):subject.queue_audits({},tmp_path,prior)
