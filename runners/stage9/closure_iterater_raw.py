"""Reconstruct consumed HUMAN rows without parsing unconsumed reserve payloads.

DESIGN CHECK: B03/H02/X01/X02/X05/X12; LESSONS 2--5, CONTROLS 6--7.
NULL: changed raw text/votes, source offsets, group repair, selected row inventory,
links or producer metadata refuse. ALTERNATIVE: the original canonical row parser
and unchanged exposure-priority repair reproduce every consumed prepared row/link.
Whole source files and unopened prepared lanes are hashed as opaque bytes only.
Only raw lines named by the completed producer's original input lanes are parsed.
No fitting, reader execution, new source allocation or reserve opening occurs.
"""
from collections import Counter, defaultdict
import json

from .common import REPO, ROOT, closure, digest, file_hash, read
from .data import document_record
from .queue import inside
from .reconcile_groups import reconcile

LANES = ('pilot', 'train', 'development', 'discovery', 'reserve')
PUBLISHED = ('train', 'dev', 'test')


def raw_inputs(source):
    archive = read(ROOT / 'intake/ITERATER_ARCHIVE.json')
    materialized = read(ROOT / 'intake/ITERATER_MATERIALIZATION.json')
    if materialized['archive'] != archive['sha256'] or materialized['executed'] is not False:
        raise ValueError('original data-only materialization identity changed')
    directory = inside(ROOT / 'private/intake/materialized' / archive['sha256'] / 'IteraTeR')
    required = {name + '.json' for name in PUBLISHED} | {'sentence/' + name + '.json' for name in PUBLISHED}
    if set(source) != required:
        raise ValueError('complete original HUMAN raw-source inventory required')
    paths = {}
    for name, sha in source.items():
        relative = ('human_sent_level/' + name.removeprefix('sentence/') if name.startswith('sentence/')
                    else 'human_doc_level/' + name)
        path = inside(directory / relative, directory)
        if materialized['materialized']['IteraTeR/' + relative]['sha256'] != sha or file_hash(path) != sha:
            raise ValueError('original HUMAN raw source differs from materialized bytes')
        paths[name] = path
    return paths


def selected_documents(paths, source, requested):
    """Scan/hash opaque lines; JSON-decode only the requested source offsets."""
    if set(requested) != set(PUBLISHED):
        raise ValueError('explicit original document splits required')
    rows, counts = {}, {}
    for split in PUBLISHED:
        wanted = requested[split]
        if any(type(line) is not int or line < 1 for line in wanted):
            raise ValueError('positive physical source offsets required')
        path = paths[split + '.json']; count = 0; found = set()
        if file_hash(path) != source[split + '.json']:
            raise ValueError('source changed before selected-row inspection')
        with path.open('rb') as stream:
            for line_no, encoded in enumerate(stream, 1):
                if encoded.strip():
                    count += 1
                if line_no not in wanted:
                    continue
                if not encoded.strip() or len(encoded) > 4 * 1024**2:
                    raise ValueError('selected source row violates the original parser boundary')
                row = document_record(json.loads(encoded), split, line_no, source[split + '.json'])
                rows[(split, line_no)] = row; found.add(line_no)
        if found != wanted or file_hash(path) != source[split + '.json']:
            raise ValueError('selected raw offset is missing or source changed during inspection')
        counts[split] = count
    if counts != {'train': 481, 'dev': 27, 'test': 51}:
        raise ValueError('complete released document counts changed')
    return rows, counts


def original_unit(group, merges):
    parents = {}
    for edge in merges:
        parents[edge['b']] = edge['a']
    seen = set()
    while group in parents:
        if group in seen:
            raise ValueError('cyclic original duplicate grouping')
        seen.add(group); group = parents[group]
    return group


def links(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['independent_unit']].append(row)
    result = []
    for group in grouped.values():
        for row in group:
            following = [r for r in group if r['revision_depth'] == row['revision_depth'] + 1
                         and r['before'] == row['artifact']]
            if len(following) == 1:
                result.append({'current': row['key'], 'future': following[0]['key'], 'split': row['split']})
    return result


