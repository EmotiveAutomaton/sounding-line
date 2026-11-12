"""N: one counted CH1 queue of separately replayed, immutable bounded units.

DESIGN CHECK: preserve every frozen roster row in ordinal order and the original
fixed-node scorer. A closed unit has separate native execute/replay identities,
all-descendant Job CPU and exact score equality. Queue final verification reads
the original roster and every sealed artifact; no unverified prefix is credited.
This adapter does not admit itself or launch another counted queue.
"""
from pathlib import Path
import gzip
import itertools
import json
import math
import os
import sys
import time

from . import week5_ch_engine as scorer
from . import week5_ch_engine_bounded as bounded
from . import week5_ch_pipeline_checkpoint as ck
from .week5_ch_source import digest, write_json

MAX_UNIT_POSITIONS = 64
UNIT_EXECUTE_WALL = 650
UNIT_VERIFY_WALL = 1000
QUEUE_WALL_LIMIT = 41400  # leave 30 minutes inside the 12-hour outer attempt
WORKER = 'runners.drive.cards.week5_ch_queue_worker_v1'


def read(path):
    with Path(path).open('rb') as stream:
        value=stream.read(16*1024**2+1)
    if len(value)>16*1024**2:
        raise ValueError('Queue metadata exceeds declared bound')
    return json.loads(value)


def spec(path):
    return dict(path=str(Path(path).resolve()),sha256=digest(path))


def identity(inputs,config):
    allowed={'offset','expected_positions','nodes','queue_wall_seconds','unit_positions','max_new_draws','constructed_fixture'}
    if set(inputs)!={'positions','engine'} or set(config)-allowed:
        raise ValueError('Unknown queue inputs or controls')
    total=config.get('expected_positions')
    offset=config.get('offset',0)
    maximum=config.get('unit_positions',MAX_UNIT_POSITIONS)
    wall=config.get('queue_wall_seconds',QUEUE_WALL_LIMIT)
    if any(type(x) is not int for x in (total,offset,maximum,wall)):
        raise ValueError('Queue bounds must be integers')
    if not 1<=total<=400000 or not 0<=offset<total or not 1<=maximum<=MAX_UNIT_POSITIONS or not 3600<=wall<=QUEUE_WALL_LIMIT:
        raise ValueError('Queue bounds exceed prospective contract')
    if type(config.get('nodes',1000000)) is not int or config.get('nodes',1000000) not in (300000,1000000,3000000):
        raise ValueError('Unregistered engine node count')
    from . import week5_ch_queue_worker_v1 as worker
    return ck.binding(inputs,config,dict(adapter=digest(__file__),worker=digest(worker.__file__),
        bounded_engine=digest(bounded.__file__),original_engine=digest(scorer.__file__)))


