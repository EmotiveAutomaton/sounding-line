"""Finite local Stage 10 dependency queue; never a cloud or recursive dispatcher.

DESIGN CHECK: existing Stage 10 scope and LESSONS 2-5. Under either scientific
outcome, successful jobs advance once, failed branches block their dependants
while independent work continues, and complete evidence cannot be overwritten.
Ambiguous interrupted ownership refuses. No timer or healthy state invokes an
agent. The entire reviewed job list is frozen before execution.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from runners.stage9.process_identity import native_identity
from soundingline.gpulock import GPU_LOCK
from .contracts import digest
from .ollama import now, write_new
from .queue import read, status

REPO = Path(__file__).resolve().parents[2]


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def under(repo, name):
    path = (repo / name).resolve()
    if not path.is_relative_to(repo.resolve()) or path == repo.resolve():
        raise ValueError('runway path leaves its repository')
    return path


def validate(plan, repo=REPO):
    if set(plan) != {'schema', 'gear', 'scope', 'sources', 'jobs'} or plan['schema'] != 'stage10.local-runway.1' or plan['gear'] != 2:
        raise ValueError('explicit local Gear 2 runway required')
    if not plan['sources'] or not plan['jobs']:
        raise ValueError('empty source closure or job list')
    for name, expected in plan['sources'].items():
        if file_hash(under(repo, name)) != expected:
            raise ValueError('frozen runway source changed: ' + name)
    seen, outputs = set(), set()
    for job in plan['jobs']:
        if set(job) != {'id', 'module', 'args', 'requires', 'output', 'resource', 'purpose'}:
            raise ValueError('unexpected job fields')
        if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,70}', job['id']) or job['id'] in seen:
            raise ValueError('invalid or duplicate job identity')
        if not re.fullmatch(r'runners\.stage10\.[a-z_]+', job['module']) or 'gear3' in job['module']:
            raise ValueError('only local Stage 10 modules are allowed')
        source = job['module'].replace('.', '/') + '.py'
        if source not in plan['sources'] or not isinstance(job['args'], list) or not all(isinstance(x, str) for x in job['args']):
            raise ValueError('unfrozen command source or arguments')
        if not isinstance(job['requires'], list) or not set(job['requires']) <= seen or len(job['requires']) != len(set(job['requires'])):
            raise ValueError('dependencies must be unique, earlier reviewed jobs')
        output = under(repo, job['output'])
        if job['args'].count('--output') != 1:
            raise ValueError('one explicit output argument required')
        index = job['args'].index('--output') + 1
        if index >= len(job['args']) or under(repo, job['args'][index]) != output:
            raise ValueError('command output differs from declared produce')
        if not output.is_relative_to(repo / 'results/phase_2_4_stage_10/raw') or output in outputs:
            raise ValueError('invalid or reused output directory')
        if any(output.is_relative_to(old) or old.is_relative_to(output) for old in outputs):
            raise ValueError('job output directories overlap')
        if job['resource'] not in {'cpu', 'gpu'} or not job['purpose']:
            raise ValueError('declared resource and purpose required')
        seen.add(job['id']); outputs.add(output)
    return plan


def inventory(output):
    return {p.relative_to(output).as_posix(): file_hash(p)
            for p in sorted(output.rglob('*')) if p.is_file()}


def run(plan_path, output, *, repo=REPO, execute=None):
    plan = validate(read(plan_path), repo)
    output = output.resolve()
    if not output.is_relative_to(repo.resolve()):
        raise ValueError('runway state must stay in the repository')
    output.mkdir(parents=True, exist_ok=True)
    manifest = {'plan_sha256': digest(plan), 'runner_sha256': file_hash(Path(__file__))}
    if (output / 'MANIFEST.json').exists():
        if read(output / 'MANIFEST.json') != manifest:
            raise ValueError('cannot resume a changed runway')
    else:
        write_new(output / 'MANIFEST.json', manifest)
    if (output / 'OWNER.json').exists() and not (output / 'COMPLETE.json').exists():
        raise ValueError('interrupted runway requires explicit ownership inspection')
    if not (output / 'COMPLETE.json').exists():
        write_new(output / 'OWNER.json', {'native': native_identity(), 'at': now()})
    results = {}
    for job in plan['jobs']:
        validate(plan, repo)
        target = under(repo, job['output'])
        saved_path = output / 'jobs' / (job['id'] + '.json')
        if saved_path.exists():
            saved = read(saved_path)
            if saved['job_sha256'] != digest(job):
                raise ValueError('saved job differs from plan')
            if saved['status'] == 'COMPLETE' and saved['files'] != inventory(target):
                raise ValueError('completed job evidence changed')
            results[job['id']] = saved
            continue
        if (output / 'COMPLETE.json').exists():
            raise ValueError('complete runway missing a job; no recomputation')
        if (output / 'CANCEL').exists():
            raise RuntimeError('owner cancelled remaining local dispatch')
        blocked = [name for name in job['requires'] if results[name]['status'] != 'COMPLETE']
        if job['resource'] == 'gpu' and GPU_LOCK.exists():
            blocked.append('GPU ownership unresolved; no lock reclamation')
        record = {'job_sha256': digest(job), 'status': 'BLOCKED' if blocked else 'RUNNING',
                  'blocked_by': blocked, 'started_at': now()}
        if not blocked:
            if target.exists():
                raise ValueError('unowned existing output requires inspection: ' + job['id'])
            status(output / 'STATUS.json', {'at': now(), 'status': 'RUNNING', 'active_job': job['id'],
                                          'finished_jobs': list(results)})
            command = [sys.executable, '-B', '-X', 'utf8', '-m', job['module'], *job['args']]
            if execute is None:
                with (output / (job['id'] + '.stdout.log')).open('xb') as stdout, (output / (job['id'] + '.stderr.log')).open('xb') as stderr:
                    child = subprocess.Popen(command, cwd=repo, stdout=stdout, stderr=stderr,
                                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                    status(output / 'ACTIVE_PROCESS.json', {'job': job['id'], 'native': native_identity(child.pid), 'command': command})
                    code = child.wait()
            else:
                code = execute(job, target)
            terminal = target / 'COMPLETE.json'
            record.update(returncode=code, status='FAILED')
            if code == 0 and terminal.is_file() and read(terminal).get('status') == 'COMPLETE':
                record.update(status='COMPLETE', files=inventory(target))
            else:
                record['reason'] = 'nonzero exit or missing/invalid complete producer receipt'
        record['finished_at'] = now()
        write_new(saved_path, record); results[job['id']] = record
    result = {'status': 'COMPLETE', 'at': now(), 'manifest_sha256': digest(manifest),
              'jobs': results, 'all_jobs_succeeded': all(r['status'] == 'COMPLETE' for r in results.values()),
              'scope': 'finite local queue disposition; scientific acceptance requires complete comparison/report write-through'}
    if (output / 'COMPLETE.json').exists():
        saved = read(output / 'COMPLETE.json')
        if any(saved[k] != result[k] for k in result.keys() - {'at'}):
            raise ValueError('complete runway differs')
        return saved
    write_new(output / 'COMPLETE.json', result)
    status(output / 'STATUS.json', {'at': now(), 'status': 'COMPLETE', 'all_jobs_succeeded': result['all_jobs_succeeded']})
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        run(args.plan, args.output)
    except Exception as exc:
        if not (args.output / 'FAILED.json').exists():
            write_new(args.output / 'FAILED.json', {'at': now(), 'error': repr(exc)})
        raise
