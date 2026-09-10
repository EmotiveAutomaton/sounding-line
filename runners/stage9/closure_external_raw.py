"""Read-only reconstruction of consumed B-roll and CommitBench raw records.

DESIGN CHECK: B03/H03/H06/X01/X02/X05/X12; LESSONS 2--5, CONTROLS 6--7.
NULL: changed raw bytes, source counts, selected records, exclusions, allocation
or producer binding refuse. ALTERNATIVE: every originally consumed input lane
reconstructs without fitting, reader execution or opening reserved responses.
CSV identity fields and API row identities locate already consumed records;
unselected B-roll responses are never literal-decoded and unselected API row
payloads are never JSON-decoded. Original whole-source grouping remains bound
to its archived metadata; this is not a new duplicate search over sealed text.
"""
from collections import Counter, defaultdict
import csv
import hashlib
import json
import zipfile

from .common import REPO, ROOT, closure, digest, file_hash, read
from .queue import inside


def value_end(text, start):
    """Locate a JSON value without decoding its payload; source hashes bind bytes."""
    if start >= len(text):
        raise ValueError('missing JSON value')
    char = text[start]
    if char == '"':
        i = start + 1
        while i < len(text):
            if text[i] == '\\':
                i += 2
            elif text[i] == '"':
                return i + 1
            else:
                i += 1
        raise ValueError('unterminated JSON string')
    if char in '[{':
        stack = [']' if char == '[' else '}']; i = start + 1
        while i < len(text):
            if text[i] == '"':
                i = value_end(text, i); continue
            if text[i] in '[{':
                stack.append(']' if text[i] == '[' else '}')
            elif text[i] in ']}':
                if text[i] != stack.pop():
                    raise ValueError('mismatched JSON container')
                if not stack:
                    return i + 1
            i += 1
        raise ValueError('unterminated JSON container')
    i = start
    while i < len(text) and text[i] not in ',]} \r\n\t':
        i += 1
    if i == start:
        raise ValueError('missing JSON scalar')
    return i


def fragments(text, object_mode=True):
    """Yield field-name/raw-value pairs or raw array items, without payload decode."""
    opening, closing = ('{', '}') if object_mode else ('[', ']')
    text = text.strip()
    if not text.startswith(opening) or not text.endswith(closing):
        raise ValueError('explicit JSON container required')
    i = 1; names = set()
    while i < len(text) - 1:
        while text[i].isspace(): i += 1
        if text[i] == closing:
            break
        name = None
        if object_mode:
            if text[i] != '"': raise ValueError('JSON field name required')
            end = value_end(text, i); name = json.loads(text[i:end]); i = end
            if name in names: raise ValueError('duplicate JSON field')
            names.add(name)
            while text[i].isspace(): i += 1
            if text[i] != ':': raise ValueError('JSON field separator required')
            i += 1
            while text[i].isspace(): i += 1
        end = value_end(text, i)
        yield (name, text[i:end]) if object_mode else text[i:end]
        i = end
        while i < len(text) and text[i].isspace(): i += 1
        if i == len(text) - 1: break
        if i >= len(text) or text[i] != ',': raise ValueError('JSON item separator required')
        i += 1
        if not text[i:-1].strip(): raise ValueError('trailing JSON comma')
    if i != len(text) - 1:
        raise ValueError('trailing JSON content')


def selected_page(path, page, total, wanted):
    """Decode only selected API row payloads; inspect index/project/commit metadata."""
    from .commitbench import PIN, FIELDS
    receipt = page['receipt']
    if (file_hash(path) != receipt['sha256'] or receipt['complete_eof'] is not True
            or page['headers'].get('X-Revision') != PIN):
        raise ValueError('original complete API source or revision changed')
    body = dict(fragments(path.read_text(encoding='utf-8')))
    if json.loads(body['partial']) is not False or json.loads(body['num_rows_total']) != total:
        raise ValueError('original complete API population differs')
    selected = {}; inventory = []
    for ordinal, encoded in enumerate(fragments(body['rows'], False)):
        item = dict(fragments(encoded))
        if (json.loads(item['row_idx']) != page['offset'] + ordinal
                or json.loads(item['truncated_cells'])):
            raise ValueError('API row range or complete-cell boundary differs')
        fields = dict(fragments(item['row']))
        if set(fields) != FIELDS:
            raise ValueError('original API row field inventory differs')
        identifiers = {key: json.loads(fields[key]) for key in ('hash', 'project', 'split')}
        if (any(not isinstance(v, str) or not v for v in identifiers.values())
                or identifiers['split'] != 'train'):
            raise ValueError('original API identity metadata differs')
        key = digest({'commit': identifiers['hash'], 'project': identifiers['project']})
        inventory.append(key)
        if key in wanted:
            row = json.loads(item['row'])
            if any(not isinstance(v, str) or not v for v in row.values()) or key in selected:
                raise ValueError('invalid or repeated selected API source row')
            selected[key] = row
    if len(inventory) != 100 or file_hash(path) != receipt['sha256']:
        raise ValueError('complete original page count changed or source raced inspection')
    return selected, inventory


