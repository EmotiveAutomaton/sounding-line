"""B03 read-only lineage and saved-call audit for four explicit human-data readers.

DESIGN CHECK: B03/H01/H02/H03/H06/H07/H08/X01/X02/X05/X06/X12;
LESSONS 3--5, CONTROLS 6--7. NULL: another source/fit/lane, altered training
allocation, a cache disconnected from actual capsule input, extra/missing units
or a lost failed call refuses. ALTERNATIVE: original producer identities and
existing source-specific reconstructions recover every saved call and unit.
No refit or capsule execution occurs. Some inherited validators recompute fitted
numerical probabilities; this is saved-result validation, not new replication.
Raw-source parser reproduction, other adapters and final claims remain separate.
"""
from .live_status import read as read_status
import importlib
from pathlib import Path

from .common import REPO, closure, digest, file_hash, read
from .confirmation_summary import arguments
from .queue import inside, verify_committed
from .revision_predictions import completed

ROUTES = {
    'runners.stage9.revision_predictions': {'validator': 'runners.stage9.revision_analysis',
        'prediction': 'ordinary-revision-predictions-v1', 'fit': 'ordinary-revision-fitting-v1', 'runtime': 'revision'},
    'runners.stage9.record_jobs': {'validator': 'runners.stage9.record_jobs',
        'prediction': 'record-predict-v1', 'fit': 'record-fit-v1', 'runtime': 'record'},
    'runners.stage9.commit_jobs': {'validator': 'runners.stage9.commit_jobs',
        'prediction': 'commit-predict-v1', 'fit': 'commit-fit-v1', 'runtime': 'commit'},
    'runners.stage9.broll_jobs': {'validator': 'runners.stage9.broll_jobs',
        'prediction': 'broll-predict-v1', 'fit': 'broll-fit-v1', 'runtime': 'broll'},
}


def producer(path, prior, state, queue_path, plan):
    jobs = [j for j in prior.values() if (REPO / j['produces']).resolve() == path]
    if len(jobs) != 1 or state['jobs'][jobs[0]['id']]['status'] != 'COMPLETE':
        raise ValueError('human source or fit lacks its original completed queue producer')
    verify_committed(queue_path, jobs[0], plan, digest(plan))
    return jobs[0]


def inspect_completed(job, plan, queue_path, prior, state):
    route = ROUTES[job['module']]
    if job['arguments'][0] != 'predict':
        raise ValueError('human semantic inspection requires the actual prediction operation')
    directory = inside(REPO / arguments(job, '--output'))
    scope, lane = arguments(job, '--scope'), arguments(job, '--lane')
    if lane not in ('development', 'evaluation') or scope not in ('pilot', 'scientific'):
        raise ValueError('original human prediction scope and lane required')
    if (REPO / job['produces']).resolve() != directory / 'COMPLETE.json':
        raise ValueError('human output differs from its actual producer')
    cases, fit = [inside(REPO / arguments(job, flag)) for flag in ('--cases', '--fit')]
    case_job = producer(cases / 'COMPLETE.json', prior, state, queue_path, plan)
    fit_job = producer(fit / 'COMPLETE.json', prior, state, queue_path, plan)
    if (fit_job['module'] != job['module'] or fit_job['arguments'][0] != 'fit'
            or fit_job['id'] not in job['after'] or case_job['id'] not in fit_job['after']
            or inside(REPO / arguments(fit_job, '--cases')) != cases):
        raise ValueError('prediction does not depend on the original source-bound fitting operation')
    identity, done = completed(directory, route['prediction'], scope)
    fitting, fit_done = completed(fit, route['fit'], scope)
    cell = digest({'manifest_sha256': digest(plan), 'job': job})
    if (identity['cell_identity'] != cell or identity['source'] != plan['sources']
            or identity['lane'] != lane or inside(identity['cases']) != cases or inside(identity['fit']) != fit
            or identity['cases_complete_sha256'] != file_hash(cases / 'COMPLETE.json')
            or identity['fit_complete_sha256'] != file_hash(fit / 'COMPLETE.json')
            or fitting['cases_complete_sha256'] != identity['cases_complete_sha256']
            or fitting['training_rows_sha256'] != digest(read(cases / 'CASES.json')['train'])
            or fit_done.get('training_only') is not True):
        raise ValueError('human source, fitting allocation or executed prediction identity changed')
    original_rows = read(cases / 'CASES.json')
    if identity['assigned_rows_sha256'] != digest(original_rows[lane]):
        raise ValueError('human prediction used another assigned population')
    module = importlib.import_module(route['validator'])
    rows, reconstructed_identity, *_ = module.verified_predictions(directory, lane, scope)
    if not rows or reconstructed_identity != identity:
        raise ValueError('source-specific prediction reconstruction is empty or misbound')
    calls = set(); units = set(); capsules = set()
    for row in rows:
        key = row['key'] if route['runtime'] == 'commit' else {'case': row['key'], 'view': row['view']}
        call_name = row['key'] if route['runtime'] == 'commit' else digest(key)
        path = directory / 'calls' / (call_name + '.json')
        if path.resolve() in calls:
            raise ValueError('human prediction repeats a saved call')
        calls.add(path.resolve()); saved = read(path)
        if set(saved) != {'input_sha256', 'result'} or saved['result'] != row['call']:
            raise ValueError('human prediction is disconnected from its actual saved call')
        cap = Path(saved['result']['capsule']).resolve()
        if not cap.is_relative_to(directory / 'capsules') or cap in capsules:
            raise ValueError('human predictions substitute or reuse a capsule')
        capsules.add(cap)
        actual = {'evidence': read(cap / 'evidence.json'), 'task': read(cap / 'task.json')}
        if saved['input_sha256'] != digest(actual):
            raise ValueError('saved human call signature differs from the actual capsule evidence/task')
        unit_path = directory / 'units' / (digest(key) + '.json'); units.add(unit_path.resolve())
        if read(unit_path) != {'identity': digest(identity), 'key': key, 'complete': True, 'row': row}:
            raise ValueError('human unit differs from its complete reconstructed prediction')
    if ({p.resolve() for p in (directory / 'calls').rglob('*.json')} != calls
            or {p.resolve() for p in (directory / 'units').rglob('*.json')} != units
            or done['assigned_calls'] != len(rows) or done['invalid_calls'] != sum(r['valid'] is not True for r in rows)):
        raise ValueError('human completion omits or adds calls, units or failures')
    if done['outputs'] != closure([REPO / p for p in done['outputs']['files']]):
        raise ValueError('human output closure changed during reconstruction')
    return {'status': 'RECONSTRUCTED', 'runtime': route['runtime'], 'calls': len(rows),
            'invalid_calls_retained': done['invalid_calls'], 'source_job': case_job['id'], 'fit_job': fit_job['id'],
            'complete_sha256': file_hash(directory / 'COMPLETE.json'), 'predictions_sha256': digest(rows),
            'new_capsule_executions': 0, 'refits': 0, 'scientific_admission': False}


def queue_audits(plan, queue_path, prior):
    state = read_status(queue_path / 'STATUS.json'); result = {}
    for key, job in prior.items():
        if job['module'] not in ROUTES or not job['arguments'] or job['arguments'][0] != 'predict':
            continue
        current = state['jobs'][key]
        if current['status'] != 'COMPLETE':
            result[key] = {k: current[k] for k in ('status', 'reason', 'disposition_sha256')}
            continue
        result[key] = inspect_completed(job, plan, queue_path, prior, state)
    return {'jobs': result, 'scope': 'four declared human-data prediction adapters; raw-source parser replay remains separate',
            'scientific_admission': False}
