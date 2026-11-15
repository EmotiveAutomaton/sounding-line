"""One counted, bounded queue over the remaining original m00 pilot ordinals.

DESIGN CHECK: LESSONS sections 3-5, read 2026-11-15. Under either scientific
direction the exact roster, source hashes, FP64 scorer, native memory limits,
fresh replay and inclusive cost rules are identical. Missing, changed, skipped,
overlapping or unverified evidence refuses. Resource/clock/quantum stops yield;
numerical or integrity failures fail. Neither is a scientific result. This is
an unqualified private candidate; no input enables a substitute scoring kernel.
"""
from pathlib import Path
import math
import os
import hashlib
import json
import shutil
import time

from .batch_runtime import read, freeze, atomic, filehash, check_files, now, REPO, PYTHON
from .batch_runtime_v8 import measured_child, job_cpu, output_bytes
from .week5_resume import output_manifest
from . import week5_at_queue_native_v2 as native_proof
from .week5_at_queue_native_v2 import prove_member
from . import week5_at_queue_child_v2  # explicit closure pin for native boundary

MODULE = 'runners.drive.cards.week5_at_queue_v1'
SCORER = 'runners.drive.cards.week5_at_scoring_guard_v1'
CHILD = 'runners.drive.cards.week5_at_queue_child_v2'
NUMERIC = dict(version='AT-FP64-1', model_computation='float64_from_pinned_float32',
    log_softmax_and_entropy='float32', cache_fresh_tolerance_nats=1e-4,
    attention_backend='original_model_default')
LIMITS = dict(start_commit_bytes=26*2**30, start_ram_bytes=20*2**30,
    request_commit_bytes=7*2**30, request_ram_bytes=7*2**30,
    hard_commit_floor_bytes=6*2**30, hard_ram_floor_bytes=6*2**30,
    cooperative_grace_seconds=60, poll_seconds=.25)
ROSTER_SHA = 'cdb90059a1439205dff7feba1517dc7fb990a57718e1e7996d431730f99a05fb'
MODEL_PROPOSAL_SHA = 'c5d3380c0bfad4ea6b97dc5700115a820da4efe27ffb902165cc9aa4d574334e'


def need(condition, message):
    if not condition:
        raise ValueError(message)


