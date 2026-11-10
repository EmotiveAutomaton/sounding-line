"""Complete five-site GO3 source authentication and metadata-only support gate.

DESIGN CHECK: LESSONS 2-5. Sources must be independently complete, pinned and
site/salt consistent. No classifier, intent scorer, accuracy or personal-habit
effect is computed. Sparse support preserves the declared descriptive route.
"""
from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import json
import math
import sqlite3
import time
import numpy as np
import pyarrow.parquet as pq
from . import week5_go_revisions as source
from . import week5_go3_source_checkpointed as producer
from .week5_la2_ic import requested

core = source.core
SITES = tuple(source.ARCHIVES)
METADATA = ('editor', 'post', 'stamp', 'site', 'type', 'reason', 'self_edit', 'owner_known')
BATCH = 4096


class Paused(Exception):
    pass


def read(path):
    return json.loads(Path(path).read_text('utf8'))


def check_roster(path):
    roster = read(path)
    if set(roster) != set(SITES):
        raise ValueError('Exact five-site source roster required')
    roots = []
    for site in SITES:
        item = roster[site]
        if set(item) != {'root', 'complete_sha256'}:
            raise ValueError('Exact source root and completion pin required')
        root = Path(item['root']).resolve()
        if root in roots:
            raise ValueError('Duplicate GO3 source root')
        roots.append(root)
        if core.sha(root / 'COMPLETE.json') != item['complete_sha256']:
            raise ValueError('GO3 source completion changed')
    return roster


def authenticate(site, entry, stop):
    root = Path(entry['root']).resolve()
    done = read(root / 'COMPLETE.json')
    if done.get('status') != 'COMPLETE' or done.get('fresh_process_verified') is not True:
        raise ValueError('GO3 source is not independently complete')
    if any((root / name).exists() for name in ('FAILED.json', 'PAUSED.json')):
        raise ValueError('Ambiguous GO3 source terminal')
    for name, expected in sorted(done['outputs'].items()):
        if stop():
            raise Paused('source authentication boundary; revalidate all bytes on resume')
        path = (root / name).resolve()
        path.relative_to(root)
        if core.sha(path) != expected:
            raise ValueError('GO3 completed source output changed')
    required = ('PLAN.json', 'VERIFIED.json', 'output/SOURCE.json', 'output/SNAPSHOT.json', 'output/edits.parquet', 'output/projection.sqlite')
    if any(name not in done['outputs'] for name in required):
        raise ValueError('Incomplete source terminal manifest')
    verified, plan = read(root / 'VERIFIED.json'), read(root / 'PLAN.json')
    receipt, snapshot = read(root / 'output/SOURCE.json'), read(root / 'output/SNAPSHOT.json')
    if verified.get('verified') is not True or verified.get('complete_independent_source_replay') is not True:
        raise ValueError('Complete source row replay required')
    if plan['module'] != 'runners.drive.cards.week5_go3_source_checkpointed' or plan['config']['site'] != site:
        raise ValueError('Source producer or site differs')
    binding = snapshot['state']['binding']
    if snapshot['database_sha256'] != done['outputs']['output/projection.sqlite']:
        raise ValueError('Source database snapshot disagrees with terminal')
    expected_binding = dict(site=site, archive_sha256=source.ARCHIVES[site], license_sha256=source.LICENSE_SHA,
                            source_sha256=core.sha(producer.__file__), integrity_sha256=core.sha(producer.integrity.__file__),
                            original_sha256=core.sha(source.__file__))
    if any(binding.get(key) != value for key, value in expected_binding.items()):
        raise ValueError('GO3 archive, producer or licence binding differs')
    if not snapshot['state'].get('projection_complete') or receipt.get('source_only') is not True:
        raise ValueError('Complete source-only projection required')
    if receipt['site'] != site or receipt['archive_sha256'] != source.ARCHIVES[site]:
        raise ValueError('GO3 source site/archive differs')
    if receipt['projection_sha256'] != done['outputs']['output/edits.parquet']:
        raise ValueError('Projection receipt differs from terminal hash')
    if set(receipt['member_sha256']) != {'Posts.xml', 'PostHistory.xml'}:
        raise ValueError('Unexpected source members')
    table = pq.ParquetFile(root / 'output/edits.parquet')
    if not table.schema_arrow.equals(producer.SCHEMA) or table.metadata.num_rows != receipt['retained_edits']:
        raise ValueError('GO3 complete projection schema or row count differs')
    counts = receipt['counts']
    attempted = sum(counts.get('edit_type_' + str(kind), 0) for kind in (4, 5, 6, 24))
    exclusions = sum(counts.get(key, 0) for key in ('anonymous_edits_excluded', 'missing_before_excluded', 'unchanged_text_excluded'))
    if attempted != receipt['retained_edits'] + exclusions:
        raise ValueError('GO3 edit/exclusion accounting does not reconcile')
    return dict(site=site, root=str(root), projection=str(root / 'output/edits.parquet'),
                complete_sha256=entry['complete_sha256'], projection_sha256=receipt['projection_sha256'],
                rows=int(table.metadata.num_rows), salt_sha256=binding['salt_sha256'],
                source_counts=counts, source_sha256=core.sha(root / 'output/SOURCE.json'))


