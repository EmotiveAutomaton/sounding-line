"""B03 component: inspect actual capsule bytes, outputs and denial probes.

DESIGN CHECK: B03/I03/X02/X06/X12; LESSONS 3--5, CONTROLS 6--7.
NULL: an accepted flag, a probe with missing attacks, changed access receipts,
or substituted copied code cannot establish the reader boundary. ALTERNATIVE:
the exact copied package has a complete actual denial probe, while every saved
call retains its actual inputs, outputs and loaded sources. Failed calls remain
failed; missing failed-call evidence is reported, never silently promoted.
This is a CPython audit-hook boundary, not OS isolation. Caller-supplied source
bindings, data semantics and complete workload coverage still need B03 validation.
"""
from .live_status import read as read_status
from pathlib import Path

from .common import REPO, ROOT, digest, file_hash, read


def materialized(result, expected_sources):
    """Expected copied bytes must come from the original reviewed caller contract."""
    if type(result.get('accepted')) is not bool or type(result.get('rc')) is not int:
        raise ValueError('capsule execution status must be an actual boolean and return code')
    cap = Path(result['capsule'])
    if cap.is_symlink() or not cap.resolve().is_relative_to(ROOT):
        raise ValueError('capsule is outside the declared Stage 9 root')
    cap = cap.resolve(); copied = result['copied_sources']
    if (not expected_sources or copied['files'] != expected_sources
            or copied['sha256'] != digest(expected_sources)
            or not {'bootstrap.py', 'reader/__init__.py', 'reader/worker.py'} <= set(expected_sources)):
        raise ValueError('copied package differs from the reviewed original source binding')
    for name, sha in expected_sources.items():
        path = cap / name
        if Path(name).is_absolute() or path.is_symlink() or not path.resolve().is_relative_to(cap) or file_hash(path) != sha:
            raise ValueError('copied source escaped its capsule or changed')
    task = read(cap / 'task.json')
    evidence = read(cap / 'evidence.json') if (cap / 'evidence.json').exists() else None
    if digest(task) != copied['task_sha256'] or digest(evidence) != copied['evidence_sha256']:
        raise ValueError('actual capsule input changed')
    missing = []
    for name in ('prediction', 'receipt', 'error', 'access'):
        path = cap / 'out' / (name + '.json')
        if path.exists():
            if read(path) != result.get(name):
                raise ValueError('saved capsule ' + name + ' differs from its actual output')
        elif result.get(name) is not None:
            raise ValueError('saved capsule output has no actual file: ' + name)
        else:
            missing.append(name)
    access = result.get('access')
    if access is not None:
        if Path(access['cwd']).resolve() != cap:
            raise ValueError('access receipt belongs to another capsule')
        counts = access['counts']
        if any(type(counts.get(k)) is not int or counts[k] < 0 for k in ('allowed', 'denied')):
            raise ValueError('invalid actual access counters')
    return cap, task, missing


def denial_probe(result, expected_sources):
    cap, task, missing = materialized(result, expected_sources)
    if (task.get('probe') is not True or result['accepted'] is not True or result['rc'] != 0
            or 'receipt' in missing or 'access' in missing):
        raise ValueError('an actual complete denial probe is required')
    paths = task.get('forbidden_paths')
    if not isinstance(paths, list) or not paths or len(paths) != len(set(paths)):
        raise ValueError('probe must exercise explicit distinct forbidden paths')
    if any(not Path(p).is_file() or Path(p).resolve().is_relative_to(cap) for p in paths):
        raise ValueError('probe paths must be existing files outside the capsule')
    required = {f'{kind}_{i}' for kind in ('read', 'write') for i in range(len(paths))}
    required |= {'import_' + k for k in ('runners', 'soundingline', 'torch', 'ctypes', 'subprocess')}
    required |= {'other_loopback', 'external_network', 'environment_mutation'}
    receipt = result['receipt']; attempts = receipt.get('attempts', [])
    if (receipt.get('all_raised') is not True or len(attempts) != len(required)
            or {a.get('name') for a in attempts} != required
            or any(a.get('denied') is not True or not a.get('error', '').startswith('capsule boundary:') for a in attempts)
            or result['access']['counts']['denied'] < len(attempts)):
        raise ValueError('probe omitted an attack or did not observe actual boundary denial')
    return {'attempts': len(attempts), 'receipt_sha256': file_hash(cap / 'out/receipt.json'),
            'access_sha256': file_hash(cap / 'out/access.json'),
            'source_sha256': digest(expected_sources), 'mechanism': 'CPython audit-hook boundary; not OS isolation'}


