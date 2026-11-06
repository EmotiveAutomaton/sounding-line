"""Unchanged VAL main allocation; requires fully landed fresh calibration.

DESIGN CHECK: LESSONS 3-5 read November 5. Both NULL and ALTERNATIVE require
every whole valid message and exact coverage; any missing/invalid item holds the
reader. No value inference, retry, prompt correction or automatic consumer call.
"""
from decimal import Decimal, ROUND_CEILING
from pathlib import Path
import argparse
import json
import re
import time
from runners.stage14.common import REPO, atomic, digest, filehash, freeze, read
from runners.stage14_midweek.api import request
from runners.drive import budget_week4 as budget, week4_val_prompt_h1 as calibration

MODEL=calibration.MODEL
ROOT=REPO/'results/phase_2_4_stage_15/raw/drive-week4-cloud-20261102/VAL-main'
PHASE='main'
LANDING=REPO/'results/phase_2_4_stage_15/DRIVE/WEEK4_VAL_H1_CALIBRATION_20261105.json'


def admitted():
    calibration.check_sources();calibration.bound_plan(calibration.PHASE)
    root=calibration.ROOT/calibration.PHASE
    landed=read(LANDING);done=read(root/'COMPLETE.json')
    if (landed.get('full_write_through') is not True or
        landed.get('agreement_passes') is not True or landed.get('format_passes') is not True or
        landed['complete_sha256']!=filehash(root/'COMPLETE.json') or
        landed['settlement_sha256']!=filehash(root/'RECONCILED.json') or
        landed['gold_sha256']!=filehash(calibration.ROOT/'GOLD.json') or
        landed['labels_sha256']!=filehash(root/'LABELS.json') or done.get('passes') is not True):
        raise ValueError('complete landed calibration required')
    for n,h in read(root/'RECONCILED.json')['proof'].items():
        if filehash(root/n)!=h:raise ValueError('calibration settlement changed')
    labels=read(root/'LABELS.json')
    if set(labels)!={r['custom_id'] for r in calibration.selected(calibration.PHASE)}:
        raise ValueError('complete reusable calibration labels required')
    if any(not calibration.original.valid_label(v) for v in labels.values()):
        raise ValueError('valid reusable labels required')
    return root


def prepare():
    started=time.process_time()
    if ROOT.exists():raise ValueError('existing preparation; inspect it')
    previous=admitted();rows=read(calibration.ROOT/'REQUESTS.json')[100:]
    if len(rows)!=8231 or len({r['custom_id'] for r in rows})!=8231:raise ValueError('main allocation')
    from runners.drive.week4_launch_v8 import closure
    paths=closure(['runners.drive.week4_val_main','runners.drive.week4_val_main_monitor'])
    paths|={LANDING,previous/'LABELS.json',previous/'COMPLETE.json',previous/'RECONCILED.json',
        calibration.ROOT/'REQUESTS.json',calibration.ROOT/'PRIVATE_JOIN.json',
        calibration.ROOT/'PRIVATE_POPULATION.json',calibration.ROOT/'SOURCE.json',
        REPO/'docs/design/stage-15/week4/VAL_MAIN.md',REPO/'tests/test_week4_val_main.py',budget.APPROVAL,budget.PACKET}
    freeze(ROOT/'REQUESTS.json',rows)
    cpu=time.process_time()-started
    if cpu>60:raise ValueError('preparation overhead ceiling')
    freeze(ROOT/'SOURCE.json',dict(request_sha256=filehash(ROOT/'REQUESTS.json'),
        pins={str(path):filehash(path) for path in paths},cpu_interface_allocation_seconds=600,
        cpu_cumulative_interface_allocation_seconds=1200,cpu_charged_to='V2',
        preparation_cpu_seconds=cpu,main_items=8231,reused_calibration_items=100,total_items=8331))
    check_sources()
    return dict(main_items=8231,reused_calibration_items=100,total_items=8331,cpu_cumulative_interface_allocation_seconds=1200,preparation_cpu_seconds=cpu)


def check_sources():
    admitted();s=read(ROOT/'SOURCE.json')
    for path,h in s['pins'].items():
        if filehash(path)!=h:raise ValueError('frozen main source changed')
    if filehash(ROOT/'REQUESTS.json')!=s['request_sha256']:raise ValueError('main requests changed')
    if read(ROOT/'REQUESTS.json')!=read(calibration.ROOT/'REQUESTS.json')[100:]:raise ValueError('main reconstruction')
    return s


def selected(phase):
    if phase!=PHASE:raise ValueError('other phase blocked')
    rows=read(ROOT/'REQUESTS.json')
    if len(rows)!=8231 or len({r['custom_id'] for r in rows})!=8231:raise ValueError('full main coverage')
    for r in rows:
        text=json.loads(r['params']['messages'][0]['content'])['text']
        expected=calibration.original.params(text,calibration.CORRECTION)
        if r['item_id']!=digest({'VAL-text':text}) or r['params']!=expected or r['custom_id']!=digest(['VAL',1,r['item_id'],expected]):
            raise ValueError('unchanged prompt required')
    return rows


