"""B03 raw-source reconstruction for already-exposed human preparations.

DESIGN CHECK: B03/H01/H02/H07/H08/X01/X02/X05/X12; LESSONS 2--5, CONTROLS 6--7.
NULL: missing raw files, altered prepared rows or exclusions, wrong source archive,
unlinked preparation, omitted scientific source review, or an invented reserve
refuse. ALTERNATIVE: every scheduled human preparation has its exact parser
review, including failed/unrun jobs, and the complete
original workbooks/drafts or released edit rows reconstruct every saved payload
through the same canonical constructor. Exact comparison or explicit refusal; no fitting,
reader calls, new reserve opening, scientific inference or source modification.
Project-scoped ScholaWrite authors never become global people or raw keystrokes.
CoAuthor replay retains mixed agency, excluded sessions and unreproduced source counts.
HUMAN reconstruction decodes only rows already consumed by its completed producer;
unused raw lines and prepared reserve payloads are hashed as opaque bytes only.
Other raw parsers remain outside these explicit routes.
"""
from .live_status import read as read_status
import math

from .common import REPO, closure, digest, file_hash, read
from .queue import inside, verify_committed


def validate_scientific_reviews(plan, jobs):
    """Require the six supported human routes before launch and final raw replay.

    This checks declarations without reading data. Historical component pilots
    retain their explicit partial scope; it does not certify other raw sources.
    """
    if plan.get('kind') != 'science':
        return
    from .closure_cases import is_preparation
    kinds = {'runners.stage9.revision_cases': 'argrewrite',
             'runners.stage9.iterater_cases': 'iterater',
             'runners.stage9.commit_jobs': 'commitbench',
             'runners.stage9.broll_jobs': 'broll'}
    preparations = {key: job for key, job in jobs.items() if is_preparation(job)}
    reviews = plan.get('raw_source_reviews', {})
    if not isinstance(reviews, dict) or set(reviews) != set(preparations):
        raise ValueError('scientific raw reviews must cover every human preparation exactly')
    for key, job in preparations.items():
        expected = kinds.get(job['module'])
        if job['module'] == 'runners.stage9.record_jobs':
            args = job['arguments']
            if args.count('--dataset') != 1:
                raise ValueError('raw record review requires one actual dataset argument')
            index = args.index('--dataset') + 1
            if index == len(args) or args[index] not in ('coauthor', 'scholawrite'):
                raise ValueError('raw record review names an unsupported dataset')
            expected = args[index]
        review = reviews[key]
        if (not isinstance(review, dict) or set(review) != {'kind', 'prepared', 'source_archive'}
                or review['kind'] != expected
                or any(not isinstance(review[k], str) or not review[k].strip()
                       for k in ('prepared', 'source_archive'))):
            raise ValueError('scientific raw review must bind the actual preparation and parser')


