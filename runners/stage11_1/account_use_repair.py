"""Bounded valid-account diagnostic after L398; no change to frozen producers.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-6 read for this design.
NULL: identical retained inputs may vary; movement alone cannot establish use.
ALTERNATIVE: removal/replacement contrasts exceed contemporaneous repeat movement
and improve independently witnessed targets. Report both without a fitted threshold
or significance claim. Invalid/empty sources, same-writer donors, changed evidence,
duplicate tasks, context overflow and incomplete cells fail closed before scoring.
This reuses one account variant, selected on mechanical validity, never accuracy.
"""
import argparse
import copy
import hashlib
import subprocess
import sys
from collections import Counter
from pathlib import Path

from .common import PRIVATE, read, freeze, digest, contract, allocation
from . import branch_runtime as br, run_v3b as base, models_v3 as model, preflight

JOB = 'S1-account-initial-v3b'
NAME = 'S1-account-use-repair-v1'


def source(root, row, view):
    path = root/'calls'/JOB/row['key']/view/'account'/'0'
    if not (path/'ATTEMPT.json').exists():
        raise ValueError('missing original account; preparation cannot dispatch')
    result = base.call(path, row['views'][view], 'account', 'S1', threads=4,
                       fake=br.fake_from(read(root/'jobs'/JOB/'COMPLETE.json')))
    return result['forecast']


def tasks_for(root, units, donors):
    tasks = []
    for row, view in units:
        modes = ['remove', 'replace']
        if int(digest(row['views'][view])[:8], 16) % 2:
            modes.reverse()
        for label in ['keep-a', *modes, 'keep-b']:
            mode = label if label in modes else 'retain'
            donor = donors[(row['key'], view)] if mode == 'replace' else row
            task = preflight.forecast(row, 'account-'+label+'-'+view, 'account',
                public=row['views'][view], account_ref=dict(job=JOB,
                key=donor['key'], view=view, mode=mode))
            evidence, intermediate = br.public_for(task, {}, root)
            assert evidence == row['views'][view]
            assert mode in ('retain', 'remove', 'replace')
            request = model.request_for(evidence, 'account_predict', intermediate, 4)
            original = root/'calls'/JOB/row['key']/view/'account'/'1/REQUEST.json'
            if mode == 'retain':
                assert request == read(original)['request']
            elif mode == 'remove':
                assert intermediate == {'events': []}
            else:
                assert donor['writer'] != row['writer']
                # Validate remapped donor graph against recipient anchors too.
                model.parse(dict(done=True, done_reason='stop',
                    message=dict(content=br.canonical(intermediate))), evidence, 'account')
            tasks.append(task)
    return tasks


