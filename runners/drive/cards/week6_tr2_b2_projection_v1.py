"""Bounded constructed B2 pair projection; no TR2 scientific operationalization.

DESIGN CHECK: LESSONS 2-5. Pair validity and exact source dispositions do not
depend on scientific direction. Every valid pair supplies Intervention, even
without focal metadata. Unknown schema/pins refuse; a duplicate is not repaired.
No halves, selected triples, estimator, human source admission or launch exists.
"""
from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import json
import sqlite3

COLUMNS = ('ResponseID', 'ExtendedSessionID', 'UserID', 'Intervention',
           'Saved', 'AttributeLevel', 'ScenarioType', 'ScenarioTypeStrict')
LEVELS = {'Species': {'Humans': 1, 'Hoomans': 1, 'Pets': 0},
          'Gender': {'Female': 1, 'Females': 1, 'Male': 0, 'Males': 0},
          'Fitness': {'Fit': 1, 'Fat': 0}}
MAX_ROWS = 100000
MAX_BYTES = 32 * 2**20
SCHEMA = 'TR2-B2-CONSTRUCTED-ROWS-v1'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=True, allow_nan=False) + '\n').encode()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked_row(row):
    require(isinstance(row, dict) and set(row) == set(COLUMNS),
            'Exact eight-column schema required')
    require(all(type(row[k]) is str for k in COLUMNS),
            'Source fields must be literal strings')
    return row


def summarize(pairs, projection, row_count):
    """Aggregation only; producer and verifier supply independently built rows."""
    users = defaultdict(dict)
    for record in projection:
        values = users[record['user']].setdefault(record['dimension'], [0, 0, set()])
        values[0] += 1
        values[1] += record['positive']
        values[2].add(record['session_id'])
    records = []
    by_dimension = Counter()
    for user in sorted(users):
        values = {dim: [v[0], v[1], len(v[2])]
                  for dim, v in sorted(users[user].items())}
        for dim, v in values.items():
            if v[0] >= 3:
                by_dimension[dim] += 1
        eligible = (all(values.get(d, [0])[0] >= 3
                        for d in ('Species', 'Intervention', 'Gender', 'Fitness'))
                    and values.get('Intervention', [0, 0, 0])[2] >= 2)
        records.append(dict(user=user, dimensions=values, eligible=eligible))
    common = sum(x['eligible'] for x in records)
    return dict(pairs=pairs, projection=projection, users=records,
                census=dict(rows=row_count, responses=len(pairs),
                    orphans=sum(p['row_count'] == 1 for p in pairs),
                    duplicated_responses=sum(p['row_count'] > 2 for p in pairs),
                    complete_valid_pairs=sum(p['valid'] for p in pairs),
                    invalid_exact_two_pairs=sum(p['row_count'] == 2 and not p['valid'] for p in pairs),
                    fingerprints=len(records), common_returning_fingerprints=common,
                    three_scenario_fingerprints=dict(sorted(by_dimension.items())),
                    original_B2_source_case_pass=common >= 1000))


