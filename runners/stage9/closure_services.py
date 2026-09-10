"""B03 component: original resident compilation and complete service request storage.

DESIGN CHECK: B03/I03/X02/X06/X12; LESSONS 3--5, CONTROLS 6--7.
NULL: omitted service bytes, swapped compiled sources, wrong owner/cell identity
or a successful capsule without its accepted request refuse reconciliation.
ALTERNATIVE: original committed service records and saved capsules reconcile
without model calls. Constructed omissions/substitutions must fail; legacy missing
receipts and unmatched accepted requests stay explicitly unresolved. Bands:
verified recorded provenance, retained incomplete provenance, or refusal. This
does not establish OS isolation, numeric competence or scientific admission.
"""
from .live_status import read as read_status
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

from .common import REPO, closure, digest, file_hash, read

REQUIRED_SOURCES = {'runners/stage9/source_bootstrap.py', 'runners/stage9/model_service.py',
                    'runners/stage9/common.py', 'runners/stage9/neural.py', 'runners/stage9/train.py'}
REQUIRED_FILES = {'READY.json', 'LIFECYCLE.json', 'EXECUTION_CONFIG.json', 'config.json',
                  'execution/READY.json', 'execution/EXECUTION.json'}
# Both source versions were compared in full. The bounded CPU request timeout
# changes transport waiting only; choice/generation payload bytes are identical.
TEXT_READER_PROTOCOLS = {
    '5ffa1ed5115281b5b3652b1b64450810ddb99f9ba44b6ae677d9d493cbff286f': 'fixed-600-second-timeout',
    'c3e12059fadeb6b56b140be0c0fe35d72a2e64b9d5be50132ff426438cbbc434': 'bounded-cpu-timeout',
}


def protocol_sources(source):
    from runners.stage7.runtime import BOOTSTRAP
    originals = {'reader/worker.py': 'runners/stage9/reader.py',
                 'reader/readout.py': 'runners/readout_repair.py',
                 'reader/features.py': 'runners/stage9/features.py'}
    if (source['files'].get(originals['reader/worker.py']) not in TEXT_READER_PROTOCOLS
            or any(source['files'].get(p) != file_hash(REPO / p) for p in
                   ['runners/readout_repair.py', 'runners/stage9/features.py', 'runners/stage7/runtime.py'])):
        raise ValueError('historical text-reader protocol needs a separately reviewed adapter')
    expected = {name: source['files'][p] for name, p in originals.items()}
    expected.update({'reader/__init__.py': hashlib.sha256(b'').hexdigest(),
                     'bootstrap.py': hashlib.sha256(BOOTSTRAP.encode('utf-8')).hexdigest()})
    return expected


def json_lines(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()] if path.is_file() else []


def inventory(directory, outputs):
    """All actual service-root bytes must belong to the completed producer."""
    directory = Path(directory).resolve()
    declared = {(REPO / name).resolve(): sha for name, sha in outputs.get('files', {}).items()}
    roots = {p for p in directory.rglob('services') if p.is_dir()}
    roots.update(directory.joinpath(*p.relative_to(directory).parts[:p.relative_to(directory).parts.index('services') + 1])
                 for p in declared if p.is_relative_to(directory) and 'services' in p.relative_to(directory).parts)
    services = []
    for root in sorted(roots):
        expected = {p: sha for p, sha in declared.items() if p.is_relative_to(root)}
        actual = {(REPO / name).resolve(): sha for name, sha in closure([root])['files'].items()}
        if actual != expected:
            raise ValueError('service storage has missing, changed or uncommitted bytes')
        for path in root.iterdir():
            if path.is_symlink() or not path.is_dir():
                raise ValueError('service container must retain distinct actual process directories')
            services.append(path.resolve())
    if len(set(services)) != len(services):
        raise ValueError('ambiguous nested resident service ownership')
    return services


