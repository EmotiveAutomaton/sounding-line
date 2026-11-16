"""Checkpointed full original B2 source, never TR2 reliability inference.

DESIGN CHECK: LESSONS 2-5. All scientific directions retain identical pairs,
nonfocal Intervention, source dispositions and original cohort. Missing/corrupt
checkpoints, source/reader changes or incomplete coverage refuse. Independent
literal-pair replay must match all projected records and the original cohort.
"""
from collections import Counter
from contextlib import ExitStack
from pathlib import Path
import gzip
import hashlib
import heapq
import itertools
import json
import math
import os
import sqlite3
import tarfile
import time
import uuid

from runners.drive.cards import week6_tr2_b2_projection_v1 as core
from runners.theory_days import moral, backlog_intake

OFFICIAL = '4c8e32872b432831a4b8670b3a2b4b797f4af8f9b39543b784a939aaf49bd7a9'
MAX_OUTPUT = 96 * 2**30
FIELDS = ('rows', 'responses', 'orphans', 'duplicated_responses', 'complete_valid_pairs',
          'fingerprints', 'common_returning_fingerprints', 'three_scenario_fingerprints', 'source_case_pass')


class YieldNow(Exception):
    pass


def need(value, message):
    if not value:
        raise ValueError(message)


def data(value):
    return (json.dumps(value, sort_keys=True, allow_nan=False) + '\n').encode('utf8')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def atomic(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temporary.write_bytes(data(value))
    os.replace(temporary, path)


def sha(path, guard=None):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(2**20), b''):
            if guard:
                guard.check()
            result.update(block)
    return result.hexdigest()


def bucket(kind, identity, count):
    payload = json.dumps(['TR2-B2-archive-v1', kind, identity],
                         separators=(',', ':'), ensure_ascii=True).encode('utf8')
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], 'big') % count


def zipped(stack, path):
    raw = stack.enter_context(Path(path).open('xb'))
    return stack.enter_context(gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0))


def lines(path):
    with gzip.open(path, 'rt', encoding='utf8') as stream:
        for line in stream:
            yield json.loads(line)


class Guard:
    def __init__(self, root, config):
        self.root = root
        self.start = time.monotonic()
        self.cpu0 = time.process_time()
        remaining = config['owner_remaining_card_cpu_seconds']
        need(type(remaining) in (int, float) and math.isfinite(remaining) and 30 < remaining <= 60000,
             'Owner must bind the remaining original TR2 inclusive allowance')
        self.cpu = min(float(config.get('slice_cpu_seconds', 900)), remaining - 30)
        self.wall = float(config.get('slice_wall_seconds', 1500))
        self.output = config.get('max_output_bytes', MAX_OUTPUT)
        need(0 < self.cpu <= 1700 and 0 < self.wall <= 1700, 'Bounded native quantum required')
        need(type(self.output) is int and 0 < self.output <= MAX_OUTPUT, 'Derived output ceiling')
        self.next_disk_check = 0.0
        self.next_progress = 0.0
        self.current_unit = 'checkpoint_authentication'
        self.reason = None

    def start_unit(self, label):
        self.current_unit = label
        self.next_progress = 0.0
        self.check()

    def check(self):
        now = time.monotonic()
        if time.process_time() - self.cpu0 + 2 >= self.cpu:
            self.reason = 'cooperative_CPU_boundary'
        elif now - self.start >= self.wall:
            self.reason = 'cooperative_wall_boundary'
        elif (self.root/'YIELD_REQUEST').exists() or (self.root/'YIELD_REQUEST.json').exists():
            self.reason = 'YIELD_REQUEST'
        elif now >= self.next_disk_check:
            self.next_disk_check = now + 10
            size = 0
            for parent, _, names in os.walk(self.root):
                for name in names:
                    size += (Path(parent)/name).stat().st_size
            if size >= self.output:
                self.reason = 'derived_output_boundary'
        if self.reason:
            raise YieldNow(self.reason)
        if now >= self.next_progress:
            self.next_progress = now + 30
            atomic(self.root/'CHECKPOINT_PROGRESS.json', dict(status='running',
                unit=self.current_unit, local_call_CPU_seconds=time.process_time()-self.cpu0,
                local_call_wall_seconds=now-self.start, source_only=True,
                scientific_admission=False, local_cost_is_not_a_second_debit=True))

    def sqlite_progress(self):
        try:
            self.check()
            return 0
        except YieldNow:
            return 1


