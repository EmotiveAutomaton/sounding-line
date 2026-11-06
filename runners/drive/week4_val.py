"""Week 4 explanation-only VAL calibration; no main or automatic correction.

DESIGN CHECK: LESSONS 3-5 reread November 5. NULL constant/unrelated codes
fail agreement; ALTERNATIVE exact known codes pass. Format >=98/100 and
pooled kappa >=.6 are exhaustive; undefined fails. Invalid replies stay in
the denominator as abstentions, never value labels. Foreign source, identities,
unsettled usage and changed pins refuse. No outcome selects the sample.
"""
import argparse
from collections import Counter
from decimal import Decimal, ROUND_CEILING
import gzip
import json
from pathlib import Path
import re
import time

from runners.stage14.common import REPO, atomic, digest, filehash, freeze, read
from runners.stage14_midweek.api import request
from runners.drive import budget_week4 as budget, week3_val as original
from runners.drive.cards.week3_values_inputs import choice_sample, deduplicate

ROOT = REPO/'results/phase_2_4_stage_15/raw/drive-week4-cloud-20261102/VAL'
PHASE = 'calibration'
MODEL = original.MODEL
VALUES = original.VALUES
OLD = REPO/'results/phase_2_4_stage_15/raw/drive-week3-20261025/VAL-inputs'
SAMPLE = REPO/'results/phase_2_4_stage_15/raw/drive-week4-20261102/CA1.s1-inputs'
TERMINALS = {
    OLD:'40f4d9ce4b33214417debb91d6030394599f38d48cf61e525edb6e982c70b8b2',
    SAMPLE:'9f38412e9af9e2fe9adc8c6f74eb9ea4210ba48ced659a5e4f065db139d29df8'}
INVOCATION = 'week4-VAL-calibration'


def restricted(items, joins, population, membership, comparisons):
    people = membership['selected']
    if len(set(people)) != len(people) or not set(membership['mandatory']) <= set(people):
        raise ValueError('membership identity')
    chosen, census = choice_sample(comparisons, people)
    expected_items, expected_joins = deduplicate(chosen)
    kept = {k:[j for j in links if j['kind']=='choice-explanation' and j['writer'] in set(people)]
            for k,links in joins.items()}
    kept = {k:v for k,v in kept.items() if v}
    subset = [i for i in items if i['item_id'] in kept]
    if subset != expected_items or kept != expected_joins:
        raise ValueError('frozen Week 3 text, sample or private joins differ')
    prior_census = [c for c in population['choice'] if c['writer'] in set(people)]
    if prior_census != census:
        raise ValueError('complete person census differs')
    if len(subset)<200:
        raise ValueError('fresh calibration support')
    return subset, kept, dict(choice=census, membership=membership)


def rebuild():
    paths = set()
    names = {OLD:['ITEMS.json','PRIVATE_JOIN.json','PRIVATE_POPULATION.json'],
             SAMPLE:['PRIVATE_SAMPLE.json','COMPARISONS.jsonl.gz']}
    for root, sha in TERMINALS.items():
        terminal=root/'COMPLETE.json'
        if filehash(terminal)!=sha: raise ValueError('source terminal changed')
        completed=read(terminal)
        if completed['status']!='COMPLETE' or completed['fresh_process_verified'] is not True:
            raise ValueError('complete verified source required')
        paths.add(terminal)
        for name in names[root]:
            p=root/'output'/name
            if filehash(p)!=completed['outputs']['output/'+name]: raise ValueError('source artifact changed')
            paths.add(p)
    membership=read(SAMPLE/'output/PRIVATE_SAMPLE.json')
    if (len(membership['mandatory']),len(membership['random']),len(membership['selected']),membership['seed'])!=(836,200,1036,20261102):
        raise ValueError('approved sample differs')
    if set(membership['mandatory']) & set(membership['random']) or sorted(membership['mandatory']+membership['random'])!=membership['selected']:
        raise ValueError('sample partition differs')
    with gzip.open(SAMPLE/'output/COMPARISONS.jsonl.gz','rt',encoding='utf8') as f:
        comparisons=[json.loads(line) for line in f]
    values=restricted(read(OLD/'output/ITEMS.json'),read(OLD/'output/PRIVATE_JOIN.json'),
        read(OLD/'output/PRIVATE_POPULATION.json'),membership,comparisons)
    return values,paths


