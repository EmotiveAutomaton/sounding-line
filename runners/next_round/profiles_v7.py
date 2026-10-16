"""R3 array-only compatibility repair v7, using the existing Gear 3 campaign guard API.

DESIGN CHECK: LESSONS 3-5. NULL: invalid, duplicate, truncated, empty or
unsupported profiles do not admit a main. ALTERNATIVE: all discarded-pilot
profiles pass the literal schema and evidence-index checks. Neither outcome
admits a predictive feature or human-value claim. Full cost is reserved through
runners.gear3's locked ledger before the only POST; uncertain POST never retries.
"""
import argparse
import json
import re
import time
from decimal import Decimal, ROUND_CEILING
from pathlib import Path

from runners.stage14.common import REPO, read, freeze, atomic, digest, filehash, check_pins
from runners.stage14_midweek import api, budget
from runners.stage14_midweek.data import RAW as OLD_RAW, render_history, key

from runners.next_round import profiles as original

ROOT = REPO / 'results/phase_2_4_stage_15/raw/r3-profiles-v7'
# Original parser retained. Array constraints remain; no provider string pattern.
# Empty/whitespace statements still fail the unchanged full-response validator.
# LESSONS 3-5 reread 2026-10-15; actual generation still gates provider readiness.
from copy import deepcopy
from runners.next_round import profiles_v4 as prior
SCHEMA = original.SCHEMA
SYSTEM = prior.SYSTEM.split('Schema: ', 1)[0] + (
    'Copy evidence_indices from the displayed record_index fields exactly. '
    'The first record is 0. Do not count records starting from 1, renumber them, '
    'or cite a record not present. Every reference must be in the schema enum. ')
CANARY_RECORDS = 32


def schema_for(count):
    if type(count) is not int or not 1 <= count <= CANARY_RECORDS:
        raise ValueError('history cardinality exceeds tested reference grammar')
    schema = deepcopy(SCHEMA)
    schema['properties']['preferences']['items']['properties']['evidence_indices']['items']['enum'] = list(range(count))
    schema['properties']['preferences']['minItems'] = 1
    fields = schema['properties']['preferences']['items']['properties']
    fields['evidence_indices']['minItems'] = 1
    return schema


def rows_for(phase):
    if phase not in ('canary', 'pilot', 'main'):
        raise ValueError('unknown phase')
    if phase == 'canary':
        history = [dict(prompt='synthetic', draft_end=f'A fictional fox waited at gate {i}.',
                        menu=['The fox left.', 'The fox stayed.'], decision='accept',
                        inserted='The fox stayed.') for i in range(CANARY_RECORDS)]
        rows = [dict(custom_id=key('s15-r3-v7', 'synthetic-canary'), writer='synthetic',
                     arm='canary', reader='RS', history_records=len(history), evidence_sha256=digest(history),
                     params=dict(model=api.MODELS['RS'], max_tokens=1500, thinking={'type':'between_tools'},
                                 output_config={'effort':'low'}, messages=[{'role':'user','content':json.dumps({'history':history},ensure_ascii=False)}]))]
    else:
        rows = deepcopy(prior.rows_for(phase))
    for row in rows:
        if phase != 'canary': row['custom_id'] = key('s15-r3-v7', row['writer'], row['arm'])
        history = json.loads(row['params']['messages'][0]['content'])['history']
        assert digest(history) == row['evidence_sha256']
        if any('record_index' in record for record in history):
            raise ValueError('source field collision')
        indexed = [dict(record_index=i, **record) for i, record in enumerate(history)]
        schema = schema_for(len(history))
        row['params']['messages'] = [{'role':'user','content':json.dumps({'history':indexed},ensure_ascii=False)}]
        row['params']['system'] = SYSTEM + 'Schema: ' + json.dumps(schema)
        row['params']['output_config']['format'] = {'type':'json_schema','schema':schema}
        api._assert_no_tools(**row['params'])
    return rows


# Reuse the exact originally commissioned acceptance rule; no decoder regex.
strict_json = original.strict_json
parse = original.parse


def admit_prior(phase):
    if phase not in ('canary', 'pilot', 'main'):
        raise ValueError('unknown phase')
    if phase == 'canary':
        return
    prior, expected = ('canary', 1) if phase == 'pilot' else ('pilot', 6)
    gate = replay(prior)
    landing = read(ROOT/prior/'LANDED.json')
    if gate['attempted'] != expected or gate['valid'] != expected or not gate['usage_complete'] or not landing['full_write_through']:
        raise ValueError('fully landed all-valid prerequisite required before any egress')
    if landing['complete_sha256'] != filehash(ROOT/prior/'COMPLETE.json'):
        raise ValueError('changed prerequisite terminal')
    if not landing.get('verification_pins') or not landing.get('write_through_pins'):
        raise ValueError('independent verification and write-through bindings required')
    check_pins(landing['verification_pins'])
    check_pins(landing['write_through_pins'])


