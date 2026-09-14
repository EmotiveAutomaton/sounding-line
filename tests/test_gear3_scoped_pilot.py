"""Known-answer scoped admission failures and replay of the actual supplement."""
from copy import deepcopy
import json,os,zipfile
from pathlib import Path
from types import SimpleNamespace
import pytest
from runners import gear3_plan,gear3_scoped_pilot as scoped,gear3_supplement
from runners.stage10.contracts import digest


def fixture(tmp_path,monkeypatch):
    grant=gear3_supplement.authorization(); models=scoped.gear3_batch.PINS
    source=Path(gear3_supplement.__file__).resolve().parents[1]/gear3_supplement.AUTHORIZATION_PATH
    target=tmp_path/gear3_supplement.AUTHORIZATION_PATH;target.parent.mkdir(parents=True);target.write_bytes(source.read_bytes())
    def block(identifier,family):
        return {'block_id':identifier,'node':'P','tasks':[{'record':{'family':family}}],
            'units':[{'task_id':identifier,'model':m,'arm':'R0'} for m in models],'scope':'discarded'}
    blocks=[block(k,f) for k,f in scoped.WHOLE.items()]+[block(scoped.DEFERRED,'ghost-reading'),block(grant['block'],'coauthor-handling')]
    old_bundle=tmp_path/'original.zip';new_bundle=tmp_path/'supplement.zip'
    for target,items in [(old_bundle,blocks),(new_bundle,blocks[-1:])]:
        with zipfile.ZipFile(target,'w') as z:
            for m in items:z.writestr(m['block_id']+'.json',json.dumps(m))
    base={'mode':'science','execution_source_hashes':{},'profiles':{m:{} for m in models},'native_source_identity':{},'server_version':'frozen'}
    old_job={**base,'blocks':[m['block_id']+'.json' for m in blocks]};new_job={**base,'blocks':[blocks[-1]['block_id']+'.json']}
    old={'campaign_id':grant['campaign'],'invocation_id':grant['original_invocation'],'node':'P','status':'FAILED','owner_ended':True,
        'resources':{'gpu':'L40S'},'command':['runners/gear3.py','round1',grant['original_bundle_sha256']],
        'profile':{'job_sha256':grant['original_job_sha256'],'image':grant['image']},'recovery_of':None}
    new={'campaign_id':grant['campaign'],'invocation_id':grant['invocation'],'node':'Reserve','status':'COMPLETE','owner_ended':True,
        'resources':{'gpu':'L40S'},'command':['runners/gear3.py','round1',grant['bundle_sha256']],
        'profile':{'job_sha256':grant['job_sha256'],'image':grant['image'],'startup_seconds':300},'recovery_of':None,
        'duration_cap_seconds':600,'overhead_cents':25,'reserved_cents':64,'approval':grant['owner_instruction'],'supplement_authorization':deepcopy(grant)}
    data={'runs':[old,new]};dirs=[tmp_path/'old',tmp_path/'new']
    terminals=[{'status':'FAILED','error':deepcopy(scoped.FAILURE),'reservation_sha256':'old','gpu_observation':{'samples':2},'duration_seconds':30},
               {'status':'COMPLETE','reservation_sha256':'new','gpu_observation':{'samples':2},'duration_seconds':10}]
    def put(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v))
    for folder,items in [(dirs[0],blocks[:-1]),(dirs[1],blocks[-1:])]:
        put(folder/'GPU_DEVICE.json',{'returncode':0,'stdout':'L40S'})
        for i,sha in enumerate(models.values()):put(folder/f'load-{i}-memory.json',{'models':[{'digest':sha,'context_length':16384,'size':8,'size_vram':8}]})
        for m in items:
            if m['block_id']!=scoped.DEFERRED:put(folder/'blocks'/m['block_id']/'COMPLETE.json',{'status':'COMPLETE'})
            for u in m['units']:
                route=folder/'blocks'/m['block_id']/'units'/digest(u)[:32]
                put(route/'UNIT.json',{'result':{'status':'VALID'},'unit_wall_seconds':1})
                put(route/'route/ATTEMPT.json',{});put(route/'route/RAW.json',{'message':{'content':'literal'}})
    def invoke(repo,identifier,*a):
        idx=0 if identifier==grant['original_invocation'] else 1
        return (old if idx==0 else new,old_job if idx==0 else new_job,terminals[idx],{'archive_sha256':'old' if idx==0 else 'new'},dirs[idx])
    monkeypatch.setattr(scoped,'verify_invocation',invoke)
    monkeypatch.setattr(scoped,'verify_payload',lambda *a:grant)
    monkeypatch.setattr(scoped.gear3_batch,'validate',lambda m:({m['units'][0]['task_id']:(SimpleNamespace(family=m['tasks'][0]['record']['family']),{})},{}))
    replay=[];monkeypatch.setattr(scoped.gear3_batch,'run_block',lambda m,*a,**kw:replay.append(m['block_id']))
    run=lambda:scoped.compose(tmp_path,old_bundle,new_bundle,data,tmp_path)
    return run,data,terminals,dirs,replay,old_bundle,new_bundle,new_job


