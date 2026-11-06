"""Unchanged AUTH main allocation after the fully landed fresh calibration.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 4-7 read November 5; AUTH_MAIN.md.
Under NULL and ALTERNATIVE, exact allocation, whole valid replies and source
identity are required for complete collection. Invalids remain abstentions;
no score-dependent selection, scientific estimate, prompt fix or retry here.
"""
from collections import Counter
from decimal import Decimal, ROUND_CEILING
from pathlib import Path
import argparse
import json
import re
import time
from runners.stage14.common import REPO, atomic, digest, filehash, freeze, read
from runners.stage14_midweek.api import request
from runners.drive import budget_week4 as budget, week4_auth_prompt_h1 as calibration

MODEL=calibration.MODEL
ROOT=REPO/'results/phase_2_4_stage_15/raw/drive-week4-cloud-20261102/AUTH-main'
PHASE='main'
LANDING=REPO/'results/phase_2_4_stage_15/DRIVE/WEEK4_AUTH_H1_CALIBRATION_20261105.json'


def admitted():
    calibration.check_sources();calibration.bound_plan(calibration.PHASE)
    root=calibration.ROOT/calibration.PHASE
    landed=read(LANDING);done=read(root/'COMPLETE.json')
    if (landed.get('full_write_through') is not True or
        landed.get('discrimination_passes') is not True or landed.get('format_passes') is not True or
        landed['complete_sha256']!=filehash(root/'COMPLETE.json') or
        landed['settlement_sha256']!=filehash(root/'RECONCILED.json') or
        landed['truth_sha256']!=filehash(calibration.ROOT/'GOLD.json') or
        landed['labels_sha256']!=filehash(root/'LABELS.json') or
        landed['source_sha256']!=filehash(calibration.ROOT/'SOURCE.json') or
        done.get('passes') is not True or done.get('usage_complete') is not True):
        raise ValueError('complete landed calibration required')
    for n,h in read(root/'RECONCILED.json')['proof'].items():
        if filehash(root/n)!=h:raise ValueError('calibration settlement changed')
    labels=read(root/'LABELS.json')
    if set(labels)!={r['custom_id'] for r in calibration.selected(calibration.PHASE)}:
        raise ValueError('complete calibration labels required')
    if any(type(v) is not int or not 0<=v<=9 for v in labels.values()):
        raise ValueError('valid calibration labels required')
    return root


def remainder(pairs,selection,initial,fresh):
    if len(pairs)!=4000 or len({r['pair_id'] for r in pairs})!=4000:
        raise ValueError('complete original pair bank required')
    arguments=[r['pair_id'] for r in pairs if r['genre']=='argumentative']
    if initial!=selection['calibration'] or fresh!=selection['fresh'] or initial!=arguments[:100] or fresh!=arguments[100:200]:
        raise ValueError('used calibration partition changed')
    excluded=set(initial+fresh)
    if len(initial)!=100 or len(fresh)!=100 or len(excluded)!=200:
        raise ValueError('two complete disjoint used calibration sets required')
    chosen=[r for r in pairs if r['pair_id'] not in excluded]
    expected={('creative',True):1000,('creative',False):1000,('argumentative',True):900,('argumentative',False):900}
    if len(chosen)!=3800 or Counter((r['genre'],r['same_writer']) for r in chosen)!=expected:
        raise ValueError('unchanged main truth and genre allocation required')
    return chosen


def rebuild():
    # Revalidate both original allocation and the exact already-used fresh set.
    fresh_rows,_,paths=calibration.rebuild()
    pairs=read(calibration.PAIRS/'output/PRIVATE_PAIRS.json')
    selection=read(calibration.PAIRS/'output/SELECTION.json')
    initial=read(REPO/'results/phase_2_4_stage_15/raw/drive-week4-cloud-20261102/AUTH/REQUESTS.json')
    chosen=remainder(pairs,selection,[r['item_id'] for r in initial],[r['item_id'] for r in fresh_rows])
    rows=[]
    for r in chosen:
        if r['pair_id']!=digest(sorted(r['texts'])):raise ValueError('pair text binding')
        params=calibration.params(r['texts'])
        rows.append(dict(item_id=r['pair_id'],custom_id=digest(['AUTH',1,r['pair_id'],params]),params=params))
    return rows,chosen,paths