class Journal:
    def __init__(self, root, binding, guard):
        self.root, self.binding, self.guard = root, binding, guard
        root.mkdir(parents=True, exist_ok=True)
        self.state_path = root/'STATE.json'
        if (root/'BINDING.json').exists():
            need(read(root/'BINDING.json') == binding, 'Resume binding changed')
        else:
            need(not any(root.iterdir()), 'Unbound existing work directory')
            atomic(root/'BINDING.json', binding)
        self.state = read(self.state_path) if self.state_path.exists() else {}
        self.cache = {}
        for key, pin in self.state.items():
            need((root/key/'RECEIPT.json').is_file(), 'Missing journaled work unit: ' + key)
            need(sha(root/key/'RECEIPT.json') == pin, 'Work-unit receipt changed: ' + key)
            self.unit(key)
        # Reconcile a seal that preceded the final atomic journal update, and
        # expose extra sealed units rather than hiding them outside the state.
        for family in ('raw', 'pairs', 'users'):
            folder = root/family
            if folder.exists():
                for directory in sorted(folder.iterdir()):
                    need(directory.is_dir() and directory.name.isdecimal(), 'Unexpected work-unit directory')
                    self.unit(family + '/' + directory.name)
        for key in ('raw_complete', 'merge'):
            if (root/key).exists():
                self.unit(key)

    def unit(self, key):
        parts = key.split('/')
        need(key in ('raw_complete', 'merge') or (len(parts) == 2
             and parts[0] in ('raw', 'pairs', 'users') and parts[1].isdecimal()
             and parts[1] == (f'{int(parts[1]):06d}' if parts[0] == 'raw' else f'{int(parts[1]):02d}')),
             'Unsafe or noncanonical work-unit key')
        if key in self.cache:
            return self.cache[key]
        directory = self.root/key
        if not directory.exists():
            return None
        receipt = read(directory/'RECEIPT.json')
        need(receipt['key'] == key and receipt['binding'] == self.binding, 'Work-unit binding changed')
        expected = set(receipt['files']) | {'RECEIPT.json'}
        need({p.name for p in directory.iterdir()} == expected, 'Work-unit file coverage differs')
        for name, record in receipt['files'].items():
            need(Path(name).name == name, 'Unsafe artifact name')
            path = directory/name
            need(path.stat().st_size == record['bytes'] and sha(path, self.guard) == record['sha256'],
                 'Work-unit artifact changed: ' + key + '/' + name)
        self.cache[key] = receipt
        pin = sha(directory/'RECEIPT.json')
        if key not in self.state:
            # A fully sealed unit may precede its journal update after a power loss.
            self.state[key] = pin
            atomic(self.state_path, self.state)
        return receipt

    def temporary(self):
        directory = self.root/'partial'/uuid.uuid4().hex
        directory.mkdir(parents=True)
        return directory

    def seal(self, key, temporary, meta, cpu0, wall0):
        self.guard.check()
        files = {p.name: dict(sha256=sha(p, self.guard), bytes=p.stat().st_size)
                 for p in sorted(temporary.iterdir()) if p.is_file()}
        receipt = dict(key=key, binding=self.binding, files=files, meta=meta,
                       local_unit_CPU_seconds=time.process_time()-cpu0,
                       local_unit_wall_seconds=time.monotonic()-wall0,
                       local_cost_is_not_a_second_debit=True)
        (temporary/'RECEIPT.json').write_bytes(data(receipt))
        target = self.root/key
        target.parent.mkdir(exist_ok=True)
        need(not target.exists(), 'Immutable work unit already exists')
        temporary.rename(target)
        self.state[key] = sha(target/'RECEIPT.json')
        atomic(self.state_path, self.state)
        self.cache[key] = receipt
        return receipt


