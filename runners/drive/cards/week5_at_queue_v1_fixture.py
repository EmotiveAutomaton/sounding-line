"""UNRUN native constructed queue proof; no human data or pretrained weights.

DESIGN CHECK: LESSONS 3-5. Exercise the actual queue, generic child, original
FP64 scorer and nested native job containment. Both scientific directions have
identical integrity controls. Tamper refuses. Synthetic memory snapshots prove
control flow only, never the production reader's memory admission. This module
cannot be selected by a production queue input or manifest.
"""
from pathlib import Path
from types import FunctionType
import argparse
import copy
import shutil
import time

from . import week5_at_queue_v1 as q
from .batch_runtime import freeze, read, filehash
from .timing_p6 import gzip_equal

FIXTURE_MODULE = 'runners.drive.cards.week5_at_queue_v1_fixture'


def fixture_child(operation, root):
    from . import week5_child_v7 as child
    from . import week5_at_scoring_guard_v1 as guard
    from .week5_at_scoring_v4_fixture import loader
    plan = read(root/'PLAN.json')
    case = plan.get('fixture_native_case')
    if case:
        q.need(root.parent.name == 'constructed-native-cases' and case in {'fast-output-overflow','forced-deadline'},
               'Unknown native fixture case')
        (root/'output').mkdir(parents=True,exist_ok=True)
        if case == 'fast-output-overflow':
            (root/'output/oversized.bin').write_bytes(b'x'*(2**20))
            freeze(root/'RESULT.json',dict(status='complete',fixture_only=True))
        else:
            from runners.stage9.process_identity import native_identity
            freeze(root/'OWNED_IDENTITY.json',dict(native=native_identity()))
            time.sleep(10)
        return
    q.need(plan['module'] == q.SCORER and plan.get('counted_parent_only') is True, 'Wrong constructed child plan')
    manifest = read(plan['inputs']['model_manifest'])
    q.need(manifest == dict(model='constructed-gpt2', family='gpt2', revision='fixture-at-queue-v1'),
           'Fixture refuses every real model manifest')
    rows = Path(plan['inputs']['rows']).resolve()
    # The fixture never has a real-row decode route: the path is in its own
    # generated fixture sources and both exact source pins are required.
    q.need(rows.name in {'fixture-0163.json.gz', 'fixture-0164.json.gz'} and
           rows.parent.name == 'constructed-sources', 'Fixture input namespace mismatch')
    q.need(plan['pins'].get(str(rows)) == filehash(rows), 'Unpinned constructed rows')
    guard.load_model = loader
    guard.memory = lambda: dict(commit_headroom_bytes=30*2**30, ram_available_bytes=30*2**30)
    child.run(root, operation)


def fixture_spec(root):
    from .week5_at_admission_prepare_v3 import closure
    source = root/'constructed-sources'; source.mkdir(parents=True, exist_ok=True)
    model = source/'MODEL.json'
    freeze(model,dict(model='constructed-gpt2', family='gpt2', revision='fixture-at-queue-v1'))
    batches = [None]*163
    for ordinal in (163,164):
        path = source/f'fixture-{ordinal:04d}.json.gz'
        gzip_equal(path,[dict(row_key=f'constructed-{ordinal}-{i}', final_prefix='a '*i, target=' b') for i in range(18)])
        batches.append(dict(batch_ordinal=ordinal,input_rows=str(path.resolve()),input_sha256=filehash(path),words=18))
    return dict(start_ordinal=163, model='constructed-gpt2',model_revision='fixture-at-queue-v1',
        model_manifest=str(model.resolve()),model_manifest_sha256=filehash(model),batches=batches,
        score_config=dict(context='final',context_length=1024,max_wall_seconds=900),
        child_pins=closure([FIXTURE_MODULE]),caps=dict(queue_wall_seconds=1200,queue_cpu_seconds=1200,
             chunk_wall_seconds=600,chunk_cpu_seconds=600,output_bytes=128*2**20),
        fixture_only=True)


