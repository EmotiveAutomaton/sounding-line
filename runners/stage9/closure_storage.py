"""Read-only inventory of flat and nested immutable reader storage.

DESIGN CHECK: B03/X02/X06/X12; LESSONS 3--5, CONTROLS 6--7.
NULL: omitted bytes, an unknown sidecar, a capsule reused by two cached calls,
or an uncached partial silently counted as a completed call must refuse or retain
an explicit unresolved disposition. ALTERNATIVE: exact committed files separate
call caches, copied capsules and their original source-closure records without
executing a reader. Uncached capsules never gain an execution or scientific claim;
their actual attempt attribution and costs remain the enclosing ledger's duty.
"""
from pathlib import Path

from . import common
from .common import closure, digest, file_hash, read


def inventory(directory, outputs, repository):
    directory, repository = Path(directory).resolve(), Path(repository).resolve()
    declared = {(repository / name).resolve(): sha for name, sha in outputs.get('files', {}).items()}
    local = {path: sha for path, sha in declared.items() if path.is_relative_to(directory)}
    roots = {directory.joinpath(*path.relative_to(directory).parts[:path.relative_to(directory).parts.index('calls') + 1])
             for path in local if 'calls' in path.relative_to(directory).parts}
    if not roots:
        return {'call_files': [], 'capsules': [], 'uncached_capsules': [], 'scientific_admission': False}
    # Compare all bytes, not merely JSON names. Ancillary capsule files are outputs.
    for root in roots:
        actual = {(common.REPO / name).resolve(): sha for name, sha in closure([root])['files'].items()}
        expected = {path: sha for path, sha in local.items() if path.is_relative_to(root)}
        if actual != expected:
            raise ValueError('reader storage contains missing, changed or uncommitted files')
    capsules = {path.parent for path in local if path.name == 'bootstrap.py'}
    if any(first != second and first.is_relative_to(second) for first in capsules for second in capsules):
        raise ValueError('nested capsule ownership is ambiguous')
    sidecars = {cap.parent / 'closures' / (cap.name + '.json'): cap for cap in capsules}
    calls = {}; used = set()
    def relative(path):
        return path.relative_to(repository).as_posix()
    for path in sorted(local):
        if not any(path.is_relative_to(root) for root in roots):
            continue
        if any(path.is_relative_to(cap) for cap in capsules) or path in sidecars:
            continue
        if path.suffix != '.json':
            raise ValueError('unsupported file outside a reader capsule or call cache')
        cached = read(path)
        if (not isinstance(cached, dict) or set(cached) != {'input_sha256', 'result'}
                or not isinstance(cached['input_sha256'], str) or len(cached['input_sha256']) != 64
                or not isinstance(cached['result'], dict)):
            raise ValueError('unsupported or incomplete saved reader call format')
        cap = Path(cached['result']['capsule']).resolve()
        if cap not in capsules or cap in used:
            raise ValueError('saved call lacks a committed capsule or reuses another call capsule')
        used.add(cap); calls[path] = cached
    records = []
    for sidecar, cap in sorted(sidecars.items()):
        actual = {(common.REPO / name).resolve(): sha for name, sha in closure([cap])['files'].items()}
        if actual != {path: sha for path, sha in local.items() if path.is_relative_to(cap)}:
            raise ValueError('capsule output contains missing, changed or uncommitted files')
        if sidecar not in local or file_hash(sidecar) != local[sidecar]:
            raise ValueError('capsule lacks its committed original source closure')
        copied = read(sidecar)
        if (not isinstance(copied, dict) or not copied.get('files')
                or copied.get('sha256') != digest(copied['files'])):
            raise ValueError('invalid original capsule source closure')
        for name, sha in copied['files'].items():
            path = cap / name
            if Path(name).is_absolute() or path.is_symlink() or not path.resolve().is_relative_to(cap):
                raise ValueError('copied source escapes the recorded capsule')
            if path.resolve() not in local or file_hash(path) != sha:
                raise ValueError('copied source missing or changed from original capsule closure')
        if digest(read(cap / 'task.json')) != copied['task_sha256']:
            raise ValueError('capsule task changed from original source closure')
        evidence = read(cap / 'evidence.json') if (cap / 'evidence.json').is_file() else None
        if digest(evidence) != copied['evidence_sha256']:
            raise ValueError('capsule evidence changed from original source closure')
        for cached in calls.values():
            if Path(cached['result']['capsule']).resolve() == cap and cached['result']['copied_sources'] != copied:
                raise ValueError('saved call differs from its original capsule source closure')
        output_names = [name for name in ('prediction', 'receipt', 'error', 'access') if (cap / 'out' / (name + '.json')).is_file()]
        records.append({'path': relative(cap), 'source_closure': relative(sidecar), 'copied_sources_sha256': copied['sha256'],
            'files_sha256': digest({relative(p): sha for p, sha in local.items() if p.is_relative_to(cap)}),
            'cached_call_present': cap in used, 'actual_output_records': output_names,
            'disposition': 'CACHED_CALL' if cap in used else 'UNCACHED_CAPSULE_RETAINED',
            'scientific_admission': False})
    uncached = [row for row in records if not row['cached_call_present']]
    return {'call_files': [relative(path) for path in sorted(calls)], 'capsules': records,
            'uncached_capsules': uncached, 'scientific_admission': False,
            'uncached_scope': 'bytes retained without inferring execution, cause, attempt attribution or scientific validity'}