def bound(prepared, archive, cases, kind):
    prepared, archive, cases = map(inside, (prepared, archive, cases))
    before = closure([prepared, cases])
    identity, done = read(prepared/'IDENTITY.json'), read(prepared/'COMPLETE.json')
    required = {'runners/stage9/common.py', 'runners/stage9/'+('broll.py' if kind == 'broll' else 'commitbench.py')}
    if kind == 'commitbench': required.add('runners/stage9/commitbench_allocation.py')
    source = identity['sources']; archived = read(archive/'SOURCE.json')
    if (set(source['files']) != required or source['sha256'] != digest(source['files'])
            or archived['sha256'] != digest(archived['files'])
            or any(archived['files'].get(p) != sha or file_hash(inside(archive/p, archive)) != sha
                   or file_hash(REPO/p) != sha for p, sha in source['files'].items())
            or done['identity_sha256'] != digest(identity)):
        raise ValueError('original raw parser, archive or prepared identity differs')
    producer, complete = read(cases/'IDENTITY.json'), read(cases/'COMPLETE.json')
    operation = 'broll-cases-v1' if kind == 'broll' else 'commit-cases-v1'
    if (producer['operation'] != operation or producer['scope'] not in ('pilot', 'scientific')
            or complete['execution_complete'] is not True or complete['identity_sha256'] != digest(producer)
            or complete['outputs'] != closure([REPO/p for p in complete['outputs']['files']])):
        raise ValueError('raw audit requires its actual completed source consumer')
    return prepared, archive, cases, before, identity, done, producer


def result(prepared, archive, cases, before, identity, producer, payloads, **extra):
    if closure([prepared, cases]) != before:
        raise ValueError('raw-source inspection changed or raced original evidence')
    return {'status': 'RECONSTRUCTED', 'prepared_identity_sha256': digest(identity),
        'prepared_complete_sha256': file_hash(prepared/'COMPLETE.json'),
        'case_identity_sha256': digest(producer), 'case_complete_sha256': file_hash(cases/'COMPLETE.json'),
        'original_source_sha256': identity['sources']['sha256'],
        'source_archive': archive.relative_to(REPO).as_posix(), 'payload_sha256': digest(payloads),
        'new_fits': 0, 'new_reader_calls': 0, 'new_reserve_openings': 0,
        'reserve_payloads_parsed': False, 'scientific_admission': False, **extra}