def project_rows(rows, db_path, chunk_size=1000, max_rows=MAX_ROWS):
    require(type(max_rows) is int and 0 < max_rows <= MAX_ROWS, 'Constructed row bound')
    require(type(chunk_size) is int and chunk_size > 0, 'Positive chunk size required')
    db_path = Path(db_path)
    require(not db_path.exists(), 'Fresh pair database required')
    connection = sqlite3.connect(db_path)
    try:
        connection.execute('PRAGMA cache_size=-8192')
        connection.execute('PRAGMA temp_store=FILE')
        connection.execute('''CREATE TABLE raw (
            rid TEXT, usr TEXT, session TEXT, saved INT, intervention INT,
            chosen INT, level INT, bad_flag INT, bad_id INT, dim TEXT, positive INT)''')
        batch = []
        count = 0
        for row in rows:
            checked_row(row)
            count += 1
            require(count <= max_rows, 'Constructed row bound')
            saved, intervention = row['Saved'], row['Intervention']
            flag_ok = saved in ('0', '1') and intervention in ('0', '1')
            sv = int(saved) if saved in ('0', '1') else 0
            iv = int(intervention) if intervention in ('0', '1') else 0
            kind, strict, level = row['ScenarioType'], row['ScenarioTypeStrict'], row['AttributeLevel']
            dimension = kind if kind == strict and level in LEVELS.get(kind, {}) else ''
            value = LEVELS[dimension][level] if dimension else 0
            batch.append((row['ResponseID'], row['UserID'], row['ExtendedSessionID'],
                          sv, iv, sv * (1-iv), value, int(not flag_ok),
                          int(not all(row[k] for k in ('ResponseID', 'UserID', 'ExtendedSessionID'))),
                          dimension, sv * value))
            if len(batch) >= chunk_size:
                connection.executemany('INSERT INTO raw VALUES(?,?,?,?,?,?,?,?,?,?,?)', batch)
                connection.commit()
                batch.clear()
        if batch:
            connection.executemany('INSERT INTO raw VALUES(?,?,?,?,?,?,?,?,?,?,?)', batch)
            connection.commit()
        query = '''SELECT rid,count(*),min(usr),max(usr),min(session),max(session),
            sum(saved),sum(intervention),sum(chosen),sum(level),sum(bad_flag),sum(bad_id),
            min(dim),max(dim),sum(positive) FROM raw GROUP BY rid ORDER BY rid'''
        pairs, projection = [], []
        for rid, n, u0, u1, s0, s1, sv, iv, chosen, level, flags, ids, d0, d1, positive in connection.execute(query):
            reasons = []
            if n != 2:
                reasons.append('row_count')
            if flags:
                reasons.append('nonbinary_flag')
            if ids:
                reasons.append('empty_identifier')
            if u0 != u1 or s0 != s1:
                reasons.append('identity_mismatch')
            if sv != 1:
                reasons.append('saved_sum')
            if iv != 1:
                reasons.append('intervention_sum')
            valid = not reasons
            pairs.append(dict(response_id=rid, row_count=n, valid=valid, reasons=sorted(reasons)))
            if valid:
                projection.append(dict(response_id=rid, user=u0, session_id=s0,
                                       dimension='Intervention', positive=chosen))
                if d0 == d1 and d0 and level == 1:
                    projection.append(dict(response_id=rid, user=u0, session_id=s0,
                                           dimension=d0, positive=positive))
        projection.sort(key=lambda r: (r['response_id'], r['dimension']))
        return summarize(pairs, projection, count)
    finally:
        connection.close()


def independent_replay(rows, max_rows=MAX_ROWS):
    """Direct complete-pair oracle: no SQL, producer encoder or LEVELS lookup."""
    require(type(max_rows) is int and 0 < max_rows <= MAX_ROWS, 'Constructed row bound')
    grouped = defaultdict(list)
    count = 0
    for row in rows:
        checked_row(row)
        count += 1
        require(count <= max_rows, 'Constructed row bound')
        grouped[row['ResponseID']].append({key: row[key] for key in COLUMNS})
    positive_levels = {'Species': ('Humans', 'Hoomans'), 'Gender': ('Female', 'Females'), 'Fitness': ('Fit',)}
    negative_levels = {'Species': ('Pets',), 'Gender': ('Male', 'Males'), 'Fitness': ('Fat',)}
    pairs, projection = [], []
    for rid in sorted(grouped):
        group = grouped[rid]
        flags = any(r[k] not in ('0', '1') for r in group for k in ('Saved', 'Intervention'))
        empty = any(not r[k] for r in group for k in ('ResponseID', 'UserID', 'ExtendedSessionID'))
        identity = len({(r['UserID'], r['ExtendedSessionID']) for r in group}) != 1
        saved_sum = sum(r['Saved'] == '1' for r in group)
        intervention_sum = sum(r['Intervention'] == '1' for r in group)
        reasons = [label for bad, label in ((len(group) != 2, 'row_count'),
                   (flags, 'nonbinary_flag'), (empty, 'empty_identifier'),
                   (identity, 'identity_mismatch'), (saved_sum != 1, 'saved_sum'),
                   (intervention_sum != 1, 'intervention_sum')) if bad]
        valid = not reasons
        pairs.append(dict(response_id=rid, row_count=len(group), valid=valid, reasons=sorted(reasons)))
        if not valid:
            continue
        saved = next(r for r in group if r['Saved'] == '1')
        base = dict(response_id=rid, user=saved['UserID'], session_id=saved['ExtendedSessionID'])
        projection.append(dict(base, dimension='Intervention', positive=int(saved['Intervention'] == '0')))
        kind = group[0]['ScenarioType']
        if kind in positive_levels and all(r['ScenarioType'] == r['ScenarioTypeStrict'] == kind for r in group):
            signs = [1 if r['AttributeLevel'] in positive_levels[kind] else
                     0 if r['AttributeLevel'] in negative_levels[kind] else None for r in group]
            if sorted(signs, key=lambda v: -1 if v is None else v) == [0, 1]:
                projection.append(dict(base, dimension=kind,
                                       positive=int(saved['AttributeLevel'] in positive_levels[kind])))
    projection.sort(key=lambda r: (r['response_id'], r['dimension']))
    # Independent cohort/census replay too: do not reuse producer aggregation.
    person_records = []
    dimension_counts = {}
    by_user = defaultdict(list)
    for record in projection:
        by_user[record['user']].append(record)
    for user in sorted(by_user):
        dimensions = {}
        for dimension in sorted({record['dimension'] for record in by_user[user]}):
            selected = [record for record in by_user[user] if record['dimension'] == dimension]
            dimensions[dimension] = [len(selected), sum(record['positive'] for record in selected),
                                      len({record['session_id'] for record in selected})]
            if len(selected) >= 3:
                dimension_counts[dimension] = dimension_counts.get(dimension, 0) + 1
        eligible = set(('Species', 'Intervention', 'Gender', 'Fitness')) <= set(dimensions)
        if eligible:
            eligible = min(dimensions[d][0] for d in ('Species', 'Intervention', 'Gender', 'Fitness')) >= 3
        if eligible:
            eligible = dimensions['Intervention'][2] >= 2
        person_records.append(dict(user=user, dimensions=dimensions, eligible=eligible))
    census = dict(rows=count, responses=len(grouped),
        orphans=len([group for group in grouped.values() if len(group) == 1]),
        duplicated_responses=len([group for group in grouped.values() if len(group) > 2]),
        complete_valid_pairs=len([pair for pair in pairs if pair['valid']]),
        invalid_exact_two_pairs=len([pair for pair in pairs if pair['row_count'] == 2 and not pair['valid']]),
        fingerprints=len(person_records),
        common_returning_fingerprints=len([record for record in person_records if record['eligible']]),
        three_scenario_fingerprints=dict(sorted(dimension_counts.items())))
    census['original_B2_source_case_pass'] = census['common_returning_fingerprints'] >= 1000
    return dict(pairs=pairs, projection=projection, users=person_records, census=census)