def contract(inputs, config):
    reference = inputs['source_contract']
    need(sha(reference['path']) == reference['sha256'], 'Source metadata contract changed')
    value = read(reference['path'])
    need(value['kind'] in ('original_B2', 'constructed_fixture'), 'Unknown source contract')
    if value['kind'] == 'original_B2':
        need(value['archive']['sha256'] == OFFICIAL and value['archive']['bytes'] == 3212547438,
             'Different original B2 archive refused')
        need(value['member'] == 'SharedResponses.csv' and value['expanded_bytes'] == 11601104964
             and value['expected_census']['rows'] == 70332355, 'Original source coverage changed')
        need(config.get('buckets', 32) == 32 and config.get('chunk_rows', 100000) == 100000,
             'Frozen production engineering partition changed')
        need(value['expected_counts_sha256'] == 'b2fcaf48ba51b80367884e0c801eca1e0029c86fdfa8accd08dd1e68a0b566c3',
             'Original cohort pin changed')
        need(len(value['metadata_pins']) >= 4, 'Preserved intake/source completion metadata required')
        for item in value['metadata_pins']:
            need(sha(item['path']) == item['sha256'], 'Preserved metadata pin changed')
    else:
        need(config.get('constructed_only') is True, 'Constructed fixture contract requires explicit scope')
    return value


def ingest(journal, source, config, take):
    root, guard = journal.root, journal.guard
    count = config.get('buckets', 32)
    chunk_rows = config.get('chunk_rows', 100000)
    need(type(count) is int and 1 <= count <= 32 and type(chunk_rows) is int and chunk_rows > 0,
         'Invalid engineering partition')
    if (root/'SOURCE_COST_PREFIX.json').exists():
        prefix = read(root/'SOURCE_COST_PREFIX.json')
        need(prefix['binding'] == journal.binding
             and prefix['complete_chunk_receipt_sha256'] in journal.state.values(),
             'Source cost-prefix binding changed')
    if journal.unit('raw_complete'):
        return True
    guard.start_unit('archive_authentication_and_ingestion')
    path = Path(source['archive']['path'])
    need(path.stat().st_size == source['archive']['bytes'] and sha(path, guard) == source['archive']['sha256'],
         'Original archive hash or size changed')
    schema = backlog_intake.moral_header(path)
    need(schema['member'] == source['member'] and schema['expanded_bytes'] == source['expanded_bytes'],
         'Archive member coverage changed')
    import pandas as pd
    total = 0
    completed = 0
    with tarfile.open(path, 'r:gz') as archive:
        member = next(iter(archive))
        with archive.extractfile(member) as stream:
            for ordinal, frame in enumerate(pd.read_csv(stream, usecols=list(core.COLUMNS), dtype=str,
                                      keep_default_na=False, chunksize=chunk_rows)):
                guard.check()
                key = 'raw/' + f'{ordinal:06d}'
                guard.current_unit = key
                existing = journal.unit(key)
                if existing:
                    need(existing['meta']['start_row'] == total and existing['meta']['rows'] == len(frame),
                         'Source chunk ordinal coverage changed')
                else:
                    cpu0, wall0 = time.process_time(), time.monotonic()
                    temporary = journal.temporary()
                    sizes = [0] * count
                    with ExitStack() as stack:
                        outputs = [zipped(stack, temporary/f'b{b:02d}.jsonl.gz') for b in range(count)]
                        for n, values in enumerate(frame[list(core.COLUMNS)].itertuples(index=False, name=None)):
                            if n % 1000 == 0:
                                guard.check()
                            b = bucket('response', values[0], count)
                            outputs[b].write(data(list(values)))
                            sizes[b] += 1
                    journal.seal(key, temporary, dict(start_row=total, rows=len(frame), bucket_rows=sizes), cpu0, wall0)
                    take()
                total += len(frame)
                completed += 1
                prefix = root/'SOURCE_COST_PREFIX.json'
                if config.get('first_cost_prefix', True) and not prefix.exists() and total >= math.ceil(source['expected_census']['rows'] * .05):
                    atomic(prefix, dict(binding=journal.binding, rows=total,
                        complete_chunk_receipt_sha256=journal.state[key],
                        local_call_CPU_seconds=time.process_time()-guard.cpu0,
                        local_call_wall_seconds=time.monotonic()-guard.start,
                        complete_program_cost_forecast=False, source_population_complete=False))
                    raise YieldNow('first_five_percent_source_cost_prefix')
            consumed = stream.tell()
    need(total == source['expected_census']['rows'] and consumed == source['expanded_bytes'],
         'Original full-source row/member coverage failed')
    need(sha(path, guard) == source['archive']['sha256'], 'Archive changed during source extraction')
    folder = root/'raw'
    names = {p.name for p in folder.iterdir()} if folder.exists() else set()
    need(names == {f'{i:06d}' for i in range(completed)}, 'Missing or extra source chunk')
    temporary = journal.temporary()
    journal.seal('raw_complete', temporary, dict(rows=total, chunks=completed, expanded_bytes=consumed),
                 time.process_time(), time.monotonic())
    take()
    return True