def below(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    path.relative_to(root)
    return path


def finite_positive(value, maximum):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and 0 < value <= maximum


def validate_manifest(spec):
    need(spec.get('schema') == 'AT_QUEUE_V1' and spec.get('owner_bound') is True,
         'Owner-bound original queue manifest required')
    need(spec['original_roster']['sha256'] == ROSTER_SHA and
         spec['model_proposal']['sha256'] == MODEL_PROPOSAL_SHA, 'Original roster changed')
    need(spec['model_ordinal'] == 0 and spec['numerical_spec'] == NUMERIC and
         spec['native_limits'] == LIMITS, 'Changed reader, precision or guard')
    need(spec['scorer'] == SCORER and spec['numerical_threads'] == 2, 'Changed scientific producer')
    batches = spec['batches']
    need(len(batches) == 165 and [b['batch_ordinal'] for b in batches] == list(range(165)),
         'Exactly the original 165 ordinals required')
    need(sum(b['words'] for b in batches) == 27007, 'Original pilot word scope changed')
    need(len({str(Path(b['input_rows']).resolve()).casefold() for b in batches}) == 165,
         'Duplicated original batch')
    start = spec['start_ordinal']
    need(isinstance(start, int) and 1 <= start < 165 and spec['end_ordinal_exclusive'] == 165,
         'Queue must complete consecutive remaining pilot ordinals')
    need(spec['score_config'] == dict(context='final', context_length=1024, max_wall_seconds=900),
         'Original scoring configuration changed')
    cap = spec['caps']
    need(finite_positive(cap['queue_wall_seconds'], 43200), 'Queue exceeds twelve hours')
    need(finite_positive(cap['queue_cpu_seconds'], 750000), 'Queue CPU outside original family ceiling')
    need(finite_positive(cap['chunk_cpu_seconds'], 7200), 'Chunk CPU ceiling changed')
    need(finite_positive(cap['chunk_wall_seconds'], 1700) and cap['chunk_wall_seconds'] >= 120,
         'Chunk quantum outside preserved bounds')
    need(cap['projected_peak_ram_GiB'] >= 20 and finite_positive(cap['output_bytes'], 32*2**30),
         'Missing finite resource caps')
    need(spec['prefix']['count'] == start and spec['prefix']['owner_reviewed'] is True,
         'Complete-prefix owner review required')
    need(spec['prefix']['file_pins'] and spec['child_pins'], 'Missing immutable dependencies')


def authenticate(spec, include_prefix):
    validate_manifest(spec)
    for key in ('original_roster', 'model_proposal'):
        ref = spec[key]
        need(filehash(ref['path']) == ref['sha256'], key + ' bytes changed')
    proposal = read(spec['model_proposal']['path'])
    need(proposal['pilot_batches'] == spec['batches'] and proposal['model_ordinal'] == 0 and
         proposal['model'] == spec['model'] and proposal['model_revision'] == spec['model_revision'] and
         proposal['model_manifest_sha256'] == spec['model_manifest_sha256'], 'Pilot binding changed')
    check_files(spec['child_pins'])
    if include_prefix:
        # A single deduplicated hash pass per queue invocation, never per new chunk.
        check_files(spec['prefix']['file_pins'])
        plain = {k:v for k,v in spec['prefix'].items() if k != 'manifest_sha256'}
        need(hashlib.sha256(json.dumps(plain,sort_keys=True,separators=(',', ':')).encode()).hexdigest()
             == spec['prefix']['manifest_sha256'], 'Prefix manifest identity differs')
        need([r['ordinal'] for r in spec['prefix']['chunks']] == list(range(spec['start_ordinal'])),
             'Prefix has a gap or overlap')
        from .week5_historical_exit_v1 import stopped
        for row in spec['prefix']['chunks']:
            root = Path(row['root']); done = read(root/'COMPLETE.json'); plan = read(root/'PLAN.json')
            batch = spec['batches'][row['ordinal']]
            need(done.get('status') == 'COMPLETE' and done.get('fresh_process_verified') is True,
                 'Prefix lacks complete fresh verification')
            need(filehash(root/'COMPLETE.json') == row['complete_sha256'] and
                 plan['module'] == SCORER and plan['config']['context'] == 'final' and
                 plan['config']['context_length'] == 1024 and
                 Path(plan['inputs']['rows']).resolve() == Path(batch['input_rows']).resolve(),
                 'Prefix scientific binding mismatch')
            need(stopped(read(root/'OWNER.json')['native'], done['at']), 'Prefix native exit unknown')
            summary = read(root/'output/SUMMARY.json')
            need(summary['numerical_spec'] == NUMERIC and summary['words'] == batch['words'] and
                 summary['model'] == spec['model'] and summary['model_revision'] == spec['model_revision'],
                 'Prefix result scope mismatch')
        for prior in spec['prefix']['attempts']:
            root = Path(prior['root']); terminal = read(root/prior['terminal'])
            need(stopped(read(root/'OWNER.json')['native'], terminal['at']), 'Retained chain exit unknown')


def inventory(root):
    return {p.relative_to(root).as_posix(): filehash(p) for p in sorted(Path(root).rglob('*'))
            if p.is_file() and p.name not in {'CHUNK_COMPLETE.json', 'CHUNK_PAUSED.json', 'PROGRESS.json', 'YIELD_REQUEST.json'}
            and not p.name.endswith('.tmp') and '.tmp.' not in p.name}


def check_seal(root, seal):
    need(inventory(root) == seal['files'], 'Changed or incomplete chunk files')


def completed(output, spec):
    result = []
    chunks = output/'chunks'
    if not chunks.exists():
        return result
    expected = spec['start_ordinal']
    for chunk in sorted(chunks.iterdir()):
        need(chunk.is_dir() and chunk.name == f'{expected:04d}', 'Chunk checkpoint gap or foreign directory')
        complete = list(chunk.glob('a*/CHUNK_COMPLETE.json'))
        attempts = sorted(chunk.glob('a*'))
        need([p.name for p in attempts] == [f'a{i:03d}' for i in range(len(attempts))], 'Attempt gap')
        for index, attempt in enumerate(attempts):
            if index:
                inherited = read(attempt/'RESUMED_CHUNK.json')
                need(inherited == dict(predecessor=attempts[index-1].relative_to(output).as_posix(),
                     paused_sha256=filehash(attempts[index-1]/'CHUNK_PAUSED.json')), 'Changed attempt ancestry')
            if (attempt/'CHUNK_PAUSED.json').is_file():
                check_seal(attempt, read(attempt/'CHUNK_PAUSED.json'))
            elif not (attempt/'CHUNK_COMPLETE.json').is_file():
                raise ValueError('Unsealed interrupted chunk requires owner recovery')
        need(len(complete) <= 1 and (not complete or complete[0].parent == attempts[-1]), 'Duplicate or nonterminal complete chunk')
        if not complete:
            need(chunk == sorted(chunks.iterdir())[-1], 'Work after unfinished chunk')
            break
        seal = read(complete[0]); check_seal(complete[0].parent, seal)
        audit_chunk(complete[0].parent, spec, expected)
        result.append(dict(ordinal=expected, root=complete[0].parent.relative_to(output).as_posix(),
                           sha256=filehash(complete[0])))
        expected += 1
    need(expected <= 165, 'Work beyond frozen pilot')
    return result


def audit_chunk(root, spec, ordinal):
    plan = read(root/'PLAN.json'); batch = spec['batches'][ordinal]
    need(plan['module'] == SCORER and plan['config'] == spec['score_config'] and
         plan['inputs'] == dict(rows=batch['input_rows'], model_manifest=spec['model_manifest']),
         'Chunk scientific plan changed')
    need(read(root/'RESULT.json').get('status') == 'complete', 'Execute incomplete')
    verification = read(root/'VERIFIED.json')
    need(verification.get('verified') is True and verification.get('status') != 'yielded',
         'Fresh scorer verification incomplete')
    need(verification['fresh_forward_count'] == max(1, math.ceil(.02*batch['words'])) and
         verification['max_error'] <= 1e-4, 'Original fresh-forward gate missing')
    summary = read(root/'output/SUMMARY.json')
    need(summary['numerical_spec'] == NUMERIC and summary['words'] == batch['words'] and
         summary['model'] == spec['model'] and summary['model_revision'] == spec['model_revision'] and
         summary['context'] == 'final' and summary['context_length'] == 1024, 'Summary changed scope')
    natives = []
    for phase in ('EXECUTE', 'VERIFY'):
        usage = read(root/f'{phase}_JOB_USAGE.json')
        need(usage['includes_all_descendants_and_exited_processes'] is True and
             usage['exit_code'] == 0 and usage['cpu_seconds'] >= 0, 'Native phase usage missing')
        native = read(root/f'{phase}_NATIVE.json')['native']; natives.append(native)
        native_proof.require_phase_proof(root, phase, native)
        environment = read(root/f'{phase}_ENVIRONMENT.json')
        need(environment['threads'] == 2 and environment['cuda_visible'] == '' and
             all(p['num_threads'] <= 2 for p in environment['pools']), 'Actual numerical environment mismatch')
        guards = [read(p) for p in (root/'output').glob(f'GUARD_{phase}_*.json')]
        need(any(g.get('status') == 'returned' and g.get('limits') == LIMITS and
                 g.get('identity', {}).get('pid') == native['pid'] and
                 abs(g['identity']['creation_time'] - ((native['created_ticks']-116444736000000000)/1e7)) <= .000002 and
                 Path(g['identity']['executable']).resolve() == Path(native['executable']).resolve() and
                 g['initial']['commit_headroom_bytes'] >= LIMITS['start_commit_bytes'] and
                 g['initial']['ram_available_bytes'] >= LIMITS['start_ram_bytes']
                 for g in guards), 'Original native guard proof missing')
    need(natives[0] != natives[1], 'Execute and verify must be separate native processes')


def request_yield(root, reason):
    for path in (root/'output/YIELD_REQUEST.json', root/'output/scores/YIELD_REQUEST.json'):
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            freeze(path, dict(at=now(), reason=reason))


def native_phase(root, operation, queue_output, deadline, cpu_left, output_cap):
    """Authenticate launcher and actual scorer separately inside the exact Job."""
    from runners.stage9.process_identity import native_identity
    command = [str(PYTHON), '-X', 'utf8', '-B', '-m', CHILD, operation, str(root)]
    requested = reason = actual = error = None; forced = False
    observed = {}; phase = operation.upper(); next_size_check = time.monotonic()
    def remember(snapshot):
        for identity in snapshot['identities']:
            observed[(identity['pid'],identity['created_ticks'])] = identity
    with measured_child(root, operation, command) as worker:
        launch = native_identity(worker.pid)
        need(launch is not None, 'Launch native identity unavailable')
        observed[(launch['pid'],launch['created_ticks'])] = launch
        freeze(root/(phase+'_OWNED.json'),dict(at=now(),native=launch,role='launch_redirector'))
        try:
            freeze(root/(phase+'_LAUNCH_MEMBER.json'),prove_member(worker,launch))
            while True:
                snapshot = native_proof.sample_job(worker); remember(snapshot)
                ready_path = root/(phase+'_READY.json')
                if actual is None and ready_path.is_file():
                    ready = read(ready_path)
                    need(ready['phase']==operation and ready['plan_sha256']==filehash(root/'PLAN.json'),
                         'Scorer ready handshake has wrong phase or plan')
                    actual = ready['native']; member = prove_member(worker,actual)
                    observed[(actual['pid'],actual['created_ticks'])] = actual
                    freeze(root/(phase+'_MEMBER.json'),dict(member,launch_native=launch,
                           ready_sha256=filehash(ready_path)))
                code = worker.poll()
                if code is not None and native_proof.empty(snapshot): break
                moment = time.monotonic()
                if requested is None:
                    if (queue_output/'YIELD_REQUEST.json').exists(): reason='outer_yield_request'
                    elif moment >= deadline-60: reason='chunk_or_queue_wall_boundary'
                    elif snapshot['cpu_seconds'] >= cpu_left: reason='inclusive_chunk_cpu_boundary'
                    elif moment >= next_size_check:
                        next_size_check=moment+30
                        if output_bytes(queue_output)>output_cap: reason='queue_output_cap'
                    if reason: request_yield(root,reason); requested=moment
                if moment >= deadline or (requested is not None and moment-requested>=60):
                    forced=True; break
                time.sleep(.05)
        except BaseException as exc:
            error=exc; forced=True; reason=reason or 'native_phase_exception'
        finally:
            snapshot=native_proof.sample_job(worker);remember(snapshot)
            if forced or not native_proof.empty(snapshot):
                forced=True
                freeze(root/(phase+'_FORCED_STOP.json'),dict(at=now(),reason=reason,
                       native=actual,launch_native=launch,observed_identities=list(observed.values())))
                snapshot=native_proof.terminate_and_drain(worker,remember)
            need(native_proof.empty(snapshot),'Owned Job emptiness not proved')
            freeze(root/(phase+'_JOB_EMPTY.json'),snapshot)
            code=worker.poll()
            need(code is not None,'Launch exit unknown after empty Job')
            freeze(root/(phase+'_EXIT.json'),dict(at=now(),native=actual,launch_native=launch,exit_code=code))
    # Context close follows the empty-Job observation. Unknown identities raise.
    checks=native_proof.exited_identities(list(observed.values()))
    freeze(root/(phase+'_CLOSED.json'),dict(at=now(),native=actual,launch_native=launch,
           identity_checks=checks,known_not_same_live=True,native_inspection_completed=True,
           job_empty_before_close=True,job_closed=True,forced=forced))
    if error is not None: raise error
    if forced: raise RuntimeError('Native child exceeded checkpoint grace; authenticated resume review required')
    need(actual is not None,'Actual scorer membership was never authenticated')
    need(output_bytes(queue_output)<=output_cap,'Final retained output exceeds cap')
    need(code==0,'Native phase failed; preserve all costs and require owner recovery')
    value=read(root/('RESULT.json' if operation=='execute' else 'VERIFIED.json'))
    usage=read(root/(phase+'_JOB_USAGE.json'))
    need(usage['cpu_seconds']<=cpu_left,'Native child exceeded inclusive chunk CPU boundary')
    return value,usage['cpu_seconds']


def new_attempt(output, spec, ordinal):
    chunk = output/'chunks'/f'{ordinal:04d}'
    chunk.mkdir(parents=True, exist_ok=True)
    prior = sorted(chunk.glob('a*'))
    need([p.name for p in prior] == [f'a{i:03d}' for i in range(len(prior))], 'Attempt sequence gap')
    if prior:
        last = prior[-1]
        need((last/'CHUNK_PAUSED.json').is_file(), 'Unsealed interrupted attempt needs owner recovery')
        paused = read(last/'CHUNK_PAUSED.json'); check_seal(last, paused)
    target = chunk/f'a{len(prior):03d}'; target.mkdir()
    if prior:
        for name, digest in output_manifest(prior[-1]/'output').items():
            source = below(prior[-1]/'output', name); destination = below(target/'output', name)
            destination.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, destination)
            need(filehash(destination) == digest, 'Checkpoint copy mismatch')
        freeze(target/'RESUMED_CHUNK.json', dict(predecessor=prior[-1].relative_to(output).as_posix(),
               paused_sha256=filehash(prior[-1]/'CHUNK_PAUSED.json')))
    batch = spec['batches'][ordinal]
    pins = dict(spec['child_pins'])
    pins[batch['input_rows']] = batch['input_sha256']
    pins[spec['model_manifest']] = spec['model_manifest_sha256']
    freeze(target/'PLAN.json', dict(module=SCORER, inputs=dict(rows=batch['input_rows'],
           model_manifest=spec['model_manifest']), config=spec['score_config'], pins=pins,
           queue_ordinal=ordinal, counted_parent_only=True))
    return target