def inspect_call(result, expected_sources, probe_result):
    """No scientific predictions or scores are recomputed by this component."""
    probe = denial_probe(probe_result, expected_sources)
    cap, task, missing = materialized(result, expected_sources)
    if task.get('probe'):
        raise ValueError('a denial probe is not a normal reader prediction')
    if result['accepted']:
        expected_loaded = {('reader' if p == 'reader/__init__.py' else p[:-3].replace('/', '.')): sha
                           for p, sha in expected_sources.items() if p.startswith('reader/')}
        if (result['rc'] != 0 or any(k in missing for k in ('prediction', 'receipt', 'access'))
                or result.get('inputs_and_sources_unchanged') is not True
                or result['receipt'].get('loaded_sources') != expected_loaded
                or result['prediction'].get('valid') is not True):
            raise ValueError('accepted call lacks its actual complete loaded-source output')
    access = result.get('access')
    if access is not None:
        reference = probe_result['access']
        def paths(values, directory):
            return ['CAPSULE' if Path(p).resolve() == directory else str(Path(p).resolve()).lower() for p in values]
        if (access['env'] != reference['env']
                or paths(access['sys_path'], cap) != paths(reference['sys_path'], Path(probe_result['capsule']).resolve())):
            raise ValueError('reader environment or import path differs from its probed boundary')
    missing_execution = [k for k in ('receipt', 'access') if k in missing]
    return {'status': 'VERIFIED' if result['accepted'] else
                     ('INCOMPLETE_FAILED_RETAINED' if missing_execution else 'FAILED_RETAINED'),
            'accepted': result['accepted'], 'returncode': result['rc'],
            'copied_source_sha256': digest(expected_sources), 'denial_probe': probe,
            'actual_output_hashes': {k: file_hash(cap / 'out' / (k + '.json'))
                                    for k in ('prediction', 'receipt', 'error', 'access') if k not in missing},
            'missing_execution_outputs': missing_execution, 'scientific_admission': False,
            'remaining_validation': 'original caller source bindings, data/adapter semantics and complete workload coverage'}


def queue_audits(plan, queue_path, prior):
    """Cover flat/nested call caches and explicit per-job copied-package rosters."""
    from .closure_probe import bindings
    from .closure_storage import inventory
    from .queue import verify_committed
    reviews = plan.get('capsule_reviews', {})
    if not isinstance(reviews, dict) or not set(reviews) <= set(prior):
        raise ValueError('capsule review must name original prior jobs')
    state = read_status(queue_path / 'STATUS.json'); result = {}
    for key, job in prior.items():
        current = state['jobs'][key]
        if current['status'] != 'COMPLETE':
            if key in reviews:
                result[key] = {'status': current['status'], 'reason': current['reason'],
                               'disposition_sha256': current['disposition_sha256'], 'scientific_admission': False}
            continue
        directory = (REPO / job['produces']).parent.resolve()
        done = read(REPO / job['produces'])
        storage = inventory(directory, done.get('outputs', {}), REPO)
        calls = [REPO / name for name in storage['call_files']]
        if not calls and key not in reviews:
            continue
        if not calls or key not in reviews:
            raise ValueError('all committed reader calls require an explicit original capsule review')
        review = reviews[key]
        packages = review.get('packages') if isinstance(review, dict) and set(review) == {'packages'} else [review]
        if not isinstance(packages, list) or not packages:
            raise ValueError('capsule review requires an explicit nonempty package roster')
        verified = {}
        for package in packages:
            if (not isinstance(package, dict) or set(package) != {'runtime', 'probe_job'}
                    or package['probe_job'] not in prior or package['runtime'] in verified):
                raise ValueError('capsule review requires unique original runtimes and prior probe jobs')
            probe_id = package['probe_job']; probe_job = prior[probe_id]
            required = {'job': probe_id, 'field': ['isolation_probe_verified'], 'equals': True}
            if (probe_job['module'] != 'runners.stage9.closure_probe' or state['jobs'][probe_id]['status'] != 'COMPLETE'
                    or probe_id not in job['after'] or required not in job.get('requires', [])):
                raise ValueError('reader did not require the actual successful isolation probe')
            verify_committed(queue_path, probe_job, plan, digest(plan))
            probe_directory = (REPO / probe_job['produces']).parent
            binding = bindings(package['runtime'], plan['sources'])
            if read(probe_directory / 'BINDING.json') != binding:
                raise ValueError('actual probe tested a different copied package')
            verified[package['runtime']] = {'binding': binding, 'probe': read(probe_directory / 'PROBE.json'),
                                          'complete_sha256': file_hash(probe_directory / 'COMPLETE.json')}
        checked = []
        for path in sorted(calls):
            call = read(path)
            matched = [runtime for runtime, value in verified.items()
                       if call['result']['copied_sources']['files'] == value['binding']['copied_sources']]
            if len(matched) != 1:
                raise ValueError('actual reader call does not match one original probed package')
            runtime = matched[0]; value = verified[runtime]
            checked.append({'call_sha256': file_hash(path), 'path': path.relative_to(REPO).as_posix(),
                            'runtime': runtime,
                            'inspection': inspect_call(call['result'], value['binding']['copied_sources'], value['probe'])})
        for retained in storage['uncached_capsules']:
            copied = read(REPO / retained['source_closure'])
            matched = [runtime for runtime, value in verified.items() if copied['files'] == value['binding']['copied_sources']]
            if len(matched) != 1:
                raise ValueError('uncached capsule does not match one original reviewed package')
            retained['runtime'] = matched[0]
        result[key] = {'status': 'INSPECTED', 'calls': checked, 'call_count': len(checked),
                       'probes': {runtime: value['complete_sha256'] for runtime, value in verified.items()},
                       'storage': storage, 'scientific_admission': False}
        if len(verified) == 1:
            result[key]['probe_complete_sha256'] = next(iter(verified.values()))['complete_sha256']
    return {'jobs': result, 'scope': 'committed flat/nested call storage and explicit mixed-package rosters; uncached capsules remain unresolved',
            'scientific_admission': False}
