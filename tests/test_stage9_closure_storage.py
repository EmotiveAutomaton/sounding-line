"""Storage guards use literal files; the mixed-package integration uses real capsules."""
from pathlib import Path

import pytest

from runners.stage9 import closure_storage, closure_capsules, closure_probe
from runners.stage9.common import digest, file_hash, read, write


def outputs(directory, repository):
    files={p.relative_to(repository).as_posix():file_hash(p) for p in directory.rglob('*')
           if p.is_file() and p.name!='COMPLETE.json' and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    return {'files':files,'sha256':digest(files)}


def make_call(directory, name='one', runtime='reader', nested=True):
    cap=directory/('calls/capsules' if nested else 'capsules')/name
    for path,content in [('bootstrap.py','fixture bootstrap'),('reader/worker.py',runtime)]:
        target=cap/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content)
    task={'operation':'fixture'};evidence={'public':name}
    write(cap/'task.json',task);write(cap/'evidence.json',evidence)
    copied={'files':{name:file_hash(cap/name) for name in ('bootstrap.py','reader/worker.py')},
            'task_sha256':digest(task),'evidence_sha256':digest(evidence)}
    copied['sha256']=digest(copied['files'])
    write(cap.parent/'closures'/(cap.name+'.json'),copied)
    result={'capsule':str(cap.resolve()),'copied_sources':copied}
    path=directory/'calls'/(name+'.json');write(path,{'input_sha256':digest({'evidence':evidence,'task':task}),'result':result})
    return path,cap,result


@pytest.mark.parametrize('nested',[False,True])
def test_flat_and_nested_records_have_one_call_and_immutable_capsule_inventory(tmp_path,nested):
    work=tmp_path/'work';make_call(work,nested=nested)
    before=outputs(work,tmp_path);actual=closure_storage.inventory(work,before,tmp_path)
    assert actual['call_files']==['work/calls/one.json'] and len(actual['capsules'])==1
    assert not actual['uncached_capsules'] and not actual['scientific_admission']
    assert outputs(work,tmp_path)==before


def test_uncached_partial_bytes_are_retained_without_inventing_execution_or_cause(tmp_path):
    work=tmp_path/'work';make_call(work);path,cap,_=make_call(work,'partial');path.unlink()
    actual=closure_storage.inventory(work,outputs(work,tmp_path),tmp_path)
    assert len(actual['call_files'])==1 and len(actual['uncached_capsules'])==1
    retained=actual['uncached_capsules'][0]
    assert retained['disposition']=='UNCACHED_CAPSULE_RETAINED' and retained['actual_output_records']==[]
    assert not retained['cached_call_present'] and not retained['scientific_admission']


@pytest.mark.parametrize('fault',['uncommitted','unknown_json','unknown_binary','cache_fields','changed_task',
                                 'changed_evidence','missing_closure','changed_copy','reused_capsule'])
def test_storage_refuses_incomplete_unknown_or_disconnected_bytes(tmp_path,fault):
    work=tmp_path/'work';path,cap,result=make_call(work);declared=outputs(work,tmp_path)
    if fault=='uncommitted':write(work/'calls/new.json',{'input_sha256':'b'*64,'result':result})
    elif fault=='unknown_json':write(work/'calls/unknown.json',{'opaque':'data'})
    elif fault=='unknown_binary':(work/'calls/opaque.bin').write_bytes(b'unknown')
    elif fault=='cache_fields':write(path,{'result':result})
    elif fault=='changed_task':write(cap/'task.json',{'operation':'different'})
    elif fault=='changed_evidence':write(cap/'evidence.json',{'public':'different'})
    elif fault=='missing_closure':(cap.parent/'closures'/(cap.name+'.json')).unlink()
    elif fault=='changed_copy':(cap/'reader/worker.py').write_text('changed')
    else:write(work/'calls/second.json',{'input_sha256':'b'*64,'result':result})
    if fault!='uncommitted':declared=outputs(work,tmp_path)
    with pytest.raises((ValueError,FileNotFoundError)):
        closure_storage.inventory(work,declared,tmp_path)