def prepare(root=PRIVATE):
    terminal = read(root/'jobs'/JOB/'COMPLETE.json')
    assert terminal['status'] == 'COMPLETE' and not terminal.get('fake')
    cohort = read(root/'COHORT-v3.json')
    keys = read(root/'plans/S1-account-initial-v3b-only.json')['jobs'][0]['keys']
    rows = {r['key']: r for lane in cohort.values() for r in lane}
    units = []; excluded = []; donors = {}
    for key in keys:
        for view in ('artifact', 'alternatives'):
            value = source(root, rows[key], view)
            if value is not None and value['events']:
                units.append((rows[key], view))
            else:
                excluded.append(dict(key=key, view=view, reason='invalid or empty original account'))
    for row, view in units:
        candidates = [r for r, v in units if v == view and r['writer'] != row['writer']]
        candidates.sort(key=lambda r: digest([row['key'], view, r['key']]))
        donor = next(iter(candidates), None)
        if donor is None:
            raise ValueError('no valid different-writer donor')
        donors[(row['key'], view)] = donor
    tasks = tasks_for(root, units, donors)
    # No identical replacement payloads are admitted in the real diagnostic.
    for i in range(0, len(tasks), 4):
        own = br.public_for(tasks[i], {}, root)[1]
        replacement = next(t for t in tasks[i:i+4] if t['account_ref']['mode'] == 'replace')
        assert br.public_for(replacement, {}, root)[1] != own
    plan = preflight.plan(NAME, 'S1', tasks,
        'Separate valid-account intervention movement from contemporaneous request-repeat variation',
        'Mechanical-validity-selected descriptive diagnostic on exposed human records; no human-mechanism or fresh-confirmation claim',
        'Land complete keep/remove/replace matrix with repeat variability and accuracy together; retain original L398 and all charges',
        ['ACCOUNT_PILOT_PASSED-v3.json'],
        source_job=JOB, excluded=excluded,
        recipe='All valid nonempty original case/view accounts; other-writer same-view valid donor chosen by fixed hash; own A, hash-ordered interventions, own B',
        primary='Within each view compare each treatment with the arithmetic mean of the two keep-arm summary metrics; display keep A versus B movement beside both treatment-versus-keep transitions. Original baseline is secondary. Do not average probabilities, pool views, fit a noise threshold or infer mechanism from movement alone.',
        preparation_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    freeze(root/'branch_plans'/f'{NAME}.json', plan)
    return dict(status='PREPARED', plan_digest=digest(plan), case_views=len(units),
        unique_episodes=len({r['key'] for r,v in units}), writers=len({r['writer'] for r,v in units}),
        per_view=dict(Counter(v for r,v in units)), excluded_case_views=len(excluded),
        maximum_calls=len(tasks), exact_own_requests_checked=2*len(units),
        valid_other_writer_replacements=len(units), sources=br.sources(),
        preparation_source_sha256=plan['preparation_source_sha256'])


def rehearse(root):
    if root.exists():
        raise ValueError('choose a new scratch namespace; preserve previous rehearsal')
    contract(root); allocation(root)
    cohort = read(PRIVATE/'COHORT-v3.json')
    freeze(root/'COHORT-v3.json', cohort)
    freeze(root/'CHEAP_FIT.json', read(PRIVATE/'CHEAP_FIT.json'))
    gate = dict(status='COMPLETE', fake=True, sources=base.source_pin())
    freeze(root/'ACCOUNT_PILOT_PASSED-v3.json', gate)
    plan = copy.deepcopy(read(PRIVATE/'plans/S1-account-initial-v3b-only.json'))
    job = plan['jobs'][0]
    lookup = {r['key']:r for lane in cohort.values() for r in lane}
    first = lookup[job['keys'][0]]
    second = next(lookup[k] for k in job['keys'] if lookup[k]['writer'] != first['writer'])
    job['keys'] = [first['key'], second['key']]
    freeze(root/plan['cohort_file'], read(PRIVATE/plan['cohort_file']))
    freeze(root/'source-plan.json', plan)
    base.execute(root, root/'source-plan.json', fake=True)
    units = [(r,v) for r in (first,second) for v in ('artifact','alternatives')]
    donors = {(r['key'],v):second if r==first else first for r,v in units}
    tasks = tasks_for(root, units, donors)
    p = preflight.plan(NAME, 'S1', tasks, 'scratch routes', 'fake empty accounts only', 'retain scratch')
    freeze(root/'repair.json', p)
    manifest = dict(id='repair-smoke', gear=2, items=[dict(id=NAME,
        runner='branch', path='repair.json', digest=digest(p), calls=len(tasks),
        requires=['ACCOUNT_PILOT_PASSED-v3.json'], next_action='retain scratch')])
    freeze(root/'QUEUE.json', manifest)
    command = [sys.executable,'-B','-m','runners.stage11_1.continuation',str(root/'QUEUE.json'),'--root',str(root),'--fake']
    before = None
    for label in ('first','reentry'):
        result = subprocess.run(command, capture_output=True, text=True, timeout=180)
        (root/(label+'.stderr')).write_text(result.stderr, encoding='utf-8')
        assert result.returncode == 0, result.stderr
        current = base.budget(root)
        if before is not None: assert before == current
        before = current
    _, output = br.execute(root,root/'repair.json',fake=True,replay_only=True)
    scores = [br.episode(t['evaluator'],output[t['id']]['forecast']) for t in tasks[:4]]
    null = br.paired_transitions([scores[0]],[scores[3]])
    assert null['forecast_moved_per_episode']==0 and null['useful_change_per_episode']==0
    known = copy.deepcopy(scores[0]); wrong = copy.deepcopy(known)
    for fact in known['facts']:
        for value in fact['scores'].values(): value['accuracy']=1
    for fact in wrong['facts']:
        for value in fact['scores'].values(): value['accuracy']=0
    assert br.paired_transitions([wrong],[known])['corrected_per_episode']==6
    assert br.paired_transitions([known],[wrong])['new_errors_per_episode']==6
    result = dict(status='PASS', fake_attempts=before['attempts'],
        repair_fake_calls=len(tasks), source_fake_calls=8, no_call_reentry=True,
        null_and_known_transition_checks=True, real_requests_validated_separately=True,
        scope='Literal existing CLI routes and cost replay with fake empty accounts; real nonempty graph/remapping/request checks are separate', sources=br.sources())
    freeze(root/'REHEARSAL.json',result)
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('command',choices=['prepare','rehearse'])
    parser.add_argument('--scratch',type=Path)
    args=parser.parse_args()
    print(br.canonical(prepare() if args.command=='prepare' else rehearse(args.scratch)))