def open_state(output, binding):
    path = output / 'projection.sqlite'
    if path.exists():
        snapshot = read(output / 'SNAPSHOT.json')
        if snapshot['sha256'] != core.sha(path) or snapshot['binding'] != binding:
            raise ValueError('GO3 collection checkpoint changed')
        db = sqlite3.connect(path)
        state = json.loads(db.execute('SELECT value FROM state').fetchone()[0])
        if state != snapshot['state']:
            db.close()
            raise ValueError('GO3 collection state seal differs')
    else:
        db = sqlite3.connect(path)
        db.executescript('CREATE TABLE state(value TEXT);'
                         'CREATE TABLE counts(cell TEXT,editor TEXT,label TEXT,n INTEGER,PRIMARY KEY(cell,editor,label));'
                         'CREATE TABLE posts(editor TEXT,site TEXT,post TEXT,stamp TEXT,ordinal INTEGER,PRIMARY KEY(editor,site,post));'
                         'CREATE TABLE users(editor TEXT PRIMARY KEY,site TEXT);')
        state = dict(site_index=0, site_rows=0, all_rows=0, last_key=None, reason_counts={}, type_counts={},
                     self_rows=0, batches_completed=0, pilot_done=False)
        db.execute('INSERT INTO state VALUES(?)', (json.dumps(state, sort_keys=True),))
        db.commit()
    db.execute('PRAGMA journal_mode=DELETE')
    db.execute('PRAGMA synchronous=FULL')
    db.execute('PRAGMA cache_size=-65536')
    return db, state


def seal(output, db, state, binding):
    db.close()
    core.write(output / 'SNAPSHOT.json', dict(binding=binding, state=state, sha256=core.sha(output / 'projection.sqlite')))


def ingest(db, state, info, stop, output, pilot_batches):
    site = info['site']
    position = 0
    table = pq.ParquetFile(info['projection'])
    reason_counts, type_counts = Counter(state['reason_counts']), Counter(state['type_counts'])
    previous = tuple(state['last_key']) if state['last_key'] is not None else None
    for batch in table.iter_batches(batch_size=BATCH, columns=METADATA):
        end = position + batch.num_rows
        if end <= state['site_rows']:
            position = end
            continue
        if position != state['site_rows']:
            raise ValueError('Collection cursor is not a complete metadata batch')
        if stop():
            raise Paused('complete metadata batch boundary')
        rows = batch.to_pylist()
        db.execute('BEGIN')
        try:
            for offset, row in enumerate(rows):
                if row['site'] != site or row['type'] not in (4, 5, 6, 24) or row['reason'] not in (*source.REASONS, 'other', 'multiple'):
                    raise ValueError('GO3 metadata category/site differs')
                if any(not isinstance(row[key], str) or len(row[key]) != 64 or any(c not in '0123456789abcdef' for c in row[key]) for key in ('editor', 'post')):
                    raise ValueError('Only complete salted source keys may enter collection')
                if not isinstance(row['stamp'], str) or not row['stamp']:
                    raise ValueError('Missing source ordering key')
                key = (row['post'], row['stamp'])
                if previous is not None and key < previous:
                    raise ValueError('GO3 source row order changed')
                previous = key
                if row['self_edit'] and not row['owner_known']:
                    raise ValueError('Self edit without known owner')
                old = db.execute('SELECT site FROM users WHERE editor=?', (row['editor'],)).fetchone()
                if old and old[0] != site:
                    raise ValueError('Salted editor appears in two site namespaces')
                db.execute('INSERT OR IGNORE INTO users VALUES(?,?)', (row['editor'], site))
                db.execute('INSERT INTO posts VALUES(?,?,?,?,?) ON CONFLICT(editor,site,post) DO UPDATE SET stamp=min(stamp,excluded.stamp)',
                           (row['editor'], site, row['post'], row['stamp'], state['all_rows'] + offset))
                reason_counts[row['reason']] += 1
                type_counts[str(row['type'])] += 1
                if row['self_edit'] and row['owner_known']:
                    state['self_rows'] += 1
                if row['type'] in (5, 24) and row['reason'] in source.PRIMARY:
                    cells = ['all', site]
                    if row['self_edit'] and row['owner_known']:
                        cells.append('self')
                    for cell in cells:
                        db.execute('INSERT INTO counts VALUES(?,?,?,1) ON CONFLICT(cell,editor,label) DO UPDATE SET n=n+1',
                                   (cell, row['editor'], row['reason']))
            state.update(site_rows=end, all_rows=state['all_rows'] + len(rows), last_key=list(previous),
                         batches_completed=state['batches_completed'] + 1,
                         reason_counts=dict(reason_counts), type_counts=dict(type_counts))
            pilot = not state['pilot_done'] and state['batches_completed'] >= pilot_batches
            if pilot:
                state['pilot_done'] = True
            db.execute('UPDATE state SET value=?', (json.dumps(state, sort_keys=True),))
            db.commit()
        except BaseException:
            db.rollback()
            raise
        position = end
        core.write(output / 'PROGRESS.json', dict(phase='metadata_collection', completed=state['all_rows'], site=site))
        if pilot:
            raise Paused('first five percent of declared metadata batches')
    if position != info['rows'] or state['site_rows'] != info['rows']:
        raise ValueError('GO3 metadata row census differs')


