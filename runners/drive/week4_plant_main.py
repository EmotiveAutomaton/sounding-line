"""Unchanged PLANT main allocation; requires fully landed calibration.

DESIGN CHECK: LESSONS 3-5 read November 5. Both NULL and ALTERNATIVE require
600 whole valid messages and exact coverage; any missing/invalid item holds the
reader. No realization claim, retry, prompt correction or automatic REV call.
"""
from decimal import Decimal, ROUND_CEILING
from pathlib import Path
import argparse
import json
import re
import time
from runners.stage14.common import REPO, atomic, digest, filehash, freeze, read
from runners.stage14_midweek.api import request
from runners.drive import budget_week4 as budget, week4_plant as calibration

MODEL=calibration.MODEL
ROOT=REPO/'results/phase_2_4_stage_15/raw/drive-week4-cloud-20261102/PLANT-main'
PHASE='main'
LANDING=REPO/'results/phase_2_4_stage_15/DRIVE/WEEK4_PLANT_CALIBRATION_20261105.json'


def admitted():
    calibration.check_sources()
    root=calibration.ROOT/calibration.PHASE
    landed=read(LANDING);verified=read(root/'CALIBRATION_VERIFIED.json')
    if (not landed.get('full_write_through') or not landed.get('calibration_passes') or
        landed['complete_sha256']!=filehash(root/'COMPLETE.json') or
        landed['verified_sha256']!=filehash(root/'CALIBRATION_VERIFIED.json') or
        landed['blind_judgments_sha256']!=filehash(root/'BLIND_JUDGMENTS.json') or
        not verified['format_passes'] or not verified['blind_passes']):
        raise ValueError('complete landed calibration required')
    settlement=read(root/'RECONCILED.json')
    for n,h in settlement['proof'].items():
        if filehash(root/n)!=h:raise ValueError('calibration settlement changed')
    return root


def prepare():
    started=time.process_time()
    if ROOT.exists():raise ValueError('existing preparation; inspect it')
    previous=admitted()
    banks=read(calibration.ROOT/'ALLOCATION.json')
    rows=banks['main']
    if len(rows)!=600 or len({r['custom_id'] for r in rows})!=600:raise ValueError('main allocation')
    from runners.drive.week4_launch_v8 import closure
    paths=closure(['runners.drive.week4_plant_main','runners.drive.week4_plant_main_monitor'])
    paths|={LANDING,previous/'CALIBRATION_VERIFIED.json',previous/'BLIND_JUDGMENTS.json',
        previous/'COMPLETE.json',previous/'RECONCILED.json',calibration.ROOT/'ALLOCATION.json',
        calibration.ROOT/'SOURCE.json',REPO/'docs/design/stage-15/week4/PLANT_MAIN.md',
        REPO/'tests/test_week4_plant_main.py',budget.APPROVAL,budget.PACKET}
    freeze(ROOT/'REQUESTS.json',rows)
    cpu=time.process_time()-started
    prior=read(calibration.ROOT/'SOURCE.json')['cpu_preparation_seconds']
    if 240+cpu+prior+1500>1800:raise ValueError('local interface ceiling')
    freeze(ROOT/'SOURCE.json',dict(request_sha256=filehash(ROOT/'REQUESTS.json'),
        pins={str(path):filehash(path) for path in paths},cumulative_cpu_reserve=240,
        cumulative_preparation_cpu_seconds=cpu+prior,main_pieces=600))
    check_sources()
    return dict(main_pieces=600,cumulative_cpu_reserve=240,cumulative_preparation_cpu_seconds=cpu+prior)


def check_sources():
    admitted()
    s=read(ROOT/'SOURCE.json')
    for path,h in s['pins'].items():
        if filehash(path)!=h:raise ValueError('frozen main source changed')
    if filehash(ROOT/'REQUESTS.json')!=s['request_sha256']:raise ValueError('main requests changed')
    if read(ROOT/'REQUESTS.json')!=calibration.allocation()['main']:raise ValueError('main reconstruction')