def prepare():
    started=time.process_time()
    if ROOT.exists(): raise ValueError('existing preparation; inspect')
    (items,joins,population),paths=rebuild()
    from runners.drive.week4_launch_v8 import closure
    paths |= closure(['runners.drive.week4_val','runners.drive.week4_val_monitor'])
    paths |= {budget.APPROVAL,budget.PACKET,REPO/'docs/design/stage-15/week4/VAL_CALIBRATION.md',REPO/'tests/test_week4_val.py'}
    rows=original.requests_for(items,0)
    freeze(ROOT/'REQUESTS.json',rows);freeze(ROOT/'PRIVATE_JOIN.json',joins)
    freeze(ROOT/'PRIVATE_POPULATION.json',population)
    freeze(ROOT/'CALIBRATION_VIEW.json',[dict(index=i,custom_id=r['custom_id'],text=items[i]['text']) for i,r in enumerate(rows[:100])])
    freeze(ROOT/'SELECTION.json',dict(calibration=[r['custom_id'] for r in rows[:100]],fresh=[r['custom_id'] for r in rows[100:200]]))
    cpu=time.process_time()-started
    if cpu>60: raise ValueError('source preparation exceeded overhead allocation')
    result=dict(requests=len(rows),people=len(population['choice']),mandatory_people=836,
        explanation_links=sum(len(v) for v in joins.values()),
        people_without_explanations=sum(c['selected_explanations']==0 for c in population['choice']),
        cpu_preparation_seconds=cpu,cpu_interface_allocation_seconds=300,cpu_charged_to='V2',
        scientific_admission=False,source_scope='Week 3 frozen public explanations restricted to CA1.s1')
    freeze(ROOT/'SOURCE.json',dict(result, pins={str(p):filehash(p) for p in paths},
        prepared={n:filehash(ROOT/n) for n in ['REQUESTS.json','PRIVATE_JOIN.json','PRIVATE_POPULATION.json','CALIBRATION_VIEW.json','SELECTION.json']}))
    check_sources();return result


def check_sources():
    s=read(ROOT/'SOURCE.json')
    for path,h in s['pins'].items():
        if filehash(path)!=h: raise ValueError('frozen source changed')
    for name,h in s['prepared'].items():
        if filehash(ROOT/name)!=h: raise ValueError('prepared artifact changed')
    return s


def selected(phase):
    if phase!=PHASE: raise ValueError('only initial calibration implemented')
    rows=read(ROOT/'REQUESTS.json')[:100]
    if len(rows)!=100 or [r['custom_id'] for r in rows]!=read(ROOT/'SELECTION.json')['calibration']:
        raise ValueError('complete fixed calibration required')
    for row in rows:
        p=original.params(json.loads(row['params']['messages'][0]['content'])['text'])
        if row['params']!=p or row['custom_id']!=digest(['VAL',0,row['item_id'],p]):
            raise ValueError('request reconstruction differs')
    return rows


def gold_check():
    gold=read(ROOT/'GOLD.json');rows=selected(PHASE)
    if gold.get('provenance')!='agent-made blind before provider access': raise ValueError('blind provenance')
    labels=gold['labels']
    if len(labels)!=100 or len({g['custom_id'] for g in labels})!=100 or {g['custom_id'] for g in labels}!={r['custom_id'] for r in rows}:
        raise ValueError('complete blind reference required')
    if any(not original.valid_label({k:g[k] for k in ('v','o')}) or not isinstance(g.get('rationale'),str) or not g['rationale'].strip() for g in labels):
        raise ValueError('blind code or rationale missing')
    return labels


