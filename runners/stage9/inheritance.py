"""Read-only inventory of inherited checkout bytes and measured reader exclusion.

DESIGN CHECK: Stage 9 I01/I02. A .git directory or an expected commit is not runnable
source. NULL: empty checkout, changed head, missing tracked bytes or capsule access
cannot pass as an executable reference. ALTERNATIVE: actual source state is receipted.
This module never checks out, installs or executes any reference component.
"""
import ast
from pathlib import Path
import subprocess
import time

from runners.stage9.common import REPO, ROOT, file_hash, read, write
from runners.stage9.runtime import execute


def literal(path, name):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    matches = [ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    if len(matches) != 1:
        raise ValueError('expected one reviewed literal')
    return matches[0]


def git(path, *arguments):
    # Disable optional writes and configured fsmonitor helpers even for read commands.
    command = ['git', '--no-optional-locks', '-c', 'core.fsmonitor=false', '-C', str(path), *arguments]
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=60)
    return {'returncode': result.returncode, 'stdout': result.stdout.strip(), 'stderr_present': bool(result.stderr)}


def audit():
    started = time.time()
    historical = read(REPO / 'results/phase_2_4_stage_8/TESTBED_SOURCES.json')['clones']
    path = REPO / 'runners/stage8/testbed/clones.py'
    definitions = literal(path, 'CLONES')
    if len(definitions) != 17:
        raise ValueError('inherited reference inventory changed')
    result, probe_paths = {}, []
    for name, definition in definitions.items():
        root = REPO.parent / 'reference' / name
        prior = historical[name]['receipt']
        record = {'repository': definition['repo'], 'operation': definition['card'],
                  'recorded_requested_commit': prior.get('head'), 'present': root.is_dir(),
                  'historical_materialized_files': prior.get('files_on_disk'),
                  'historical_read_only_flag_was_measured': False,
                  'component_execution': 'not performed; entrypoint/assets/environment acceptance required separately'}
        if root.is_dir():
            head = git(root, 'rev-parse', 'HEAD')
            status = git(root, 'status', '--porcelain=v1', '--untracked-files=normal')
            tracked = git(root, 'ls-files', '-z')
            tree = git(root, 'ls-tree', '-r', '-z', 'HEAD')
            head_entries = []
            if tree['returncode'] == 0:
                for entry in tree['stdout'].split('\0'):
                    if not entry:
                        continue
                    metadata, relative = entry.split('\t', 1)
                    mode, kind, sha = metadata.split()
                    head_entries.append({'mode': mode, 'kind': kind, 'sha': sha, 'path': relative})
            files = sorted(p for p in root.rglob('*') if '.git' not in p.relative_to(root).parts and p.is_file())
            regular = [p for p in files if not p.is_symlink()]
            code = [p for p in regular if p.suffix.lower() in ('.py', '.jl', '.m', '.r', '.cpp', '.c', '.rs', '.js')]
            missing = [p for p in tracked['stdout'].split('\0') if p and not (root / p).is_file()]
            missing_head = [e['path'] for e in head_entries if e['kind'] == 'blob' and not (root / e['path']).is_file()]
            record.update(current_head=head['stdout'] if head['returncode'] == 0 else None,
                          head_matches_requested=(head['stdout'] == prior.get('head')) if head['returncode'] == 0 else None,
                          head_returncode=head['returncode'],
                          status=status, tracked_inventory_returncode=tracked['returncode'],
                          head_tree_returncode=tree['returncode'], expected_head_files=sum(e['kind'] == 'blob' for e in head_entries),
                          missing_head_files=missing_head, submodules=[e for e in head_entries if e['mode'] == '160000'],
                          materialized_files=len(files), materialized_source_files=len(code),
                          missing_tracked_files=missing, link_paths=[p.relative_to(root).as_posix() for p in files if p.is_symlink()],
                          inspected_source_files={p.relative_to(root).as_posix(): file_hash(p) for p in code},
                          checkout_readiness=('NOT_EXECUTABLE_CHECKOUT' if not code or missing or missing_head else
                                              'UNVERIFIED_GIT_STATE' if head['returncode'] or tracked['returncode'] or tree['returncode'] or status['returncode'] else
                                              'PIN_OR_CHECKOUT_MISMATCH' if head['stdout'] != prior.get('head') or status['stdout'] else
                                              'MATERIALIZED_SOURCE_REQUIRES_OPERATION_REVIEW'))
            if regular:
                candidate = next((p for p in regular if p.name.lower().startswith('readme')), regular[0])
                record['reader_probe_file'] = candidate.relative_to(REPO.parent).as_posix()
                probe_paths.append(str(candidate))
            elif (root / '.git/HEAD').is_file():
                record['reader_probe_file'] = (root / '.git/HEAD').relative_to(REPO.parent).as_posix()
                probe_paths.append(str(root / '.git/HEAD'))
        result[name] = record
    access = execute(None, {'probe': True, 'forbidden_paths': probe_paths, 'other_port': 65534})
    receipt = {'at': time.time(), 'wall_seconds': time.time() - started, 'inherited_definition_sha256': file_hash(path),
               'references': result, 'reader_access': access,
               'measured_reference_reader_exclusion': access['accepted'],
               'reference_mutations': 'none requested; read-only git with optional locks/fsmonitor disabled',
               'scientific_operation_reproductions': 'not established by checkout inventory'}
    write(ROOT / 'intake/INHERITED_REFERENCES.json', receipt)
    return receipt


if __name__ == '__main__':
    import json
    result = audit()
    print(json.dumps({'references': len(result['references']), 'access_passed': result['measured_reference_reader_exclusion'],
                      'unready': [k for k, r in result['references'].items() if r.get('checkout_readiness') != 'MATERIALIZED_SOURCE_REQUIRES_OPERATION_REVIEW'],
                      'changed_heads': [k for k, r in result['references'].items() if r.get('head_matches_requested') is False],
                      'unverified_heads': [k for k, r in result['references'].items() if r.get('head_matches_requested') is None]}))