def inspect_service(directory, source, cell):
    directory = Path(directory).resolve()
    missing = sorted(name for name in REQUIRED_FILES if not (directory / name).is_file())
    identity = read(directory / 'READY.json').get('identity') if (directory / 'READY.json').is_file() else None
    record = {'path': directory.relative_to(REPO).as_posix(), 'files': closure([directory]),
              'identity_sha256': digest(identity), 'missing_execution_files': missing,
              'scientific_admission': False}
    usage = json_lines(directory / 'USAGE.jsonl'); errors = json_lines(directory / 'ERRORS.jsonl')
    accepted = Counter()
    for row in usage:
        sha = row.get('request_sha256')
        if not isinstance(sha, str) or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
            raise ValueError('service usage lost the actual request digest')
        accepted[sha] += 1
    if any(row.get('valid') is not False or not isinstance(row.get('error'), str) or not row['error'] for row in errors):
        raise ValueError('service error ledger has a missing or promoted error')
    record.update(accepted_requests=dict(accepted), accepted_request_count=len(usage),
                  retained_errors=len(errors), errors_sha256=digest(errors))
    if missing:
        record['status'] = 'INCOMPLETE_SERVICE_RETAINED'
        return record, identity
    config = read(directory / 'EXECUTION_CONFIG.json'); execution = read(directory / 'execution/EXECUTION.json')
    ready = read(directory / 'execution/READY.json'); model_ready = read(directory / 'READY.json')
    life = read(directory / 'LIFECYCLE.json'); loaded = execution['loaded_project_sources']
    settings = read(directory / 'config.json')  # Private settings stay out of the audit output.
    subset = config['sources']
    if (subset['sha256'] != digest(subset['files']) or not subset['files']
            or any(source['files'].get(p) != sha for p, sha in subset['files'].items())
            or config['module'] != 'runners.stage9.model_service'
            or Path(config['repo']).resolve() != REPO
            or Path(config['attempt']).resolve() != directory / 'execution'
            or config['arguments'] != [str(directory / 'config.json')]
            or config['cell_identity'] != cell or execution['cell_identity'] != cell or ready['cell_identity'] != cell
            or ready['command'] != config['module'] or not REQUIRED_SOURCES <= loaded.keys()
            or any(subset['files'].get(p) != sha for p, sha in loaded.items())):
        raise ValueError('resident compilation differs from its actual original caller/source/cell')
    if (execution['returncode'] != 0 or execution['error'] is not None
            or life.get('compiled_execution_sha256') != file_hash(directory / 'execution/EXECUTION.json')
            or life.get('compiled_execution_error') is not None or life['returncode'] != 0
            or life['graceful_shutdown'] is not True
            or model_ready['pid'] != ready['process']['pid'] or life['worker_pid'] != model_ready['pid']):
        raise ValueError('resident lifecycle lacks its actual successful compiled execution')
    if (not isinstance(identity, dict) or identity['base_files_sha256'] != digest(identity['base_files'])
            or identity['scorer_sources']['sha256'] != digest(identity['scorer_sources']['files'])
            or identity['scorer_sha256'] != identity['scorer_sources']['sha256']
            or any(subset['files'].get(p) != sha for p, sha in identity['scorer_sources']['files'].items())):
        raise ValueError('resident identity differs from its recorded original source package')
    times = [life['started_at'], execution['started_at'], ready['at'], model_ready['at'],
             execution['ended_at'], life['ended_at']]
    if (any(type(t) not in (int, float) or not math.isfinite(t) or t < 0 for t in times)
            or times != sorted(times)
            or any(not times[3] <= row['at'] <= times[-2] for row in usage + errors)):
        raise ValueError('resident readiness, requests and shutdown chronology differ')
    fields = ('precision', 'device', 'batch_size', 'max_context', 'max_support', 'max_new_tokens')
    adapter = settings['adapter_sha256'] if settings.get('adapter') else 'base-no-adapter'
    if (any(identity[key] != settings[key] for key in fields)
            or identity['adapter_sha256'] != adapter or Path(settings['output']).resolve() != directory):
        raise ValueError('resident model package differs from its original invocation')
    record.update(status='RECORDED_EXECUTION_VERIFIED', process=ready['process'],
                  execution_sha256=file_hash(directory / 'execution/EXECUTION.json'), loaded_sources_sha256=digest(loaded))
    return record, identity


def capsule_requests(directory, outputs, source):
    """Reconstruct the fixed text-reader request protocol from original saved inputs."""
    from .artifact_comparisons import audit_execution
    declared = {(REPO / name).resolve(): sha for name, sha in outputs.get('files', {}).items()}
    result = {}; incomplete = []
    for path in sorted(declared):
        if path.name != 'task.json' or not path.is_relative_to(directory):
            continue
        if not path.is_file() or file_hash(path) != declared[path]:
            raise ValueError('committed capsule task changed')
        task = read(path); identity = task.get('identity', {})
        if not {'model', 'revision', 'adapter_sha256', 'information_sha256'} <= set(identity) or task.get('probe'):
            continue
        cap = path.parent; sidecar = cap.parent / 'closures' / (cap.name + '.json')
        required = [sidecar, cap / 'evidence.json', cap / 'out/prediction.json', cap / 'out/receipt.json', cap / 'out/access.json']
        if any(p not in declared for p in required):
            incomplete.append(cap.relative_to(REPO).as_posix()); continue
        for own in required:
            if not own.is_file() or file_hash(own) != declared[own]:
                raise ValueError('committed model capsule evidence changed')
        prediction = read(cap / 'out/prediction.json')
        if prediction.get('valid') is not True:
            incomplete.append(cap.relative_to(REPO).as_posix()); continue
        evidence = read(cap / 'evidence.json'); copied = read(sidecar)
        expected = protocol_sources(source)
        if copied['files'] != expected:
            raise ValueError('model capsule differs from the reviewed original text-reader protocol')
        audit_execution({'capsule': str(cap), 'copied_sources': copied, 'prediction': prediction,
                         'receipt': read(cap / 'out/receipt.json'), 'accepted': True, 'rc': 0})
        if prediction.get('identity') != identity or identity['information_sha256'] != digest(evidence):
            raise ValueError('saved model request identity differs from its capsule evidence')
        if task['operation'] == 'choice':
            payload = {'operation': 'score', 'prefix': evidence['prefix'],
                       'options': {k: evidence['options'][k] for k in sorted(evidence['options'])}, 'identity': identity}
        elif task['operation'] == 'generate' and not evidence['options']:
            payload = {'operation': 'generate', 'prefix': evidence['prefix'], 'identity': identity,
                       'max_new_tokens': task['max_new_tokens'], 'seed': task['seed']}
        else:
            raise ValueError('unreviewed model request protocol')
        package = {k: v for k, v in identity.items() if k != 'information_sha256'}
        key = digest(package); result.setdefault(key, Counter())
        result[key][hashlib.sha256(json.dumps(payload, ensure_ascii=False, allow_nan=False).encode()).hexdigest()] += 1
    return result, incomplete