def count(phase):
    check_sources();rows=selected(phase);gold_check();folder=ROOT/phase
    if (folder/'PLAN.json').exists():return preflight(phase)
    freeze(ROOT/'GOLD_FROZEN.json',dict(gold_sha256=filehash(ROOT/'GOLD.json')))
    access=json.loads(request('/v1/models/'+MODEL))
    if access.get('id')!=MODEL:raise ValueError('model identity')
    counts={}
    for r in rows:
        p=folder/'counts'/(r['custom_id']+'.json')
        if not p.exists():freeze(p,json.loads(request('/v1/messages/count_tokens',{k:v for k,v in r['params'].items() if k!='max_tokens'})))
        counts[r['custom_id']]=read(p)['input_tokens']
    freeze(folder/'COUNTS.json',counts);freeze(folder/'ACCESS.json',access)
    freeze(folder/'WIRE.json',dict(requests=[{k:r[k] for k in ('custom_id','params')} for r in rows]))
    paths=[ROOT/n for n in ['SOURCE.json','GOLD.json','GOLD_FROZEN.json']]+[folder/n for n in ['COUNTS.json','ACCESS.json','WIRE.json']]
    plan=dict(at=time.time(),node='VAL',phase=phase,attempted=100,reserved_cents=budget.ceiling(rows,counts),pins={str(p):filehash(p) for p in paths})
    freeze(folder/'PLAN.json',plan);return preflight(phase)


def bound_plan(phase):
    check_sources();rows=selected(phase);gold_check();folder=ROOT/phase;plan=read(folder/'PLAN.json')
    for p,h in plan['pins'].items():
        if filehash(p)!=h:raise ValueError('plan binding changed')
    if read(ROOT/'GOLD_FROZEN.json')['gold_sha256']!=filehash(ROOT/'GOLD.json'):raise ValueError('blind reference changed')
    if read(folder/'WIRE.json')!=dict(requests=[{k:r[k] for k in ('custom_id','params')} for r in rows]):raise ValueError('wire projection')
    if plan['reserved_cents']!=budget.ceiling(rows,read(folder/'COUNTS.json')):raise ValueError('budget ceiling changed')
    return plan


def preflight(phase):
    plan=bound_plan(phase)
    if not 0<=time.time()-plan['at']<=86400:raise ValueError('stale preflight')
    return plan


def submit(phase):
    plan=preflight(phase);folder=ROOT/phase
    if any((folder/n).exists() for n in ['RESERVATION.json','SUBMITTED.json','UNKNOWN.json']):raise ValueError('consumed identity; retrieve only')
    freeze(folder/'RESERVATION.json',budget.reserve(INVOCATION,'VAL',plan['reserved_cents'],filehash(folder/'PLAN.json')))
    try:
        raw=request('/v1/messages/batches',read(folder/'WIRE.json'))
        (folder/'SUBMIT_RESPONSE.json').write_bytes(raw);value=json.loads(raw)
        if not isinstance(value.get('id'),str) or not re.fullmatch(r'msgbatch_[A-Za-z0-9]+',value['id']):raise ValueError('batch identity')
        freeze(folder/'SUBMITTED.json',dict(batch_id=value['id'],at=time.time()))
        return dict(status='SUBMITTED',batch_id=value['id'],reserved_cents=plan['reserved_cents'])
    except BaseException as exc:
        freeze(folder/'UNKNOWN.json',dict(error_type=type(exc).__name__,reservation_retained=True));raise


