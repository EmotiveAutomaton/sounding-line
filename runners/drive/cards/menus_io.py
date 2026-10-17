"""Private, deterministic I/O for the October 17 menu cards."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(Path(path).read_text(encoding="utf8"))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf8", newline="\n") as stream:
        json.dump(value, stream, sort_keys=True, separators=(",", ":"), allow_nan=False)
        stream.write("\n")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def assert_equal(actual, expected):
    if canonical(actual) != canonical(expected):
        raise ValueError("saved primary recomputation differs")


def input_hashes(inputs):
    return {key: sha256(value) for key, value in sorted(inputs.items())
            if isinstance(value, (str, Path)) and Path(value).is_file()}