def drive(output, spec, phase_runner=native_phase):
    """Internal orchestration seam used only by the separately labelled fixture."""
    started = time.monotonic(); start_cpu = time.process_time(); cap = spec['caps']
    existing = completed(output, spec)
    phase_cpu = 0.0
    end = started + cap['queue_wall_seconds']
    for ordinal in range(spec['start_ordinal'] + len(existing), 165):
        if (output/'YIELD_REQUEST.json').exists() or time.monotonic() >= end-120:
            return dict(status='yielded', completed_chunks=len(existing), next_ordinal=ordinal)
        if phase_cpu + time.process_time()-start_cpu >= cap['queue_cpu_seconds']:
            return dict(status='yielded', completed_chunks=len(existing), next_ordinal=ordinal, reason='queue_cpu_boundary')
        root = new_attempt(output, spec, ordinal)
        deadline = min(end, time.monotonic()+cap['chunk_wall_seconds'])
        chunk_cpu = 0.0
        yielded = False
        for operation in ('execute', 'verify'):
            left = min(cap['chunk_cpu_seconds']-chunk_cpu,
                       cap['queue_cpu_seconds']-phase_cpu-(time.process_time()-start_cpu))
            if left <= 0 or time.monotonic() >= deadline-60:
                yielded = True; break
            value, used = phase_runner(root, operation, output, deadline, left, cap['output_bytes'])
            phase_cpu += used; chunk_cpu += used
            if value.get('status') == 'yielded': yielded = True; break
        need(output_bytes(output) <= cap['output_bytes'], 'Final retained output exceeds queue cap')
        seal = dict(schema='AT_QUEUE_CHUNK_V1', ordinal=ordinal, at=now(),
                    files=inventory(root), native_cpu_seconds=chunk_cpu,
                    charge_rule='diagnostic subset of outer all-descendant job CPU; never add twice')
        if yielded:
            freeze(root/'CHUNK_PAUSED.json', seal)
            return dict(status='yielded', completed_chunks=len(existing), next_ordinal=ordinal,
                        reason='original_chunk_checkpoint', native_cpu_seconds=phase_cpu)
        audit_chunk(root, spec, ordinal)
        freeze(root/'CHUNK_COMPLETE.json', seal)
        existing.append(dict(ordinal=ordinal, root=root.relative_to(output).as_posix(),
                             sha256=filehash(root/'CHUNK_COMPLETE.json')))
        atomic(output/'PROGRESS.json', dict(at=now(), completed_chunks=len(existing),
               last_ordinal=ordinal, next_ordinal=ordinal+1, reporting='internal_checkpoint_only'))
    result = dict(status='complete', start_ordinal=spec['start_ordinal'], end_ordinal_exclusive=165,
                  original_chunks=165, completed_chunks=existing, original_pilot_words=27007,
                  numerical_spec=NUMERIC, model=spec['model'], model_revision=spec['model_revision'],
                  scientific_analysis_performed=False, queue_landing_required=True)
    freeze(output/'QUEUE_SUMMARY.json', result)
    return result


