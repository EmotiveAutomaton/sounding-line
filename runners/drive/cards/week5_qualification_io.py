"""Explicit child-local publication adapter for new qualification attempts.

No numerical operation or supervisor rule is changed. JSON uses the existing
supervisor's UUID temporary-file convention. Fit arrays write directly to a
new final name, then seal; unsealed crash output is never an admissible resume.
"""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import json
import os
import time
import uuid
import numpy as np


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.' + uuid.uuid4().hex + '.tmp')
    with temp.open('x', encoding='utf8', newline='\n') as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + '\n')
    for attempt in range(10):
        try:
            os.replace(temp, path)
            return
        except PermissionError:
            if attempt == 9:
                raise
            time.sleep(.02 * (attempt + 1))


def save_fit(path, binding, fit):
    path = Path(path)
    if path.exists() or path.with_suffix('.sha256.json').exists():
        raise ValueError('Refusing to overwrite a sealed or unsealed numerical fit')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        np.savez_compressed(stream, **{key: np.asarray(value) for key, value in fit.items()})
    write_json(path.with_suffix('.sha256.json'), dict(binding=binding, sha256=sha(path)))


@contextmanager
def publication(writers, fit_writers=()):
    """Install only named publication callables in this one native child."""
    originals = []
    try:
        for module, name in writers:
            originals.append((module, name, getattr(module, name)))
            setattr(module, name, write_json)
        for module, name in fit_writers:
            originals.append((module, name, getattr(module, name)))
            setattr(module, name, save_fit)
        yield
    finally:
        for module, name, function in reversed(originals):
            setattr(module, name, function)