def connect(path, guard):
    connection = sqlite3.connect(path)
    connection.execute('PRAGMA cache_size=-8192')
    connection.execute('PRAGMA temp_store=FILE')
    connection.set_progress_handler(guard.sqlite_progress, 10000)
    return connection


def encoded(values):
    rid, session, user, intervention, saved, level, kind, strict = values
    valid = intervention in ('0', '1') and saved in ('0', '1') and bool(rid and user and session)
    sv = int(saved) if saved in ('0', '1') else 0
    iv = int(intervention) if intervention in ('0', '1') else 0
    dim = kind if kind == strict and level in core.LEVELS.get(kind, {}) else ''
    level_value = core.LEVELS[dim][level] if dim else 0
    return rid, user, session, 1, sv, iv, sv*(1-iv), level_value, int(not valid), dim, sv*level_value


def producer_pairs(connection):
    for row in connection.execute('SELECT * FROM pairs ORDER BY rid'):
        rid, user, session, n, saved, interventions, chosen, levels, bad, dim, positive = row
        valid = n == 2 and saved == 1 and interventions == 1 and bad == 0
        result = [('Intervention', chosen)] if valid else []
        if valid and dim and levels == 1:
            result.append((dim, positive))
        yield rid, user, session, n, valid, sorted(result)


def oracle_pairs(connection):
    cursor = connection.execute('SELECT * FROM raw ORDER BY rid,ordinal')
    for rid, rows in itertools.groupby(cursor, key=lambda r: r[0]):
        retained = []
        n = 0
        for row in rows:
            n += 1
            if n <= 2:
                retained.append(dict(zip(core.COLUMNS, row[:8])))
        if n != 2:
            yield rid, '', '', n, False, []
            continue
        # The qualified direct-pair oracle neither calls encoded nor the SQL predicate.
        replay = core.independent_replay(retained)
        valid = replay['pairs'][0]['valid']
        projected = replay['projection']
        user = projected[0]['user'] if projected else ''
        session = projected[0]['session_id'] if projected else ''
        yield rid, user, session, n, valid, [(p['dimension'], p['positive']) for p in projected]


