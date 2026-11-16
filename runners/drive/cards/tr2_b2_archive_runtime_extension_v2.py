"""Two-phase original B2 source route; prepared, not qualified.

DESIGN CHECK: LESSONS 2-5. Identical source, native proof and bounds under all
scientific directions. A replay pause never verifies. Missing pins, checkpoint
coverage, Job membership or exact native exits refuse. No estimator is selected.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import math
import os
import shutil
import stat
import sys
import time

REPO = next(p for p in Path(__file__).resolve().parents if (p/'runners/drive/native_job.py').is_file())
sys.path.insert(0, str(REPO))
from runners.drive.cards import batch_runtime_v8 as kernel
from runners.drive.cards import week6_policy_extension_v2 as policy
from runners.drive.cards import week6_runtime_extension_v2 as inherited
from runners.drive.cards import week5_at_queue_native_v2 as proof
from runners.drive.cards import week5_output_size_v2 as byte_guard
from runners.drive.cards.batch_runtime import (PYTHON, read, freeze, atomic, filehash,
    check_files, native_identity, release_slot, resource_snapshot, now)

CHILD = Path(__file__).with_name('tr2_b2_archive_child_v1.py')
SOURCE_DELIVERY_SHA = '0e8b83eb8e46cbd9ec5d216bc8d7ba8f9df3a5d9e390a4dc7aa9c07cd5848183'
SOURCE_HANDLER_SHA = '714fadf9ce7bd69559943ec32c5424e6cbd36ad65930731af5e0561427cb81b2'
SOURCE_CONTRACT_SHA = '29c25d1e0ee9aa0530b7fab1fd20aada36a2477a82e6990f04ad508afb86e185'
MAX_BYTES = 96 * 2**30
IGNORED_RUNTIME_FILES = {'.week3-admission.lock', '_RUNTIME_HEAD.json'}


def need(value, message):
    if not value:
        raise ValueError(message)


def below(root, relative):
    path = (Path(root)/relative).resolve()
    path.relative_to(Path(root).resolve())
    return path


def strict_files(root):
    root = Path(root)
    try:
        root_info=root.lstat()
    except FileNotFoundError:
        return
    byte_guard.reject_link(root_info)
    need(stat.S_ISDIR(root_info.st_mode), 'Workspace scan root is not a directory')
    pending = [root]
    while pending:
        directory = pending.pop()
        byte_guard.reject_link(directory.lstat())
        with os.scandir(directory) as entries:
            for entry in entries:
                path = Path(entry.path)
                try:
                    info = path.lstat()
                except FileNotFoundError:
                    # Only the original atomic JSON grammar and this exact source
                    # workspace's SQLite rollback journal may disappear mid-scan.
                    if byte_guard.ATOMIC_JSON.fullmatch(path.name):
                        continue
                    relative = path.relative_to(root).parts
                    if (len(relative) == 4 and relative[0] in ('producer','replay')
                            and relative[1] == 'partial' and len(relative[2]) == 32
                            and all(c in '0123456789abcdef' for c in relative[2])
                            and relative[3] == 'work.sqlite-journal'):
                        sibling = path.with_name('work.sqlite').lstat()
                        byte_guard.reject_link(sibling)
                        need(stat.S_ISREG(sibling.st_mode), 'Missing SQLite journal companion')
                        continue
                    raise
                byte_guard.reject_link(info)
                if stat.S_ISDIR(info.st_mode):
                    pending.append(path)
                elif stat.S_ISREG(info.st_mode):
                    yield path, info.st_size
                else:
                    raise ValueError('Nonregular workspace artifact')


def source_bytes(workspace):
    return sum(size for _, size in strict_files(workspace))


def retained_bytes(workspace, audit_root):
    # Workspace and attempt are disjoint; include logs and control snapshots,
    # not only the source handler's own files.
    need(not Path(workspace).resolve().is_relative_to(Path(audit_root).resolve()) and
         not Path(audit_root).resolve().is_relative_to(Path(workspace).resolve()),
         'Source and audit roots must be disjoint')
    return source_bytes(workspace)+byte_guard.output_bytes(audit_root)


def digest(path, guard=lambda: None):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(2**20), b''):
            guard()
            h.update(block)
    return h.hexdigest()


def workspace_manifest(workspace, guard=lambda: None):
    return {p.relative_to(workspace).as_posix(): dict(bytes=size, sha256=digest(p, guard))
            for p, size in strict_files(workspace)
            if p.relative_to(workspace).as_posix() not in IGNORED_RUNTIME_FILES}


def source_binding(plan):
    return {key: plan[key] for key in ('source_runtime', 'family', 'budget_key', 'inputs',
                                      'source_delivery', 'source_handler', 'workspace', 'source_config')}


def validate_plan(root, plan):
    root.resolve().relative_to(policy.ROOT.resolve())
    need(root.parent.resolve() == policy.ROOT.resolve(), 'Top-level counted attempt required')
    need(plan.get('source_runtime') == 'tr2-b2-archive-runtime-v1' and
         plan.get('campaign') == 'S15-WEEK6' and plan.get('family') == 'MD' and
         plan.get('budget_key') == 'TR2' and plan.get('fixture_only') is not True,
         'Original TR2 source-only campaign boundary')
    policy.runtime_contract(plan)
    for key in ('max_cpu_seconds','max_wall_seconds'):
        need(0 < policy.finite(plan[key]) <= 1800, 'At most thirty-minute counted quantum')
    need(plan['numerical_threads'] == 2 and plan['projected_peak_ram_GiB'] == 2,
         'Frozen source resource envelope changed')
    need(plan['max_output_bytes'] == MAX_BYTES, 'Frozen source output cap changed')
    workspace = Path(plan['workspace']).resolve()
    need(workspace == (policy.ROOT/'_source-work/TR2-B2-archive-v1').resolve(),
         'Different shared source workspace')
    expected = dict(buckets=32, chunk_rows=100000, first_cost_prefix=True,
                    slice_cpu_seconds=900, slice_wall_seconds=1500, max_output_bytes=MAX_BYTES)
    need(plan['source_config'] == expected, 'Original extraction or quantum configuration changed')
    need(plan['source_delivery']['sha256'] == SOURCE_DELIVERY_SHA and
         plan['source_handler']['sha256'] == SOURCE_HANDLER_SHA and
         plan['inputs']['source_contract']['sha256'] == SOURCE_CONTRACT_SHA,
         'Frozen source delivery changed')
    for item in (plan['source_delivery'], plan['source_handler'], plan['inputs']['source_contract']):
        need(filehash(item['path']) == item['sha256'], 'Changed source delivery/input file')
        need(plan['pins'].get(str(Path(item['path']).resolve())) == item['sha256'], 'Unpinned source input')
    for path in (Path(__file__).resolve(), CHILD.resolve()):
        need(plan['pins'].get(str(path)) == filehash(path), 'Unpinned runtime component')
    delivery_root=Path(plan['source_delivery']['path']).resolve().parent
    delivery=read(plan['source_delivery']['path'])
    for name,item in delivery['files'].items():
        need(filehash(below(delivery_root,name))==item['sha256'], 'Frozen source package changed')
    inherited_pins=read(delivery_root/'PREPARED.json')['source_pins']
    for name,pin in inherited_pins.items():
        need(plan['pins'].get(str((REPO/name).resolve()))==pin, 'Frozen source closure pin omitted')
    check_files(plan['pins'])
    return workspace


def phase_action(phase, result):
    need(phase in ('execute','verify'), 'Unknown source phase')
    if result.get('status') == 'yielded':
        need(result.get('verified') is not True, 'Yielded phase claims verification')
        return 'PAUSED'
    need(result.get('status') == 'complete' and result.get('scientific_admission') is False,
         'Source phase did not complete safely')
    if phase == 'execute':
        need(result.get('verified') is not True, 'Producer cannot independently verify')
        return 'VERIFY'
    need(result.get('verified') is True and result.get('independent_complete_archive_replay') is True
         and result.get('original_census_reconciled') is True, 'Complete independent source replay required')
    return 'COMPLETE'


def proof_manifest(phase_root, phase):
    proof.require_phase_proof(phase_root, phase.upper())
    environment=read(phase_root/(phase.upper()+'_ENVIRONMENT.json'))
    need(environment['threads']==2 and environment['cuda_visible']=='' and
         all(p['num_threads']<=2 for p in environment['pools']), 'Actual numerical environment changed')
    names = [p for p in phase_root.iterdir() if p.is_file()]
    return {p.name: filehash(p) for p in names}


def verify_completed_phases(completed, plan=None):
    for operation, item in completed.items():
        need(operation in ('execute','verify'), 'Unknown completed phase')
        root = Path(item['root'])
        if plan is not None:
            request=read(root/'PLAN.json')
            need(request.get('fixture_only') is False and request['handler']==plan['source_handler']
                 and request['inputs']==plan['inputs'] and request['workspace']==plan['workspace'],
                 'Completed phase has different source scope')
            need(request['owner_plan_sha256']==filehash(root.parents[1]/'PLAN.json'),
                 'Completed phase owner plan differs')
            for name in ('buckets','chunk_rows','first_cost_prefix','max_output_bytes'):
                need(request['config'][name]==plan['source_config'][name], 'Completed phase changed source configuration')
        need({p.name:filehash(p) for p in root.iterdir() if p.is_file()} == item['files'],
             'Prior completed phase evidence changed')
        proof.require_phase_proof(root, operation.upper())
        environment=read(root/(operation.upper()+'_ENVIRONMENT.json'))
        need(environment['threads']==2 and environment['cuda_visible']=='' and
             all(p['num_threads']<=2 for p in environment['pools']), 'Prior numerical environment changed')
        result = read(root/('RESULT.json' if operation=='execute' else 'VERIFIED.json'))
        need(phase_action(operation,result) == ('VERIFY' if operation=='execute' else 'COMPLETE'),
             'Prior phase was not complete')


def resume_state(root, workspace, plan, guard=lambda: None):
    spec = plan.get('resume')
    if spec is None:
        need(not (workspace/'_RUNTIME_HEAD.json').exists(), 'Existing source head requires exact continuation')
        need(not workspace_manifest(workspace,guard), 'Initial workspace is not empty')
        return 'execute', {}
    prior = Path(spec['root']).resolve()
    need(prior != root.resolve() and prior.parent == root.parent.resolve(), 'Invalid prior attempt path')
    for name,key in [('PLAN.json','plan_sha256'),('PAUSED.json','paused_sha256')]:
        need(filehash(prior/name)==spec[key], 'Changed predecessor receipt')
    need(not any((prior/name).exists() for name in ('COMPLETE.json','FAILED.json')), 'Ambiguous predecessor terminal')
    old,paused,owner = read(prior/'PLAN.json'),read(prior/'PAUSED.json'),read(prior/'OWNER.json')
    need(owner['plan_sha256']==spec['plan_sha256'] and native_identity(owner['native']['pid']) != owner['native'],
         'Prior exact owner exit is not proved')
    need(source_binding(old)==source_binding(plan), 'Changed source resume semantics')
    need(all(plan['pins'].get(p)==h for p,h in old['pins'].items()), 'Prior code/source pins dropped')
    check_files(old['pins'])
    need(paused['status']=='PAUSED' and paused['verified'] is False and paused['checkpoint_validation_required'] is True,
         'Not an authenticated source pause')
    need(read(workspace/'_RUNTIME_HEAD.json') == dict(root=str(prior),terminal='PAUSED',sha256=spec['paused_sha256']),
         'Source head differs from supplied predecessor')
    need(workspace_manifest(workspace,guard)==paused['checkpoint_outputs'], 'Shared checkpoint changed or incomplete')
    need(workspace_manifest(prior/'control-snapshot',guard)==paused['control_snapshot_outputs'],
         'Historical control snapshot changed or incomplete')
    expected_controls={name:item for name,item in paused['checkpoint_outputs'].items()
                       if name.endswith('.json') and not name.endswith('/RECEIPT.json')}
    need(paused['control_snapshot_outputs']==expected_controls, 'Historical control snapshot coverage differs')
    completed=paused['completed_phases']
    verify_completed_phases(completed,plan)
    need(paused['next_phase'] in ('execute','verify') and
         (paused['next_phase']=='execute' or 'execute' in completed), 'Replay lacks completed producer')
    if paused.get('paused_phase_root') is not None:
        phase_root=Path(paused['paused_phase_root']).resolve()
        need(phase_root == prior/'phases'/paused['next_phase'], 'Paused phase path differs')
        need({p.name:filehash(p) for p in phase_root.iterdir() if p.is_file()} == paused['paused_phase_files'],
             'Paused native evidence changed')
        proof.require_phase_proof(phase_root,paused['next_phase'].upper(),allow_forced=True)
    # Preserve each old request exactly; never clear a cancellation request.
    for name in ('YIELD_REQUEST','YIELD_REQUEST.json'):
        path=workspace/name
        if path.exists():
            dest=workspace/'retired-requests'/root.name/name
            dest.parent.mkdir(parents=True,exist_ok=True)
            need(not dest.exists(), 'Request-history collision')
            path.rename(dest)
    return paused['next_phase'],completed


def seal_checkpoint(root, workspace, guard=lambda: None):
    manifest=workspace_manifest(workspace,guard)
    for name,item in manifest.items():
        if name.endswith('.json') and not name.endswith('/RECEIPT.json'):
            source=below(workspace,name);target=below(root/'control-snapshot',name)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,target)
            need(digest(target,guard)==item['sha256'], 'Control snapshot copy changed')
    return manifest


def native_phase(root, operation, workspace, deadline, cpu_left, output_cap, inspect=lambda cpu: None, audit_root=None):
    phase=operation.upper();observed={};actual=None;reason=None;forced=False;error=None
    requested=None;next_size=0;launch=None;code=None
    command=[str(PYTHON),'-X','utf8','-B',str(CHILD),operation,str(root)]
    audit_root=root if audit_root is None else audit_root
    def remember(snapshot):
        for identity in snapshot['identities']:
            observed[(identity['pid'],identity['created_ticks'])]=identity
    with kernel.measured_child(root,operation,command) as worker:
        launch=native_identity(worker.pid)
        need(launch is not None,'Missing launch identity')
        observed[(launch['pid'],launch['created_ticks'])]=launch
        freeze(root/(phase+'_OWNED.json'),dict(native=launch,role='launch_redirector'))
        try:
            freeze(root/(phase+'_LAUNCH_MEMBER.json'),proof.prove_member(worker,launch))
            while True:
                snapshot=proof.sample_job(worker);remember(snapshot)
                ready_path=root/(phase+'_READY.json')
                if actual is None and ready_path.is_file():
                    ready=read(ready_path)
                    need(ready['phase']==operation and ready['plan_sha256']==filehash(root/'PLAN.json'),
                         'Native ready phase/plan differs')
                    actual=ready['native'];member=proof.prove_member(worker,actual)
                    observed[(actual['pid'],actual['created_ticks'])]=actual
                    freeze(root/(phase+'_MEMBER.json'),dict(member,launch_native=launch,ready_sha256=filehash(ready_path)))
                code=worker.poll()
                if code is not None and proof.empty(snapshot):
                    break
                moment=time.monotonic()
                external=inspect(snapshot['cpu_seconds'])
                if requested is None:
                    if external: reason=external
                    elif moment>=deadline-60: reason='wall_quantum'
                    elif snapshot['cpu_seconds']>=cpu_left-10: reason='inclusive_CPU_quantum'
                    elif moment>=next_size:
                        next_size=moment+10
                        if retained_bytes(workspace,audit_root)>output_cap: reason='source_output_cap'
                    if reason:
                        requested=moment
                        if not (workspace/'YIELD_REQUEST.json').exists():
                            freeze(workspace/'YIELD_REQUEST.json',dict(at=now(),reason=reason))
                if moment>=deadline or snapshot['cpu_seconds']>=cpu_left-2 or (requested and moment-requested>=60):
                    forced=True;break
                time.sleep(.05)
        except BaseException as exc:
            error=exc;forced=True
        finally:
            snapshot=proof.sample_job(worker);remember(snapshot)
            if forced or not proof.empty(snapshot):
                forced=True
                freeze(root/(phase+'_FORCED_STOP.json'),dict(native=actual,launch_native=launch,
                    reason=reason or repr(error),observed_identities=list(observed.values())))
                snapshot=proof.terminate_and_drain(worker,remember)
            need(proof.empty(snapshot),'Owned Job emptiness unproved')
            freeze(root/(phase+'_JOB_EMPTY.json'),snapshot)
            code=worker.poll();need(code is not None,'Unknown launch exit')
            freeze(root/(phase+'_EXIT.json'),dict(native=actual,launch_native=launch,exit_code=code))
    checks=proof.exited_identities(list(observed.values()))
    freeze(root/(phase+'_CLOSED.json'),dict(native=actual,launch_native=launch,identity_checks=checks,
        known_not_same_live=True,native_inspection_completed=True,job_empty_before_close=True,job_closed=True,forced=forced))
    if error is not None: raise error
    need(actual is not None,'Actual child was never authenticated')
    proof.require_phase_proof(root,phase,actual,allow_forced=forced)
    need(retained_bytes(workspace,audit_root)<=output_cap,'Final source output exceeds cap')
    used=read(root/(phase+'_JOB_USAGE.json'))['cpu_seconds']
    need(used<=cpu_left,'Final native phase exceeds CPU allowance')
    if forced:
        return dict(status='yielded',verified=False,reason=reason,forced=True),used
    need(code==0,'Native phase exited unsuccessfully')
    result=read(root/('RESULT.json' if operation=='execute' else 'VERIFIED.json'))
    phase_action(operation,result)
    return result,used


def run(root):
    root=Path(root).resolve();started=time.monotonic();plan=read(root/'PLAN.json')
    workspace=validate_plan(root,plan)
    os.environ['CUDA_VISIBLE_DEVICES']=''
    for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        os.environ[name]='2'
    freeze(root/'ATTEMPT.claim',dict(at=now()))
    freeze(root/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(root/'PLAN.json')))
    lease=None;charged=0.0;operations=[];cap=plan['max_cpu_seconds'];error=None
    def used():return charged+time.process_time()
    deadline=started+min(plan['max_wall_seconds'],(policy.DRAIN-datetime.now(timezone.utc)).total_seconds())
    def guard():
        need(time.monotonic()<deadline and used()+2<cap,'Closing CPU/wall bound exhausted')
    terminal=None
    try:
        with kernel.admission_lock(workspace):
            lease,resources=inherited.claim(root,plan)
            cap=min(cap,resources['remaining_cpu_seconds'])
            freeze(root/'ADMISSION.json',dict(resources,lease=str(lease[0]),source_only=True))
            phase,completed=resume_state(root,workspace,plan,guard)
            while True:
                guard()
                check_files(plan['pins'])
                if time.monotonic()>=deadline-180 or cap-used()<90:
                    terminal=dict(status='PAUSED',verified=False,next_phase=phase,reason='closing_quantum_before_phase',
                        checkpoint_validation_required=True,completed_phases=completed,
                        paused_phase_root=None,paused_phase_files=None)
                    break
                left=min(cap-used()-30,policy.available(plan,exclude=root)-used()-30)
                need(left>30,'Original inclusive TR2/MD room exhausted')
                phase_root=root/'phases'/phase;phase_root.mkdir(parents=True)
                config=dict(plan['source_config'],owner_remaining_card_cpu_seconds=left,
                    slice_cpu_seconds=min(900,left-30),slice_wall_seconds=min(1500,max(1,deadline-time.monotonic()-120)))
                request=dict(phase=phase,owner_plan_sha256=filehash(root/'PLAN.json'),pins=plan['pins'],
                    handler=plan['source_handler'],inputs=plan['inputs'],config=config,workspace=str(workspace),fixture_only=False)
                freeze(phase_root/'PLAN.json',request)
                operations.append((phase_root,phase))
                next_budget=0.0;next_resources=0.0
                def inspect(cpu):
                    nonlocal next_budget,next_resources
                    moment=time.monotonic()
                    if moment>=next_budget:
                        next_budget=moment+2
                        atomic(root/'BUDGET_PROGRESS.json',dict(at=now(),cpu_seconds=used()+cpu))
                        need(used()+cpu+30<policy.available(plan,exclude=root),'Inclusive family/card budget boundary')
                    if datetime.now(timezone.utc)>=policy.DRAIN:return 'week6_drain'
                    if (workspace/'CANCEL_REQUEST.json').exists():return 'owner_cancel'
                    if moment>=next_resources:
                        next_resources=moment+10
                        snapshot=resource_snapshot()
                        atomic(root/'PROGRESS.json',dict(at=now(),phase=phase,cpu_seconds=used()+cpu,resources=snapshot))
                        if any(snapshot[k]<v for k,v in [('ram_available_GiB',4),('commit_headroom_GiB',6),('disk_free_GiB',20)]):
                            return 'resource_floor'
                    return None
                result,cpu=native_phase(phase_root,phase,workspace,min(deadline-60,time.monotonic()+1560),left,MAX_BYTES,inspect,root)
                charged+=cpu
                action=phase_action(phase,result)
                if action=='PAUSED':
                    terminal=dict(status='PAUSED',verified=False,next_phase=phase,reason=result,
                        checkpoint_validation_required=True,completed_phases=completed,
                        paused_phase_root=str(phase_root),paused_phase_files={p.name:filehash(p) for p in phase_root.iterdir() if p.is_file()})
                    break
                completed[phase]=dict(root=str(phase_root),files=proof_manifest(phase_root,phase))
                if action=='COMPLETE':
                    need('execute' in completed,'Complete replay lacks separate producer proof')
                    verify_completed_phases(completed,plan)
                    execute_native=read(Path(completed['execute']['root'])/'EXECUTE_NATIVE.json')['native']
                    verify_native=read(phase_root/'VERIFY_NATIVE.json')['native']
                    need(execute_native!=verify_native,'Source and replay must use different native identities')
                    terminal=dict(status='COMPLETE',verified=True,independent_complete_archive_replay=True,
                        fresh_process_verified=True,completed_phases=completed)
                    break
                phase='verify'
                if time.monotonic()>=deadline-180 or cap-used()<90:
                    terminal=dict(status='PAUSED',verified=False,next_phase='verify',reason='remaining_quantum',
                        checkpoint_validation_required=True,completed_phases=completed,
                        paused_phase_root=None,paused_phase_files=None)
                    break
            manifest=seal_checkpoint(root,workspace,guard)
            controls=workspace_manifest(root/'control-snapshot',guard)
            need(retained_bytes(workspace,root)<=MAX_BYTES,'Final workspace and audit output cap')
            check_files(plan['pins']);guard()
            need(used()+30<policy.available(plan,exclude=root),'Final inclusive TR2/MD/campaign cap')
            snapshot=resource_snapshot()
            floors_met=all(snapshot[k]>=v for k,v in [('ram_available_GiB',4),('commit_headroom_GiB',6),('disk_free_GiB',20)])
            if terminal['status']=='COMPLETE':need(floors_met,'Final runtime resource floor')
            # Release under the same mutex as claim before publishing terminal success.
            with kernel.admission_lock(policy.OLD_SLOTS):release_slot(*lease)
            lease=None
            terminal.update(at=now(),card=plan['card'],source_only=True,scientific_admission=False,
                cpu_seconds=used(),native_descendant_CPU_seconds=charged,supervisor_CPU_seconds=time.process_time(),
                CPU_accounting='all descendants plus full supervisor process once; inherited policy retains coordination envelope',
                wall_seconds=time.monotonic()-started,checkpoint_outputs=manifest,workspace=str(workspace),
                control_snapshot_outputs=controls,
                final_resources=snapshot,final_resource_floors_met=floors_met,
                owned_lease_released=True,write_through_required=True)
            path=root/(terminal['status']+'.json');freeze(path,terminal)
            atomic(workspace/'_RUNTIME_HEAD.json',dict(root=str(root),terminal=terminal['status'],sha256=filehash(path)))
    except BaseException as exc:
        error=repr(exc)
        try:
            measured=0.0
            for p,op in operations:
                prefix=op.upper()
                closure=read(p/(prefix+'_CLOSED.json'))
                need(closure['job_closed'] is True and closure['job_empty_before_close'] is True
                     and all(c['exited'] is True and c['query_completed'] is True for c in closure['identity_checks']),
                     'Unclosed native Job requires full-cap accounting reconciliation')
                need(proof.empty(read(p/(prefix+'_JOB_EMPTY.json'))),'Unknown final native Job population')
                measured+=policy.finite(read(p/(prefix+'_JOB_USAGE.json'))['cpu_seconds'])
            charged=max(charged,measured);unknown=False
        except BaseException:
            charged=max(charged,cap);unknown=True
        if not any((root/name).exists() for name in ('COMPLETE.json','PAUSED.json','FAILED.json')):
            freeze(root/'FAILED.json',dict(at=now(),status='FAILED',card=plan['card'],error=error,
                cpu_seconds=charged+time.process_time(),accounting_reconciliation_required=unknown,
                scientific_admission=False,verified=False,source_only=True,workspace=str(workspace)))
        raise
    finally:
        if lease:
            with kernel.admission_lock(policy.OLD_SLOTS):release_slot(*lease)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path)
    run(parser.parse_args().root)
