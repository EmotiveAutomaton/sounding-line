import copy
import time
import pytest
from runners.stage9.queue import validate_manifest, conditions, inside
from runners.stage9.common import ROOT


def plan():
    return {'kind':'prelaunch_rehearsal','horizon_epoch':time.time()+60,
            'sources':{'files':{'runners/stage9/rehearsal_job.py':'fixture'}},
            'jobs':[{'id':'a','after':[],'module':'runners.stage9.rehearsal_job','arguments':[],
                     'produces':str(ROOT/'private/fixture/COMPLETE.json'), 'resource':'cpu',
                     'role':'work','estimated_gpu_seconds':0}]}


def test_duplicate_produces_cycles_and_unbounded_work_fail():
    p=plan();assert validate_manifest(p)
    duplicate=copy.deepcopy(p);duplicate['jobs'].append(duplicate['jobs'][0]|{'id':'b'})
    with pytest.raises(ValueError):validate_manifest(duplicate)
    cycle=copy.deepcopy(p);cycle['jobs'][0]['after']=['a']
    with pytest.raises(ValueError):validate_manifest(cycle)
    unbounded=copy.deepcopy(p);unbounded['jobs'][0]['estimated_gpu_seconds']=float('nan')
    with pytest.raises(ValueError):validate_manifest(unbounded)
    over=copy.deepcopy(p);over['jobs'][0]['estimated_gpu_seconds']=92*3600+1
    with pytest.raises(ValueError):validate_manifest(over)


def test_missing_gate_pass_cannot_be_borrowed_from_terminal_status():
    job={'requires':[{'job':'first','field':['admitted'],'equals':True}]}
    assert conditions(job,{'first':{'status':'NOT_RUN'}},{}) is not None


def test_gate_field_path_and_failed_dependency_permission_have_exact_types():
    original=plan();second=copy.deepcopy(original['jobs'][0]);second.update(id='b',after=['a'],
        produces=str(ROOT/'private/fixture-second/COMPLETE.json'),requires=[{'job':'a','field':['accepted'],'equals':True}])
    original['jobs'].append(second);assert validate_manifest(original)
    for field in ('accepted',[],[1],['']):
        broken=copy.deepcopy(original);broken['jobs'][1]['requires'][0]['field']=field
        with pytest.raises(ValueError,match='field path'):validate_manifest(broken)
    for value in ('false',1,[]):
        broken=copy.deepcopy(original);broken['jobs'][1]['allow_failed_dependencies']=value
        with pytest.raises(ValueError,match='boolean'):validate_manifest(broken)


def test_outputs_cannot_escape_scientific_root():
    with pytest.raises(ValueError):inside(ROOT/'..'/'elsewhere')
    with pytest.raises(ValueError):inside(ROOT)


def test_recovery_checks_wrapper_and_unknown_spawn_window(tmp_path, monkeypatch):
    import runners.stage9.queue as queue
    monkeypatch.setattr(queue, 'is_same_live_process', lambda p: p.get('live', False))
    with pytest.raises(RuntimeError, match='wrapper'):
        queue.recoverable_attempt({'directory': 'attempt', 'wrapper_process': {'live': True}}, tmp_path)
    with pytest.raises(RuntimeError, match='spawn window'):
        queue.recoverable_attempt({'directory': 'attempt'}, tmp_path)
    queue.recoverable_attempt({'directory': 'attempt', 'wrapper_process': {'live': False}}, tmp_path)


def test_execution_receipt_requires_actual_entrypoint_and_support(tmp_path):
    from runners.stage9.queue import verify_execution
    from runners.stage9.common import write
    p=plan(); job=p['jobs'][0]
    loaded={k:'fixture' for k in ('runners/stage9/source_bootstrap.py', 'runners/stage9/common.py',
                                'runners/stage9/process_identity.py', 'runners/stage9/rehearsal_job.py')}
    p['sources']['files']=dict(loaded)
    receipt={'returncode':0,'cell_identity':'id','error':None,'loaded_project_sources':loaded}
    path=tmp_path/'EXECUTION.json';write(path,receipt)
    verify_execution(path,'id',p,job)
    del loaded['runners/stage9/rehearsal_job.py'];write(path,receipt)
    with pytest.raises(ValueError, match='source closure'):
        verify_execution(path,'id',p,job)


def test_failure_only_blocks_consumers_and_horizon_only_stops_expansion():
    from runners.stage9.queue import admission_reason
    states={'failed':{'status':'FAILED'}}
    work={'after':[],'requires':[],'role':'work'}
    assert admission_reason(work,states,{},0,10) is None
    assert admission_reason(work|{'after':['failed']},states,{},0,10) is not None
    assert admission_reason(work|{'role':'expansion'},states,{},0,10) is not None
    assert admission_reason(work|{'role':'closure','after':['failed'],'allow_failed_dependencies':True},states,{},0,10) is None


def test_disposition_is_durable_and_tampering_is_refused(tmp_path,monkeypatch):
    import runners.stage9.queue as queue
    from runners.stage9.common import write
    monkeypatch.setattr(queue,'REPO',tmp_path)
    job={'id':'blocked','produces':'work/COMPLETE.json'}
    current={'status':'NOT_RUN','reason':'dependent gate failed'}
    queue.disposition(tmp_path/'queue',job,{},'manifest',current)
    queue.verify_disposition(tmp_path/'queue',job,current)
    write(tmp_path/'work/COMPLETE.json',{'status':'COMPLETE'})
    with pytest.raises(ValueError,match='produce changed'):
        queue.verify_disposition(tmp_path/'queue',job,current)


def test_direct_bootstrap_preserves_standard_library_queue(tmp_path):
    """A cold dependency import must not resolve the scheduler's sibling file."""
    import subprocess
    import sys
    import shutil
    from runners.stage9.common import REPO,digest,file_hash,read,write
    root=tmp_path/'isolated-repository';stage=root/'runners/stage9';stage.mkdir(parents=True)
    for name in ('source_bootstrap.py','common.py','process_identity.py'):
        shutil.copyfile(REPO/'runners/stage9'/name,stage/name)
    for path in (root/'runners/__init__.py',stage/'__init__.py'):
        path.write_text('',encoding='utf-8')
    (stage/'queue.py').write_text("raise RuntimeError('package sibling shadowed stdlib')\n",encoding='utf-8')
    (stage/'probe.py').write_text(
        "from queue import Queue\nfrom runners.stage9.common import write\n"
        "import sys\nq=Queue();q.put('stdlib')\nwrite(sys.argv[1],{'value':q.get()})\n",encoding='utf-8')
    files={p.relative_to(root).as_posix():file_hash(p) for p in root.rglob('*.py')}
    sources={'files':files,'sha256':digest(files)}
    attempt=root/'attempt';attempt.mkdir();produce=root/'out.json'
    config={'repo':str(root),'attempt':str(attempt),'sources':sources,
        'cell_identity':'a'*64,'module':'runners.stage9.probe','arguments':[str(produce)]}
    write(root/'CONFIG.json',config)
    result=subprocess.run([sys.executable,'-B',str(stage/'source_bootstrap.py'),str(root/'CONFIG.json')],
        cwd=root,capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr
    assert read(produce)=={'value':'stdlib'}
    execution=read(attempt/'EXECUTION.json')
    assert 'runners/stage9/probe.py' in execution['loaded_project_sources']
    assert 'runners/stage9/queue.py' not in execution['loaded_project_sources']
