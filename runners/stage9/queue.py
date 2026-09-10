"""Finite manually enumerated queue with one OS-held writer and source-bound commits.

DESIGN CHECK: X12/B01; LESSONS 3--5, CONTROLS 6--7.
A produce alone, stale PID, missing execution receipt or changed
input cannot complete a job. Failed attempts and occupied GPU wall time stay visible.
Only prelaunch fixtures may be resumed after a deliberately interrupted child. A
scientific queue requires a separately verified launch certificate tied to its plan.
No job is automatically invented, repaired, expanded, or substituted by this module.
NULL: absent or paused GPU allocation cannot spawn a GPU job or close its consumers.
ALTERNATIVE: independent CPU work completes while GPU work remains pending; an
explicit later allocation permits the same untouched pending jobs. Exhaustive states
are terminal, running, resource-paused or awaiting the coding operator's B01 review,
with no false scientific disposition. Missing manual review never starts B01 or
turns a completed discovery into a failed study; it is not a request for new authority.
"""
import argparse
from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

from runners.stage9.common import REPO, ROOT, closure, digest, file_hash, freeze, read, write
from runners.stage9.process_identity import native_identity, is_same_live_process

TERMINAL = {'COMPLETE', 'NOT_RUN', 'FAILED'}
RESOURCE_PAUSED = 75
DISPOSITIONS = {'IMPLEMENTATION INVALID': 'INVALID', 'INCONCLUSIVE': 'INCONCLUSIVE',
                'PRACTICALLY SMALL': 'SMALL', 'COUNTEREVIDENCE': 'COUNTEREVIDENCE',
                'SUPPORT CANDIDATE': 'CANDIDATE', 'CONFIRMED WITHIN SCOPE': 'CONFIRMED',
                'DESCRIPTIVE': 'DESCRIPTIVE', 'NOT RUN WITH REASON': 'NOT_RUN'}


@contextmanager
def writer(directory):
    import msvcrt
    directory.mkdir(parents=True, exist_ok=True)
    with (directory/'WRITER.lock').open('a+b') as handle:
        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            raise RuntimeError('another writer owns this queue; status was not changed') from exc
        try:
            yield
        finally:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def inside(path, root=ROOT):
    path, root = Path(path).resolve(), Path(root).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError('queue output must stay under its declared Stage 9 root')
    return path


def verify_sources(sources):
    paths = [REPO/path for path in sources['files']]
    if closure(paths) != sources:
        raise ValueError('reviewed source closure changed')


def manual_review_path(job):
    """B01 selection and B04 synthesis wait for their declared operator review."""
    if job['module'] not in ('runners.stage9.confirmation_freeze', 'runners.stage9.final_packet'):
        return None
    args = job['arguments']
    if (job['role'] != 'closure' or job['resource'] != 'cpu'
            or job.get('allow_failed_dependencies') is not True or job.get('requires')):
        raise ValueError('manual review must inspect completed and failed upstream work as CPU closure')
    if args.count('--review') != 1:
        raise ValueError('manual closure needs one explicit review path')
    index = args.index('--review')
    if index + 1 == len(args) or args[index + 1].startswith('--'):
        raise ValueError('manual closure review path is absent')
    return inside(REPO / args[index + 1])


def current_allocation():
    """Current owner instruction is separate from the immutable campaign clock.

    The operator writes ALLOCATION.json only from actual owner authorization.
    Re-read before each spawn; old campaign Gear 2 metadata grants nothing now.
    Missing allocation defaults to Gear 1 with GPU work held.
    """
    path = ROOT/'ALLOCATION.json'
    if not path.exists():
        return {'version':1,'gear':1,'gpu_available':False,
                'basis':'default Gear 1; no current GPU allocation recorded',
                'recorded_at':None,'sha256':None}
    value = read(path)
    fields = {'version','gear','gpu_available','basis','recorded_at'}
    if (not isinstance(value,dict) or set(value)!=fields
            or type(value['version']) is not int or value['version']!=1
            or type(value['gear']) is not int or value['gear'] not in (1,2)
            or type(value['gpu_available']) is not bool
            or value['gear']==1 and value['gpu_available']
            or any(not isinstance(value[k],str) or not value[k].strip()
                   for k in ('basis','recorded_at'))):
        raise ValueError('current owner allocation must explicitly preserve gear and GPU availability')
    return {**value,'sha256':file_hash(path)}