def count_inner(phase):
    started=time.monotonic();cpu=time.process_time()
    check_sources()
    rows = selected(phase)
    folder = ROOT / phase
    if (folder / 'PLAN.json').exists():
        return preflight(phase)
    if time.time()>=budget.CUTOFF:
        raise TimeoutError('finite count authority expired; no generation submitted')
    access = json.loads(request('/v1/models/' + MODEL))
    if access.get('id') != MODEL:
        raise ValueError('unexpected model identity')
    counts = {}
    for i,r in enumerate(rows):
        if time.time()>=budget.CUTOFF or time.monotonic()-started>10800 or time.process_time()-cpu>480:
            raise TimeoutError('finite count allocation exhausted; no generation submitted')
        path = folder / 'counts' / (r['custom_id'] + '.json')
        if not path.exists():
            q = {k: v for k, v in r['params'].items() if k != 'max_tokens'}
            value=json.loads(request('/v1/messages/count_tokens', q))
            freeze(path,dict(request_sha256=digest(q),response=value))
        q={k:v for k,v in r['params'].items() if k!='max_tokens'}
        saved=read(path)
        if saved['request_sha256']!=digest(q):raise ValueError('count checkpoint request changed')
        value=saved['response']['input_tokens']
        if type(value) is not int or value<=0:raise ValueError('invalid actual input count')
        counts[r['custom_id']]=value
        if i%25==0 or i+1==len(rows):
            atomic(folder/'COUNT_PROGRESS.json',dict(at=time.time(),completed=i+1,total=len(rows),cpu_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-started))
    freeze(folder / 'COUNTS.json', counts)
    freeze(folder / 'ACCESS.json', access)
    freeze(folder / 'WIRE.json', {'requests': [{k: r[k] for k in ('custom_id', 'params')} for r in rows]})
    paths = [ROOT / 'SOURCE.json', ROOT / 'REQUESTS.json', folder / 'COUNTS.json',
             folder / 'WIRE.json', folder / 'ACCESS.json', Path(__file__), Path(budget.__file__)]
    plan = dict(at=time.time(), phase=phase, node='VAL', attempted=len(rows),
                reserved_cents=budget.ceiling(rows, counts), pins={str(p): filehash(p) for p in paths})
    freeze(folder / 'PLAN.json', plan)
    return plan


def count(phase):
    folder=ROOT/phase
    if (folder/'COUNT_FAILED.json').exists():raise ValueError('failed count attempt; inspect before recovery')
    if (folder/'COUNT_COMPLETE.json').exists():return preflight(phase)
    from runners.stage9.process_identity import native_identity
    freeze(folder/'COUNT_OWNER.json',dict(native=native_identity(),at=time.time()))
    try:
        plan=count_inner(phase)
        freeze(folder/'COUNT_COMPLETE.json',dict(status='COMPLETE',phase='count-only',attempted=plan['attempted'],
            plan_sha256=filehash(folder/'PLAN.json'),reserved_ceiling_cents=plan['reserved_cents'],generation_submitted=False))
        return plan
    except BaseException as exc:
        freeze(folder/'COUNT_FAILED.json',dict(status='FAILED',error_type=type(exc).__name__,error=str(exc),generation_submitted=False))
        raise


def bound_plan(phase):
    check_sources()
    rows = selected(phase)
    folder = ROOT / phase
    plan = read(folder / 'PLAN.json')
    if (plan.get('node'),plan.get('phase'),plan.get('attempted'))!=('VAL',phase,len(rows)):
        raise ValueError('plan allocation changed')
    for p, h in plan['pins'].items():
        if filehash(p) != h:
            raise ValueError('frozen wire or preflight changed')
    if read(folder / 'WIRE.json') != {'requests': [{k: r[k] for k in ('custom_id', 'params')} for r in rows]}:
        raise ValueError('wire differs from approved projection')
    if plan['reserved_cents'] != budget.ceiling(rows, read(folder / 'COUNTS.json')):
        raise ValueError('reservation ceiling changed')
    return plan


def preflight(phase):
    plan=bound_plan(phase)
    if not 0<=time.time()-plan['at']<=86400:raise ValueError('stale token/access preflight')
    return plan


def submit(phase):
    plan = preflight(phase)
    folder = ROOT / phase
    if any((folder / n).exists() for n in ('RESERVATION.json', 'SUBMITTED.json', 'UNKNOWN.json')):
        raise ValueError('submission identity consumed; retrieve only')
    reservation = budget.reserve('week4-VAL-main-' + phase, 'VAL', plan['reserved_cents'], filehash(folder / 'PLAN.json'))
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
    return calibration.original.parse(message)


def replay(phase):
    bound_plan(phase)
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
    receipt = dict(status='COMPLETE', phase=phase, attempted=len(rows), valid=len(labels),
        format_passes=len(labels) == len(rows), complete_main_corpus=len(labels) == len(rows),reused_calibration_items=100,collection_assembled=False,
        node_calibration_complete=True, main_admission=False, scientific_admission=False,
        usage_complete=usage_complete, measured_token_cents=int(cost.to_integral_value(rounding=ROUND_CEILING)),
        results_sha256=filehash(folder / 'RESULTS.jsonl'))
    freeze(folder / 'LABELS.json', labels)
    # Private accounting receipt precedes COMPLETE so a completion wake sees settlement.
    freeze(folder / 'FORMAT_RECEIPT.json', receipt)
    if usage_complete:
        proof = {n: filehash(folder / n) for n in ('RESULTS.jsonl', 'STATUS.json', 'SUBMITTED.json', 'FORMAT_RECEIPT.json')}
        budget.reconcile('week4-VAL-main-' + phase, receipt['measured_token_cents'], digest(proof))
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