def classifier_support(db, cell):
    rows = db.execute('SELECT editor,label,n FROM counts WHERE cell=? ORDER BY editor,label', (cell,)).fetchall()
    keys = sorted({row[0] for row in rows})
    index = {key: i for i, key in enumerate(keys)}
    matrix = np.zeros((len(keys), len(source.PRIMARY)), dtype=np.int64)
    for user, label, count in rows:
        matrix[index[user], source.PRIMARY.index(label)] = count
    assignment = {str(key): i % 5 for i, key in enumerate(np.random.default_rng(core.SEED).permutation(keys))}
    folds = np.asarray([assignment[key] for key in keys], int)
    totals = matrix.sum(axis=0)
    fold_counts = []
    supported = len(keys) >= 20
    for fold in range(5):
        train = matrix[folds != fold].sum(axis=0)
        test = matrix[folds == fold].sum(axis=0)
        supported &= bool(np.all(train > 0))
        fold_counts.append(dict(fold=fold, train_users=int((folds != fold).sum()), test_users=int((folds == fold).sum()),
                                train_counts=train.tolist(), test_counts=test.tolist()))
    return dict(cell=cell, rows=int(totals.sum()), users=len(keys), classes=list(source.PRIMARY),
                category_counts=totals.tolist(), folds=fold_counts, user_disjoint_support=supported,
                disposition='supported design; no fit performed' if supported else 'below floor, pooled descriptive route only',
                pooled_fit_estimable=int(np.count_nonzero(totals)) >= 2)


def habit_support(db):
    records = db.execute('SELECT editor,site,post,stamp,ordinal FROM posts ORDER BY editor,stamp,ordinal').fetchall()
    profiles = defaultdict(list)
    for editor, site, post, stamp, ordinal in records:
        profiles[editor].append((site, post))
    profiles = {key: (value[::2], value[1::2]) for key, value in profiles.items() if len(value) >= 2}
    eligible = sorted(profiles)
    folds = {str(key): i % 3 for i, key in enumerate(np.random.default_rng(core.SEED).permutation(eligible))}
    rng = np.random.default_rng(core.SEED + 1)
    details = []
    missing = 0
    all_gallery = True
    for role in range(3):
        donors = set(item for key, halves in profiles.items() if folds[key] == role for half in halves for item in half)
        gallery = [key for key in eligible if folds[key] != role]
        probes = [key for key in eligible if folds[key] == (role + 1) % 3]
        all_gallery &= len(gallery) >= 30
        failures = 0
        if len(gallery) >= 30:
            for key in probes:
                candidates = [key] + rng.choice([other for other in gallery if other != key], 29, replace=False).tolist()
                needs = set(profiles[key][0])
                for other in candidates:
                    needs.update(profiles[other][1])
                failures += int(not needs <= donors)
        details.append(dict(role=role, donor_users=sum(value == role for value in folds.values()),
                            gallery_users=len(gallery), probes=len(probes), probes_missing_same_post_donors=failures))
        missing += failures
    return dict(eligible_users=len(eligible), roles=details, gallery_size=30,
                fixed_gallery_structural_support=bool(all_gallery and not missing),
                conditional_permutation_support='not evaluated; every fixed allocation remains a downstream obligation',
                no_accuracy_or_habit_effect_computed=True)