def prepare(phase):
    admit_prior(phase)
    folder = ROOT / phase
    if folder.exists():
        raise ValueError('existing attempt; inspect, do not repeat')
    rows = rows_for(phase)
    access = json.loads(api.request('/v1/models/' + api.MODELS['RS']))
    if access['id'] != api.MODELS['RS']:
        raise ValueError('model access mismatch')
    counts = {r['custom_id']: json.loads(api.request('/v1/messages/count_tokens',
              {k: v for k, v in r['params'].items() if k != 'max_tokens'}))['input_tokens'] for r in rows}
    for name, data in [('REQUESTS', rows), ('COUNTS', counts), ('ACCESS', access)]:
        freeze(folder / (name + '.json'), data)
    files = [Path(__file__), Path(__file__).with_name('profile_supervisor_v7.py'),
             REPO/'docs/design/stage-15/R3_ARRAY_COMPATIBILITY_V7.md',
             REPO/'tests/test_next_round_profiles_v7.py',
             REPO/'runners/next_round/profiles.py', REPO/'runners/next_round/profiles_v2.py',
             REPO/'runners/next_round/profiles_v3.py', REPO/'runners/next_round/profiles_v4.py',
             REPO/'runners/next_round/profiles_v5.py', REPO/'runners/next_round/profiles_v6.py',
             REPO/'results/phase_2_4_stage_15/raw/r3-profiles-v6/canary/COMPLETE.json',
             REPO/'results/phase_2_4_stage_15/raw/r3-profiles-v6/canary/LANDED.json',
             REPO/'results/phase_2_4_stage_15/raw/r3-profiles-v6/canary/INDEPENDENT_VERIFICATION.json',
             REPO/'results/phase_2_4_stage_15/raw/r3-profiles-v5/main/COMPLETE.json',
             REPO/'results/phase_2_4_stage_15/raw/r3-profiles-v5/main/LANDED.json',
             REPO/'results/phase_2_4_stage_15/raw/r3-profiles-v5/main/INDEPENDENT_VERIFICATION.json',
             REPO/'results/phase_2_4_stage_15/raw/r3-profiles-v4/pilot/COMPLETE.json',
             REPO/'results/phase_2_4_stage_15/raw/r3-profiles-v3/canary/COMPLETE.json',
             REPO/'results/phase_2_4_stage_15/raw/r3-profiles-v2/pilot/COMPLETE.json',
             REPO/'results/phase_2_4_stage_15/raw/r3-profiles-v1/pilot/COMPLETE.json', REPO/'runners/gear3.py', REPO/'runners/stage14/common.py',
             * (REPO/'runners/stage14_midweek').glob('*.py'),
             * (OLD_RAW/'data-v2').glob('*.json'), budget.ROOT/'APPROVAL.json',
             folder/'REQUESTS.json', folder/'COUNTS.json', folder/'ACCESS.json']
    plan = dict(phase=phase, at=time.time(), requests=len(rows), reserved_cents=api.ceiling(rows, counts),
                request_digest=digest(rows), source_pins={p.relative_to(REPO).as_posix(): filehash(p) for p in files},
                batch_rates_usd_per_million={'input': 1, 'output': 5}, max_seconds=86400,
                pricing_source='https://platform.claude.com/docs/en/about-claude/pricing',
                authority='October 15 curator explicitly authorizes Gear 3 healing; existing R3 tranche',
                schema_version='r3-array-only-profiles-v7', prior_attempt_preserved=True,
                scientific_admission=False, automatic_main=False, automatic_resubmission=False)
    freeze(folder/'PLAN.json', plan)
    return plan


def validate_plan(folder):
    plan = read(folder/'PLAN.json')
    check_pins(plan['source_pins'])
    if digest(read(folder/'REQUESTS.json')) != plan['request_digest']:
        raise ValueError('request digest changed')
    return plan