def clone(function, **overrides):
    result=FunctionType(function.__code__, dict(function.__globals__,**overrides),
                        function.__name__,function.__defaults__,function.__closure__)
    result.__kwdefaults__=function.__kwdefaults__
    return result


def native_runner():
    return clone(q.native_phase, CHILD=FIXTURE_MODULE)


def run(output, inputs, config, verifying=False):
    q.need(not inputs and not config,'Constructed native queue has no external inputs')
    output = Path(output); output.mkdir(parents=True,exist_ok=True)
    # Complete independent native fixture repetition in the outer verify phase.
    work = output/('verification' if verifying else 'execution')
    work.mkdir(parents=True,exist_ok=True)
    import importlib.util,unittest,io
    test_path=q.REPO/'tests/test_week5_at_queue_v1.py'
    test_spec=importlib.util.spec_from_file_location('at_queue_counted_targeted',test_path)
    tests=importlib.util.module_from_spec(test_spec);test_spec.loader.exec_module(tests)
    transcript=io.StringIO();suite=unittest.defaultTestLoader.loadTestsFromModule(tests)
    checked=unittest.TextTestRunner(stream=transcript,verbosity=2).run(suite)
    freeze(work/'TARGETED_CHECKS.json',dict(tests=checked.testsRun,passed=checked.wasSuccessful(),
           failures=len(checked.failures),errors=len(checked.errors),test_source_sha256=filehash(test_path)))
    (work/'TARGETED_CHECKS.txt').write_text(transcript.getvalue(),encoding='utf8')
    q.need(checked.wasSuccessful(),'Counted targeted queue checks failed')
    spec = fixture_spec(work)
    result = q.drive(work/'queue',spec,phase_runner=native_runner())
    q.need(result['status']=='complete' and len(q.completed(work/'queue',spec))==2,'Full native queue did not complete')
    native_pairs=[]; cost=0
    for row in result['completed_chunks']:
        chunk=work/'queue'/row['root']
        native_pairs.append([read(chunk/f'{p}_NATIVE.json')['native'] for p in ('EXECUTE','VERIFY')])
        cost+=sum(read(chunk/f'{p}_JOB_USAGE.json')['cpu_seconds'] for p in ('EXECUTE','VERIFY'))
    q.need(len({(v['pid'],v['created_ticks']) for pair in native_pairs for v in pair})==4,
           'Four distinct native scorer processes required')
    # Resume actual retained partial output: force the first native operation
    # to return a sealed yield by a precreated request, then remove no original
    # evidence. The queue's new-attempt copy excludes operational requests.
    paused=work/'pause-queue'; first=[True]; real=native_runner()
    def once(root,operation,*args):
        if first[0]:
            first[0]=False;q.request_yield(root,'constructed outer yield before model loading')
        return real(root,operation,*args)
    stop=q.drive(paused,spec,phase_runner=once)
    q.need(stop['status']=='yielded','Constructed pause failed')
    retained=q.inventory(paused/'chunks/0163/a000')
    resumed=q.drive(paused,spec,phase_runner=real)
    q.need(resumed['status']=='complete' and q.inventory(paused/'chunks/0163/a000')==retained,
           'Native resume changed retained evidence')
    # Independent scratch tamper refusal leaves all completed originals alone.
    bad=work/'tampered';shutil.copytree(work/'queue',bad)
    target=bad/'chunks/0163/a000/output/block-00000.json'
    target.write_bytes(target.read_bytes()+b' ')
    try:q.completed(bad,spec)
    except ValueError:pass
    else:raise ValueError('Changed sealed score was accepted')
    # The final byte cap must catch a child that writes and exits between scans.
    # Hard-deadline containment kills only the exact owned native job.
    for case in ('fast-output-overflow','forced-deadline'):
        target=work/'constructed-native-cases'/case;target.mkdir(parents=True)
        freeze(target/'PLAN.json',dict(fixture_native_case=case))
        deadline=time.monotonic()+(120 if case=='fast-output-overflow' else 2)
        try:native_runner()(target,'execute',target,deadline,120,65536 if case=='fast-output-overflow' else 2**20)
        except (ValueError,RuntimeError) as error:
            wanted=('Final retained output exceeds cap' if case=='fast-output-overflow' else
                    'Native child exceeded checkpoint grace; authenticated resume review required')
            q.need(str(error)==wanted,'Wrong native refusal reason: '+repr(error))
        else:raise ValueError('Native refusal case did not refuse: '+case)
        q.need((target/'EXECUTE_JOB_USAGE.json').is_file(),'Refused native cost disappeared')
        owned=read(target/'EXECUTE_OWNED.json')['native'];closed=read(target/'EXECUTE_CLOSED.json')
        q.need(closed['native']==owned and closed['known_not_same_live'] is True and
               closed['native_inspection_completed'] is True,'Actual known native closure absent')
        if case=='forced-deadline':
            forced=read(target/'EXECUTE_FORCED_STOP.json')
            q.need(forced['native']==owned and forced['reason']=='chunk_or_queue_wall_boundary' and
                   closed['forced'] is True,'Deadline did not close the actual owned job')
        else:
            q.need(read(target/'EXECUTE_EXIT.json')['exit_code']==0 and
                   read(target/'RESULT.json').get('status')=='complete' and closed['forced'] is False,
                   'Fast output test did not reach its successful child return')
    context_bad=work/'changed-summary-context';shutil.copytree(work/'queue',context_bad)
    bad_root=context_bad/'chunks/0163/a000'
    altered=read(bad_root/'output/SUMMARY.json');altered['context_length']=64
    import json
    (bad_root/'output/SUMMARY.json').write_text(json.dumps(altered),encoding='utf8')
    try:q.audit_chunk(bad_root,spec,163)
    except ValueError as error:q.need(str(error)=='Summary changed scope','Unexpected changed-summary refusal')
    else:raise ValueError('Changed summary context length accepted')
    identity_deltas=[]
    for row in result['completed_chunks']:
        chunk=work/'queue'/row['root']
        for phase in ('EXECUTE','VERIFY'):
            native=read(chunk/(phase+'_NATIVE.json'))['native']
            for path in (chunk/'output').glob('GUARD_'+phase+'_*.json'):
                guard=read(path)
                if guard['identity']['pid']==native['pid']:
                    identity_deltas.append(abs(guard['identity']['creation_time']-
                        ((native['created_ticks']-116444736000000000)/1e7)))
    q.need(len(identity_deltas)==4 and max(identity_deltas)<=.000002,'Actual native identity conversion mismatch')
    freeze(work/'IDENTITY_CONVERSION.json',dict(deltas_seconds=identity_deltas,
           unchanged_tolerance_seconds=.000002,integer_epoch_subtraction_before_float=True))
    receipt=dict(fixture_only=True,complete_queue_chunks=2,serial_fresh_native_pairs=True,
        original_fp64_kernel_and_two_percent_fresh_forwards=True,nested_job_measurement_present=True,
        actual_thread_environment_checked=True,original_memory_guard_synthetic_snapshots=True,
        real_pretrained_memory_measurement=False,full_production_admission=False,
        authenticated_pause_copy_and_resume=True,prior_evidence_unchanged=True,tampered_chunk_refused=True)
    receipt.update(fast_exit_output_cap_refused=True,forced_native_deadline_refused=True,
                   refused_attempt_native_costs_retained=True,changed_summary_context_refused=True)
    freeze(work/'FIXTURE.json',receipt)
    if verifying:
        q.need(receipt==read(output/'execution/FIXTURE.json'),'Constructed replay differs')
        return dict(verified=True,fixture_only=True)
    return dict(status='complete',fixture_only=True,native_phase_cpu_seconds=cost,
                charge_rule='outer all-descendant Job CPU is authoritative, includes both queues and all resumes')


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=['execute','verify']);parser.add_argument('root',type=Path)
    args=parser.parse_args();fixture_child(args.operation,args.root.resolve())
