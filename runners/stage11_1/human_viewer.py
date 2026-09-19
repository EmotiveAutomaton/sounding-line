"""Offline illustrations from complete, independently landed Stage 11.1 cells.

DESIGN CHECK: LESSONS 3-5 reread for this build. NULL: invalid or absent forecasts
remain visibly unavailable; changing a passage never conceals unlocated claims.
ALTERNATIVE: source-replayed facts and retained forecasts remain distinguishable,
and revealing evidence preserves the blind forecast. Refuse changed source,
incomplete cells, unsupported selection predicates or altered immutable outputs.
Outcome-selected illustrations establish no new performance estimate. No inference.
"""
import argparse
import copy
import hashlib
from pathlib import Path
from .common import PRIVATE, read, freeze, digest, canonical
from . import branch_runtime as br, run_v3b as runner
from .preflight import source_rows
from .targets import project, public, norm
from .score import episode
from .cheap import fit, predict

LABELS = ('accurate attribution', 'confident error', 'correction after context',
          'unresolved history', 'substantial human continuation', 'formatting-only change')


def predicates(row, forecasts, assisted):
    aligned = episode(row, forecasts['alternatives']['alignment'])
    blind = episode(row, forecasts['artifact']['account'])
    facts = row['target']['facts']
    correction = []
    for method, pair in assisted.items():
        before, after = [episode(row, pair[k]['forecast']) for k in ('blind', 'fixed')]
        for a, b in zip(before['facts'], after['facts']):
            # A valid but wrong operation becomes correct on this source episode.
            if a['scores']['operation']['choice'] not in ('invalid', 'unknown') and not a['scores']['operation']['accuracy'] and b['scores']['operation']['accuracy']:
                correction.append(dict(method=method, slot=a['slot']))
    continuation = next(f for f in facts if f['slot'] == 'continuation')
    text = ''.join(row['views']['artifact']['endpoint'][a:b] for a, b in continuation['exact_spans'])
    return {
        LABELS[0]: any(f['useful_positive_with_span'] for f in aligned['facts']),
        LABELS[1]: any(f['scores']['operation']['confidence'] >= .9 and not f['scores']['operation']['accuracy'] for f in blind['facts']),
        LABELS[2]: bool(correction),
        LABELS[3]: any(f['span_state'] == 'unlocated' and f['operation'] != 'absent' for f in facts),
        LABELS[4]: continuation['operation'] == 'insert' and len(norm(text)) >= 40,
        LABELS[5]: any(f['operation'] == 'format_edit' for f in facts),
    }, correction


