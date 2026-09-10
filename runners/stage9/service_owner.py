"""Owner-only lifecycle for an offline local service; readers get no shutdown token.

DESIGN CHECK: I03/X12. An exited process or stale READY never counts as a live service.
NULL: startup/request failure is retained; no model substitution or unverified PID kill.
ALTERNATIVE: the exact launched service responds and shuts down through its own endpoint.
"""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
import urllib.request

from runners.stage9.common import REPO, closure, digest, file_hash, read, write


def execution_config(directory,config_path):
    """Track bytes compiled by the model process as well as the outer scheduler."""
    source=closure([REPO/'runners/stage9',REPO/'runners/stage7',REPO/'runners/stage8',REPO/'soundingline',
        REPO/'runners/__init__.py',REPO/'runners/readout_repair.py',
        REPO/'runners/s3_lib.py',REPO/'runners/s4_lib.py',REPO/'runners/s5_lib.py'])
    attempt=directory/'execution';attempt.mkdir()
    cell=os.environ.get('S9_CELL_IDENTITY') or digest({'discarded_service':str(directory),'sources':source['sha256']})
    config={'repo':str(REPO),'attempt':str(attempt),'sources':source,'cell_identity':cell,
        'module':'runners.stage9.model_service','arguments':[str(config_path)]}
    path=directory/'EXECUTION_CONFIG.json';write(path,config)
    return path,config


def verify_execution(directory,config):
    """A current-file hash alone does not identify what the resident compiled."""
    receipt=read(directory/'execution/EXECUTION.json');loaded=receipt['loaded_project_sources']
    required={'runners/stage9/source_bootstrap.py','runners/stage9/model_service.py',
        'runners/stage9/common.py','runners/stage9/neural.py','runners/stage9/train.py'}
    if (receipt['returncode']!=0 or receipt['error'] is not None or receipt['cell_identity']!=config['cell_identity']
        or not required<=loaded.keys() or any(config['sources']['files'].get(p)!=sha for p,sha in loaded.items())
        or closure([REPO/p for p in config['sources']['files']])!=config['sources']):
        raise ValueError('resident execution failed or its actual compiled source closure differs')
    return file_hash(directory/'execution/EXECUTION.json')


def post(endpoint, token, path, body, timeout=600):
    payload = json.dumps(body, ensure_ascii=False, allow_nan=False).encode('utf-8')
    request = urllib.request.Request(endpoint + path, payload,
                                    {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request, timeout=timeout) as response:
        raw = response.read(4 * 1024**2 + 1)
        if len(raw) > 4 * 1024**2:
            raise ValueError('oversized service response')
        return json.loads(raw) if raw else None


@contextmanager
def resident(directory, config):
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    settings = {**config, 'output': str(directory), 'port': 0,
                'token': secrets.token_hex(32), 'shutdown_token': secrets.token_hex(32)}
    write(directory / 'config.json', settings)
    bootstrap_path,bootstrap=execution_config(directory,directory/'config.json')
    environment = {**os.environ, 'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1', 'PYTHONDONTWRITEBYTECODE': '1'}
    started = time.time()
    command=[sys.executable, '-B', str(REPO/'runners/stage9/source_bootstrap.py'),str(bootstrap_path)]
    with (directory / 'stdout.log').open('wb') as stdout, (directory / 'stderr.log').open('wb') as stderr:
        process = subprocess.Popen(command,
                                   cwd=REPO, env=environment, stdout=stdout, stderr=stderr,
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        write(directory / 'OWNER.json', {'wrapper_pid': process.pid, 'launched_at': started,
                                         'command':command,'entrypoint':'runners.stage9.model_service', 'directory': str(directory)})
        ready = None
        try:
            while time.time() - started < 600:
                if process.poll() is not None:
                    raise RuntimeError('service exited before readiness; inspect private stderr')
                if (directory / 'READY.json').exists():
                    ready = read(directory / 'READY.json')
                    if ready['at'] < started:
                        raise ValueError('stale readiness')
                    break
                time.sleep(.25)
            if ready is None:
                raise TimeoutError('service startup timed out; native verified cleanup required')
            yield ready, settings['token']
        finally:
            stopped = False
            if ready and process.poll() is None:
                try:
                    post(ready['endpoint'], settings['shutdown_token'], '/shutdown', {}, timeout=20)
                    process.wait(timeout=30)
                    stopped = True
                except Exception as exc:
                    write(directory / 'SHUTDOWN_ERROR.json', {'error': repr(exc), 'at': time.time(),
                                                             'native_verified_cleanup_required': True})
            execution_sha,execution_error=None,None
            if stopped and process.returncode==0:
                try:execution_sha=verify_execution(directory,bootstrap)
                except Exception as exc:execution_error=repr(exc)
            write(directory / 'LIFECYCLE.json', {'started_at': started, 'ended_at': time.time(),
                                                'wrapper_pid': process.pid, 'worker_pid': ready['pid'] if ready else None,
                                                'returncode': process.poll(), 'graceful_shutdown': stopped,
                                                'compiled_execution_sha256':execution_sha,
                                                'compiled_execution_error':execution_error})
            if process.poll() is None:
                raise RuntimeError('owned service remains live; inspect and clean its verified native process before continuing')
            if execution_error:
                raise ValueError('resident compiled-source validation failed: '+execution_error)