def submit(phase):
    folder = ROOT/phase
    plan = validate_plan(folder)
    if not 0 <= time.time() - plan['at'] < 86400:
        raise ValueError('stale preparation')
    if any((folder/n).exists() for n in ('RESERVATION.json', 'SUBMITTED.json', 'UNKNOWN.json')):
        raise ValueError('attempt already reserved; no resubmission')
    admit_prior(phase)
    rows = read(folder/'REQUESTS.json')
    wire = {'requests': [{k: r[k] for k in ('custom_id', 'params')} for r in rows]}
    freeze(folder/'WIRE.json', wire)
    # Canonical Gear 3 locked ledger and unchanged campaign/node/duplicate guards.
    reservation = budget.reserve('api-s15-r3-'+phase+'-v7', 'P' if phase in ('pilot', 'canary') else 'M-API',
                                 plan['reserved_cents'], digest(plan), plan['max_seconds'])
    freeze(folder/'RESERVATION.json', reservation)
    try:
        raw = api.request('/v1/messages/batches', wire)
        (folder/'SUBMIT_RESPONSE.json').write_bytes(raw)
        batch = json.loads(raw)
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', batch['id']):
            raise ValueError('invalid batch identity')
        freeze(folder/'SUBMITTED.json', dict(status='SUBMITTED', batch_id=batch['id'], at=time.time(),
                                            reservation_sha256=filehash(folder/'RESERVATION.json')))
    except BaseException as exc:
        freeze(folder/'UNKNOWN.json', dict(status='UNKNOWN', error_type=type(exc).__name__, reservation_retained=True))
        raise


def replay(phase):
    folder = ROOT/phase
    validate_plan(folder)
    reqs = read(folder/'REQUESTS.json')
    rows = [strict_json(s) for s in (folder/'RESULTS.jsonl').read_text(encoding='utf8').splitlines()]
    by = {r['custom_id']: r for r in rows}
    if len(by) != len(rows) or set(by) != {r['custom_id'] for r in reqs}:
        raise ValueError('result coverage')
    profiles, errors = {}, {}
    cost = Decimal(0)
    usage_complete = True
    for req in reqs:
        result = by[req['custom_id']]['result']
        if result['type'] != 'succeeded':
            usage_complete = False
            errors[req['custom_id']] = result['type']
            continue
        msg = result['message']
        if msg['model'] != req['params']['model']:
            raise ValueError('model substitution')
        usage = msg['usage']
        if any(type(usage.get(k)) != int or usage[k] < 0 for k in ('input_tokens', 'output_tokens')):
            raise ValueError('invalid token accounting')
        if usage.get('cache_creation_input_tokens', 0) or usage.get('cache_read_input_tokens', 0):
            usage_complete = False
        cost += (Decimal(usage['input_tokens']) + Decimal(5)*usage['output_tokens'])/10000
        try:
            profiles[req['custom_id']] = parse(msg, req['history_records'])
        except (ValueError, KeyError, TypeError) as exc:
            errors[req['custom_id']] = str(exc)
    freeze(folder/'PROFILES.json', profiles)
    freeze(folder/'VALIDATION.json', dict(errors=errors, semantic_faithfulness_not_established=True))
    receipt = dict(status='COMPLETE', attempted=len(reqs), valid=len(profiles),
                   usage_complete=usage_complete, measured_token_cents=int(cost.to_integral_value(rounding=ROUND_CEILING)),
                   results_sha256=filehash(folder/'RESULTS.jsonl'), scientific_admission=False,
                   role='candidate features only; format admission is not predictive validation')
    freeze(folder/'COMPLETE.json', receipt)
    return receipt


def retrieve(phase):
    folder = ROOT/phase
    batch = read(folder/'SUBMITTED.json')['batch_id']
    status = json.loads(api.request('/v1/messages/batches/'+batch))
    if status['id'] != batch:
        raise ValueError('batch identity changed')
    atomic(folder/'STATUS.json', status)
    if status['processing_status'] != 'ended':
        return {'status': status['processing_status']}
    if not (folder/'RESULTS.jsonl').exists():
        (folder/'RESULTS.jsonl').write_bytes(api.request('/v1/messages/batches/'+batch+'/results'))
    return replay(phase)


def reconcile(phase):
    folder = ROOT/phase
    receipt = replay(phase)
    status = read(folder/'STATUS.json')
    if status['processing_status'] != 'ended' or status['id'] != read(folder/'SUBMITTED.json')['batch_id']:
        raise ValueError('ended identity required')
    if not receipt['usage_complete']:
        return {'status': 'RESERVATION_RETAINED'}
    proof = {n: filehash(folder/n) for n in ('STATUS.json', 'SUBMITTED.json', 'RESULTS.jsonl', 'COMPLETE.json')}
    budget.reconcile_tokens('api-s15-r3-'+phase+'-v7', receipt['measured_token_cents'], digest(proof))
    freeze(folder/'RECONCILED.json', dict(proof=proof, booked_cents=receipt['measured_token_cents']))
    return {'status': 'RECONCILED', 'cents': receipt['measured_token_cents']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'submit', 'retrieve', 'replay', 'reconcile'])
    parser.add_argument('phase', choices=['canary', 'pilot', 'main'])
    args = parser.parse_args()
    result = globals()[args.action](args.phase)
    print(json.dumps(result))
