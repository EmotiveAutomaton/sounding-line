"""Compose the specifically approved context supplement with whole pilot blocks.

DESIGN CHECK: LESSONS sections 3-5, G3-V6 and G3R1.7. Under NULL and
ALTERNATIVE the same original complete blocks and both context calls must
reproduce. Missing, substituted, partial or fabricated evidence refuses;
no accuracy selects admission and no failed work, time or charge is erased.
"""
import json
import math
import zipfile
from unittest.mock import patch

from .gear3_plan import verify_invocation
from .gear3_supplement import authorization, verify_payload, verify_reservation
from .stage10 import gear3_batch, ollama
from .stage10.contracts import digest

SCHEMA = 'gear3.scoped_pilot_admission.1'
FAILURE = {'type': 'ValueError', 'message': 'cloud execution feedback exceeded reserved allowance'}
WHOLE = {'P-literal-human-001': 'coauthor-handling',
         'P-literal-opportunity-002': 'ghost-opportunity'}
DEFERRED = 'P-literal-reading-003'


def device_evidence(restored, terminal):
    device = json.loads((restored / 'GPU_DEVICE.json').read_text())
    if (device['returncode'] != 0 or 'L40S' not in device['stdout']
            or terminal['gpu_observation']['samples'] < 1):
        raise ValueError('actual L40S observation required for each producer')
    loads = []
    for path in sorted(restored.glob('load-*-memory.json')):
        value = json.loads(path.read_text()); models = value.get('models', [])
        if (len(models) != 1 or models[0]['digest'] not in gear3_batch.PINS.values()
                or models[0].get('context_length') != 16384
                or type(models[0].get('size_vram')) is not int
                or models[0]['size_vram'] < models[0]['size']):
            raise ValueError('both original models must fit fully on GPU')
        loads.append(value)
    if {x['models'][0]['digest'] for x in loads} != set(gear3_batch.PINS.values()):
        raise ValueError('both original model loads required')
    return {'device': device, 'loads': loads, 'gpu_observation': terminal['gpu_observation']}


def whole_block(manifest, restored, ghost_root):
    folder = restored / 'blocks' / manifest['block_id']
    if not (folder / 'COMPLETE.json').is_file():
        raise ValueError('whole original paired block required')
    def forbidden(*args, **kwargs):
        raise ValueError('pilot inspection cannot call a model')
    with patch.object(ollama, 'api', forbidden):
        gear3_batch.run_block(manifest, folder, ghost_root=ghost_root)
    tasks, _ = gear3_batch.validate(manifest)
    timings = []; attempted = set(); valid = set()
    for unit in manifest['units']:
        route = folder / 'units' / digest(unit)[:32]
        saved = json.loads((route / 'UNIT.json').read_text())
        task, _ = tasks[unit['task_id']]
        key = (task.family, unit['model'], unit['arm']); attempted.add(key)
        if saved['result']['status'] == 'VALID': valid.add(key)
        calls = list((route / 'route').rglob('ATTEMPT.json'))
        if not calls: raise ValueError('literal calls missing from completed pilot unit')
        for call in calls:
            raw = json.loads(call.with_name('RAW.json').read_text())
            if raw.get('fixture') or raw.get('simulated') or raw.get('message', {}).get('thinking'):
                raise ValueError('constructed transport or unexpected thinking in pilot')
        seconds = saved['unit_wall_seconds']
        if not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds <= 0:
            raise ValueError('positive measured unit duration required')
        timings.append({'family': key[0], 'model': key[1], 'arm': key[2], 'seconds': seconds})
    return timings, attempted, valid