def build(root=PRIVATE):
    if br.sources() != read(root/'GATES-CONTINUATION.json')['sources']:
        raise ValueError('scientific source pin changed')
    # The only executable model transport is disabled even on accidental misuse.
    def forbidden(*args, **kwargs):
        raise AssertionError('viewer cannot dispatch inference')
    br.api = runner.api = forbidden
    cohort = read(root/'COHORT-v3.json')
    cheap = fit(cohort['train'])
    path = root/'branch_plans/S2-evidence-review-account-v1.json'
    plan = read(path)
    assert read(root/'branch_jobs'/plan['id']/'COMPLETE.json')['status'] == 'COMPLETE'
    terminal, outputs = br.execute(root, path, replay_only=True)
    assisted = {}
    for task in plan['tasks']:
        if task['kind'] == 'forecast' and task['condition'] in ('human-blind', 'human-fixed'):
            assisted.setdefault(task['evaluator']['key'], {}).setdefault(task['method'], {})[task['condition'][6:]] = outputs[task['id']]
    candidates = []
    for row in cohort['discovery']:
        forecasts = {view: {} for view in ('artifact', 'alternatives')}
        accounts = {}
        for view in forecasts:
            forecasts[view]['alignment'] = predict(row['views'][view], cheap)[0]
            for method in ('direct', 'review', 'account'):
                job = f'S1-{method}-{row["tranche"]}-v3b'
                complete = read(root/'jobs'/job/'COMPLETE.json')
                assert complete['status'] == 'COMPLETE' and not complete['fake'] and complete['sources'] == runner.source_pin()
                folder = root/'calls'/job/row['key']/view/method
                last = '0' if method == 'direct' else '1'
                forecasts[view][method] = read(folder/last/'ATTEMPT.json')['forecast']
                if method == 'account':
                    accounts[view] = read(folder/'0'/'ATTEMPT.json')['forecast']
        pair = assisted.get(row['key'], {})
        flags, changes = predicates(row, forecasts, pair)
        candidates.append(dict(row=row, forecasts=forecasts, accounts=accounts, assisted=pair, flags=flags, changes=changes))
    selected = []; used = set(); writers = set(); selection = []
    # Scarce categories first; each category is selected twice when distinct support exists.
    counts = {label: sum(c['flags'][label] for c in candidates) for label in LABELS}
    for repeat in range(2):
        for label in sorted(LABELS, key=lambda x: (counts[x], LABELS.index(x))):
            available = [c for c in candidates if c['flags'][label] and c['row']['key'] not in used]
            if not available:
                selection.append(dict(category=label, round=repeat+1, disposition='no further distinct eligible illustration'))
                continue
            c = min(available, key=lambda c: (c['row']['writer'] in writers, digest(['S5-human-v1', label, c['row']['key']])))
            selected.append(c); used.add(c['row']['key']); writers.add(c['row']['writer'])
            selection.append(dict(category=label, round=repeat+1, key=c['row']['key'], disposition='selected'))
    if not 8 <= len(selected) <= 12 or not all(any(c['flags'][label] for c in selected) for label in LABELS):
        raise ValueError('illustration coverage not realized')
    sources = source_rows(root); cases = []
    for i, c in enumerate(selected):
        row = c['row']; lines, events = sources[row['session']]; event = events[row['ordinal']]
        assert project(event, lines) == row['target']
        assert all(public(event, view) == row['views'][view] for view in row['views'])
        for view in c['forecasts']:
            for method in ('direct', 'review', 'account'):
                job = read(root/'jobs'/f'S1-{method}-{row["tranche"]}-v3b'/'JOB.json')
                folder = root/'calls'/job['id']/row['key']/view/method
                assert all((folder/str(n)/'ATTEMPT.json').exists() for n in range(len(runner.chain(method))))
                state, parts = runner.execute_block(root, job, row, view, method)
                assert state == 'COMPLETE' and parts[-1]['forecast'] == c['forecasts'][view][method]
                if method == 'account':
                    assert parts[0]['forecast'] == c['accounts'][view]
        fixed = {m: dict(blind=v['blind']['forecast'], after=v['fixed']['forecast'], evidence=v['fixed']['evidence']) for m, v in c['assisted'].items()}
        cases.append(dict(name=f'Illustration {i+1:02d}', key=row['key'], categories=[k for k,v in c['flags'].items() if v],
                          views=row['views'], forecasts=c['forecasts'], accounts=c['accounts'], assisted=fixed,
                          observed=row['target'], correction_examples=c['changes']))
    data = dict(scope='Outcome-selected human illustrations from completed, exposed CoAuthor records. These cases are not a benchmark. No human contribution percentage is estimated.',
                selection_rule='Two rounds over six categories, scarce categories first. Prefer a new writer, then a fixed digest order. Never reuse an episode. Accurate means a correctly located positive alignment claim; confident error means an account operation at >= .9 is wrong; correction means valid wrong operation becomes right in a fresh fixed-before chain; unresolved means a witnessed event has no surviving location; substantial continuation means at least 40 alphanumeric characters, not importance; formatting follows the frozen target rule.',
                cases=cases)
    selection_record = dict(status='PASS', scope=data['scope'], rule=data['selection_rule'], pool=len(candidates), available_by_category=counts,
                            selection=selection, cases=len(cases), writers=len(writers), source_replays=len(cases),
                            cohort_digest=digest(cohort), evidence_plan_digest=digest(plan), evidence_terminal_digest=digest(terminal),
                            sources=br.sources(), no_model_calls=True, data_digest=digest(data))
    freeze(root/'S5/HUMAN-SELECTION-v1.json', selection_record)
    freeze(root/'S5/HUMAN-CASES-v1.json', data)
    template = Path(__file__).with_name('human_viewer.html').read_text(encoding='utf-8')
    html = template.replace('__DATA__', canonical(data).replace('<', '\\u003c'))
    output = root/'S5/contribution-map-human-v1.html'
    if output.exists() and output.read_text(encoding='utf-8') != html:
        raise ValueError('immutable human viewer changed')
    output.write_text(html, encoding='utf-8', newline='\n')
    return dict(status='PASS', cases=len(cases), writers=len(writers), categories=counts, source_replays=len(cases), no_model_calls=True,
                html_sha256=hashlib.sha256(output.read_bytes()).hexdigest(), selection_digest=digest(selection_record), path=str(output))


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=PRIVATE)
    print(canonical(build(p.parse_args().root)))