def pair_unit(journal, index, config, take, independent):
    key = f'pairs/{index:02d}'
    if journal.unit(key):
        return
    journal.guard.start_unit(key)
    count = config.get('buckets', 32)
    raw_done = journal.unit('raw_complete')
    need(raw_done is not None, 'Pairing requires complete original source coverage')
    cpu0, wall0 = time.process_time(), time.monotonic()
    temporary = journal.temporary()
    connection = connect(temporary/'work.sqlite', journal.guard)
    try:
        if independent:
            connection.execute('CREATE TABLE raw(rid TEXT,session TEXT,usr TEXT,intervention TEXT,saved TEXT,level TEXT,kind TEXT,strict TEXT,ordinal INTEGER)')
        else:
            connection.execute('CREATE TABLE pairs(rid TEXT PRIMARY KEY,usr TEXT,session TEXT,n INT,saved INT,interventions INT,chosen INT,levels INT,bad INT,dim TEXT,positive INT) WITHOUT ROWID')
        consumed = 0
        for ordinal in range(raw_done['meta']['chunks']):
            journal.guard.check()
            raw_key = f'raw/{ordinal:06d}'
            receipt = journal.unit(raw_key)
            batch = list(lines(journal.root/raw_key/f'b{index:02d}.jsonl.gz'))
            need(len(batch) == receipt['meta']['bucket_rows'][index], 'Bucket row coverage differs')
            need(all(bucket('response', row[0], count) == index for row in batch), 'Misrouted response row')
            if independent:
                connection.executemany('INSERT INTO raw VALUES(?,?,?,?,?,?,?,?,?)',
                    [tuple(row)+(consumed+i,) for i, row in enumerate(batch)])
            else:
                connection.executemany(moral.UPSERT, (encoded(row) for row in batch))
            consumed += len(batch)
            connection.commit()
        if independent:
            connection.execute('CREATE INDEX raw_order ON raw(rid,ordinal)')
            iterator = oracle_pairs(connection)
        else:
            iterator = producer_pairs(connection)
        census = dict(rows=0, responses=0, orphans=0, duplicated_responses=0, complete_valid_pairs=0,
                      invalid_exact_two_pairs=0, projected_observations=0)
        user_rows = [0] * count
        with ExitStack() as stack:
            disposition = zipped(stack, temporary/'DISPOSITIONS.jsonl.gz')
            projection = zipped(stack, temporary/'PROJECTION.jsonl.gz')
            users = [zipped(stack, temporary/f'u{b:02d}.jsonl.gz') for b in range(count)]
            for rid, user, session, n, valid, dimensions in iterator:
                if census['responses'] % 1000 == 0:
                    journal.guard.check()
                census['rows'] += n
                census['responses'] += 1
                census['orphans'] += int(n == 1)
                census['duplicated_responses'] += int(n > 2)
                census['complete_valid_pairs'] += int(valid)
                census['invalid_exact_two_pairs'] += int(n == 2 and not valid)
                status = 'valid' if valid else 'orphan' if n == 1 else 'duplicate' if n > 2 else 'invalid_exact_two'
                disposition.write(data(dict(response_id=rid, row_count=n, status=status)))
                for dimension, positive in dimensions:
                    record = dict(response_id=rid, user=user, session_id=session, dimension=dimension, positive=positive)
                    payload = data(record)
                    projection.write(payload)
                    target = bucket('user', user, count)
                    users[target].write(payload)
                    user_rows[target] += 1
                    census['projected_observations'] += 1
        need(census['rows'] == consumed, 'Complete-pair row coverage failed')
    finally:
        connection.close()
    journal.seal(key, temporary, dict(census=census, user_rows=user_rows), cpu0, wall0)
    take()


def user_unit(journal, index, config, take, independent):
    key = f'users/{index:02d}'
    if journal.unit(key):
        return
    journal.guard.start_unit(key)
    count = config.get('buckets', 32)
    cpu0, wall0 = time.process_time(), time.monotonic()
    temporary = journal.temporary()
    connection = connect(temporary/'work.sqlite', journal.guard)
    try:
        connection.execute('CREATE TABLE observations(usr TEXT,dim TEXT,positive INT,session TEXT)')
        total = 0
        for b in range(count):
            receipt = journal.unit(f'pairs/{b:02d}')
            need(receipt is not None, 'User cohort requires all response buckets')
            n = 0
            batch = []
            for record in lines(journal.root/f'pairs/{b:02d}'/f'u{index:02d}.jsonl.gz'):
                if n % 1000 == 0:
                    journal.guard.check()
                need(bucket('user', record['user'], count) == index, 'Misrouted user observation')
                batch.append((record['user'], record['dimension'], record['positive'], record['session_id']))
                n += 1
                if len(batch) == 10000:
                    connection.executemany('INSERT INTO observations VALUES(?,?,?,?)', batch)
                    connection.commit()
                    batch.clear()
            if batch:
                connection.executemany('INSERT INTO observations VALUES(?,?,?,?)', batch)
                connection.commit()
            need(n == receipt['meta']['user_rows'][index], 'User-shard coverage failed')
            total += n
        if independent:
            query = '''SELECT usr,dim,count(*),sum(positive),count(DISTINCT session)
                       FROM observations GROUP BY dim,usr ORDER BY usr,dim'''
        else:
            query = '''SELECT usr,dim,count(*),sum(positive),count(DISTINCT session)
                       FROM observations GROUP BY usr,dim ORDER BY usr,dim'''
        census = dict(fingerprints=0, common_returning_fingerprints=0,
                      three_scenario_fingerprints={}, observations=total)
        with ExitStack() as stack:
            stream = zipped(stack, temporary/'COUNTS.jsonl.gz')
            for user, group in itertools.groupby(connection.execute(query), key=lambda r: r[0]):
                journal.guard.check()
                dimensions = {row[1]: list(row[2:]) for row in group}
                if independent:
                    eligible = set(('Species', 'Intervention', 'Gender', 'Fitness')) <= set(dimensions)
                    eligible = eligible and min(dimensions[d][0] for d in ('Species', 'Intervention', 'Gender', 'Fitness')) >= 3
                    eligible = eligible and dimensions['Intervention'][2] >= 2
                else:
                    eligible = all(dimensions.get(d, [0])[0] >= 3 for d in (*core.LEVELS, 'Intervention')) and dimensions.get('Intervention', [0, 0, 0])[2] >= 2
                stream.write(data(dict(user=user, dimensions=dimensions, eligible=bool(eligible))))
                census['fingerprints'] += 1
                census['common_returning_fingerprints'] += int(eligible)
                for dimension, values in dimensions.items():
                    if values[0] >= 3:
                        census['three_scenario_fingerprints'][dimension] = census['three_scenario_fingerprints'].get(dimension, 0) + 1
    finally:
        connection.close()
    journal.seal(key, temporary, dict(census=census), cpu0, wall0)
    take()