def mixed_fixture(tmp_path,monkeypatch):
    monkeypatch.setattr(closure_capsules,'REPO',tmp_path)
    monkeypatch.setattr('runners.stage9.queue.verify_committed',lambda *args:None)
    monkeypatch.setattr(closure_capsules,'inspect_call',lambda *args:{'status':'VERIFIED','scientific_admission':False})
    work=tmp_path/'work';pairs=[make_call(work,runtime,runtime) for runtime in ('reader','comparison')]
    maps={runtime:result['copied_sources']['files'] for runtime,(_,_,result) in zip(('reader','comparison'),pairs)}
    monkeypatch.setattr(closure_probe,'bindings',lambda runtime,source:{'runtime':runtime,'copied_sources':maps[runtime]})
    prior={runtime:{'id':runtime,'module':'runners.stage9.closure_probe','produces':runtime+'/COMPLETE.json'} for runtime in maps}
    prior['work']={'id':'work','produces':'work/COMPLETE.json','after':list(maps),
        'requires':[{'job':runtime,'field':['isolation_probe_verified'],'equals':True} for runtime in maps]}
    for runtime in maps:
        write(tmp_path/runtime/'COMPLETE.json',{'outputs':{'files':{}}})
        write(tmp_path/runtime/'BINDING.json',{'runtime':runtime,'copied_sources':maps[runtime]})
        write(tmp_path/runtime/'PROBE.json',{})
    write(work/'COMPLETE.json',{'outputs':outputs(work,tmp_path)})
    write(tmp_path/'queue/STATUS.json',{'jobs':{key:{'status':'COMPLETE'} for key in prior}})
    plan={'jobs':list(prior.values()),'sources':{},'capsule_reviews':{'work':{'packages':[
        {'runtime':runtime,'probe_job':runtime} for runtime in maps]}}}
    return plan,tmp_path/'queue',prior


def test_mixed_roster_matches_actual_copied_bindings_instead_of_filename(tmp_path,monkeypatch):
    plan,queue,prior=mixed_fixture(tmp_path,monkeypatch)
    result=closure_capsules.queue_audits(plan,queue,prior)['jobs']['work']
    assert result['call_count']==2 and {row['runtime'] for row in result['calls']}=={'reader','comparison'}
    assert set(result['probes'])=={'reader','comparison'} and not result['scientific_admission']


@pytest.mark.parametrize('fault',['empty_roster','duplicate_runtime','missing_package','missing_gate'])
def test_mixed_roster_refuses_missing_ambiguous_or_unprobed_package(tmp_path,monkeypatch,fault):
    plan,queue,prior=mixed_fixture(tmp_path,monkeypatch);packages=plan['capsule_reviews']['work']['packages']
    if fault=='empty_roster':packages.clear()
    elif fault=='duplicate_runtime':packages.append(dict(packages[0]))
    elif fault=='missing_package':packages.pop()
    else:prior['work']['requires'].pop()
    with pytest.raises(ValueError):closure_capsules.queue_audits(plan,queue,prior)


def test_real_mixed_packages_and_nested_capsules_pass_original_probes(tmp_path,monkeypatch):
    from runners.stage9 import baseline_matrix_runtime,comparison_runtime
    from runners.stage9.revision_predictions import sources
    from tests.test_stage9_baseline_matrix import inputs
    from tests.test_stage9_comparison_runtime import bundle
    monkeypatch.setattr(closure_capsules,'REPO',tmp_path);monkeypatch.setattr(closure_capsules,'ROOT',tmp_path)
    monkeypatch.setattr('runners.stage9.queue.verify_committed',lambda *args:None)
    work=tmp_path/'work';sentinel=tmp_path/'existing-hidden.json';sentinel.write_text('keep')
    plan={'sources':sources(),'capsule_reviews':{'work':{'packages':[]}}};prior={}
    for runtime,module,data in [('baseline_matrix',baseline_matrix_runtime,inputs()),('comparison',comparison_runtime,bundle())]:
        probe_dir=tmp_path/runtime
        probe=module.execute(None,task={'probe':True,'forbidden_paths':[str(sentinel)],'other_port':65534},root=probe_dir/'capsules')
        write(probe_dir/'PROBE.json',probe);write(probe_dir/'BINDING.json',closure_probe.bindings(runtime,plan['sources']))
        write(probe_dir/'COMPLETE.json',{'outputs':{'files':{}}})
        prior[runtime]={'id':runtime,'module':'runners.stage9.closure_probe','produces':runtime+'/COMPLETE.json'}
        call=module.execute(data,root=work/'calls'/('caps-'+runtime));assert call['accepted']
        write(work/'calls'/(runtime+'.json'),{'input_sha256':digest(data),'result':call})
        plan['capsule_reviews']['work']['packages'].append({'runtime':runtime,'probe_job':runtime})
    prior['work']={'id':'work','produces':'work/COMPLETE.json','after':list(prior),
        'requires':[{'job':runtime,'field':['isolation_probe_verified'],'equals':True} for runtime in prior]}
    plan['jobs']=list(prior.values());write(work/'COMPLETE.json',{'outputs':outputs(work,tmp_path)})
    write(tmp_path/'queue/STATUS.json',{'jobs':{key:{'status':'COMPLETE'} for key in prior}})
    result=closure_capsules.queue_audits(plan,tmp_path/'queue',prior)['jobs']['work']
    assert result['call_count']==2 and all(row['inspection']['status']=='VERIFIED' for row in result['calls'])
    assert len(result['storage']['capsules'])==2 and not result['storage']['uncached_capsules']
    assert sentinel.read_text()=='keep'
