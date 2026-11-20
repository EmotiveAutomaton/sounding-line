"""Portable support for sealed aggregate jobs; no data are loaded on import.

DESIGN CHECK: LESSONS 2-5. The writer requires actual integer person counts;
missing identifiers never become row counts. Small cells are suppressed; an
oversized table fails rather than silently truncating. Read budgets are charged
before each whole-file read. Fixtures must exercise each refusal as well as
ordinary output. Passing this mechanical boundary is not scientific admission.
"""
import csv
import io
import math
import numbers
from pathlib import Path

MIN_N = 11
MAX_ROWS = 2000
MAX_BYTES = 262144
MAX_READ_BYTES = 2_000_000_000


class SealedFailure(Exception):
    def __init__(self, code, reason):
        self.code = code
        super().__init__(reason)


def force_threads(count=2):
    import os
    if type(count) is not int or count not in (1, 2, 3, 4):
        raise ValueError('At most four numerical threads on the sealed lane')
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
                 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
        os.environ[name] = str(count)
    os.environ['CUDA_VISIBLE_DEVICES'] = ''


class ReadBudget:
    def __init__(self, root, maximum=MAX_READ_BYTES):
        self.root = Path(root).resolve(strict=True)
        self.maximum = maximum
        self.charged = 0

    def reserve(self, path, passes=1):
        p = Path(path)
        if p.is_symlink() or not p.is_file():
            raise SealedFailure(13, 'Expected a regular source file')
        p = p.resolve(strict=True)
        try:
            p.relative_to(self.root)
        except ValueError:
            raise SealedFailure(13, 'Source path outside the declared mount') from None
        if type(passes) is not int or passes < 1:
            raise ValueError('Positive read-pass count required')
        charge = p.stat().st_size * passes
        if self.charged + charge > self.maximum:
            raise SealedFailure(13, 'Private-source read allowance exceeded')
        self.charged += charge
        return p


def unique_people(values):
    if values is None:
        raise SealedFailure(12, 'A participant identifier is required for any returned count')
    people = set()
    for value in values:
        if value is None or (isinstance(value, float) and not math.isfinite(value)) or value == '':
            continue
        people.add(value)
    return len(people)


def write_tables(out, tables):
    """Validate the entire result set before creating any file.

    Caller supplies only reviewed aggregate fields, never identifiers or raw text.
    The separate installed gate remains authoritative and is not changed here.
    """
    payloads, dropped = {}, {}
    for name, rows in tables.items():
        if not name or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_' for c in name):
            raise SealedFailure(14, 'Neutral fixed table names required')
        kept = []
        dropped[name] = 0
        for row in rows:
            n = row.get('n')
            if not isinstance(n, numbers.Integral) or isinstance(n, bool) or n < 0:
                raise SealedFailure(14, 'Count must already be a nonnegative integer number of people')
            if n < MIN_N:
                dropped[name] += 1
                continue
            kept.append(dict(row, n=int(n)))
        if not kept:
            continue
        if len(kept) > MAX_ROWS:
            raise SealedFailure(14, 'Too many aggregate rows; no truncation permitted')
        columns = list(kept[0])
        if any(set(r) != set(columns) for r in kept):
            raise SealedFailure(14, 'Nonuniform aggregate columns')
        s = io.StringIO(newline='')
        writer = csv.DictWriter(s, fieldnames=columns, lineterminator='\n')
        writer.writeheader()
        writer.writerows(kept)
        payloads[name+'.csv'] = s.getvalue().encode('utf-8')
    if not payloads:
        raise SealedFailure(12, 'No publishable status or result row')
    if sum(map(len, payloads.values())) > MAX_BYTES:
        raise SealedFailure(14, 'Aggregate output byte limit exceeded')
    out = Path(out)
    if not out.is_dir():
        raise SealedFailure(11, 'Output directory unavailable')
    if any(out.iterdir()):
        raise SealedFailure(14, 'Fresh empty output directory required')
    for name, payload in payloads.items():
        with (out/name).open('xb') as f:
            f.write(payload)
    return dict(written={n:len(b) for n,b in payloads.items()}, dropped=dropped)