def inspect(prepared, archive, case_directory):
    prepared, archive, case_directory = map(inside, (prepared, archive, case_directory))
    before = closure([prepared, case_directory])
    identity = read(prepared / 'IDENTITY.json')
    parent = prepared.parent / 'iterater'; old = read(parent / 'IDENTITY.json')
    repair = identity['source_group_repair']
    receipt = read(ROOT / 'intake/ITERATER_GROUP_REPAIR.json')
    audit_path = prepared.parent / 'iterater-duplicate-audit-v1.json'; audit = read(audit_path)
    required = {'runners/stage9/data.py': old['preparation_sha256'],
                'runners/stage9/reconcile_groups.py': repair['source_sha256']}
    archived = read(archive / 'SOURCE.json')
    if (archived['sha256'] != digest(archived['files'])
            or any(archived['files'].get(name) != sha or file_hash(archive / name) != sha for name, sha in required.items())
            or file_hash(REPO / 'runners/stage9/reconcile_groups.py') != repair['source_sha256']
            or repair['parent_identity_sha256'] != digest(old)
            or file_hash(audit_path) != repair['duplicate_audit_sha256']
            or receipt['identity_sha256'] != digest(identity)):
        raise ValueError('original parser, group repair or preparation identity differs')
    for name, sha in audit['input_files'].items():
        if file_hash(inside(REPO / name)) != sha:
            raise ValueError('original duplicate-audit input changed')
    mapping, allocation, components = reconcile(old['allocation'], audit['edges'])
    expected = {**old, 'allocation': allocation, 'source_group_repair': {
        'parent_identity_sha256': digest(old), 'duplicate_audit_sha256': file_hash(audit_path),
        'source_sha256': repair['source_sha256'], 'old_to_new': mapping, 'components': components,
        'rule': 'exposed split takes precedence; reserve requires an existing unexposed reserved member; no fresh reserve replacements'}}
    if (identity != expected or receipt['group_counts'] != dict(Counter(allocation.values()))
            or receipt['wholly_new_reserve_groups'] != 0):
        raise ValueError('original exposure-priority grouping does not reconstruct')
    producer = read(case_directory / 'IDENTITY.json'); metadata = read(case_directory / 'METADATA.json')
    done = read(case_directory / 'COMPLETE.json')
    if (producer['operation'] != 'iterater-actual-revision-cases-v1'
            or producer['scope'] not in ('pilot', 'scientific')
            or producer['metadata_sha256'] != digest(metadata)
            or metadata['prepared_identity_sha256'] != digest(identity)
            or done['identity_sha256'] != digest(producer) or done['execution_complete'] is not True
            or done['outputs'] != closure([REPO / p for p in done['outputs']['files']])):
        raise ValueError('raw audit requires the actual completed HUMAN case input')
    lanes = ('train', 'development') if producer['scope'] == 'pilot' else ('train', 'development', 'discovery')
    expected_paths = {prepared / lane / name for lane in lanes for name in ('records.json', 'future_links.json')}
    if {inside(name) for name in metadata['prepared_files']} != expected_paths:
        raise ValueError('producer raw audit cannot widen its original input lanes')
    if any(file_hash(inside(name)) != sha for name, sha in metadata['prepared_files'].items()):
        raise ValueError('producer input bytes changed')
    saved = {lane: read(prepared / lane / 'records.json') for lane in lanes}
    requested = {split: set() for split in PUBLISHED}; source_keys = set()
    for lane, rows in saved.items():
        if len(rows) != receipt['record_counts'][lane]:
            raise ValueError('complete original consumed lane required')
        for row in rows:
            key = (row['published_split'], row['source_line'])
            if (key in source_keys or key[0] not in requested or row['split'] != lane
                    or allocation.get(row['independent_unit']) != lane):
                raise ValueError('repeated source row or incorrect consumed allocation')
            source_keys.add(key); requested[key[0]].add(key[1])
    paths = raw_inputs(identity['source'])
    raw, counts = selected_documents(paths, identity['source'], requested)
    rebuilt = {lane: [] for lane in lanes}
    for row in raw.values():
        previous = original_unit(row['group'], old['duplicates'])
        current = mapping[previous]; lane = allocation[current]
        if lane not in rebuilt:
            raise ValueError('consumed row resolves to an unopened source lane')
        rebuilt[lane].append({**row, 'independent_unit': current, 'split': lane,
            'previous_independent_unit': previous, 'previous_split': old['allocation'][previous]})
    for lane, rows in rebuilt.items():
        rows.sort(key=lambda r: (LANES.index(r['previous_split']), PUBLISHED.index(r['published_split']), r['source_line']))
        if rows != saved[lane] or links(rows) != read(prepared / lane / 'future_links.json'):
            raise ValueError('consumed canonical rows, votes, grouping or successor links do not reconstruct')
    if raw_inputs(identity['source']) != paths or closure([prepared, case_directory]) != before:
        raise ValueError('raw inspection changed or raced its original evidence')
    return {'status': 'RECONSTRUCTED', 'prepared_identity_sha256': digest(identity),
        'case_identity_sha256': digest(producer), 'case_complete_sha256': file_hash(case_directory / 'COMPLETE.json'),
        'original_parser_sha256': old['preparation_sha256'], 'original_group_repair_sha256': repair['source_sha256'],
        'raw_source_sha256': digest(identity['source']), 'source_archive': archive.relative_to(REPO).as_posix(),
        'lanes': list(lanes), 'records': {lane: len(rows) for lane, rows in rebuilt.items()},
        'payload_sha256': digest(rebuilt), 'published_document_counts': counts,
        'raw_document_rows_parsed': len(raw), 'unselected_raw_rows_json_parsed': 0,
        'reserve_payloads_parsed': False, 'new_reserve_openings': 0, 'new_fits': 0, 'new_reader_calls': 0,
        'scientific_admission': False,
        'scope': 'exact raw rows and links in the completed producer input lanes; other raw rows and unused prepared lanes hashed only, original reserve allocation unchanged'}