def selected(phase):
    if phase!=PHASE:raise ValueError('other phase blocked')
    rows=read(ROOT/'REQUESTS.json')
    if len(rows)!=600 or len({r['custom_id'] for r in rows})!=600:raise ValueError('full main coverage')
    for r in rows:
        expected=calibration.params(r['prompt'],r['assignment'])
        if r['params']!=expected or r['custom_id']!=digest(expected):raise ValueError('unchanged prompt required')
    return rows


def count(phase):
    check_sources()
    rows = selected(phase)
    folder = ROOT / phase
    if (folder / 'PLAN.json').exists():
        return preflight(phase)
    access = json.loads(request('/v1/models/' + MODEL))
    if access.get('id') != MODEL:
        raise ValueError('unexpected model identity')
    counts = {}
    for r in rows:
        path = folder / 'counts' / (r['custom_id'] + '.json')
        if not path.exists():
            q = {k: v for k, v in r['params'].items() if k != 'max_tokens'}
            freeze(path, json.loads(request('/v1/messages/count_tokens', q)))
        counts[r['custom_id']] = read(path)['input_tokens']
    freeze(folder / 'COUNTS.json', counts)
    freeze(folder / 'ACCESS.json', access)
    freeze(folder / 'WIRE.json', {'requests': [{k: r[k] for k in ('custom_id', 'params')} for r in rows]})
    paths = [ROOT / 'SOURCE.json', ROOT / 'REQUESTS.json', folder / 'COUNTS.json',
             folder / 'WIRE.json', folder / 'ACCESS.json', Path(__file__), Path(budget.__file__)]
    plan = dict(at=time.time(), phase=phase, node='PLANT', attempted=600,
                reserved_cents=budget.ceiling(rows, counts), pins={str(p): filehash(p) for p in paths})
    freeze(folder / 'PLAN.json', plan)
    return plan


def preflight(phase):
    check_sources()
    rows = selected(phase)
    folder = ROOT / phase
    plan = read(folder / 'PLAN.json')
    if not 0 <= time.time() - plan['at'] <= 86400:
        raise ValueError('stale token/access preflight')
    for p, h in plan['pins'].items():
        if filehash(p) != h:
            raise ValueError('frozen wire or preflight changed')
    if read(folder / 'WIRE.json') != {'requests': [{k: r[k] for k in ('custom_id', 'params')} for r in rows]}:
        raise ValueError('wire differs from approved projection')
    if plan['reserved_cents'] != budget.ceiling(rows, read(folder / 'COUNTS.json')):
        raise ValueError('reservation ceiling changed')
    return plan


def submit(phase):
    plan = preflight(phase)
    folder = ROOT / phase
    if any((folder / n).exists() for n in ('RESERVATION.json', 'SUBMITTED.json', 'UNKNOWN.json')):
        raise ValueError('submission identity consumed; retrieve only')
    reservation = budget.reserve('week4-PLANT-main-' + phase, 'PLANT', plan['reserved_cents'], filehash(folder / 'PLAN.json'))
    freeze(folder / 'RESERVATION.json', reservation)
    try:
        raw = request('/v1/messages/batches', read(folder / 'WIRE.json'))
        (folder / 'SUBMIT_RESPONSE.json').write_bytes(raw)
        value = json.loads(raw)
        if not isinstance(value.get('id'), str) or not re.fullmatch(r'msgbatch_[A-Za-z0-9]+', value['id']):
            raise ValueError('missing batch identity')
        freeze(folder / 'SUBMITTED.json', dict(batch_id=value['id'], at=time.time()))
        return dict(status='SUBMITTED', batch_id=value['id'], reserved_cents=plan['reserved_cents'])
    except BaseException as exc:
        freeze(folder / 'UNKNOWN.json', dict(error_type=type(exc).__name__, reservation_retained=True))
        raise