def inspect_commit(prepared, archive, cases):
    from .commitbench import PIN, parse_diff
    from .commitbench_allocation import allocate
    prepared, archive, cases, before, identity, done, producer = bound(prepared, archive, cases, 'commitbench')
    lanes = ('train', 'development') if producer['scope'] == 'pilot' else ('train', 'development', 'discovery')
    if (producer['prepared_complete_sha256'] != file_hash(prepared/'COMPLETE.json')
            or set(producer['source_splits']) != set(lanes) or producer['reserve_payload_parsed'] is not False
            or done['reserve_allocation_meets_fraction'] is not True):
        raise ValueError('code source audit cannot widen original consumed lanes')
    if any(file_hash(prepared/lane/'RECORDS.json') != producer['source_splits'][lane] for lane in lanes):
        raise ValueError('original consumed code records changed')
    if (closure([REPO/p for p in identity['parent_preparation']['files']]) != identity['parent_preparation']
            or file_hash(ROOT/'intake/COMMITBENCH_BASELINE.json') != identity['prior_baseline_sha256']):
        raise ValueError('original source exposure changed')
    old_path, extension_path = ROOT/'intake/COMMITBENCH_SOURCE_SLICE.json', ROOT/'intake/COMMITBENCH_SOURCE_EXTENSION.json'
    old, extension = read(old_path), read(extension_path)
    if (file_hash(old_path) != identity['source_slice_sha256'] or file_hash(extension_path) != identity['extension_sha256']
            or extension['parent_slice_sha256'] != identity['source_slice_sha256']
            or old['pin'] != PIN or extension['pin'] != PIN or old['rows'] != 1200 or extension['rows'] != 1200):
        raise ValueError('original bounded source selection changed')
    for name, sha in done['files'].items():
        if file_hash(inside(prepared/name, prepared)) != sha: raise ValueError('original prepared code inventory changed')
    splits, repair = read(prepared/'SPLITS.json'), read(prepared/'GROUP_REPAIR.json')
    allocation, receipt = allocate(splits, repair['eligible_components'], repair['prior_allocations'])
    if allocation != splits or receipt != repair['allocation_receipt'] or receipt != done['allocation']:
        raise ValueError('original exposure-priority allocation does not reconstruct')
    attempts = read(prepared/'ATTEMPTS.json'); wanted = {r['key']: r for r in attempts if r['split'] in lanes}
    if len({r['key'] for r in attempts}) != len(attempts) or len(attempts) != done['attempts']:
        raise ValueError('original code attempt inventory differs')
    rows = {}; inventory = []; offsets = set()
    pages = old['pages'] + extension['new_pages']
    for page in pages:
        positions = set(range(page['offset'], page['offset'] + 100))
        if positions & offsets: raise ValueError('original source pages overlap')
        offsets.update(positions)
        selected, keys = selected_page(ROOT/'private/intake/objects'/page['receipt']['sha256'], page, old['total_source_rows'], wanted)
        if set(rows) & set(selected): raise ValueError('repeated consumed code source')
        rows.update(selected); inventory.extend(keys)
    if (len(inventory) != done['source_rows'] or len(inventory) != 2400 or len(set(inventory)) != len(inventory)
            or set(inventory) != {a['key'] for a in attempts} or set(rows) != set(wanted)
            or done['duplicate_source_rows'] != 0):
        raise ValueError('complete source identity inventory or consumed population differs')
    rebuilt = {lane: [] for lane in lanes}; exclusions = Counter()
    for key in inventory:
        if key not in rows: continue
        row, attempt = rows[key], wanted[key]; reason = None; parsed = None
        try: parsed = parse_diff(row['diff'])
        except ValueError as exc: reason = str(exc)
        if attempt['exclusion'] != reason or splits[attempt['unit']] != attempt['split']:
            raise ValueError('consumed diff exclusion or original group allocation differs')
        if reason: exclusions[reason] += 1; continue
        rebuilt[attempt['split']].append(row | {'key': key, 'unit': attempt['unit'], 'source_split': row['split'],
            'parsed': parsed, 'languages': row['diff_languages'].split(','), 'content_sha256': digest(row['diff']), 'split': attempt['split']})
    if any(own != read(prepared/lane/'RECORDS.json') for lane, own in rebuilt.items()):
        raise ValueError('consumed complete code records do not reconstruct from raw source')
    if any(file_hash(ROOT/'private/intake/objects'/p['receipt']['sha256']) != p['receipt']['sha256'] for p in pages):
        raise ValueError('raw API source changed during reconstruction')
    return result(prepared, archive, cases, before, identity, producer, rebuilt,
        lanes=list(lanes), records={lane: len(own) for lane, own in rebuilt.items()},
        raw_payloads_decoded=len(rows), source_identity_records=len(inventory), exclusions=dict(exclusions),
        unselected_raw_payloads_decoded=0, original_allocation_reconstructed=True,
        new_whole_source_duplicate_search=False,
        scope='consumed complete-diff/stated-description records and exclusions; original group metadata preserved, sealed diffs not reopened for duplicate search; no individual intention claim')