def compose(repo, original_bundle, supplement_bundle, data, ghost_root):
    approved = authorization(repo)
    old = verify_invocation(repo, approved['original_invocation'], original_bundle, data, ghost_root)
    new = verify_invocation(repo, approved['invocation'], supplement_bundle, data, ghost_root)
    row, job, terminal, receipt, restored = old
    extra, extra_job, extra_terminal, extra_receipt, extra_restored = new
    if (row['node'] != 'P' or row['status'] != 'FAILED' or terminal.get('error') != FAILURE
            or extra['node'] != 'Reserve' or extra['status'] != 'COMPLETE'
            or row['resources']['gpu'] != 'L40S' or extra['resources']['gpu'] != 'L40S'
            or job['mode'] != 'science' or extra.get('supplement_authorization') != approved):
        raise ValueError('only the approved original failure and complete supplement may compose')
    verify_payload(repo, supplement_bundle, extra_job)
    prior = {**data, 'runs': [r for r in data['runs'] if r is not extra]}
    verify_reservation(prior, approved, invocation=extra['invocation_id'], node=extra['node'],
        command=extra['command'], profile=extra['profile'], seconds=extra['duration_cap_seconds'],
        overhead_cents=extra['overhead_cents'], cost=extra['reserved_cents'], approval=extra['approval'],
        cache=False, recovery_of=extra['recovery_of'])
    if any(job[k] != extra_job[k] for k in ('execution_source_hashes', 'profiles', 'native_source_identity', 'server_version')):
        raise ValueError('supplement changes original execution or serving identity')
    original_device = device_evidence(restored, terminal)
    supplement_device = device_evidence(extra_restored, extra_terminal)
    with zipfile.ZipFile(original_bundle) as archive:
        blocks = {m['block_id']: m for m in (json.loads(archive.read(n)) for n in job['blocks'])}
    if set(blocks) != set(WHOLE) | {DEFERRED, approved['block']}:
        raise ValueError('original discarded block roster differs')
    if any(m['node'] != 'P' for m in blocks.values()):
        raise ValueError('scientific evidence cannot enter discarded admission')
    with zipfile.ZipFile(supplement_bundle) as archive:
        context = json.loads(archive.read(extra_job['blocks'][0]))
    if context != blocks[approved['block']]:
        raise ValueError('context supplement is not the original unchanged block')
    if (restored / 'blocks' / DEFERRED / 'COMPLETE.json').exists():
        raise ValueError('unexpected completion changes the diagnosed original disposition')
    if {t.family for t, _ in gear3_batch.validate(blocks[DEFERRED])[0].values()} != {'ghost-reading'}:
        raise ValueError('only the diagnosed reading block may be deferred')
    timings = []; attempted = set(); valid = set()
    for identifier, family in WHOLE.items():
        if {t.family for t, _ in gear3_batch.validate(blocks[identifier])[0].values()} != {family}:
            raise ValueError('original admitted family differs')
        measured, tried, passed = whole_block(blocks[identifier], restored, ghost_root)
        timings.extend(measured); attempted.update(tried); valid.update(passed)
    _, context_tried, context_valid = whole_block(context, extra_restored, ghost_root)
    if context_tried != context_valid or {k[1] for k in context_valid} != set(job['profiles']):
        raise ValueError('both original context interfaces must be valid')
    duration = terminal['duration_seconds'] + extra_terminal['duration_seconds']
    if not math.isfinite(duration) or duration < sum(t['seconds'] for t in timings):
        raise ValueError('complete producer duration must retain all failed work and overhead')
    return {'schema': SCHEMA, 'status': 'PASS_SCOPED',
        'authorization_sha256': digest(approved),
        'invocation': approved['original_invocation'], 'bundle': original_bundle.relative_to(repo).as_posix(),
        'bundle_sha256': row['command'][-1], 'reservation_sha256': terminal['reservation_sha256'],
        'archive_sha256': receipt['archive_sha256'], 'original_terminal_status': terminal['status'],
        'original_error': terminal['error'], 'execution_sources': job['execution_source_hashes'],
        'profiles': job['profiles'], **original_device, 'route_timings': timings,
        'valid_routes': [list(k) for k in sorted(valid)],
        'unrealized_routes': [list(k) for k in sorted(attempted - valid)],
        'admitted_blocks': list(WHOLE),
        'excluded_blocks': [{'block_id': DEFERRED, 'family': 'ghost-reading', 'reason': 'original incomplete block; no units admitted'}],
        'supplement': {'invocation': approved['invocation'], 'bundle': supplement_bundle.relative_to(repo).as_posix(),
            'bundle_sha256': extra['command'][-1], 'reservation_sha256': extra_terminal['reservation_sha256'],
            'archive_sha256': extra_receipt['archive_sha256'], 'block_id': context['block_id'],
            'block_sha256': digest(context), **supplement_device},
        'measurement_margin': 1.25, 'service_duration_seconds': duration,
        'scope': 'Owner-approved complete human/opportunity blocks plus exact context supplement; Ghost reading deferred; no scientific scores'}