def argrewrite(prepared, archive):
    from .argrewrite import raw_inputs, reconstruct
    prepared, archive = inside(prepared), inside(archive)
    before = closure([prepared]); identity = read(prepared / 'IDENTITY.json'); done = read(prepared / 'COMPLETE.json')
    source = identity['sources']
    required = {'runners/stage9/argrewrite.py', 'runners/stage9/common.py', 'runners/run_arg_replication.py'}
    if (source['sha256'] != digest(source['files']) or set(source['files']) != required
            or any(file_hash(inside(archive / name, archive)) != sha for name, sha in source['files'].items())
            or any(read(archive / 'SOURCE.json')['files'].get(name) != sha for name, sha in source['files'].items())
            or done['identity_sha256'] != digest(identity) or done['completed'] is not True
            or done['reserve_groups'] != 0 or done['historical_v4_exact'] is not True):
        raise ValueError('raw preparation lacks its original archived source, completion or exposure identity')
    files, drafts, current = raw_inputs()
    if {k: v for k, v in identity.items() if k != 'sources'} != {k: v for k, v in current.items() if k != 'sources'}:
        raise ValueError('original complete raw inventory or preparation contract changed')
    essays, ledger, summary = reconstruct(files, drafts, identity['inputs'])
    if read(prepared / 'LEDGER.json') != ledger:
        raise ValueError('raw workbook lineage or exclusion ledger does not reconstruct')
    expected = {prepared / 'essays' / (key + '.json') for key in essays}
    if {p for p in (prepared / 'essays').rglob('*') if p.is_file()} != expected:
        raise ValueError('prepared essay inventory differs from the complete original source population')
    if any(read(path) != essays[path.stem] for path in expected):
        raise ValueError('prepared essay, draft correspondence or excluded canonical unit does not reconstruct')
    omitted = {'identity_sha256', 'elapsed_seconds', 'completed_at'}
    if ({k: v for k, v in done.items() if k not in omitted} != summary
            or any(type(done[k]) not in (int, float) or not math.isfinite(done[k]) or done[k] < 0
                   for k in ('elapsed_seconds', 'completed_at'))):
        raise ValueError('original raw-source summary differs from complete reconstruction')
    if closure([prepared]) != before or raw_inputs()[2]['inputs'] != identity['inputs']:
        raise ValueError('raw-source inspection changed or raced its original bytes')
    return {'status': 'RECONSTRUCTED', 'prepared_identity_sha256': digest(identity),
        'prepared_complete_sha256': file_hash(prepared / 'COMPLETE.json'), 'raw_inputs_sha256': identity['inputs']['sha256'],
        'original_source_sha256': source['sha256'], 'source_archive': archive.relative_to(REPO).as_posix(),
        'essay_payload_sha256': digest(essays), 'ledger_sha256': digest(ledger), 'summary_sha256': digest(summary),
        'workbooks': len(files), 'draft_files': len(drafts), 'essay_groups': len(essays),
        'new_fits': 0, 'new_reader_calls': 0, 'new_reserve_openings': 0, 'scientific_admission': False,
        'scope': 'already-exposed ArgRewrite; canonical source reproduction, not a published classifier replication'}


def scholawrite(prepared, archive):
    from .scholawrite import raw_inputs, reconstruct
    prepared, archive = inside(prepared), inside(archive)
    before = closure([prepared]); identity = read(prepared / 'IDENTITY.json'); done = read(prepared / 'COMPLETE.json')
    source = identity['code']; required = {'runners/stage9/scholawrite.py', 'runners/stage9/common.py'}
    if (source['sha256'] != digest(source['files']) or set(source['files']) != required
            or any(file_hash(inside(archive / name, archive)) != sha for name, sha in source['files'].items())
            or any(read(archive / 'SOURCE.json')['files'].get(name) != sha for name, sha in source['files'].items())
            or done['identity_sha256'] != digest(identity) or done['source_counts_match'] is not True
            or done['reserve_groups'] != 0):
        raise ValueError('released-edit preparation lacks its original source, completion or exposure identity')
    directory, current = raw_inputs()
    if {k: v for k, v in identity.items() if k != 'code'} != {k: v for k, v in current.items() if k != 'code'}:
        raise ValueError('original released-row inventory or preparation contract changed')
    projects, ledger, summary = reconstruct(directory)
    if read(prepared / 'LEDGER.json') != ledger:
        raise ValueError('released-edit project, session or exclusion ledger does not reconstruct')
    expected = {prepared / 'projects' / (key + '.json') for key in projects}
    if {p for p in (prepared / 'projects').rglob('*') if p.is_file()} != expected:
        raise ValueError('prepared project inventory differs from the complete released population')
    if any(read(path) != projects[path.stem] for path in expected):
        raise ValueError('prepared editor state, successor link or excluded source row does not reconstruct')
    omitted = {'identity_sha256', 'elapsed_seconds', 'completed_at'}
    if ({k: v for k, v in done.items() if k not in omitted} != summary
            or any(type(done[k]) not in (int, float) or not math.isfinite(done[k]) or done[k] < 0
                   for k in ('elapsed_seconds', 'completed_at'))):
        raise ValueError('original released-edit summary differs from complete reconstruction')
    if closure([prepared]) != before or raw_inputs()[1]['source_files'] != identity['source_files']:
        raise ValueError('released-edit inspection changed or raced its original bytes')
    return {'status': 'RECONSTRUCTED', 'prepared_identity_sha256': digest(identity),
        'prepared_complete_sha256': file_hash(prepared / 'COMPLETE.json'),
        'raw_inputs_sha256': identity['source_files']['sha256'], 'original_source_sha256': source['sha256'],
        'source_archive': archive.relative_to(REPO).as_posix(), 'project_payload_sha256': digest(projects),
        'ledger_sha256': digest(ledger), 'summary_sha256': digest(summary),
        'projects': len(projects), 'released_rows': summary['source_rows'],
        'project_scoped_author_ids': summary['project_scoped_author_ids'],
        'global_people_count': summary['global_people_count'],
        'new_fits': 0, 'new_reader_calls': 0, 'new_reserve_openings': 0, 'scientific_admission': False,
        'original_raw_closure_scope': 'all_sorted released stream and dataset_dict metadata; auxiliary split counts rechecked without inventing historical hashes for their unused row bytes',
        'scope': 'already-exposed ScholaWrite; annotated released edits with original continuity/exclusions, not raw keystrokes or writer-reported intention'}