def agreement(gold,labels):
    a=[[int(x) for x in g['v']]+[g['o']] for g in gold]
    b=[[int(x) for x in labels[g['custom_id']]['v']]+[labels[g['custom_id']]['o']]
       if g['custom_id'] in labels else [2]*11 for g in gold]
    pooled=original.kappa([v for r in a for v in r],[v for r in b for v in r]);per={}
    for j,name in enumerate(VALUES+('other',)):
        left,right=[r[j] for r in a],[r[j] for r in b];prev=sum(left)/len(left)
        per[name]=dict(gold_prevalence=prev,provider_positive_prevalence=sum(v==1 for v in right)/len(right),
            invalid=sum(v==2 for v in right),reportable=prev>=.05,kappa=original.kappa(left,right) if prev>=.05 else None)
    return dict(pooled_kappa=pooled,per_category=per,agreement_passes=pooled is not None and pooled>=.6,
        denominator=len(gold)*11,invalid_policy='distinct abstention in complete denominator; never a value label')


def replay(phase):
    bound_plan(phase);folder=ROOT/phase;rows=selected(phase);status=read(folder/'STATUS.json')
    if status['processing_status']!='ended' or status['id']!=read(folder/'SUBMITTED.json')['batch_id']:raise ValueError('ended exact batch required')
    results=[json.loads(x) for x in (folder/'RESULTS.jsonl').read_text(encoding='utf8').splitlines()]
    by={r['custom_id']:r for r in results}
    if len(by)!=len(results) or set(by)!={r['custom_id'] for r in rows}:raise ValueError('complete result coverage')
    labels={};cost=Decimal(0);usage_complete=True;tokens=Counter()
    for row in rows:
        result=by[row['custom_id']]['result']
        if result['type']!='succeeded':usage_complete=False;continue
        msg=result['message'];usage=msg['usage']
        if any(type(usage.get(k)) is not int or usage[k]<0 for k in ('input_tokens','output_tokens')):raise ValueError('invalid usage')
        if usage.get('cache_creation_input_tokens',0) or usage.get('cache_read_input_tokens',0):usage_complete=False
        tokens.update({k:usage[k] for k in ('input_tokens','output_tokens')})
        cost+=(Decimal('.05')*usage['input_tokens']+Decimal('.25')*usage['output_tokens'])/10000
        label=original.parse(msg)
        if label is not None:labels[row['custom_id']]=label
    stats=agreement(gold_check(),labels)
    receipt=dict(status='COMPLETE',phase=phase,attempted=100,valid=len(labels),format_passes=len(labels)>=98,
        passes=len(labels)>=98 and stats['agreement_passes'],**stats,usage_complete=usage_complete,
        measured_token_cents=int(cost.to_integral_value(rounding=ROUND_CEILING)),tokens=dict(tokens),
        scientific_admission=False,labeler='model compared with blind agent reference; not human gold',
        results_sha256=filehash(folder/'RESULTS.jsonl'))
    freeze(folder/'LABELS.json',labels);freeze(folder/'CALIBRATION_RECEIPT.json',receipt)
    if usage_complete:
        proof={n:filehash(folder/n) for n in ['RESULTS.jsonl','STATUS.json','SUBMITTED.json','CALIBRATION_RECEIPT.json']}
        budget.reconcile(INVOCATION,receipt['measured_token_cents'],digest(proof))
        freeze(folder/'RECONCILED.json',dict(booked_cents=receipt['measured_token_cents'],proof=proof))
    freeze(folder/'COMPLETE.json',receipt);return receipt


def retrieve(phase):
    folder=ROOT/phase
    if (folder/'COMPLETE.json').exists():return read(folder/'COMPLETE.json')
    check_sources();bid=read(folder/'SUBMITTED.json')['batch_id']
    status=json.loads(request('/v1/messages/batches/'+bid))
    if status.get('id')!=bid:raise ValueError('batch identity changed')
    atomic(folder/'STATUS.json',status)
    if status['processing_status']!='ended':return dict(status=status['processing_status'])
    p=folder/'RESULTS.jsonl'
    if not p.exists():p.write_bytes(request('/v1/messages/batches/'+bid+'/results'))
    return replay(phase)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','count','submit','retrieve','replay']);a=p.parse_args()
    result=prepare() if a.action=='prepare' else globals()[a.action](PHASE)
    print(json.dumps(result))