def prepare():
    started=time.process_time()
    if ROOT.exists():raise ValueError('existing preparation; inspect it')
    previous=admitted();rows,joins,paths=rebuild()
    from runners.drive.week4_launch_v8 import closure
    paths|=closure(['runners.drive.week4_auth_main','runners.drive.week4_auth_main_monitor'])
    paths|={LANDING,previous/'LABELS.json',previous/'COMPLETE.json',previous/'RECONCILED.json',
        calibration.ROOT/'REQUESTS.json',calibration.ROOT/'SOURCE.json',
        REPO/'docs/design/stage-15/week4/AUTH_MAIN.md',REPO/'tests/test_week4_auth_main.py',budget.APPROVAL,budget.PACKET}
    freeze(ROOT/'REQUESTS.json',rows);freeze(ROOT/'PRIVATE_JOIN.json',joins)
    cpu=time.process_time()-started
    if cpu>30:raise ValueError('preparation overhead ceiling')
    result=dict(main_items=3800,excluded_calibration_items=200,reused_calibration_items=0,
        creative_items=2000,argumentative_items=1800,original_items=4000,
        cpu_interface_allocation_seconds=180,cpu_charged_to='FIC1',
        fic1_cumulative_charged_and_reserved_seconds=4673.59375,fic1_original_ceiling_seconds=7200,
        preparation_cpu_seconds=cpu,scientific_admission=False)
    freeze(ROOT/'SOURCE.json',dict(result,pins={str(path):filehash(path) for path in paths},
        prepared={n:filehash(ROOT/n) for n in ('REQUESTS.json','PRIVATE_JOIN.json')}))
    check_sources()
    return result


def check_sources():
    admitted();s=read(ROOT/'SOURCE.json')
    for path,h in s['pins'].items():
        if filehash(path)!=h:raise ValueError('frozen main source changed')
    for n,h in s['prepared'].items():
        if filehash(ROOT/n)!=h:raise ValueError('prepared main source changed')
    rows,joins,_=rebuild()
    if read(ROOT/'REQUESTS.json')!=rows or read(ROOT/'PRIVATE_JOIN.json')!=joins:
        raise ValueError('main reconstruction')
    return s


def selected(phase):
    if phase!=PHASE:raise ValueError('other phase blocked')
    rows=read(ROOT/'REQUESTS.json')
    if len(rows)!=3800 or len({r['custom_id'] for r in rows})!=3800:raise ValueError('full main coverage')
    for r in rows:
        texts=json.loads(r['params']['messages'][0]['content'])
        if set(texts)!={'text_a','text_b'}:raise ValueError('foreign request metadata')
        expected=calibration.params([texts['text_a'],texts['text_b']])
        if r['item_id']!=digest(sorted(texts.values())) or r['params']!=expected or r['custom_id']!=digest(['AUTH',1,r['item_id'],expected]):
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
        if time.time()>=budget.CUTOFF or time.monotonic()-started>10800 or time.process_time()-cpu>120:
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
    plan = dict(at=time.time(), phase=phase, node='AUTH', attempted=len(rows),
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
    if (plan.get('node'),plan.get('phase'),plan.get('attempted'))!=('AUTH',phase,len(rows)):
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
    reservation = budget.reserve('week4-AUTH-main-' + phase, 'AUTH', plan['reserved_cents'], filehash(folder / 'PLAN.json'))
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
    return calibration.parse(message)


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
        format_passes=len(labels) == len(rows), complete_main_corpus=len(labels) == len(rows),reused_calibration_items=0,excluded_calibration_items=200,collection_assembled=False,
        node_calibration_complete=True, main_admission=False, scientific_admission=False,
        usage_complete=usage_complete, measured_token_cents=int(cost.to_integral_value(rounding=ROUND_CEILING)),
        results_sha256=filehash(folder / 'RESULTS.jsonl'))
    freeze(folder / 'LABELS.json', labels)
    # Private accounting receipt precedes COMPLETE so a completion wake sees settlement.
    freeze(folder / 'FORMAT_RECEIPT.json', receipt)
    if usage_complete:
        proof = {n: filehash(folder / n) for n in ('RESULTS.jsonl', 'STATUS.json', 'SUBMITTED.json', 'FORMAT_RECEIPT.json')}
        budget.reconcile('week4-AUTH-main-' + phase, receipt['measured_token_cents'], digest(proof))
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