def test_complete_branches_plus_exact_supplement_keep_failed_cost_and_scope(tmp_path,monkeypatch):
    run,data,terms,dirs,replay,*_=fixture(tmp_path,monkeypatch);before=deepcopy(data);r=run()
    assert r['status']=='PASS_SCOPED' and r['original_terminal_status']=='FAILED' and data==before
    assert replay==[*scoped.WHOLE,'P-context-boundary-004']
    assert len(r['route_timings'])==4 and len(r['valid_routes'])==4 and r['service_duration_seconds']==40
    assert all(k[0]!='ghost-reading' for k in r['valid_routes'])
    path=tmp_path/'PILOT.json';path.write_text(json.dumps(r));assert gear3_plan.validate_pilot(tmp_path,path,data,tmp_path)==r
    r['valid_routes'].append(['ghost-reading','27b','R3']);path.write_text(json.dumps(r))
    with pytest.raises(ValueError,match='does not reproduce'):gear3_plan.validate_pilot(tmp_path,path,data,tmp_path)


@pytest.mark.parametrize('fault',['unknown-failure','unfinished-supplement','changed-authorization','different-source','missing-whole-block','missing-context','context-invalid','fake-raw','offload','missing-model','corrupt-replay','duration','substituted-context'])
def test_scoped_composition_refuses_incomplete_or_changed_evidence(tmp_path,monkeypatch,fault):
    run,data,terms,dirs,replay,old_bundle,new_bundle,new_job=fixture(tmp_path,monkeypatch)
    if fault=='unknown-failure':terms[0]['error']={'type':'OSError','message':'unknown'}
    if fault=='unfinished-supplement':data['runs'][1]['status']='FAILED'
    if fault=='changed-authorization':data['runs'][1]['supplement_authorization']['seconds']=601
    if fault=='different-source':new_job['execution_source_hashes']={'altered':'hash'}
    if fault=='missing-whole-block':(dirs[0]/'blocks/P-literal-human-001/COMPLETE.json').unlink()
    if fault=='missing-context':(dirs[1]/'blocks/P-context-boundary-004/COMPLETE.json').unlink()
    if fault in {'context-invalid','fake-raw'}:
        p=next(dirs[1].rglob('UNIT.json' if fault=='context-invalid' else 'RAW.json'));v=json.loads(p.read_text())
        if fault=='context-invalid':v['result']['status']='INVALID'
        else:v['simulated']=True
        p.write_text(json.dumps(v))
    if fault=='offload':
        p=dirs[1]/'load-0-memory.json';v=json.loads(p.read_text());v['models'][0]['size_vram']=1;p.write_text(json.dumps(v))
    if fault=='missing-model':(dirs[1]/'load-0-memory.json').unlink()
    if fault=='corrupt-replay':
        def broken(*a,**k):raise ValueError('original parse changed')
        monkeypatch.setattr(scoped.gear3_batch,'run_block',broken)
    if fault=='duration':terms[0]['duration_seconds']=-100
    if fault=='substituted-context':
        with zipfile.ZipFile(new_bundle) as z:m=json.loads(z.read(new_job['blocks'][0]))
        m['scope']='modified'
        with zipfile.ZipFile(new_bundle,'w') as z:z.writestr(new_job['blocks'][0],json.dumps(m))
    with pytest.raises(ValueError):run()


def test_actual_original_archives_compose_and_legacy_full_p_stays_closed(tmp_path):
    if 'G3_SCOPED_REAL_ROOT' not in os.environ:pytest.skip('actual private campaign archives are not installed')
    root=Path(os.environ['G3_SCOPED_REAL_ROOT']);main=root.parent/'sounding-line';data=json.loads((main/'results/gear3_ledger.json').read_text())
    original=root/'.agent-state/gear3-panel-prepared-v1/pilot/INPUT.zip';extra=root/'.agent-state/gear3-context-supplement-proposal-v1/bundle/INPUT.zip';native=main/'results/phase_2_4_stage_10/raw/interface-v3/ghost-public'
    r=scoped.compose(root,original,extra,data,native)
    assert r['admitted_blocks']==list(scoped.WHOLE) and r['supplement']['block_id']=='P-context-boundary-004'
    path=tmp_path/'PILOT.json';path.write_text(json.dumps(r));assert gear3_plan.validate_pilot(root,path,data,native)==r
    with pytest.raises(ValueError,match='complete literal GPU pilot required'):
        gear3_plan.pilot_evidence(root,'p-gpu-panel-v1',original,data,native)
