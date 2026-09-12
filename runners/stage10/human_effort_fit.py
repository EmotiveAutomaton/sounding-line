"""Fit human effort only after complete, source-bound development predictions.

DESIGN CHECK: LESSONS3-5. Under NULL or insufficient writer support the existing
selector admits no extra route; consistent supported improvement can admit one.
Only frozen development outcomes enter fit. Incomplete producers, wrong joins,
changed source evidence and changed saved policy refuse. Evaluation stays closed.
"""
from __future__ import annotations
import argparse
import hashlib
import time
from pathlib import Path
from unittest.mock import patch
from . import effort, human_effort_queue as queue, human_effort_readers as readers
from .contracts import digest
from .ollama import now, write_new
from .queue import read


def fit(prepared, training, producer, output, pilot):
    start = time.perf_counter()
    if not (producer/'COMPLETE.json').is_file():
        raise ValueError('development producer must complete before label access')
    with patch.object(readers.ollama, 'api', side_effect=AssertionError('fit cannot infer')), \
         patch.object(readers.programs, 'evaluate', side_effect=AssertionError('fit cannot execute')):
        complete = queue.run(prepared, training, producer, 'development', pilot)
    frozen = read(prepared/'FROZEN.json')
    public = read(prepared/'development-public.json')
    labels = read(prepared/'development-evaluator.json')
    if digest(public) != frozen['public_sha256']['development'] or digest(labels) != frozen['evaluator_sha256']['development']:
        raise ValueError('original development input changed')
    targets = {r['task_id']: r for r in labels['targets']}
    if len(targets) != len(labels['targets']) or set(targets) != {r['task_id'] for r in public['tasks']}:
        raise ValueError('development outcome join not unique or complete')
    rows = []; events = set(); groups = set(); seen = set()
    for task in public['tasks']:
        label = targets[task['task_id']]
        group = label.get('writer_component'); event = label.get('source_event')
        if not isinstance(group, str) or not group or not isinstance(event, str) or not event:
            raise ValueError('original writer and event identity required')
        key = (event, task['evidence_view'])
        if key in seen:
            raise ValueError('duplicate event/view cannot add fitting support')
        seen.add(key); groups.add(group); events.add(event)
        routes = {arm: read(producer/'attempts'/task['task_id']/arm/'BUDGET_ATTEMPT.json')['result'] for arm in ('R0', 'R1', 'R3')}
        rows.append({'task': task, 'group': group, 'truth': label['correct_choice'], 'routes': routes})
    manifest = {'sources': queue.identity(), 'fitter_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'frozen_sha256': digest(frozen), 'producer_sha256': digest(complete),
                'development_public_sha256': digest(public), 'development_evaluator_sha256': digest(labels)}
    bundle = {'schema': 'stage10.effort-development.1', 'phase': 'development', 'complete': True,
              'producers': {'original-complete': digest(complete), 'original-development-outcomes': digest(labels)}, 'rows': rows}
    policy = effort.fit(bundle)
    if (output/'COMPLETE.json').exists():
        saved = read(output/'COMPLETE.json')
        if read(output/'MANIFEST.json') != manifest or read(output/'DEVELOPMENT.json') != bundle or read(output/'POLICY.json') != policy or saved['policy_sha256'] != policy['policy_sha256'] or saved['manifest_sha256'] != digest(manifest):
            raise ValueError('saved human policy fit does not reproduce')
        return saved
    output.mkdir(parents=True, exist_ok=False)
    write_new(output/'MANIFEST.json', manifest)
    write_new(output/'DEVELOPMENT.json', bundle)
    write_new(output/'POLICY.json', policy)
    result = {'at': now(), 'status': 'FITTED', 'policy_sha256': policy['policy_sha256'], 'manifest_sha256': digest(manifest),
              'fit_tasks': len(rows), 'fit_events': len(events), 'fit_writer_components': len(groups),
              'admitted_strata_routes': sum(c['admitted'] for c in policy['policy']['cells']),
              'evaluation_outcomes_opened': False, 'producer_replay_new_calls': 0, 'producer_replay_new_executions': 0,
              'fit_wall_seconds': time.perf_counter()-start,
              'scope': 'development-fitted heuristic; one-writer strata cannot admit a learned route; evaluation benefit untested'}
    write_new(output/'COMPLETE.json', result)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('prepared', 'training', 'producer', 'output', 'pilot'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    try:
        fit(a.prepared, a.training, a.producer, a.output, a.pilot)
    except Exception as exc:
        if not (a.output/'FAILED.json').exists():
            write_new(a.output/'FAILED.json', {'at': now(), 'error': repr(exc)})
        raise
