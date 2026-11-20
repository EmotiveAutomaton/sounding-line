"""SM0: minimum necessary, person-counted sealed tabular structure probe.

DESIGN CHECK: LESSONS 2-5. Missing identifiers never become row counts. Repeated
person rows count once. Counts below eleven are suppressed by the separate
writer. A read-cap or unknown format is unsupported, not an empty population.
Only fixed column-group flags leave the job; no names, identifiers or values.
This probe does not fit models or admit a scientific source.
"""
import csv
from pathlib import Path
from runners.drive.cards.week6_sealed_support_v1 import ReadBudget, SealedFailure, unique_people, write_tables

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
