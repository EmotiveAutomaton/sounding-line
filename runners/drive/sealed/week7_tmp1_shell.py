"""Reader-independent checks for the sealed TP58 job. This build cannot run a reader."""
import csv
import hashlib
import math
import os
from pathlib import Path
import re
import sys


# Populated only after review of the engine's frozen handoff. Keys are exact CSV
# basenames. Values bind an exact header, interval column pairs, and the permitted
# categorical values for each label column. Remaining columns must be numeric.
TP58_TABLES = {}


def check_image(sys_root=Path("/sys"), dev_root=Path("/dev")):
    interfaces = {path.name for path in (sys_root / "class/net").iterdir()}
    if interfaces != {"lo"}:
        raise ValueError("network isolation")
    if (any(dev_root.glob("nvidia*")) or (dev_root / "kfd").exists()
            or any((dev_root / "dri").glob("renderD*"))
            or any((dev_root / "accel").glob("accel*"))
            or any((dev_root / "infiniband").glob("*"))):
        raise ValueError("accelerator or fabric exposed")
    if os.environ.get("CUDA_VISIBLE_DEVICES", "") not in ("", "-1"):
        raise ValueError("CUDA visibility")
    # An actual CPU operation also exercises the image's numeric dependency.
    import numpy as np
    if np.dot(np.array([1, 2]), np.array([3, 4])) != 11:
        raise ValueError("CPU arithmetic")


def verify_bundle(root, reviewed_hashes):
    """Expected relative names and SHA-256 digests come from the reviewed manifest.

    The manifest itself is pinned separately, outside the payload tree.
    """
    if not reviewed_hashes or root.is_symlink() or not root.is_dir():
        raise ValueError("missing reviewed payload")
    seen = set()
    for path in root.rglob("*"):
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            raise ValueError("linked payload")
        if path.is_dir():
            continue
        name = path.relative_to(root).as_posix()
        if not path.is_file() or name not in reviewed_hashes:
            raise ValueError("unexpected payload")
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        if digest.hexdigest() != reviewed_hashes[name]:
            raise ValueError("payload digest")
        seen.add(name)
    if seen != set(reviewed_hashes):
        raise ValueError("incomplete payload")


def check_tables(directory, approved):
    """Validate private scratch outputs before any approved CSV enters /out."""
    if not approved or directory.is_symlink() or not directory.is_dir():
        raise ValueError("no release contract")
    files = list(directory.iterdir())
    if not files or any(p.name not in approved or p.suffix != ".csv" or
                        p.is_symlink() or not p.is_file() for p in files):
        raise ValueError("unapproved output")
    if sum(p.stat().st_size for p in files) > 262144:
        raise ValueError("output byte limit")
    for path in files:
        header, intervals, categories = approved[path.name]
        if (len(set(header)) != len(header) or "n" not in header or not intervals
                or "n" in categories or not set(categories) <= set(header)
                or any(lo == hi or {lo, hi} - (set(header) - set(categories) - {"n"})
                       for lo, hi in intervals)):
            raise ValueError("unreviewed counts or interval roles")
        with path.open(encoding="utf-8", newline="") as stream:
            rows = csv.reader(stream, strict=True)
            if next(rows, []) != list(header):
                raise ValueError("output header")
            count = 0
            for count, values in enumerate(rows, 1):
                if len(values) != len(header) or count > 2000:
                    raise ValueError("output shape")
                row = dict(zip(header, values))
                if not re.fullmatch(r"[1-9][0-9]*", row["n"]) or int(row["n"]) < 11:
                    raise ValueError("participant support")
                for key, value in row.items():
                    if key in categories:
                        if value not in categories[key]:
                            raise ValueError("unapproved label")
                    elif not math.isfinite(float(value)):
                        raise ValueError("nonfinite statistic")
                if any(float(row[lo]) > float(row[hi]) for lo, hi in intervals):
                    raise ValueError("unordered interval")
            if count == 0:
                raise ValueError("empty table")


def main(argv):
    # The image smoke check needs neither a data mount nor an output mount.
    if argv not in ([], ["--check-image"]):
        return 2
    if sys.platform != "linux":
        return 20
    try:
        check_image()
    except (OSError, ImportError, ValueError):
        return 20
    if argv == ["--check-image"]:
        return 0
    return 21  # Pending engine handoff. Never opens /data or writes /out.


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