def validate_manifest(plan):
    if plan['kind'] not in ('prelaunch_rehearsal', 'science') or not plan['jobs']:
        raise ValueError('nonempty declared queue kind required')
    if not isinstance(plan['horizon_epoch'], (int,float)) or not math.isfinite(plan['horizon_epoch']):
        raise ValueError('finite campaign horizon required')
    ids, produces = set(), set()
    for job in plan['jobs']:
        if not job['id'] or job['id'] in ids or job['produces'] in produces:
            raise ValueError('duplicate job identity or produce')
        if not set(job['after']) <= ids:
            raise ValueError('jobs must be manually ordered after all prerequisites')
        if job['resource'] not in ('cpu','gpu') or job['role'] not in ('work','expansion','closure'):
            raise ValueError('explicit resource and role required')
        if 'allow_failed_dependencies' in job and type(job['allow_failed_dependencies']) is not bool:
            raise ValueError('failed-dependency permission must be an explicit boolean')
        if job.get('allow_failed_dependencies') and job['role'] != 'closure':
            raise ValueError('only closure may inspect failed dependencies without executing their science')
        review = manual_review_path(job)
        if review is not None and not {j['id'] for j in plan['jobs'] if j['role'] != 'closure'} <= set(job['after']):
            raise ValueError('manual closure must wait for every scientific and repair job')
        if job['module'] == 'runners.stage9.final_packet':
            from .packet_review import policy
            policy(plan)
            if job is not plan['jobs'][-1] or set(job['after']) != ids:
                raise ValueError('final packet must be last and wait for every preceding job')
        if not isinstance(job['estimated_gpu_seconds'], (int,float)) or job['estimated_gpu_seconds'] < 0 or not math.isfinite(job['estimated_gpu_seconds']):
            raise ValueError('finite nonnegative measured forecast required')
        if not job['module'].startswith('runners.stage9.') or not all(isinstance(x,str) for x in job['arguments']):
            raise ValueError('reviewed local module and literal argv required')
        source = job['module'].replace('.','/')+'.py'
        if source not in plan['sources']['files']:
            raise ValueError('job module missing from reviewed closure')
        inside(REPO/job['produces'])
        for condition in job.get('requires',[]):
            if (not isinstance(condition['field'],list) or not condition['field']
                or any(not isinstance(field,str) or not field for field in condition['field'])):
                raise ValueError('gate field path must be a nonempty list of field names')
            if condition['job'] not in job['after'] or not condition['field']:
                raise ValueError('gate condition must name a prior declared dependency and field')
        ids.add(job['id']); produces.add(job['produces'])
    if sum(j['estimated_gpu_seconds'] for j in plan['jobs']) > 92*3600:
        raise ValueError('planned work exceeds the authorized GPU envelope')
    if plan['kind'] == 'science' and any(j.get('interruption_rehearsal') for j in plan['jobs']):
        raise ValueError('rehearsal restart permission cannot enter scientific jobs')
    return True


def conditions(job, states, jobs):
    if not job.get('allow_failed_dependencies',False):
        for key in job.get('after',[]):
            if states[key]['status'] in ('FAILED','NOT_RUN'):
                return 'prerequisite did not complete: '+key
    for condition in job.get('requires', []):
        key = condition['job']
        if states[key]['status'] != 'COMPLETE':
            return 'required dependency did not complete: '+key
        value = read(REPO/jobs[key]['produces'])
        for field in condition['field']:
            if not isinstance(value, dict) or field not in value:
                return 'required gate field absent: '+key
            value = value[field]
        if type(value) is not type(condition['equals']) or value != condition['equals']:
            return 'operation-specific prerequisite did not pass: '+key
    return None


def admission_reason(job, states, jobs, horizon_epoch, now):
    reason = conditions(job, states, jobs)
    if now >= horizon_epoch and job['role'] == 'expansion':
        return 'campaign horizon reached; no new expansion admitted'
    return reason


def disposition(output, job, plan, manifest_hash, current):
    """Retain a separate scheduler disposition even if an invalid produce exists."""
    record = {'cell_identity':digest({'manifest_sha256':manifest_hash,'job':job}),
              'status':current['status'],'reason':current.get('reason'),
              'disposition':'NOT RUN WITH REASON' if current['status']=='NOT_RUN' else 'IMPLEMENTATION INVALID',
              'scientific_claim':'none from queue mechanics'}
    path=output/'dispositions'/(job['id']+'.json')
    freeze(path,record)
    current['disposition_path']=path.relative_to(output).as_posix()
    current['disposition_sha256']=file_hash(path)
    if current['status']=='NOT_RUN':
        freeze(REPO/job['produces'],record)
        current['produce_sha256']=file_hash(REPO/job['produces'])