def coauthor(prepared, archive):
    from .coauthor import raw_inputs, reconstruct
    prepared, archive = inside(prepared), inside(archive)
    before = closure([prepared]); identity = read(prepared / 'IDENTITY.json'); done = read(prepared / 'COMPLETE.json')
    source = identity['sources']; required = {'runners/stage9/coauthor.py', 'runners/stage9/common.py'}
    if (source['sha256'] != digest(source['files']) or set(source['files']) != required
            or any(file_hash(inside(archive / name, archive)) != sha for name, sha in source['files'].items())
            or any(read(archive / 'SOURCE.json')['files'].get(name) != sha for name, sha in source['files'].items())
            or done['identity_sha256'] != digest(identity) or done['reserve_groups'] != 0
            or done['scientific_launch_accepted'] is not False):
        raise ValueError('session preparation lacks its original source, completion or exposure identity')
    paths, metadata, current = raw_inputs()
    if {k: v for k, v in identity.items() if k != 'sources'} != {k: v for k, v in current.items() if k != 'sources'}:
        raise ValueError('original event-log roster or released task metadata changed')
    sessions, ledger, summary = reconstruct(paths, metadata)
    if read(prepared / 'LEDGER.json') != ledger:
        raise ValueError('session roster, exclusion or published-count ledger does not reconstruct')
    expected = {prepared / 'sessions' / (key + '.json') for key in sessions}
    if {p for p in (prepared / 'sessions').rglob('*') if p.is_file()} != expected:
        raise ValueError('prepared session inventory differs from the original released roster')
    if any(read(path) != sessions[path.stem] for path in expected):
        raise ValueError('session replay, suggestion correspondence or handling does not reconstruct')
    omitted = {'identity_sha256', 'elapsed_seconds', 'completed_at'}
    if ({k: v for k, v in done.items() if k not in omitted} != summary
            or any(type(done[k]) not in (int, float) or not math.isfinite(done[k]) or done[k] < 0
                   for k in ('elapsed_seconds', 'completed_at'))):
        raise ValueError('original session summary differs from complete raw reconstruction')
    after = raw_inputs()[2]
    if (closure([prepared]) != before or identity['source_files'] != after['source_files']
            or identity['metadata_sources'] != after['metadata_sources']):
        raise ValueError('session raw-source inspection changed or raced its original bytes')
    return {'status': 'RECONSTRUCTED', 'prepared_identity_sha256': digest(identity),
        'prepared_complete_sha256': file_hash(prepared / 'COMPLETE.json'),
        'raw_inputs_sha256': digest({'logs': identity['source_files'], 'metadata': identity['metadata_sources']}),
        'original_source_sha256': source['sha256'], 'source_archive': archive.relative_to(REPO).as_posix(),
        'session_payload_sha256': digest(sessions), 'ledger_sha256': digest(ledger), 'summary_sha256': digest(summary),
        'local_files': summary['local_files'], 'published_sessions': summary['published_sessions'],
        'extra_local_files': summary['extra_local_files'], 'usable_sessions': summary['usable_sessions'],
        'metadata_writers': summary['metadata_writers'], 'website_writers': summary['website_writers'],
        'writer_count_reproduced': summary['writer_count_reproduced'],
        'new_fits': 0, 'new_reader_calls': 0, 'new_reserve_openings': 0, 'scientific_admission': False,
        'scope': 'already-exposed CoAuthor; strict UTF-16 replay and source-defined mixed-agency handling, no independent final document or uniquely human intention'}


