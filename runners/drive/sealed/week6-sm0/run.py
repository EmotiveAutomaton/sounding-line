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

force_threads(2)

"""SM0: minimum necessary, person-counted sealed tabular structure probe.

DESIGN CHECK: LESSONS 2-5. Missing identifiers never become row counts. Repeated
person rows count once. Counts below eleven are suppressed by the separate
writer. A read-cap or unknown format is unsupported, not an empty population.
Only fixed column-group flags leave the job; no names, identifiers or values.
This probe does not fit models or admit a scientific source.
"""
import csv
from pathlib import Path

GROUPS = {
    'wave2_daily': ('M2ID','B2DDAY','B2DWEEKD','B2DC17','B2DC19'),
    'wave3_daily': ('M2ID','C2DDAY','C2DWEEKD','C2DC17','C2DC19'),
    'wave2_traits': ('M2ID','B1SNEURO','B1SEXTRA','B1SAGREE'),
    'wave3_traits': ('M2ID','C1SNEURO','C1SEXTRA','C1SAGREE'),
}

def column_map(names):
    result={}
    for name in names:
        key=str(name).strip().upper()
        if key in result:
            raise SealedFailure(13,'Ambiguous case-folded source columns')
        result[key]=name
    return result

def inspect_table(path, budget):
    """Read only the ID column into memory; count all I/O conservatively."""
    path=Path(path)
    suffix=path.suffix.lower()
    if suffix in ('.csv','.tsv'):
        budget.reserve(path)
        with path.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.reader(f,delimiter='\t' if suffix=='.tsv' else ',')
            try: header=next(reader)
            except StopIteration: raise SealedFailure(12,'Empty table') from None
            mapping=column_map(header)
            if 'M2ID' not in mapping:
                raise SealedFailure(12,'Declared person field absent')
            index=header.index(mapping['M2ID'])
            people=set()
            for row in reader:
                if len(row)!=len(header):
                    raise SealedFailure(13,'Malformed delimited table')
                value=row[index].strip()
                if value: people.add(value)
            n=unique_people(people)
    elif suffix in ('.sav','.dta'):
        import pyreadstat
        read=pyreadstat.read_sav if suffix=='.sav' else pyreadstat.read_dta
        budget.reserve(path,passes=2)
        _,meta=read(str(path),metadataonly=True)
        mapping=column_map(meta.column_names)
        if 'M2ID' not in mapping:
            raise SealedFailure(12,'Declared person field absent')
        frame,_=read(str(path),usecols=[mapping['M2ID']],apply_value_formats=False)
        n=unique_people(frame[mapping['M2ID']].dropna().tolist())
    else:
        raise SealedFailure(10,'No supported tabular format')
    expected=sorted({c for columns in GROUPS.values() for c in columns})
    return dict(n=n,**{name:int(all(c in mapping for c in columns)) for name,columns in GROUPS.items()},
                **{'present_'+c:int(c in mapping) for c in expected})

def run(root,out,*,max_bytes=2_000_000_000):
    root=Path(root)
    budget=ReadBudget(root,max_bytes)
    candidates=sorted(p for p in root.rglob('*') if p.is_file() and p.suffix.lower() in ('.csv','.tsv','.sav','.dta'))
    if not candidates: raise SealedFailure(10,'No supported loose tabular file; archives require a separate reviewed adapter')
    rows=[]
    for i,p in enumerate(candidates):
        # A file without the declared ID cannot manufacture an exportable n.
        # The entire probe fails closed, rather than hiding incomplete coverage.
        record=inspect_table(p,budget)
        rows.append(dict(table=f'table_{i+1:03d}',**record))
    return write_tables(out,{'structure':rows})

def main():
    try:
        run('/data','/out')
    except SealedFailure as exc:
        raise SystemExit(exc.code) from None

if __name__=='__main__':
    main()
