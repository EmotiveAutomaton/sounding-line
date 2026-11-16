"""Constructed literal bank copied by AST source spans; no generated labels.

DESIGN CHECK: unchanged original eight-column B2 known-answer cases. Parent
source SHA256 25c5f075a68ade835f1c34fb51721a92181e49db281144bf3ff03689b9801f7c.
Only the original constants and five fixture-envelope helpers are included;
no original tests execute on import, and no human source is referenced.
"""
import csv
import gzip
import io
import json
import tarfile
from runners.theory_days import moral

COLUMNS = ('ResponseID', 'ExtendedSessionID', 'UserID', 'Intervention',
           'Saved', 'AttributeLevel', 'ScenarioType', 'ScenarioTypeStrict')

VALID = [
    ('FOCAL-S', ('Species', 'Species', 'Humans'), ('Species', 'Species', 'Pets'), 'Species'),
    ('FOCAL-S-ALIAS', ('Species', 'Species', 'Hoomans'), ('Species', 'Species', 'Pets'), 'Species'),
    ('FOCAL-G', ('Gender', 'Gender', 'Female'), ('Gender', 'Gender', 'Male'), 'Gender'),
    ('FOCAL-G-ALIASES', ('Gender', 'Gender', 'Females'), ('Gender', 'Gender', 'Males'), 'Gender'),
    ('FOCAL-F', ('Fitness', 'Fitness', 'Fit'), ('Fitness', 'Fitness', 'Fat'), 'Fitness'),
    ('NONFOCAL', ('Age', 'Age', 'Young'), ('Age', 'Age', 'Old'), None),
    ('UNKNOWN-TYPE', ('Unknown', 'Unknown', 'Alpha'), ('Unknown', 'Unknown', 'Beta'), None),
    ('EMPTY-METADATA', ('', '', ''), ('', '', ''), None),
    ('UNKNOWN-LEVEL', ('Species', 'Species', 'Unknown'), ('Species', 'Species', 'Pets'), None),
    ('EMPTY-LEVEL', ('Species', 'Species', ''), ('Species', 'Species', 'Pets'), None),
    ('STRICT-MISMATCH', ('Species', 'Gender', 'Humans'), ('Species', 'Species', 'Pets'), None),
    ('ROW-DIMENSION-MISMATCH', ('Species', 'Species', 'Humans'), ('Gender', 'Gender', 'Male'), None),
    ('NONCOMPLEMENT-HIGH', ('Species', 'Species', 'Humans'), ('Species', 'Species', 'Hoomans'), None),
    ('NONCOMPLEMENT-LOW', ('Species', 'Species', 'Pets'), ('Species', 'Species', 'Pets'), None),
]

def pair(case, rid='R-SEM-0', session='SEM-S0'):
    records = []
    for side, metadata in enumerate(case[1:3]):
        kind, strict, level = metadata
        records.append(dict(ResponseID=rid, ExtendedSessionID=session,
            UserID='SEM-U0', Intervention=str(side), Saved=str(1-side),
            AttributeLevel=level, ScenarioType=kind, ScenarioTypeStrict=strict))
    return records

BAD_NAMES = ['ORPHAN', 'THREE-ROWS', 'FOUR-ROWS', 'SAVED-SUM-0', 'SAVED-SUM-1',
             'INTERVENTION-SUM-0', 'INTERVENTION-SUM-1', 'USER', 'SESSION',
             'SPLIT-RESPONSE', 'SAME-SIDE-TWICE']

BAD_NAMES += [f'BINARY-{field}-{index}' for field in ('Saved', 'Intervention')
              for index in range(4)]

BAD_NAMES += [f'EMPTY-ID-{field}' for field in ('ResponseID', 'UserID', 'ExtendedSessionID')]

def malformed(name, rid='R-BAD-0', session='SEM-S0'):
    records = pair(VALID[0], rid, session)
    if name == 'ORPHAN':
        records = records[:1]
    elif name == 'THREE-ROWS':
        records.append(dict(records[0]))
    elif name == 'FOUR-ROWS':
        records += [dict(row) for row in records]
    elif name.startswith('SAVED-SUM-'):
        for row in records:
            row['Saved'] = name[-1]
    elif name.startswith('INTERVENTION-SUM-'):
        for row in records:
            row['Intervention'] = name[-1]
    elif name.startswith('BINARY-'):
        _, field, index = name.split('-')
        records[0][field] = ('', '2', '1.0', ' 1')[int(index)]
    elif name.startswith('EMPTY-ID-'):
        field = name.removeprefix('EMPTY-ID-')
        for row in records:
            row[field] = ''
    elif name == 'USER':
        records[1]['UserID'] = 'SEM-U1'
    elif name == 'SESSION':
        records[1]['ExtendedSessionID'] = 'SEM-S1'
    elif name == 'SPLIT-RESPONSE':
        records[1]['ResponseID'] = rid + '-OTHER'
    elif name == 'SAME-SIDE-TWICE':
        records = [dict(records[0]), dict(records[0])]
    else:
        raise AssertionError(name)
    return records

def envelope(tmp_path, records, columns=COLUMNS):
    text = io.StringIO(newline='')
    writer = csv.DictWriter(text, fieldnames=columns, extrasaction='ignore', lineterminator='\n')
    writer.writeheader()
    writer.writerows(records)
    payload = text.getvalue().encode('utf8')
    path = tmp_path / 'constructed.csv.tar.gz'
    with tarfile.open(path, 'w:gz') as archive:
        member = tarfile.TarInfo('constructed.csv')
        member.size = len(payload)
        member.mtime = 0
        archive.addfile(member, io.BytesIO(payload))
    return path

def run_source(tmp_path, records, monkeypatch=None, chunksize=None):
    if chunksize is not None:
        original = moral.pd.read_csv
        def small_chunks(*args, **kwargs):
            kwargs['chunksize'] = chunksize
            return original(*args, **kwargs)
        monkeypatch.setattr(moral.pd, 'read_csv', small_chunks)
    source = envelope(tmp_path, records)
    out = tmp_path / 'COUNTS.jsonl.gz'
    census = moral.prepare(source, tmp_path / 'pairs.sqlite', out)
    with gzip.open(out, 'rt', encoding='utf8') as stream:
        counts = [json.loads(line) for line in stream]
    return census, counts

def focal_base():
    records = []
    for case in (VALID[0], VALID[2], VALID[4]):
        for index in range(3):
            records += pair(case, f'EDGE-{case[0]}-{index}', 'EDGE-S0')
    return records
