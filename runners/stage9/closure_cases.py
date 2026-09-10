"""Read-only B03 reconstruction of declared human cases from prepared sources.

DESIGN CHECK: B03/H01/H02/H03/H06/H07/H08/X01/X02/X05/X06/X12;
LESSONS 3--5, CONTROLS 6--7. NULL: rehashed altered cases, missing exclusions,
another allocation/fold, wrong producer or lost failed preparation must refuse
or retain its original failure. ALTERNATIVE: the original source-specific
projection and split logic reconstruct every saved case and metadata field.
No fitting, reader calls or reserve opening occurs. Original source integrities
may rehash reserve bytes; no new reserve payload is parsed for case construction.
This covers prepared-source projections, not every raw-download parser or claim.
"""
from .live_status import read as read_status
from .common import REPO, ROOT, closure, digest, file_hash, read
from .confirmation_summary import arguments
from .queue import inside, verify_committed
from .revision_predictions import completed

ROUTES = {
    'runners.stage9.revision_cases': 'argrewrite-actual-revision-cases-v1',
    'runners.stage9.iterater_cases': 'iterater-actual-revision-cases-v1',
    'runners.stage9.record_jobs': 'record-cases-v1',
    'runners.stage9.commit_jobs': 'commit-cases-v1',
    'runners.stage9.broll_jobs': 'broll-cases-v1',
}


def is_preparation(job):
    return job['module'] in ROUTES and (job['module'].endswith('_cases') or
        bool(job['arguments']) and job['arguments'][0] == 'prepare')


def optional(job, flag):
    return arguments(job, flag) if flag in job['arguments'] else None


def reconstruct(job, scope):
    """Return exact payloads and non-execution identity fields from original inputs."""
    module = job['module']
    if module == 'runners.stage9.revision_cases':
        from .revision_cases import inputs
        rows, excluded, separation, metadata = inputs(scope)
        return {'CASES.json': rows, 'EXCLUSIONS.json': excluded, 'SEPARATION.json': separation}, metadata
    if module == 'runners.stage9.iterater_cases':
        from .iterater_cases import INTENTS, pilot_inputs, study_inputs
        study = optional(job, '--study')
        if scope == 'scientific' and study is None:
            raise ValueError('scientific HUMAN study must be declared')
        rows, metadata = pilot_inputs() if study is None else study_inputs(scope, study)
        fields = {'classes': list(INTENTS), 'allocation': metadata['allocation'], 'metadata_sha256': digest(metadata),
            'cross_source_complete_sha256': file_hash(ROOT / 'private/prepared/cross-source-v2/COMPLETE.json'),
            'data_scope': metadata['scope'], 'target': 'released major-intent annotation agreement; disagreement retained',
            **({k: metadata[k] for k in ('study', 'active_tasks', 'task_dispositions')} if study is not None else {})}
        return {'CASES.json': rows, 'METADATA.json': metadata}, fields
    if module == 'runners.stage9.record_jobs':
        from .record_jobs import contract
        dataset, fold = arguments(job, '--dataset'), optional(job, '--fold')
        if dataset == 'coauthor':
            if fold is not None:
                raise ValueError('CoAuthor has no project rotation')
            from .coauthor_cases import inputs
            rows, metadata = inputs(scope)
            metadata = metadata | {'allocation': metadata['writer_component_allocation'], 'crossed_stimulus': True}
        elif dataset == 'scholawrite':
            from .schola_cases import inputs
            rows, metadata = inputs(scope, int(fold) if fold is not None else None)
        else:
            raise ValueError('unsupported original prospective dataset')
        classes = contract(dataset)
        if metadata['classes'] != classes:
            raise ValueError('native prospective support differs')
        return {'CASES.json': rows}, {**metadata, 'dataset': dataset, 'classes': classes, 'rows_sha256': digest(rows)}
    if module == 'runners.stage9.commit_jobs':
        from .commit_cases import inputs
        rows, metadata = inputs(scope)
        return {'CASES.json': rows}, {**metadata, 'rows_sha256': digest(rows)}
    if module == 'runners.stage9.broll_jobs':
        from .broll_cases import inputs
        rows, metadata = inputs(scope)
        return {'CASES.json': rows, 'METADATA.json': metadata}, {'metadata_sha256': digest(metadata)}
    raise ValueError('unsupported original source preparation')


def inspect_completed(job, plan, queue_path):
    if not is_preparation(job):
        raise ValueError('prepared-source audit requires an original preparation operation')
    scope = arguments(job, '--scope')
    if scope not in ('pilot', 'scientific'):
        raise ValueError('original prepared-source scope required')
    directory = inside(REPO / arguments(job, '--output'))
    if (REPO / job['produces']).resolve() != directory / 'COMPLETE.json':
        raise ValueError('prepared-source output differs from actual producer')
    verify_committed(queue_path, job, plan, digest(plan))
    identity, done = completed(directory, ROUTES[job['module']], scope)
    cell = digest({'manifest_sha256': digest(plan), 'job': job})
    if identity['cell_identity'] != cell or identity['source'] != plan['sources']:
        raise ValueError('prepared-source original execution identity changed')
    before = closure([directory])
    payloads, fields = reconstruct(job, scope)
    expected_identity = {'cell_identity': cell, 'operation': ROUTES[job['module']],
                         'scope': scope, 'source': plan['sources'], **fields}
    if identity != expected_identity:
        raise ValueError('prepared-source allocation, source or metadata differs')
    for name, value in payloads.items():
        path = directory / name
        if (done['outputs']['files'].get(path.relative_to(REPO).as_posix()) != file_hash(path)
                or read(path) != value):
            raise ValueError('prepared-source cases or retained exclusions do not reconstruct')
    if closure([directory]) != before:
        raise ValueError('prepared-source reconstruction changed original output bytes')
    return {'status': 'RECONSTRUCTED', 'operation': identity['operation'],
        'complete_sha256': file_hash(directory / 'COMPLETE.json'),
        'payload_sha256': {name: digest(value) for name, value in payloads.items()},
        'lane_records': {lane: len(rows) for lane, rows in payloads['CASES.json'].items()},
        'new_fits': 0, 'new_reader_calls': 0, 'new_reserve_openings': 0, 'scientific_admission': False}


def queue_audits(plan, queue_path, prior):
    state = read_status(queue_path / 'STATUS.json'); result = {}
    for key, job in prior.items():
        if not is_preparation(job):
            continue
        current = state['jobs'][key]
        result[key] = (inspect_completed(job, plan, queue_path) if current['status'] == 'COMPLETE'
            else {k: current[k] for k in ('status', 'reason', 'disposition_sha256')})
    return {'jobs': result, 'scope': 'six human prepared-source projection routes; raw-download parser replay remains separate',
            'scientific_admission': False}