def queue_audits(plan, queue_path, prior):
    validate_scientific_reviews(plan, prior)
    from .closure_iterater_raw import inspect as iterater
    from .closure_external_raw import inspect_broll, inspect_commit
    reviews = plan.get('raw_source_reviews', {})
    if not isinstance(reviews, dict) or not set(reviews) <= prior.keys():
        raise ValueError('raw-source review must name an actual preceding preparation job')
    state = read_status(queue_path / 'STATUS.json'); result = {}
    for key, review in reviews.items():
        job = prior[key]
        routes = {'argrewrite': ('runners.stage9.revision_cases', argrewrite, 'prepared_identity_sha256'),
                  'iterater': ('runners.stage9.iterater_cases', iterater, 'prepared_identity_sha256'),
                  'commitbench': ('runners.stage9.commit_jobs', inspect_commit, 'prepared_complete_sha256'),
                  'broll': ('runners.stage9.broll_jobs', inspect_broll, 'prepared_identity_sha256'),
                  'scholawrite': ('runners.stage9.record_jobs', scholawrite, 'prepared_complete_sha256'),
                  'coauthor': ('runners.stage9.record_jobs', coauthor, 'prepared_complete_sha256')}
        if (set(review) != {'kind', 'prepared', 'source_archive'} or review['kind'] not in routes
                or job['module'] != routes[review['kind']][0]):
            raise ValueError('unreviewed raw parser or substituted preparation job')
        current = state['jobs'][key]
        if current['status'] != 'COMPLETE':
            if current['status'] not in ('FAILED', 'NOT_RUN'):
                raise ValueError('raw-source preparation must be terminal')
            result[key] = {k: current[k] for k in ('status', 'reason', 'disposition_sha256')}; continue
        verify_committed(queue_path, job, plan, digest(plan))
        identity = read((REPO / job['produces']).parent / 'IDENTITY.json')
        if review['kind'] in ('scholawrite', 'coauthor') and (identity['operation'] != 'record-cases-v1' or identity['dataset'] != review['kind']):
            raise ValueError('raw record audit requires its actual dataset case producer')
        if review['kind'] in ('iterater', 'commitbench', 'broll'):
            if review['kind'] != 'iterater' and (not job['arguments'] or job['arguments'][0] != 'prepare'):
                raise ValueError('raw source audit requires the actual preparation dispatcher operation')
            inspected = routes[review['kind']][1](REPO / review['prepared'], REPO / review['source_archive'], (REPO / job['produces']).parent)
            if review['kind'] in ('iterater', 'broll'):
                identity = read((REPO / job['produces']).parent / 'METADATA.json')
            if review['kind'] == 'broll':
                identity = {**identity, 'prepared_identity_sha256': identity['canonical_identity_sha256']}
        else:
            inspected = routes[review['kind']][1](REPO / review['prepared'], REPO / review['source_archive'])
        link = routes[review['kind']][2]
        if identity[link] != inspected[link]:
            raise ValueError('raw audit is unrelated to the actual preparation input')
        result[key] = inspected
    historical = {}
    if 'raw_preparation_archives' in plan:
        from .closure_arxiv_raw import archive_audits
        historical['historical_preparations'] = archive_audits(plan['raw_preparation_archives'])
    return {'jobs': result, **historical, 'scientific_admission': False,
            'scope': 'explicit original-plan raw-source reviews; missing reviews and other parsers are not validated'}