def finish(journal, source, config, take):
    if journal.unit('merge'):
        return
    journal.guard.start_unit('merge')
    count = config.get('buckets', 32)
    cpu0, wall0 = time.process_time(), time.monotonic()
    temporary = journal.temporary()
    census = Counter()
    dimensions = Counter()
    for b in range(count):
        pairs = journal.unit(f'pairs/{b:02d}')['meta']['census']
        users = journal.unit(f'users/{b:02d}')['meta']['census']
        for field in ('rows', 'responses', 'orphans', 'duplicated_responses', 'complete_valid_pairs'):
            census[field] += pairs[field]
        for field in ('fingerprints', 'common_returning_fingerprints'):
            census[field] += users[field]
        dimensions.update(users['three_scenario_fingerprints'])
    result = dict(census)
    result['three_scenario_fingerprints'] = dict(dimensions)
    result['source_case_pass'] = result['common_returning_fingerprints'] >= 1000
    need(result == {field: source['expected_census'][field] for field in FIELDS},
         'Original full B2 census reconciliation failed')
    with ExitStack() as stack:
        output = zipped(stack, temporary/'PRIVATE_COUNTS.jsonl.gz')
        streams = [stack.enter_context(gzip.open(journal.root/f'users/{b:02d}'/'COUNTS.jsonl.gz', 'rt', encoding='utf8')) for b in range(count)]
        sources = [(json.loads(line) for line in stream) for stream in streams]
        previous = None
        n = 0
        for record in heapq.merge(*sources, key=lambda r: r['user']):
            if n % 1000 == 0:
                journal.guard.check()
            need(previous is None or record['user'] > previous, 'Duplicate or unordered complete user coverage')
            previous = record['user']
            output.write(data(record))
            n += 1
    need(n == result['fingerprints'], 'Full cohort coverage failed')
    need(sha(temporary/'PRIVATE_COUNTS.jsonl.gz', journal.guard) == source['expected_counts_sha256'],
         'Original cohort bytes differ')
    (temporary/'SOURCE.json').write_bytes(data(result))
    journal.seal('merge', temporary, dict(census=result, source_only=True, scientific_admission=False), cpu0, wall0)
    take()


