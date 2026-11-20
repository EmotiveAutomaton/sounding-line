"""Exact local review is independent of publication; no Git mutation occurs here.

DESIGN CHECK: LESSONS 3-5, 2026-11-19. Null and alternative receive identical
admission. Missing, changed, failed or wrong-scope evidence refuses. A reviewed
uncommitted design can pass; publication status conveys no scientific authority.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import subprocess
from .batch_runtime import REPO, read, filehash, check_files
from .week6_transition_services_v4 import regular, require_exited

AUTHORITY = REPO / 'docs/design/stage-15/week6/LOCAL_REVIEW_ADMISSION_20261119.md'


def need(condition, message):
    if not condition:
        raise ValueError(message)


def contract_digest(plan):
    """Bind every plan field except this manifest's self-reference."""
    import json
    value = deepcopy(plan)
    binding = value.pop('reviewed_local_manifest', None)
    if binding:
        value['pins'].pop(str(Path(binding['path']).resolve()), None)
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                      ensure_ascii=True).encode('utf8')).hexdigest()


def pinned(plan, path, digest):
    path = regular(Path(path).resolve())
    need(plan['pins'].get(str(path)) == digest == filehash(path),
         'Local review evidence missing or changed: ' + str(path))
    return path


def review_design(plan):
    need(plan.get('owner_reviewed') is True and plan.get('fixture_passed') is True,
         'Owner review and passed fixture required')
    design = Path(plan['design']).resolve()
    rel = design.relative_to(REPO).as_posix()
    pinned(plan, design, plan['pins'].get(str(design)))
    binding = plan.get('reviewed_local_manifest')
    if binding is None:
        commit = plan.get('reviewed_design_commit')
        need(isinstance(commit, str) and bool(commit), 'Exact local review or actual commit required')
        content = subprocess.run(['git', 'show', commit + ':' + rel], cwd=REPO,
                                 capture_output=True, check=True).stdout
        need(content == design.read_bytes(), 'Design is not the reviewed committed version')
        return 'committed'
    need(not plan.get('reviewed_design_commit'), 'Local review must not masquerade as a commit')
    manifest = read(pinned(plan, binding['path'], binding['sha256']))
    need(manifest.get('schema') == 'WEEK6_LOCAL_REVIEW_V1' and
         manifest.get('owner_reviewed') is True, 'Wrong or unreviewed local manifest')
    need(bool(plan.get('review_owner')) and manifest.get('owner') == plan['review_owner'],
         'Local review owner differs')
    stamp = datetime.fromisoformat(manifest['at'])
    need(stamp.tzinfo is not None and stamp <= datetime.now(timezone.utc), 'Invalid local review clock')
    need(manifest.get('plan_sha256') == contract_digest(plan), 'Reviewed plan changed')
    authority = manifest['authority']
    need(Path(authority['path']).resolve() == AUTHORITY.resolve(), 'Wrong local review authority')
    pinned(plan, authority['path'], authority['sha256'])
    fixtures = manifest.get('fixtures', [])
    need(bool(fixtures), 'Passed native qualification evidence required')
    for fixture in fixtures:
        path = pinned(plan, fixture['path'], fixture['sha256'])
        need(str(path) in plan['validation_receipts'], 'Fixture omitted from validation receipts')
        value = read(path)
        need(value.get('status') == 'COMPLETE' and value.get('error') is None and
             value.get('constructed_only') is True and value.get('lease_released') is True,
             'Native fixture did not pass and release its lease')
        need(type(fixture['cases']) is int and fixture['cases'] > 0 and
             value.get('cases') == fixture['cases'], 'Native fixture case count differs')
        need(bool(value.get('source_pins')) and bool(value.get('outputs')),
             'Native fixture source/output evidence absent')
        for source, digest in value['source_pins'].items():
            pinned(plan, source, digest)
        check_files(value['outputs'])
        qualification_plan = read(path.parent / 'PLAN.json')
        require_exited(qualification_plan['owner'])
        require_exited(read(path.parent / 'CHILD.json')['native'])
    return 'local-reviewed'