def load_constructed(inputs):
    source = Path(inputs['constructed_source']['path'])
    require(source.stat().st_size <= MAX_BYTES, 'Constructed byte bound')
    payload = source.read_bytes()
    require(len(payload) <= MAX_BYTES, 'Constructed byte bound')
    require(hashlib.sha256(payload).hexdigest() == inputs['constructed_source']['sha256'],
            'Constructed source hash changed')
    value = json.loads(payload.decode('utf8'))
    require(value.get('schema') == SCHEMA and value.get('constructed_only') is True,
            'Constructed source envelope required')
    require(isinstance(value.get('rows'), list), 'Constructed rows must be a list')
    return value['rows']


def execute(output, inputs, config):
    require(config.get('constructed_only') is True, 'Constructed-only handler')
    rows = load_constructed(inputs)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    require(not any(output.iterdir()), 'Fresh output directory required')
    result = project_rows(rows, output/'pairs.sqlite', config.get('chunk_size', 1000),
                          config.get('max_rows', MAX_ROWS))
    payload = canonical(result)
    require(len(payload) <= MAX_BYTES, 'Constructed output bound')
    (output/'PROJECTION.json').write_bytes(payload)
    manifest = dict(schema='TR2-B2-PROJECTION-v1', constructed_only=True,
                    source=inputs['constructed_source'], projection_sha256=digest(output/'PROJECTION.json'),
                    scientific_admission=False, tr2_split_or_fit=False)
    (output/'MANIFEST.json').write_bytes(canonical(manifest))
    return dict(status='complete', constructed_only=True, scientific_admission=False)


def verify(output, inputs, config):
    require(config.get('constructed_only') is True, 'Constructed-only handler')
    rows = load_constructed(inputs)
    output = Path(output)
    manifest = json.loads((output/'MANIFEST.json').read_text(encoding='utf8'))
    expected_manifest = dict(schema='TR2-B2-PROJECTION-v1', constructed_only=True,
        source=inputs['constructed_source'], projection_sha256=digest(output/'PROJECTION.json'),
        scientific_admission=False, tr2_split_or_fit=False)
    require(manifest == expected_manifest, 'Projection manifest mismatch')
    reference = independent_replay(rows, config.get('max_rows', MAX_ROWS))
    require((output/'PROJECTION.json').read_bytes() == canonical(reference),
            'Independent complete-pair replay mismatch')
    return dict(verified=True, independent_pair_replay=True, constructed_only=True,
                scientific_admission=False)
