"""Atomic administrative status writes; never replace a result or research registry."""
import errno
import json
import os
import tempfile
import time
from pathlib import Path


def save_status(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    tmp = Path(name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
            json.dump(state, stream, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        for attempt in range(20):
            try:
                os.replace(tmp, path)
                return
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EPERM, errno.EINVAL) or attempt == 19:
                    raise
                time.sleep(0.25)
    finally:
        tmp.unlink(missing_ok=True)