def verify_disposition(output, job, current):
    path=inside(output/current['disposition_path'],output)
    if file_hash(path)!=current['disposition_sha256'] or read(path)['status']!=current['status']:
        raise ValueError('terminal queue disposition changed')
    if current['status']=='NOT_RUN' and file_hash(REPO/job['produces'])!=current['produce_sha256']:
        raise ValueError('not-run produce changed')


def gpu_observation():
    """A device-wide point sample, not measured utilization of this child alone."""
    at=time.time()
    try:
        result=subprocess.run(['nvidia-smi','--query-gpu=index,utilization.gpu,memory.used,power.draw',
                               '--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=3,
                              creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        if result.returncode:
            return {'at':at,'available':False,'reason':'nvidia-smi nonzero exit','returncode':result.returncode}
        devices=[]
        for line in result.stdout.splitlines():
            index,utilization,memory,power=[v.strip() for v in line.split(',')]
            devices.append({'index':int(index),'utilization_percent':float(utilization),
                            'memory_used_mib':float(memory),'power_watts':float(power)})
        if not devices:raise ValueError('empty device observation')
        return {'at':at,'available':True,'devices':devices,'scope':'device-wide point sample; other users not attributed'}
    except (OSError,ValueError,subprocess.TimeoutExpired) as exc:
        return {'at':at,'available':False,'reason':type(exc).__name__}


def verify_execution(path, cell_identity, plan, job):
    execution = read(path)
    if execution['returncode'] or execution['cell_identity'] != cell_identity or execution.get('error'):
        raise ValueError('worker execution did not close under the current identity')
    loaded = execution['loaded_project_sources']
    required = {'runners/stage9/source_bootstrap.py', 'runners/stage9/common.py',
                'runners/stage9/process_identity.py', job['module'].replace('.', '/')+'.py'}
    if not required <= loaded.keys() or any(plan['sources']['files'].get(k) != v for k, v in loaded.items()):
        raise ValueError('actual executed source closure is missing or mismatched')
    return execution


def verify_committed(output, job, plan, manifest_hash):
    committed = read(output/'commits'/(job['id']+'.json'))
    cell_identity = digest({'manifest_sha256': manifest_hash, 'job': job})
    if (committed['manifest_sha256'] != manifest_hash or committed['cell_identity'] != cell_identity
            or committed['produce_sha256'] != file_hash(REPO/job['produces'])):
        raise ValueError('completed produce identity changed')
    execution_path = inside(output/committed['execution_path'], output)
    if committed['execution_sha256'] != file_hash(execution_path):
        raise ValueError('completed execution receipt changed')
    verify_execution(execution_path, cell_identity, plan, job)


def recoverable_attempt(attempt, output):
    """Refuse both a live wrapper and a live interpreter, including startup gaps."""
    wrapper = attempt.get('wrapper_process')
    ready_path = output/attempt['directory']/'READY.json'
    if wrapper and is_same_live_process(wrapper):
        raise RuntimeError('previous owned wrapper is still live; inspect native identity before recovery')
    if ready_path.exists() and is_same_live_process(read(ready_path)['process']):
        raise RuntimeError('previous owned child is still live; inspect native identity before recovery')
    if not wrapper and not ready_path.exists():
        raise RuntimeError('unobserved spawn window requires native process reconciliation before recovery')


def run(manifest, output, resume_interrupted=False):
    manifest, output = Path(manifest).resolve(), inside(output)
    plan = read(manifest)
    validate_manifest(plan)
    verify_sources(plan['sources'])
    manifest_hash = digest(plan)
    if plan['kind'] == 'science':
        from runners.stage9.launch import verify_certificate
        certificate = read(manifest.parent/'LAUNCH_ACCEPTANCE.json')
        verify_certificate(plan,certificate)
    with writer(output):
        freeze(output/'MANIFEST.json', plan)
        status_path = output/'STATUS.json'
        old = read(status_path) if status_path.exists() else None
        if old and old['manifest_sha256'] != manifest_hash:
            raise ValueError('queue lineage changed')
        completed_path = output/'COMPLETE.json'
        if completed_path.exists():
            completed = read(completed_path)
            if (not old or completed['manifest_sha256'] != manifest_hash
                    or completed['jobs'] != old['jobs'] or completed['attempts'] != old['attempts']
                    or any(row['status'] not in TERMINAL for row in old['jobs'].values())):
                raise ValueError('queue completion differs from terminal durable status')
            for job in plan['jobs']:
                if old['jobs'][job['id']]['status'] == 'COMPLETE':
                    verify_committed(output, job, plan, manifest_hash)
                else:
                    verify_disposition(output,job,old['jobs'][job['id']])
            return 0  # No new owner, timestamp, status write, or completion digest.
        if old:
            for attempt in old.get('attempts', []):
                if attempt.get('ended_at') is not None:
                    continue
                recoverable_attempt(attempt, output)
                last = attempt.get('last_heartbeat', attempt['started_at'])
                attempt['ended_at'] = time.time()
                attempt['recovered_after_owner_loss'] = True
                attempt['occupied_wall_seconds_lower_bound'] = max(0., last-attempt['started_at'])
                attempt['unobserved_wall_seconds_upper_bound'] = max(0., attempt['ended_at']-last)
                old['jobs'][attempt['job']]['status'] = 'INTERRUPTED'
        state = old or {'manifest_sha256': manifest_hash, 'jobs': {j['id']:{'status':'PENDING'} for j in plan['jobs']},
                        'attempts': [], 'campaign_start': plan['campaign_start'], 'horizon_epoch': plan['horizon_epoch']}
        state['owner'] = native_identity()
        state['phase'] = 'running'
        state.pop('pause',None)
        write(status_path, state)
        jobs = {j['id']:j for j in plan['jobs']}
        waiting = {}
        for job in plan['jobs']:
            key = job['id']; current = state['jobs'][key]
            if current['status'] == 'COMPLETE':
                verify_committed(output, job, plan, manifest_hash)
                continue
            if current['status'] in ('NOT_RUN','FAILED'):
                verify_disposition(output,job,current)
                continue
            if current['status'] in ('INTERRUPTED','RUNNING'):
                if not (resume_interrupted and current['status'] == 'INTERRUPTED' and job.get('interruption_rehearsal') and plan['kind']=='prelaunch_rehearsal'):
                    raise RuntimeError('unfinished attempt requires an explicit scoped recovery or new repair lineage')
            if not all(state['jobs'][k]['status'] in TERMINAL for k in job['after']):
                waiting[key] = {'reason':'prerequisites remain pending',
                                'dependencies':[k for k in job['after'] if state['jobs'][k]['status'] not in TERMINAL]}
                continue
            reason = admission_reason(job, state['jobs'], jobs, plan['horizon_epoch'], time.time())
            if reason:
                current.update(status='NOT_RUN', reason=reason)
                disposition(output,job,plan,manifest_hash,current)
                write(status_path,state)
                continue
            review = manual_review_path(job)
            if review is not None and not review.is_file():
                if review.exists():
                    raise ValueError('manual review path exists but is not a regular file')
                waiting[key] = {'reason':'coding operator must complete the predeclared manual review',
                                'operator_review_pending':True,
                                'review_path':review.relative_to(REPO).as_posix()}
                continue
            allocation = current_allocation()
            state['allocation'] = allocation
            if job['resource']=='gpu' and not allocation['gpu_available']:
                waiting[key] = {'reason':'GPU work paused by current allocation','allocation':allocation}
                continue
            verify_sources(plan['sources'])
            cell_identity = digest({'manifest_sha256':manifest_hash,'job':job})
            number = sum(a['job']==key for a in state['attempts'])+1
            directory = Path('attempts')/(key+'-'+str(number))
            attempt_root = output/directory
            attempt_root.mkdir(parents=True,exist_ok=False)
            config = {'repo':str(REPO),'attempt':str(attempt_root),'sources':plan['sources'],
                      'cell_identity':cell_identity,'module':job['module'],'arguments':job['arguments']}
            write(attempt_root/'CONFIG.json',config)
            start = time.time()
            attempt = {'job':key,'directory':directory.as_posix(),'started_at':start,'ended_at':None,
                       'last_heartbeat':start,'resource':job['resource'],'cell_identity':cell_identity,
                       'allocation':allocation}
            state['attempts'].append(attempt);current.update(status='RUNNING',attempt=number)
            write(status_path,state)
            command = [sys.executable,'-B',str(REPO/'runners/stage9/source_bootstrap.py'),str(attempt_root/'CONFIG.json')]
            with (attempt_root/'stdout.log').open('wb') as stdout,(attempt_root/'stderr.log').open('wb') as stderr:
                child = subprocess.Popen(command,cwd=REPO,stdout=stdout,stderr=stderr,
                                         creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                attempt['wrapper_process'] = native_identity(child.pid)
                observations=[];next_observation=0.
                while child.poll() is None:
                    attempt['last_heartbeat'] = time.time()
                    if job['resource']=='gpu' and time.time()>=next_observation:
                        observations.append(gpu_observation())
                        write(attempt_root/'GPU_OBSERVATIONS.json',observations)
                        next_observation=time.time()+15
                    write(status_path,state)
                    time.sleep(.5)
            end = time.time()
            attempt.update(ended_at=end,returncode=child.returncode,occupied_wall_seconds=end-start)
            attempt['gpu_reserved_wall_seconds'] = end-start if job['resource']=='gpu' else 0.
            attempt['gpu_utilization_measured'] = any(r['available'] for r in observations)
            attempt['gpu_observation_count'] = len(observations)
            attempt['gpu_unobserved_intervals'] = 'all intervals between device-wide point samples; no integration or attribution claimed'
            if child.returncode:
                marker = attempt_root/'INTERRUPTION_AUTHORIZATION.json'
                ready_path = attempt_root/'READY.json'
                planned = (job.get('interruption_rehearsal') and marker.exists() and ready_path.exists()
                           and read(marker).get('process') == read(ready_path)['process']
                           and not (attempt_root/'EXECUTION.json').exists())
                current['status'] = 'INTERRUPTED' if planned else 'FAILED'
                current['reason'] = 'authorized interruption rehearsal' if planned else 'worker exited unsuccessfully; failed attempt retained'
                if not planned:
                    disposition(output,job,plan,manifest_hash,current)
                write(status_path,state)
                if planned:return child.returncode
                continue
            try:
                execution = verify_execution(attempt_root/'EXECUTION.json', cell_identity, plan, job)
                verify_sources(plan['sources'])
                produce = inside(REPO/job['produces'])
                result = read(produce)
                if result.get('cell_identity') != cell_identity:
                    raise ValueError('produce lacks the actual executed cell identity')
            except (OSError,ValueError,KeyError) as exc:
                current.update(status='FAILED',reason='completion verification failed: '+str(exc))
                disposition(output,job,plan,manifest_hash,current)
                write(status_path,state)
                continue
            freeze(output/'commits'/(key+'.json'),{'manifest_sha256':manifest_hash,'cell_identity':cell_identity,
                                                 'produce_sha256':file_hash(produce),'execution_sha256':file_hash(attempt_root/'EXECUTION.json'),
                                                 'execution_path':(directory/'EXECUTION.json').as_posix()})
            current['status']='COMPLETE';write(status_path,state)
        pending = {k:v for k,v in state['jobs'].items() if v['status'] not in TERMINAL}
        if pending:
            if set(pending)!=set(waiting):
                raise RuntimeError('unfinished queue lacks an explicit resource/dependency/review reason')
            review_pending = any(v.get('operator_review_pending') for v in waiting.values())
            pause = {'active':True,'observed_at':time.time(),'manifest_sha256':manifest_hash,
                     'pending':waiting,'campaign_start':plan['campaign_start'],
                     'horizon_epoch':plan['horizon_epoch'],
                     'scientific_claim':'none from operator-review waiting' if review_pending else 'none from a resource pause'}
            number = len(list((output/'pauses').glob('*.json')))+1
            freeze(output/'pauses'/f'{number:04d}.json',pause)
            state.update(phase='review_paused' if review_pending else 'resource_paused',pause=pause)
            write(status_path,state);write(output/'PAUSED.json',pause)
            return RESOURCE_PAUSED
        state['phase']='complete';write(status_path,state)
        if (output/'PAUSED.json').exists():
            write(output/'PAUSED.json',{'active':False,'cleared_at':time.time(),'manifest_sha256':manifest_hash,
                                       'reason':'all manually scheduled jobs are terminal; prior pauses retained'})
        write(output/'COMPLETE.json',{'manifest_sha256':manifest_hash,'completed_at':time.time(),'jobs':state['jobs'],
                                     'attempts':state['attempts'],'overrun_seconds':max(0,time.time()-plan['horizon_epoch']),
                                     'scientific_claim':'none from queue mechanics'})
    return 0


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('manifest',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--resume-interrupted',action='store_true')
    args=parser.parse_args()
    raise SystemExit(run(args.manifest,args.output,args.resume_interrupted))
