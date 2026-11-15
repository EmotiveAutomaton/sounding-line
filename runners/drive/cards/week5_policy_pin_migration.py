"""Exact archived policy compatibility for the AT/BK Week 5 recovery only.

DESIGN CHECK: LESSONS 3-5. Under either scientific direction, unknown bytes,
changed non-policy pins, missing archives and a changed AT/BK ceiling refuse.
Only the previously ratified MD/EX allocation line may differ; old evidence
remains immutable and new execution uses the current separately pinned runtime.
"""
from pathlib import Path
from .batch_runtime import REPO, filehash

POLICY = REPO/'runners/drive/cards/week5_policy_v2.py'
ARCHIVE = REPO/'results/phase_2_4_stage_15/raw/drive-week5-20261107/BK-V1-output-accounting-recovery-19-20261110/source_capsule/runners/drive/cards/week5_policy_v2.py'
OLD = 'f8372703690139fac196f2657de9a88e9dfcade4b63fdffa75744352445e0f0c'
CURRENT = 'ceadda545ebe09dce71d85932e449ef217575b9b26ccdd94898de82d0b7edc82'
OLD_LINE = b'GO=600000, MD=34400, LA=450000, ID=40000, BK=1000000)'
NEW_LINE = b'GO=600000, MD=120000, LA=450000, ID=40000, BK=1000000, EX=100000)'

def qualify():
    if filehash(ARCHIVE) != OLD or filehash(POLICY) != CURRENT:
        raise ValueError('Unreviewed policy epoch or missing historical capsule')
    old = ARCHIVE.read_bytes(); current = POLICY.read_bytes()
    if old.count(OLD_LINE) != 1 or old.replace(OLD_LINE, NEW_LINE) != current:
        raise ValueError('Policy transition is not the exact ratified MD/EX line')
    return dict(original_path=str(POLICY), original_sha256=OLD,
                preserved_path=str(ARCHIVE), current_sha256=CURRENT,
                affected_families=['MD','EX'], admitted_families=['AT','BK'])

def normalize(pins, family):
    """Validate every historical byte; return explicit current execution pins."""
    if family not in {'AT','BK'}:
        raise ValueError('Policy compatibility is restricted to AT/BK')
    translated = {}; aliases = {}; changed = False
    for name, digest in pins.items():
        p = Path(name)
        if not p.is_absolute(): p = REPO/p
        p = p.resolve(); p.relative_to(REPO.resolve())
        key = str(p).casefold()
        if key in aliases and aliases[key] != digest:
            raise ValueError('Conflicting historical pin aliases')
        aliases[key] = digest
        if p == POLICY.resolve() and digest == OLD:
            qualify(); translated[str(p)] = CURRENT; changed = True
        else:
            if filehash(p) != digest:
                raise ValueError('Frozen dependency changed: '+str(p))
            translated[str(p)] = digest
    if changed: translated[str(ARCHIVE.resolve())] = OLD
    return translated
