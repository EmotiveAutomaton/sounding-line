"""Exact-commit ToMpathy interface, without an editable engine fork.

DESIGN CHECK: LESSONS 2-5. NULL: changed capsule, missing times, invented
identities or missing admission witnesses refuse. ALTERNATIVE: a pinned
canonical engine imports normalized constructed records reproducibly. Software
conformance does not admit human evidence or a predictive engine module.
"""
import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
from runners.stage14.common import REPO, freeze, read, filehash

COMMIT = '82789fdb50d9366ab9352129b01ee37622554dfa'
CAPSULE = REPO/'.agent-state/next-round-20261014'/('engine-'+COMMIT[:12])


def snapshot(source, interpreter, destination=CAPSULE):
    source, interpreter, destination = Path(source).resolve(), Path(interpreter).resolve(), Path(destination).resolve()
    if destination.exists():
        verify(destination)
        return read(destination/'PIN.json')
    command = ['git', '-c', 'safe.directory='+source.as_posix(), '-C', str(source), 'archive', COMMIT, 'engine']
    archive = subprocess.run(command, check=True, capture_output=True).stdout
    destination.mkdir(parents=True)
    (destination/'source.tar').write_bytes(archive)
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        for member in stream.getmembers():
            target = (destination/member.name).resolve()
            if not target.is_relative_to(destination) or not (member.isfile() or member.isdir()):
                raise ValueError('unsafe archive member')
            if member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(stream.extractfile(member).read())
    pins = {p.relative_to(destination).as_posix(): filehash(p) for p in sorted((destination/'engine').rglob('*')) if p.is_file()}
    pin = dict(commit=COMMIT, files=pins, archive_sha256=filehash(destination/'source.tar'),
               interpreter=str(interpreter), interpreter_sha256=filehash(interpreter),
               editable=False, scientific_admission=False)
    freeze(destination/'PIN.json', pin)
    return pin


def verify(destination=CAPSULE):
    destination=Path(destination)
    pin = read(destination/'PIN.json')
    if pin['commit'] != COMMIT or filehash(destination/'source.tar') != pin['archive_sha256']:
        raise ValueError('engine source identity differs')
    actual = {p.relative_to(destination).as_posix() for p in (destination/'engine').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    if actual != set(pin['files']): raise ValueError('engine capsule file set changed')
    for name, sha in pin['files'].items():
        if filehash(destination/name) != sha: raise ValueError('engine capsule changed')
    if filehash(Path(pin['interpreter'])) != pin['interpreter_sha256']:
        raise ValueError('interpreter changed')
    return pin


def run(code, args=(), destination=CAPSULE):
    destination=Path(destination); pin=verify(destination)
    prefix = ('import sys; from pathlib import Path; import tompathy_engine; '
              'assert Path(tompathy_engine.__file__).resolve().is_relative_to(Path(sys.argv[1]).resolve()); '
              'sys.argv=sys.argv[1:]; ')
    env = dict(os.environ, PYTHONPATH=str(destination/'engine'), PYTHONDONTWRITEBYTECODE='1',
               OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', PYTHONIOENCODING='utf8')
    return subprocess.run([pin['interpreter'], '-B', '-c', prefix+code, str(destination/'engine'), *map(str,args)],
                          cwd=destination, env=env, capture_output=True, text=True, timeout=180, check=True)


def validate_exchange(payload):
    """Validate the exchange boundary without inventing dataset-specific semantics."""
    if not payload.get('codebook') or len(payload.get('source_sha256','')) != 64:
        raise ValueError('pinned source and codebook required')
    if payload['expected_rows'] != len(payload['rows']): raise ValueError('row census mismatch')
    keys = set()
    for row in payload['rows']:
        if row['id'] in keys: raise ValueError('duplicate source row')
        keys.add(row['id'])
        for field in ('t_open','t_resolve'):
            if row.get(field):
                from datetime import datetime
                if datetime.fromisoformat(row[field]).tzinfo is None: raise ValueError('timezone absent')
        if row.get('t_open') and row.get('t_resolve'):
            from datetime import datetime
            if datetime.fromisoformat(row['t_resolve']) < datetime.fromisoformat(row['t_open']): raise ValueError('reversed chronology')
        options=[o['id'] for o in row['options']]
        if len(set(options)) != len(options): raise ValueError('duplicate option')
        if row.get('taken') is not None and row['taken'] not in options: raise ValueError('taken option absent')
    return payload


def ingest_panel(source, ledger, destination=CAPSULE):
    source,ledger=Path(source).resolve(),Path(ledger).resolve()
    if not ledger.is_relative_to(REPO/'results/phase_2_4_stage_15/raw'):
        raise ValueError('research ledger must stay in private Stage 15 raw tree')
    validate_exchange(read(source))
    return run('from tompathy_engine.cli import main; main(sys.argv[1:])',
               ['ingest','--adapter','panel','--source',source,'--ledger',ledger],destination)


if __name__ == '__main__':
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='command',required=True)
    s=sub.add_parser('snapshot');s.add_argument('--source',required=True);s.add_argument('--interpreter',required=True)
    sub.add_parser('verify');sub.add_parser('probe')
    s=sub.add_parser('panel');s.add_argument('--source',required=True);s.add_argument('--ledger',required=True)
    a=p.parse_args()
    if a.command=='snapshot': print(json.dumps(snapshot(a.source,a.interpreter)))
    elif a.command=='verify': print(json.dumps({'commit':verify()['commit'],'verified':True}))
    elif a.command=='probe': print(run('from tompathy_engine.cli import main; main(["--help"])').stdout)
    else: print(ingest_panel(a.source,a.ledger).stdout)