def load(output, inputs, config):
    need(set(inputs) == {'queue_manifest'} and not config, 'Exact frozen queue interface required')
    output = Path(output); plan = read(output.parent/'PLAN.json')
    need(plan.get('module') == MODULE and plan.get('family') == 'AT' and plan.get('owner_reviewed') is True,
         'Reviewed outer AT plan required')
    need(plan.get('gpu') is False and plan.get('paid') is False and plan.get('ollama') is False and
         plan.get('numerical_threads') == 2, 'CPU-only Gear 2 boundary required')
    spec = read(inputs['queue_manifest'])
    need(plan['pins'].get(inputs['queue_manifest']) == filehash(inputs['queue_manifest']), 'Queue manifest not pinned')
    validate_manifest(spec)
    need(plan['max_wall_seconds'] <= spec['caps']['queue_wall_seconds'] and
         plan['max_cpu_seconds'] <= spec['caps']['queue_cpu_seconds'], 'Outer plan exceeds frozen bounds')
    # The existing outer runtime enforces campaign/family remainder and closing
    # clock, claims one shared slot, contains this process, and accounts all children.
    return output, spec


def execute(output, inputs, config):
    output, spec = load(output, inputs, config)
    authenticate(spec, include_prefix=True)
    output.mkdir(parents=True, exist_ok=True)
    receipt = output/'PREFIX_AUTHENTICATED.json'
    if not receipt.exists():
        freeze(receipt, dict(prefix_manifest_sha256=spec['prefix']['manifest_sha256'],
               original_roster_sha256=ROSTER_SHA, count=spec['start_ordinal'], at=now(),
               verification='deduplicated complete historical prefix once per queue invocation'))
    else:
        need(read(receipt)['prefix_manifest_sha256'] == spec['prefix']['manifest_sha256'], 'Changed prefix on resume')
    return drive(output, spec)


def verify(output, inputs, config):
    output, spec = load(output, inputs, config)
    authenticate(spec, include_prefix=False)
    prefix = read(output/'PREFIX_AUTHENTICATED.json')
    need(prefix['count'] == spec['start_ordinal'] and
         prefix['prefix_manifest_sha256'] == spec['prefix']['manifest_sha256'], 'Prefix audit missing')
    chunks = completed(output, spec)
    need(len(chunks) == 165-spec['start_ordinal'], 'Whole declared queue not complete')
    summary = read(output/'QUEUE_SUMMARY.json')
    need(summary['completed_chunks'] == chunks, 'Queue summary differs from complete chunk seals')
    need(output_bytes(output) <= spec['caps']['output_bytes'], 'Final retained output exceeds queue cap')
    return dict(status='complete', verified=True, native_chunk_replays_already_complete=True,
                chunks=len(chunks), queue_summary_sha256=filehash(output/'QUEUE_SUMMARY.json'),
                scientific_analysis_performed=False)