def write_positions(path,rows):
    with Path(path).open('xb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as stream:
        for row in rows:
            stream.write((json.dumps(row,sort_keys=True)+'\n').encode())


def worker_pins():
    from . import week5_ch_queue_worker_v1 as worker
    from . import week5_ch_source as source
    from . import batch_runtime_v8
    from runners.drive import native_job
    return {str(Path(module.__file__).resolve()):digest(module.__file__)
            for module in (worker,bounded,scorer,source,ck,batch_runtime_v8,native_job)}


def native_operation(unit,operation,queue):
    """One contained native child. Nested Job usage is diagnostic, not recharged."""
    from .batch_runtime import REPO,native_identity
    from .batch_runtime_v8 import measured_child,job_cpu
    unit,queue=Path(unit),Path(queue)
    invocation=unit/'native'/f'{operation}-{sum(1 for _ in (unit/"native").glob(operation+"-*"))+1:06}'
    invocation.mkdir(parents=True,exist_ok=False)
    command=[sys.executable,'-X','utf8','-B','-m',WORKER,str(unit.resolve()),operation,str(invocation.resolve()),str(queue.resolve())]
    limit=UNIT_EXECUTE_WALL if operation=='execute' else UNIT_VERIFY_WALL
    started=time.monotonic()
    requested_at=None
    timeout=False
    with measured_child(invocation,operation,command) as process:
        import psutil
        p=psutil.Process(process.pid)
        write_json(invocation/'CHILD.json',dict(pid=process.pid,created=p.create_time(),executable=p.exe(),parent=native_identity()))
        while process.poll() is None:
            elapsed=time.monotonic()-started
            timeout=timeout or elapsed>=limit
            if (ck.requested(queue) or timeout) and requested_at is None:
                requested_at=time.monotonic()
                write_json(invocation/'YIELD_REQUEST.json',dict(reason='Owner yield' if not timeout else 'Bounded queue unit wall ceiling'))
            if requested_at is not None and time.monotonic()-requested_at>55:
                raise TimeoutError('Native queue child exceeded cooperative grace; contained descendants closed')
            write_json(invocation/'JOB_PROGRESS.json',dict(cpu_seconds=job_cpu(process),elapsed_wall_seconds=elapsed),mutable=True)
            time.sleep(.5)
        if process.poll()!=0:
            raise RuntimeError('Native queue '+operation+' failed; retained exact logs and Job usage')
    result=read(invocation/'RESULT.json')
    usage=read(invocation/(operation.upper()+'_JOB_USAGE.json'))
    if usage['exit_code']!=0 or not usage['includes_all_descendants_and_exited_processes']:
        raise ValueError('Native descendant accounting is incomplete')
    if timeout:
        # A repeated timeout needs owner cost review, not an infinite automatic retry.
        raise TimeoutError('Unit exceeded the declared wall ceiling; bounded evidence retained')
    return result,invocation.relative_to(unit).as_posix()


def unit_files(unit):
    return sorted(path.relative_to(unit).as_posix() for path in Path(unit).rglob('*')
                  if path.is_file() and path.name!='UNIT_SEAL.json')


def close_unit(unit,execute_native,verify_native):
    unit=Path(unit)
    plan=read(unit/'UNIT.json')
    report=read(unit/'output/BATCH.json')
    proof=read(unit/'output/VERIFY.json')
    count=report['visited_positions']
    if not proof.get('all_scores_equal') or not proof.get('fresh_from_ordinal_zero') or proof['verified_positions']!=count or count<1:
        raise ValueError('Entire scored unit requires fresh engine replay')
    identities=[]
    total_cpu=0.
    for operation,rel in [('execute',execute_native),('verify',verify_native)]:
        native=unit/rel
        result=read(native/'RESULT.json')
        if (result.get('status')!='complete' if operation=='execute' else result.get('verified') is not True):
            raise ValueError('Closed unit child did not complete')
        identities.append(read(native/'NATIVE.json'))
        usage=read(native/(operation.upper()+'_JOB_USAGE.json'))
        if usage['exit_code']!=0 or not usage['includes_all_descendants_and_exited_processes']:
            raise ValueError('Missing native exit or Job cost')
    if identities[0]==identities[1]:
        raise ValueError('Replay must have a distinct fresh native identity')
    # Include interrupted invocations as well as the final successful two.
    for usage_path in (unit/'native').glob('*/*_JOB_USAGE.json'):
        total_cpu+=read(usage_path)['cpu_seconds']
    bindings={path.name:digest(path) for path in sorted((unit/'output/PRIVATE_SCORES').glob('*.json'))}
    if len(bindings)!=count:
        raise ValueError('Score count differs from fresh replay')
    write_json(unit/'SCORE_BINDINGS.json',bindings)
    result=dict(begin=plan['begin'],end=plan['begin']+count,positions=count,
        execute_native=execute_native,verify_native=verify_native,native_identities=identities,
        all_native_exited=True,nested_job_cpu_seconds=total_cpu,
        queue_job_already_includes_this_cpu=True,
        files={name:digest(unit/name) for name in unit_files(unit)})
    write_json(unit/'UNIT_SEAL.json',result)
    return result


def check_unit(unit,check=lambda:None,*,copied=None):
    unit=Path(unit)
    seal=read(unit/'UNIT_SEAL.json')
    if unit_files(unit)!=sorted(seal['files']):
        raise ValueError('Sealed unit has missing or extra files')
    for name,expected in seal['files'].items():
        check()
        if copied is None:
            actual=ck.file_digest(unit/name,check)
        else:
            # The counted resume copier independently hashes every destination.
            # This path is legal only for a previously authenticated verifier unit.
            actual=copied.get((unit/name).relative_to(copied['_root']).as_posix())
        if actual!=expected:
            raise ValueError('Sealed unit changed')
    plan=read(unit/'UNIT.json')
    report=read(unit/'output/BATCH.json')
    proof=read(unit/'output/VERIFY.json')
    if (report['visited_positions']!=seal['positions'] or report['next_offset']!=seal['positions'] or
        plan['begin']!=seal['begin'] or seal['end']!=seal['begin']+seal['positions'] or
        not proof.get('all_scores_equal') or not proof.get('fresh_from_ordinal_zero') or
        proof['verified_positions']!=seal['positions'] or not seal['all_native_exited']):
        raise ValueError('Closed unit coverage or replay changed')
    identities=[]
    for operation in ('execute','verify'):
        invocation=unit/seal[operation+'_native']
        identities.append(read(invocation/'NATIVE.json'))
        result=read(invocation/'RESULT.json')
        usage=read(invocation/(operation.upper()+'_JOB_USAGE.json'))
        if usage['exit_code']!=0 or not usage['includes_all_descendants_and_exited_processes']:
            raise ValueError('Closed native Job did not exit with complete accounting')
        if (result.get('status')!='complete' if operation=='execute' else result.get('verified') is not True):
            raise ValueError('Missing complete native operation')
    if identities[0]==identities[1] or identities!=seal['native_identities']:
        raise ValueError('Closed unit native identities differ')
    return seal


def state_load(output,bound,operation):
    output=Path(output)
    path=output/'QUEUE_STATE.json'
    if path.exists():
        if operation=='execute':
            ck.copied(path,output,lambda:ck.require(output))
        state=read(path)
        if state['binding']!=bound:
            raise ValueError('Queue continuation controls changed')
        return state
    if operation!='execute':
        raise ValueError('Completed queue state required')
    return dict(binding=bound,next_offset=bound['config'].get('offset',0),units=[],active=None)


def _execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    bound=identity(inputs,config)
    for value in inputs.values(): ck.checked(value,lambda:ck.require(output))
    state=state_load(output,bound,'execute')
    if (output/'QUEUE.json').exists():
        return dict(status='complete',sealed_queue_reused=True,population_complete=False)
    started=time.monotonic();completed_here=0
    total=config['expected_positions'];begin=config.get('offset',0)
    quantum=config.get('max_new_draws')
    maximum=config.get('unit_positions',MAX_UNIT_POSITIONS)
    positions=scorer.iter_positions(inputs['positions']['path'])
    for _ in range(state['next_offset']):
        ck.require(output)
        if next(positions,None) is None:raise ValueError('Queue offset outside roster')
    pending=[]
    while state['next_offset']<total:
        if ck.requested(output) or (quantum is not None and completed_here>=quantum):
            write_json(output/'QUEUE_STATE.json',state,mutable=True)
            return dict(status='yielded',reason='Owner request or closed-unit quantum',next_offset=state['next_offset'],population_complete=False)
        if time.monotonic()-started>=config.get('queue_wall_seconds',QUEUE_WALL_LIMIT)-1800:
            break
        wanted=min(maximum,total-state['next_offset'])
        pending.extend(itertools.islice(positions,wanted-len(pending)))
        if len(pending)!=wanted:raise ValueError('Frozen source roster is shorter than admitted denominator')
        if state['active'] is None:
            rel=f'units/unit-{state["next_offset"]:09}'
            unit=output/rel;unit.mkdir(parents=True,exist_ok=False)
            write_positions(unit/'PRIVATE_POSITIONS.jsonl.gz',pending)
            plan=dict(begin=state['next_offset'],source_roster=inputs['positions'],inputs=dict(
                positions=spec(unit/'PRIVATE_POSITIONS.jsonl.gz'),engine=inputs['engine']),
                config=dict(offset=0,max_positions=len(pending),nodes=config.get('nodes',1000000),
                    wall_seconds=600,constructed_fixture=bool(config.get('constructed_fixture'))),pins=worker_pins())
            write_json(unit/'UNIT.json',plan)
            state['active']=dict(path=rel,execute_native=None)
            write_json(output/'QUEUE_STATE.json',state,mutable=True)
        unit=output/state['active']['path']
        local=list(scorer.iter_positions(unit/'PRIVATE_POSITIONS.jsonl.gz'))
        if local!=pending:
            raise ValueError('Active unit differs from original source roster')
        if state['active']['execute_native'] is None:
            result,rel=native_operation(unit,'execute',output)
            if result.get('status')=='yielded':
                write_json(output/'QUEUE_STATE.json',state,mutable=True)
                return dict(status='yielded',reason='Native execute saved its bounded score prefix',next_offset=state['next_offset'])
            state['active']['execute_native']=rel
            write_json(output/'QUEUE_STATE.json',state,mutable=True)
        result,rel=native_operation(unit,'verify',output)
        if result.get('status')=='yielded':
            return dict(status='yielded',reason='Native replay stopped; this unclosed unit restarts replay from zero',next_offset=state['next_offset'])
        seal=close_unit(unit,state['active']['execute_native'],rel)
        state['units'].append(dict(path=state['active']['path'],seal_sha256=digest(unit/'UNIT_SEAL.json')))
        state.update(next_offset=seal['end'],active=None)
        pending=pending[seal['positions']:];completed_here+=seal['positions']
        write_json(output/'QUEUE_STATE.json',state,mutable=True)
        write_json(output/'PROGRESS.json',dict(next_offset=state['next_offset'],expected_positions=total,
            closed_units=len(state['units']),fresh_replayed_positions=state['next_offset']-begin,
            population_complete=False),mutable=True)
        if not (output/'PILOT.json').exists() and state['next_offset']-begin>=math.ceil((total-begin)*.05):
            write_json(output/'PILOT.json',dict(completed=state['next_offset']-begin,total=total-begin,
                basis='First closed execute/replay unit crossing five percent of the declared remaining position roster',
                cpu_fraction_claim=False,population_complete=False))
    if state['next_offset']==total and next(positions,None) is not None:
        raise ValueError('Frozen source roster exceeds admitted denominator')
    if state['active'] is not None or state['next_offset']==begin:
        raise ValueError('Queue cannot seal without a complete replayed unit')
    report=dict(begin=begin,end=state['next_offset'],expected_positions=total,
        positions=state['next_offset']-begin,units=state['units'],roster_sha256=inputs['positions']['sha256'],
        node_limit=config.get('nodes',1000000),whole_roster_covered=begin==0 and state['next_offset']==total,
        population_complete=False,constructed_fixture=bool(config.get('constructed_fixture')))
    write_json(output/'QUEUE.json',report)
    return dict(status='complete',**report)


def _verify(output,inputs,config):
    output=Path(output);bound=identity(inputs,config)
    for value in inputs.values():ck.checked(value,lambda:ck.require(output))
    state=state_load(output,bound,'verify');report=read(output/'QUEUE.json')
    if report['units']!=state['units'] or report['end']!=state['next_offset'] or report['begin']!=config.get('offset',0):
        raise ValueError('Queue report and checkpoint disagree')
    verified_path=output/'QUEUE_VERIFY_CHECKPOINT.json'
    copied=None
    if verified_path.exists():
        ck.copied(verified_path,output,lambda:ck.require(output))
        prior=read(verified_path)
        if prior['binding']!=bound or prior['queue_sha256']!=digest(output/'QUEUE.json'):
            raise ValueError('Verifier checkpoint belongs to another closed queue')
        copied=dict(read(output.parent/'RESUMED_FROM.json')['copied'],_root=output)
    else:prior=dict(binding=bound,queue_sha256=digest(output/'QUEUE.json'),verified_units=[])
    positions=scorer.iter_positions(inputs['positions']['path'])
    for _ in range(report['begin']):
        if next(positions,None) is None:raise ValueError('Queue begins outside roster')
    cursor=report['begin'];batches=[];newly_verified=0
    for index,item in enumerate(report['units']):
        ck.require(output)
        if config.get('max_new_draws') is not None and newly_verified>=config['max_new_draws']:
            raise ck.YieldRequested('Closed-unit final-verification quantum')
        unit=output/item['path']
        if digest(unit/'UNIT_SEAL.json')!=item['seal_sha256']:
            raise ValueError('Unit seal changed')
        was_verified=index<len(prior['verified_units'])
        if was_verified and prior['verified_units'][index]!=item:
            raise ValueError('Verifier checkpoint sequence changed')
        seal=check_unit(unit,lambda:ck.require(output),copied=copied if was_verified else None)
        plan=read(unit/'UNIT.json')
        if (seal['begin']!=cursor or plan['source_roster']!=inputs['positions'] or
            plan['inputs']['engine']!=inputs['engine'] or plan['config']['nodes']!=config.get('nodes',1000000)):
            raise ValueError('Gapped, overlapping or differently bound queue unit')
        local=itertools.islice(scorer.iter_positions(unit/'PRIVATE_POSITIONS.jsonl.gz'),seal['positions'])
        local_count=0
        for row in local:
            ck.require(output)
            if row!=next(positions,None):raise ValueError('Queue position differs from original full roster ordinal')
            local_count+=1
        if local_count!=seal['positions']:
            raise ValueError('Unit source slice shorter than replayed interval')
        cursor=seal['end']
        batches.append(dict(path=str(unit/'output/PRIVATE_SCORES'),verify=spec(unit/'output/VERIFY.json'),
            report=spec(unit/'output/BATCH.json'),score_bindings=spec(unit/'SCORE_BINDINGS.json'),
            queue_unit_seal=spec(unit/'UNIT_SEAL.json')))
        if not was_verified:
            prior['verified_units'].append(item)
            write_json(verified_path,prior,mutable=True)
            newly_verified+=seal['positions']
    if cursor!=report['end'] or (cursor==config['expected_positions'] and next(positions,None) is not None):
        raise ValueError('Queue coverage differs from source denominator')
    write_json(output/'QUEUE_BATCHES.json',dict(batches=batches,population_complete=False,
        begin=report['begin'],end=cursor,roster_sha256=inputs['positions']['sha256']))
    result=dict(verified=True,all_closed_native_replays_authenticated=True,
        every_score_covered=True,original_roster_ordinals_verified=True,
        complete_queue_interval=True,engine_replayed_in_separate_native_per_unit=True,
        no_second_whole_queue_engine_pass=True,positions=cursor-report['begin'],population_complete=False)
    write_json(output/'QUEUE_VERIFIED.json',result)
    return result


def execute(output,inputs,config):return ck.guarded(_execute,output,inputs,config)
def verify(output,inputs,config):return ck.guarded(_verify,output,inputs,config)