def execute(output, inputs, config):
    if set(inputs) != {'roster'} or set(config) - {'phase', 'max_wall_seconds'} or config.get('phase') != 'collect':
        raise ValueError('Exact GO3 collection contract required')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    maximum = float(config.get('max_wall_seconds', 900))
    if not math.isfinite(maximum) or maximum <= 0:
        raise ValueError('Positive finite collection wall quantum required')
    began = time.monotonic()
    stop = lambda: requested(output) or time.monotonic() - began >= maximum
    roster = check_roster(inputs['roster'])
    binding = dict(roster_sha256=core.sha(inputs['roster']), collector_sha256=core.sha(__file__),
                   producer_sha256=core.sha(producer.__file__), source_sha256=core.sha(source.__file__))
    binding_path = output / 'COLLECTION_BINDING.json'
    if binding_path.exists() and read(binding_path) != binding:
        raise ValueError('GO3 collection source binding changed')
    core.write(binding_path, binding)
    db = state = None
    try:
        sources = [authenticate(site, roster[site], stop) for site in SITES]
        if len({value['salt_sha256'] for value in sources}) != 1:
            raise ValueError('GO3 sites use different campaign salts')
        planned_batches = sum(math.ceil(value['rows'] / BATCH) for value in sources)
        pilot_batches = math.ceil(.05 * planned_batches)
        db, state = open_state(output, binding)
        while state['site_index'] < len(sources):
            ingest(db, state, sources[state['site_index']], stop, output, pilot_batches)
            state.update(site_index=state['site_index'] + 1, site_rows=0, last_key=None)
            db.execute('UPDATE state SET value=?', (json.dumps(state, sort_keys=True),))
            db.commit()
        if stop():
            raise Paused('before complete metadata support summary')
        support = [classifier_support(db, cell) for cell in ('all', 'self', *SITES)]
        result = dict(source_only=True, complete_collection=True, sites=list(SITES), rows=state['all_rows'],
                      declared_metadata_batches=planned_batches, first_pilot_batches=pilot_batches,
                      reason_counts=state['reason_counts'], type_counts=state['type_counts'], self_rows=state['self_rows'],
                      classifier_support=support, habit_structural_support=habit_support(db),
                      scientific_admission=False, no_fitting_performed=True)
        collection = dict(binding=binding, sources=sources, sites=[str(Path(row['root']) / 'output') for row in sources],
                          required_next='separately admitted complete diff/IteraTeR feature preparation and full scientific consumer')
        core.write(output / 'COLLECTION.json', collection)
        core.write(output / 'SUPPORT.json', result)
        return result
    except Paused as pause:
        return dict(status='yielded', phase='source_metadata_collection' if state else 'source_authentication', reason=str(pause),
                    completed=state['all_rows'] if state else 0,
                    total=sum(value['rows'] for value in sources) if 'sources' in locals() else len(SITES),
                    source_only=True, complete_collection=False)
    finally:
        if db is not None:
            seal(output, db, state, binding)


def database_digest(path):
    db = sqlite3.connect(f'file:{Path(path).resolve().as_posix()}?mode=ro&immutable=1', uri=True)
    try:
        result = {}
        for table, order in (('counts', 'cell,editor,label'), ('posts', 'editor,site,post'), ('users', 'editor')):
            digest = hashlib.sha256()
            for row in db.execute(f'SELECT * FROM {table} ORDER BY {order}'):
                digest.update(json.dumps(row, ensure_ascii=True, separators=(',', ':')).encode() + b'\n')
            result[table] = digest.hexdigest()
        return result
    finally:
        db.close()


def verify(output, inputs, config):
    output = Path(output)
    result = execute(output / 'independent-replay', inputs, config)
    if result.get('status') == 'yielded':
        return result | dict(verified=False)
    for name in ('SUPPORT.json', 'COLLECTION.json'):
        if read(output / name) != read(output / 'independent-replay' / name):
            raise ValueError('GO3 complete collection summary differs')
    if database_digest(output / 'projection.sqlite') != database_digest(output / 'independent-replay/projection.sqlite'):
        raise ValueError('Every metadata support row must replay')
    return dict(verified=True, complete_source_collection_replayed=True, source_only=True)