def parse(message):
    try:
        if message.get('model') != MODEL or message.get('stop_reason') != 'end_turn':
            return None
        content = message['content']
        if not content or any(c.get('type') != 'text' or not isinstance(c.get('text'), str) for c in content):
            return None
        def unique(pairs):
            obj = {}
            for k, v in pairs:
                if k in obj:
                    raise ValueError('duplicate key')
                obj[k] = v
            return obj
        v = json.loads(''.join(c['text'] for c in content), object_pairs_hook=unique)
        if not isinstance(v, dict) or set(v) != {'piece'}:
            return None
        if not isinstance(v['piece'], str) or not v['piece'].strip():
            return None
        return v
    except (ValueError, KeyError, TypeError, AttributeError):
        return None


def replay(phase):
    check_sources()
    folder = ROOT / phase
    rows = selected(phase)
    status = read(folder / 'STATUS.json')
    if status['processing_status'] != 'ended' or status['id'] != read(folder / 'SUBMITTED.json')['batch_id']:
        raise ValueError('complete ended batch required')
    results = [json.loads(x) for x in (folder / 'RESULTS.jsonl').read_text(encoding='utf8').splitlines()]
    by = {r['custom_id']: r for r in results}
    if len(by) != len(results) or set(by) != {r['custom_id'] for r in rows}:
        raise ValueError('full result coverage')
    labels, cost, usage_complete = {}, Decimal(0), True
    for r in rows:
        result = by[r['custom_id']]['result']
        if result['type'] != 'succeeded':
            usage_complete = False
            continue
        m = result['message']
        u = m['usage']
        if any(type(u.get(k)) != int or u[k] < 0 for k in ('input_tokens', 'output_tokens')):
            raise ValueError('usage')
        if u.get('cache_creation_input_tokens', 0) or u.get('cache_read_input_tokens', 0):
            usage_complete = False
        cost += (Decimal('.05') * u['input_tokens'] + Decimal('.25') * u['output_tokens']) / 10000
        parsed = parse(m)
        if parsed is not None:
            labels[r['custom_id']] = parsed
    receipt = dict(status='COMPLETE', phase=phase, attempted=600, valid=len(labels),
        format_passes=len(labels) == 600, complete_main_corpus=len(labels) == 600,
        node_calibration_complete=True, main_admission=False, scientific_admission=False,
        usage_complete=usage_complete, measured_token_cents=int(cost.to_integral_value(rounding=ROUND_CEILING)),
        results_sha256=filehash(folder / 'RESULTS.jsonl'))
    freeze(folder / 'PIECES.json', labels)
    # Private accounting receipt precedes COMPLETE so a completion wake sees settlement.
    freeze(folder / 'FORMAT_RECEIPT.json', receipt)
    if usage_complete:
        proof = {n: filehash(folder / n) for n in ('RESULTS.jsonl', 'STATUS.json', 'SUBMITTED.json', 'FORMAT_RECEIPT.json')}
        budget.reconcile('week4-PLANT-main-' + phase, receipt['measured_token_cents'], digest(proof))
        freeze(folder / 'RECONCILED.json', dict(booked_cents=receipt['measured_token_cents'], proof=proof))
    freeze(folder / 'COMPLETE.json', receipt)
    return receipt


def retrieve(phase):
    folder = ROOT / phase
    if (folder / 'COMPLETE.json').exists():
        return read(folder / 'COMPLETE.json')
    check_sources()
    bid = read(folder / 'SUBMITTED.json')['batch_id']
    status = json.loads(request('/v1/messages/batches/' + bid))
    if status.get('id') != bid:
        raise ValueError('provider batch identity changed')
    atomic(folder / 'STATUS.json', status)
    if status['processing_status'] != 'ended':
        return {'status': status['processing_status']}
    path = folder / 'RESULTS.jsonl'
    if not path.exists():
        path.write_bytes(request('/v1/messages/batches/' + bid + '/results'))
    return replay(phase)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'count', 'submit', 'retrieve', 'replay'])
    args = parser.parse_args()
    result = prepare() if args.action == 'prepare' else globals()[args.action](PHASE)
    print(json.dumps(result))
