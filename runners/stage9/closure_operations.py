"""Read-only B03 reconstruction of ordinary neural-operation executions.

DESIGN CHECK: B03/C01/C02/C04/C06/C08/X01/X02/X06/X08/X11/X12;
LESSONS 3--5, CONTROLS 6--7. NULL: changed cases, package, task, call, unit,
export or omitted failed execution refuses reconstruction. ALTERNATIVE: the
original command's shared input constructor and saved-call replay recover every
assigned unit and export, retaining invalid reader behavior. No model invocation,
writer, new reserve opening or inference about capability occurs. Bands are
reconstructed evidence or explicit refusal/disposition; neither licenses full B03.
Capsule isolation, service accounting and other semantic routes remain separate.
"""
from pathlib import Path

from .common import REPO, closure, digest, file_hash, read
from .live_status import read as read_status
from .queue import inside, verify_committed, verify_disposition
from . import neural_operations as operations

MODULE = 'runners.stage9.neural_operations'


def inspect_completed(job, plan, queue_path):
    if job['module'] != MODULE:
        raise ValueError('operation audit requires the original neural dispatcher')
    args = vars(operations.argument_parser().parse_args(job['arguments']))
    directory = inside(REPO / args.pop('output'))
    if (REPO / job['produces']).resolve() != directory / 'COMPLETE.json':
        raise ValueError('operation audit output differs from its actual producer')
    verify_committed(queue_path, job, plan, digest(plan))
    before = closure([directory])
    cell = digest({'manifest_sha256': digest(plan), 'job': job})
    identity, _, cases, world_plan = operations.context(directory, cell=cell,
        source=plan['sources'], **args)
    if read(directory / 'IDENTITY.json') != identity:
        raise ValueError('operation inputs, fitting selection or source identity differ')
    done = operations.validate_complete(directory, identity)
    package = read(directory / 'PACKAGE.json'); family = operations.BASES[identity['family']]
    expected = {'model': family['model'], 'revision': family['revision'],
                'adapter_sha256': identity['adapter_sha256'], 'precision': identity['precision'],
                'max_context': identity['max_context'], 'max_support': identity['max_support'],
                'max_new_tokens': identity['max_new_tokens'], 'batch_size': 4, 'device': 'cuda'}
    scorer = package['scorer_sources']
    if (any(package.get(k) != v for k, v in expected.items())
            or package['generation']['requested'] != identity['generation']
            or scorer['sha256'] != digest(scorer['files'])
            or package['scorer_sha256'] != scorer['sha256']
            or not scorer['files']
            or any(plan['sources']['files'].get(p) != sha for p, sha in scorer['files'].items())):
        raise ValueError('operation package differs from the original fitted/reference reader')
    calls = {}; capsules = {}; units = set(); rows = []
    for case in cases:
        def call(evidence, arguments, index):
            task = operations.request_task(evidence, arguments, package)
            path = directory / 'calls' / case['unit'][:16] / ('call-' + digest(index)[:16] + '.json')
            saved = read(path)
            if set(saved) != {'input_sha256', 'result'} or saved['input_sha256'] != digest({'evidence': evidence, 'task': task}):
                raise ValueError('operation call differs from reconstructed evidence or task')
            result = saved['result']; cap = Path(result['capsule']).resolve()
            if (not cap.is_relative_to(directory / 'capsules')
                    or cap in capsules and capsules[cap] != path
                    or type(result.get('accepted')) is not bool):
                raise ValueError('operation call substitutes a capsule or invalid validity field')
            if (read(cap / 'evidence.json') != evidence or read(cap / 'task.json') != task
                    or read(cap / 'out/access.json') != result['access']):
                raise ValueError('operation capsule differs from its actual requested input or access')
            for name in ('prediction', 'receipt'):
                path_out = cap / 'out' / (name + '.json')
                if result['accepted'] or result.get(name) is not None:
                    if read(path_out) != result.get(name):
                        raise ValueError('operation result lacks its actual capsule output')
            operations.audit_execution(result)
            calls[path] = result; capsules[cap] = path
            return result
        row = operations.unit_result(case, identity['operation'], call)
        path = directory / 'units' / (digest(case['unit']) + '.json')
        saved_unit = read(path)
        if (path in units or saved_unit.get('complete') is not True
                or saved_unit != {'identity': digest(identity), 'key': case['unit'], 'complete': True, 'row': row}):
            raise ValueError('operation unit differs from complete saved-call reconstruction')
        units.add(path); rows.append(row)
    if ({p.resolve() for p in (directory / 'calls').rglob('*.json')} != set(calls)
            or {p.resolve() for p in (directory / 'units').rglob('*.json')} != units
            or not cases):
        raise ValueError('operation has extra, missing or empty calls/units')
    exports = {}; operation = identity['operation']; scope = identity['scope']
    if operation in ('artifact_choice', 'process_choice'):
        from .confirmation_neural import discovery_forecasts
        exports['FORECASTS.json'] = discovery_forecasts(cases, rows, operation)
    if operation == 'historical_prediction':
        from .historical_prediction import summarize
        from .scoring import score_json
        exports['HISTORICAL_PREDICTION.json'] = score_json(summarize(cases, [r['result'] for r in rows], scope))
    if operation in operations.BROAD:
        from .generation_analysis import summarize
        exports['GENERATION.json'] = summarize([c['source_worlds'][0] for c in cases],
            [r['result']['call'] for r in rows], world_plan['reference_scores'],
            population=operations.BROAD[operation], scope=scope)
    for name, value in exports.items():
        if read(directory / name) != value:
            raise ValueError('operation export differs from reconstructed original units')
    counts = {'execution_complete': True, 'expected_units': len(cases), 'completed_units': len(rows),
              'reader_calls': len(calls), 'operation': operation, 'scope': scope,
              'all_reader_calls_valid': all(v['accepted'] for v in calls.values())}
    if any(type(done.get(k)) is not type(v) or done[k] != v for k, v in counts.items()):
        raise ValueError('operation completion loses assigned units or failed calls')
    if closure([directory]) != before:
        raise ValueError('read-only operation audit changed original files')
    return {'status': 'RECONSTRUCTED', 'operation': operation, 'units': len(rows), 'calls': len(calls),
            'invalid_calls_retained': sum(not v['accepted'] for v in calls.values()),
            'complete_sha256': file_hash(directory / 'COMPLETE.json'), 'units_sha256': digest(rows),
            'exports': {name: digest(v) for name, v in exports.items()},
            'package_sha256': file_hash(directory / 'PACKAGE.json'),
            'new_reader_calls': 0, 'new_reserve_openings': 0, 'scientific_admission': False}


def queue_audits(plan, queue_path, prior):
    state = read_status(queue_path / 'STATUS.json'); result = {}
    for key, job in prior.items():
        if job['module'] != MODULE:
            continue
        current = state['jobs'][key]
        if current['status'] == 'COMPLETE':
            result[key] = inspect_completed(job, plan, queue_path)
        elif current['status'] in ('FAILED', 'NOT_RUN'):
            verify_disposition(queue_path, job, current)
            result[key] = {k: current[k] for k in ('status', 'reason', 'disposition_sha256')}
        else:
            raise ValueError('neural-operation semantic audit requires terminal jobs')
    return {'jobs': result, 'scientific_admission': False,
            'scope': 'Original neural-operation inputs and complete saved-call/unit/export reconstruction; not complete scientific admission'}
