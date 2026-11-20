"""Exact-edition acquisition for one sealed joined MIDUS mount."""
from hashlib import sha256

from week6_sealed_support_v1 import ReadBudget, SealedFailure


def resolve_wave(root, source_map):
    """Resolve one approved edition pair. Do not follow links or crawl other mounts."""
    if not root.is_dir() or root.is_symlink():
        raise SealedFailure(11, "Joined source folder unavailable")
    entries = {entry.name for entry in root.iterdir()}
    matches = [
        wave for wave, roles in source_map.items()
        if all(record["filename"] in entries for record in roles.values())
    ]
    if len(matches) != 1:
        raise SealedFailure(11, "Joined wave is missing or ambiguous")
    wave = matches[0]
    if any(
        record["filename"] in entries
        for other_wave, roles in source_map.items() if other_wave != wave
        for record in roles.values()
    ):
        raise SealedFailure(11, "Additional wave requires reviewed linkage")
    return wave


def take_snapshot(root, private_dir, source_map, maximum, combined_wave=None):
    """Count mount reads once. Both computations reread the authenticated private copy."""
    if combined_wave is None:
        wave = resolve_wave(root, source_map)
    else:
        if combined_wave not in ("M2", "M3") or set(source_map) != {"M2", "M3"}:
            raise SealedFailure(11, "Combined source requires both frozen editions")
        if not root.is_dir() or root.is_symlink():
            raise SealedFailure(11, "Combined source folder unavailable")
        required = {r["filename"] for roles in source_map.values() for r in roles.values()}
        if len(required) != 4 or not required.issubset(p.name for p in root.iterdir()):
            raise SealedFailure(11, "Incomplete combined source")
        wave = combined_wave
    budget = ReadBudget(root, maximum)
    snapshots = {}
    for role, record in sorted(source_map[wave].items()):
        source = root / record["filename"]
        source = budget.reserve(source)
        if record["bytes"] > 32_000_000:
            raise SealedFailure(13, "Frozen per-file allowance exceeded")
        destination = private_dir / (role + ".sav")
        digest = sha256()
        size = 0
        with source.open("rb") as incoming, destination.open("xb") as saved:
            for block in iter(lambda: incoming.read(1 << 20), b""):
                size += len(block)
                if size > record["bytes"]:
                    raise SealedFailure(11, "Source edition size differs")
                digest.update(block)
                saved.write(block)
        if size != record["bytes"] or digest.hexdigest() != record["sha256"]:
            raise SealedFailure(11, "Source edition identity differs")
        snapshots[role] = destination
    return wave, snapshots


def read_roles(snapshots, selections):
    import pyreadstat

    tables = {}
    for role, path in snapshots.items():
        names = list(selections[role])
        if len(names) != len(set(names)) or not names:
            raise SealedFailure(11, "Frozen source columns are invalid")
        frame, _ = pyreadstat.read_sav(
            str(path), usecols=names, user_missing=True,
            apply_value_formats=False, disable_datetime_conversion=True,
        )
        if set(frame.columns) != set(names) or len(frame.columns) != len(names) or len(frame) > 25000:
            raise SealedFailure(11, "Frozen source columns or row limit differs")
        tables[role] = frame.to_dict(orient="records")
    return tables