def run(output, inputs, config, independent=False):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    guard = Guard(output, config)
    units = 0
    maximum = config.get('max_new_units', 1000000)
    need(type(maximum) is int and maximum > 0, 'Positive work-unit quantum required')
    source = contract(inputs, config)
    if independent:
        need((output/'PRODUCER_COMPLETE.json').is_file(), 'Missing complete producer; replay alone cannot complete')
        need(read(output/'PRODUCER_COMPLETE.json')['source_contract'] == inputs['source_contract'],
             'Producer source binding changed')
    binding = dict(source_contract=inputs['source_contract'], archive=source['archive'],
        buckets=config.get('buckets', 32), chunk_rows=config.get('chunk_rows', 100000),
        role='independent_replay' if independent else 'producer',
        code_pins={str(Path(p).resolve()): sha(p) for p in (__file__, core.__file__, moral.__file__, backlog_intake.__file__)})
    def take():
        nonlocal units
        units += 1
        if units >= maximum:
            raise YieldNow('completed_work_unit_quantum')
    role = output/('replay' if independent else 'producer')
    try:
        journal = Journal(role, binding, guard)
        ingest(journal, source, config, take)
        for b in range(config.get('buckets', 32)):
            pair_unit(journal, b, config, take, independent)
        for b in range(config.get('buckets', 32)):
            user_unit(journal, b, config, take, independent)
        finish(journal, source, config, take)
        need(set(journal.state) == ({f'raw/{i:06d}' for i in range(journal.unit('raw_complete')['meta']['chunks'])}
             | {'raw_complete', 'merge'} | {f'pairs/{b:02d}' for b in range(config.get('buckets', 32))}
             | {f'users/{b:02d}' for b in range(config.get('buckets', 32))}), 'Unexpected sealed work-unit coverage')
        if independent:
            need((output/'PRODUCER_COMPLETE.json').is_file(), 'Missing complete producer; replay alone cannot complete')
            producer = read(output/'PRODUCER_COMPLETE.json')
            need(producer['source_contract'] == inputs['source_contract'], 'Producer source binding changed')
            producer_state = read(output/'producer/STATE.json')
            need(set(producer_state) == set(journal.state), 'Producer complete-unit coverage differs')
            expected_producer_binding = dict(binding, role='producer')
            need(producer['binding'] == expected_producer_binding, 'Producer completion binding changed')
            for key in journal.state:
                old = read(output/'producer'/key/'RECEIPT.json')
                need(sha(output/'producer'/key/'RECEIPT.json') == producer_state[key], 'Producer receipt changed')
                new = journal.unit(key)
                need(old['binding'] == expected_producer_binding and old['key'] == key,
                     'Producer work-unit binding changed')
                need(set(old['files']) == set(new['files']), 'Producer artifact coverage differs')
                for name, record in new['files'].items():
                    if name == 'work.sqlite':
                        continue
                    need(old['files'][name] == record and sha(output/'producer'/key/name, guard) == record['sha256'],
                         'Full independent source/observation replay differs: ' + key + '/' + name)
                need(old['meta'] == new['meta'], 'Independent source disposition metadata differs')
        done = dict(status='complete', source_only=True, scientific_admission=False,
                    source_contract=inputs['source_contract'], original_census_reconciled=True,
                    independent_complete_archive_replay=independent, work_units=len(journal.state),
                    local_call_CPU_seconds=time.process_time()-guard.cpu0,
                    local_call_wall_seconds=time.monotonic()-guard.start,
                    local_cost_is_not_a_second_debit=True, binding=binding)
        atomic(output/('SOURCE_VERIFIED.json' if independent else 'PRODUCER_COMPLETE.json'), done)
        return done
    except (YieldNow, sqlite3.OperationalError) as error:
        if isinstance(error, sqlite3.OperationalError) and not guard.reason:
            raise
        progress = dict(status='yielded', verified=False, source_only=True, scientific_admission=False,
                        reason=guard.reason or str(error), completed_new_units=units,
                        local_call_CPU_seconds=time.process_time()-guard.cpu0,
                        local_call_wall_seconds=time.monotonic()-guard.start,
                        local_cost_is_not_a_second_debit=True)
        atomic(output/('REPLAY_PROGRESS.json' if independent else 'PROGRESS.json'), progress)
        return progress


def execute(output, inputs, config):
    return run(output, inputs, config, independent=False)


def verify(output, inputs, config):
    result = run(output, inputs, config, independent=True)
    if result['status'] != 'complete':
        return dict(verified=False, status='yielded', complete_recalculation=False)
    return dict(verified=True, complete_recalculation=True, source_only=True, scientific_admission=False)