def inspect(directory, outputs, source, cell):
    directory = Path(directory).resolve(); services = inventory(directory, outputs)
    requests, incomplete = capsule_requests(directory, outputs, source)
    records = []; accepted = {}
    for service in services:
        record, identity = inspect_service(service, source, cell); records.append(record)
        accepted.setdefault(digest(identity), Counter()).update(record['accepted_requests'])
    unresolved = {}
    for package in set(accepted) | set(requests):
        actual = accepted.get(package, Counter()); saved = requests.get(package, Counter())
        if saved - actual:
            raise ValueError('successful model capsule lacks its original accepted service request')
        if actual - saved:
            unresolved[package] = dict(actual - saved)
    return {'services': records, 'service_count': len(records),
        'matched_saved_requests': sum(sum(r.values()) for r in requests.values()),
        'unmatched_accepted_requests': unresolved, 'incomplete_model_capsules': incomplete,
        'all_recorded_services_reconciled': not unresolved and not incomplete and all(r['status'] == 'RECORDED_EXECUTION_VERIFIED' for r in records),
        'attribution_scope': 'requests grouped by exact resident identity; no invented attribution across restarts with identical identities',
        'new_model_calls': 0, 'scientific_admission': False}


def queue_audits(plan, queue_path, prior):
    from .queue import verify_committed
    state = read_status(queue_path / 'STATUS.json'); result = {}
    for key, job in prior.items():
        if state['jobs'][key]['status'] != 'COMPLETE':
            continue  # Original failed/unrun dispositions and costs stay in the execution ledger.
        directory = (REPO / job['produces']).parent.resolve(); done = read(REPO / job['produces'])
        audit = inspect(directory, done.get('outputs', {}), plan['sources'], digest({'manifest_sha256': digest(plan), 'job': job}))
        if audit['service_count'] or audit['matched_saved_requests'] or audit['incomplete_model_capsules']:
            verify_committed(queue_path, job, plan, digest(plan)); result[key] = audit
    return {'jobs': result, 'scientific_admission': False,
            'scope': 'completed-producer resident storage and fixed text-reader request protocol; incomplete provenance remains unresolved'}


def archive_audits(references):
    """Explicit historical pointers retain original sources, dispositions and scope."""
    from .queue import inside, verify_disposition, validate_manifest
    if not isinstance(references, list):
        raise ValueError('historical service inspections require an explicit original-plan list')
    result = {}
    for item in references:
        if set(item) != {'manifest', 'queue', 'source_archive'}:
            raise ValueError('historical service reference fields differ')
        manifest, queue, archive = [inside(REPO / item[key]) for key in ('manifest', 'queue', 'source_archive')]
        name = manifest.relative_to(REPO).as_posix()
        if name in result:
            raise ValueError('duplicate historical service lineage')
        plan = read(manifest); validate_manifest(plan); state = read_status(queue / 'STATUS.json')
        done = read(queue / 'COMPLETE.json'); source = plan['sources']
        if (source['sha256'] != digest(source['files']) or read(archive / 'SOURCE.json') != source
                or any(file_hash(inside(archive / path, archive)) != sha for path, sha in source['files'].items())
                or read(queue / 'MANIFEST.json') != plan or state['manifest_sha256'] != digest(plan)
                or any(done[key] != state[key] for key in ('manifest_sha256', 'jobs', 'attempts'))
                or set(state['jobs']) != {job['id'] for job in plan['jobs']}):
            raise ValueError('historical service queue or archived original sources differ')
        for job in plan['jobs']:
            current = state['jobs'][job['id']]
            if current['status'] not in ('COMPLETE', 'FAILED', 'NOT_RUN'):
                raise ValueError('historical service lineage must be terminal')
            if current['status'] != 'COMPLETE':
                verify_disposition(queue, job, current)
        audited = queue_audits(plan, queue, {j['id']: j for j in plan['jobs']})
        result[name] = {'manifest_sha256': digest(plan), 'source_sha256': source['sha256'],
            'source_archive': archive.relative_to(REPO).as_posix(), 'queue_complete_sha256': file_hash(queue / 'COMPLETE.json'),
            'original_terminal_states': state['jobs'], 'resident_audits': audited,
            'scope': 'historical original-source inspection; not current-source model execution or new scientific evidence'}
    return {'lineages': result, 'new_model_calls': 0, 'scientific_admission': False}