def inspect_broll(prepared, archive, cases):
    from .broll import scripts, selections, partition
    prepared, archive, cases, before, identity, done, producer = bound(prepared, archive, cases, 'broll')
    metadata = read(cases/'METADATA.json')
    lanes = ('development',) if producer['scope'] == 'pilot' else ('development', 'discovery')
    expected = {prepared/'SCRIPTS.json'} | {prepared/(lane+'.json') for lane in lanes}
    if (digest(metadata) != producer['metadata_sha256'] or metadata['canonical_identity_sha256'] != digest(identity)
            or metadata['reserve_records_parsed'] is not False
            or {inside(p) for p in metadata['source_files']} != expected
            or any(file_hash(inside(p)) != sha for p, sha in metadata['source_files'].items())):
        raise ValueError('B-roll source audit cannot widen original consumed lanes')
    source, rights = read(ROOT/'intake/BROLL_ARCHIVE.json'), read(ROOT/'intake/BROLL_REUSE_REVIEW.json')
    if (identity['source'] != source or identity['reuse_review'] != rights
            or rights['private_research_analysis_accepted'] is not True or rights['archive_sha256'] != source['sha256']
            or identity['chronology_source'] != read(ROOT/'intake/BROLL_TASK_SOURCE.json') or source['complete_eof'] is not True):
        raise ValueError('original B-roll source, rights or chronology review changed')
    raw = inside(ROOT/'private/intake/materialized'/source['sha256'])
    blob = ROOT/'private/intake/objects'/source['sha256']
    if file_hash(blob) != source['sha256']: raise ValueError('original B-roll archive changed')
    hashes = dict(identity['files'])
    with zipfile.ZipFile(blob) as zipped:
        for name in (*hashes, 'broll_alldata_vocab.csv'):
            sha = hashlib.sha256(zipped.read(name)).hexdigest()
            if (name in hashes and hashes[name] != sha) or file_hash(raw/name) != sha:
                raise ValueError('materialized B-roll source differs from original archive')
            hashes[name] = sha
    csv.field_size_limit(2**24); stimuli = scripts(raw)
    if stimuli != read(prepared/'SCRIPTS.json'): raise ValueError('released script opportunities or POS annotations changed')
    with (raw/'broll_alldata_vocab.csv').open(encoding='utf-8-sig', newline='') as stream:
        first = next(csv.DictReader(stream))
    people = defaultdict(list); rebuilt = {lane: [] for lane in lanes}; first_person = None; decoded = 0
    with (raw/'broll_alldata.csv').open(encoding='utf-8-sig', newline='') as stream:
        for entry in csv.DictReader(stream):
            person = digest({'broll-person': entry['gameID']})[:24]
            if first_person is None: first_person = person
            key, trial, goal = entry['object'].casefold(), int(entry['trialNum']), entry['goal']
            if entry['eventType'] != 'test' or key not in stimuli or goal not in ('informative', 'entertaining') or not 0 <= trial < 12:
                raise ValueError('original released participant metadata differs')
            people[person].append((trial, key, goal))
            lane = identity['person_split'].get(person)
            if lane not in lanes: continue
            highlights = selections(entry['response']); decoded += 1
            chosen = {w for h in highlights for w in h['words']}; absent = chosen - set(stimuli[key]['support'])
            reason = 'selected fragment outside script vocabulary' if absent else None
            rebuilt[lane].append({'key': digest({'person': person, 'trial': trial, 'script': key})[:24],
                'person': person, 'script_key': key, 'trial': trial, 'goal': goal, 'highlights': highlights,
                'selected_words': sorted(chosen), 'labels': [int(w in chosen) for w in stimuli[key]['support']],
                'usable': reason is None, 'exclusion': reason, 'unmatched_word_count': len(absent)})
    for rows in people.values():
        if len(rows) != 12 or {r[0] for r in rows} != set(range(12)) or {r[1] for r in rows} != set(stimuli) or len({r[2] for r in rows}) != 1:
            raise ValueError('original whole-participant chronology differs')
    if (partition(people, {first_person, digest({'broll-person': first['gameID']})[:24]}) != identity['person_split']
            or partition(stimuli, {first['object'].casefold()}, 'broll-script-v1') != identity['script_split']
            or done['people'] != len(people) or done['attempted_records'] != sum(map(len, people.values()))
            or done['person_split_counts'] != dict(Counter(identity['person_split'].values()))
            or done['script_split_counts'] != dict(Counter(identity['script_split'].values()))):
        raise ValueError('original people/script population or allocation does not reconstruct')
    if any(own != read(prepared/(lane+'.json')) for lane, own in rebuilt.items()):
        raise ValueError('consumed selections, empty attempts or exclusions do not reconstruct')
    if any(file_hash(raw/name) != sha for name, sha in hashes.items()): raise ValueError('B-roll source raced inspection')
    return result(prepared, archive, cases, before, identity, producer, rebuilt,
        lanes=list(lanes), records={lane: len(own) for lane, own in rebuilt.items()},
        raw_responses_decoded=decoded, unselected_raw_responses_decoded=0,
        participant_identity_records=sum(map(len, people.values())), original_people=len(people), scripts=len(stimuli),
        scope='consumed recorded concept-word selections; crossed person/script dependence and original population disagreement retained; no unobserved imagery or values')
