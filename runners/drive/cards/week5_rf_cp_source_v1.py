"""Private checkpointed source/marker intake; not RF1/CP1 scientific admission.

DESIGN CHECK: LESSONS 2--5. All record identities are HMAC salted. Exact archive,
module and marker pins bind each immutable block. Null and alternative share the
same >=3%/100-review/80-correct gate; missing source or review is never a pass.
RF election identity remains explicitly unresolved. No text leaves local output.
"""
from collections import Counter
from pathlib import Path
import gzip
import hashlib
import hmac
import io
import json
import re
import zipfile
from . import week5_rf_cp_markers_v1 as markers

PINS = {'RF1': '88d53196fb2564a2e20286dbba818832f718cc352bb181a2101d23d2556f0862',
        'CP1': '9995d3b885338e9332496193a0b7b01453174c2d6008ec88634ad7cb884f8f41'}
COUNTS = {'RF1': 198275, 'CP1': 391294}
BLOCK = 512
SEED = 20261112


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf8')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(2**20), b''):
            h.update(block)
    return h.hexdigest()


def write_equal(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    data = canonical(value) + b'\n'
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError('Immutable source receipt changed')
        return
    with path.open('xb') as stream:
        stream.write(data)


def write_chunk(path, value):
    data = gzip.compress(canonical(value), mtime=0)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError('Immutable source block changed')
    else:
        with path.open('xb') as stream:
            stream.write(data)
    write_equal(path.with_suffix('.seal.json'), {'sha256': sha(path), 'bytes': len(data)})


def read_chunk(path):
    seal = json.loads(path.with_suffix('.seal.json').read_text('utf8'))
    if sha(path) != seal['sha256'] or path.stat().st_size != seal['bytes']:
        raise ValueError('Sealed source block changed')
    return json.loads(gzip.decompress(path.read_bytes()))


def identity(salt, family, kind, raw):
    if not isinstance(raw, str) or not raw:
        raise ValueError('Missing source identity')
    return hmac.new(salt, (family + '|' + kind + '|' + raw).encode('utf8'), hashlib.sha256).hexdigest()


def raw_rows(archive, family):
    if family == 'RF1':
        with gzip.open(archive, 'rt', encoding='utf8', errors='strict') as stream:
            row = {}; duplicate = False
            for line in stream:
                line = line.rstrip('\r\n')
                if not line:
                    if row:
                        yield dict(row, _duplicate=duplicate)
                    row = {}; duplicate = False
                    continue
                match = re.match(r'^(SRC|TGT|VOT|RES|YEA|DAT|TXT):(.*)$', line)
                if match:
                    key, value = match.groups()
                    duplicate = duplicate or key in row
                    row[key] = value.lstrip()
                elif 'TXT' in row:
                    row['TXT'] += '\n' + line
                else:
                    row['_invalid'] = True
            if row:
                yield dict(row, _duplicate=duplicate)
    elif family == 'CP1':
        with zipfile.ZipFile(archive) as source:
            metadata = json.loads(source.read('wiki-corpus/speakers.json'))
            with source.open('wiki-corpus/utterances.jsonl') as raw:
                for line in io.TextIOWrapper(raw, encoding='utf8', errors='strict'):
                    try:
                        row = json.loads(line)
                        if not isinstance(row, dict):
                            raise ValueError('Utterance is not an object')
                        row['_speaker_meta'] = metadata.get(row.get('user'))
                        yield row
                    except (ValueError, TypeError):
                        yield {'_invalid': True}
    else:
        raise ValueError('Unknown source family')


def convert(raw, ordinal, family, salt, constructed=False):
    fallback = identity(salt, family, 'ordinal', str(ordinal))
    if raw.get('_invalid') or raw.get('_duplicate'):
        return {'id': fallback, 'ordinal': ordinal, 'refused': 'malformed_record'}
    try:
        if family == 'RF1':
            if not all(key in raw for key in ('SRC', 'TGT', 'VOT', 'RES', 'YEA', 'DAT', 'TXT')):
                raise ValueError('missing_fields')
            if constructed and not all(raw[k].startswith('constructed-') for k in ('SRC', 'TGT')):
                raise ValueError('fixture_identity_refusal')
            vote, outcome, year = (int(raw[k]) for k in ('VOT', 'RES', 'YEA'))
            if vote not in (-1, 0, 1) or outcome not in (-1, 1) or not 2003 <= year <= 2013:
                raise ValueError('vote_year_domain')
            return {'id': fallback, 'ordinal': ordinal,
                'voter': identity(salt, family, 'user', raw['SRC']),
                'candidate': identity(salt, family, 'user', raw['TGT']),
                'vote': vote, 'outcome': outcome, 'year': year, 'source_timestamp': raw['DAT'],
                'election': None, 'election_identity_qualified': False,
                'markers': markers.rf_counts(raw['TXT'])}
        if not all(key in raw for key in ('id', 'root', 'user', 'reply-to', 'timestamp', 'text', 'meta')):
            raise ValueError('missing_fields')
        if constructed and not raw['user'].startswith('constructed-'):
            raise ValueError('fixture_identity_refusal')
        sm = raw['_speaker_meta']
        if not isinstance(sm, dict) or type(raw['meta'].get('is-admin')) is not bool or type(sm.get('is-admin')) is not bool:
            raise ValueError('missing_admin_metadata')
        ec = int(sm['edit-count'])
        if ec < 0:
            raise ValueError('negative_edit_count')
        return {'id': identity(salt, family, 'utterance', raw['id']), 'ordinal': ordinal,
            'speaker': identity(salt, family, 'user', raw['user']),
            'conversation': identity(salt, family, 'conversation', raw['root']),
            'reply_to': identity(salt, family, 'utterance', raw['reply-to']) if raw['reply-to'] is not None else None,
            'source_timestamp': raw['timestamp'], 'is_admin': raw['meta']['is-admin'],
            'speaker_is_admin': sm['is-admin'], 'edit_count': ec,
            'edit_count_clock_qualified': False, 'markers': markers.cp_counts(raw['text'])}
    except (KeyError, ValueError, TypeError, AttributeError):
        # Raw values and usernames never appear in error messages or receipts.
        if constructed:
            raise ValueError('Constructed source schema/identity refusal') from None
        return {'id': fallback, 'ordinal': ordinal, 'refused': 'schema_or_value_domain'}


def requested(output):
    return any((p / 'YIELD_REQUEST.json').exists() for p in (output, output.parent))


def binding_for(inputs, config):
    family = config['family']; markers.families(family)
    salt = Path(inputs['identity_salt']).read_bytes()
    if len(salt) != 32:
        raise ValueError('Expected existing private 32-byte campaign identity salt')
    archive_pin = sha(inputs['archive'])
    expected = config['fixture_archive_sha256'] if config.get('constructed_fixture') else PINS[family]
    if archive_pin != expected:
        raise ValueError('Source archive pin changed')
    value = {'schema': 'RF-CP-SOURCE-1', 'family': family, 'archive_sha256': archive_pin,
        'identity_salt_sha256': hashlib.sha256(salt).hexdigest(), 'block_size': BLOCK, 'review_seed': SEED,
        'source_module_sha256': sha(__file__), 'marker_module_sha256': sha(markers.__file__),
        'constructed_fixture': bool(config.get('constructed_fixture')),
        'expected_records': config['fixture_expected_records'] if config.get('constructed_fixture') else COUNTS[family]}
    return value, salt


def produce(output, inputs, config):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    bind, salt = binding_for(inputs, config); family = bind['family']
    write_equal(output / 'BINDING.json', bind)
    prefix = list(sorted(output.glob('block-*.json.gz')))
    if [p.name for p in prefix] != [f'block-{i:06d}.json.gz' for i in range(len(prefix))]:
        raise ValueError('Noncontiguous sealed source prefix')
    blocks = 0; new = 0; chunk = []; total = 0
    for ordinal, raw in enumerate(raw_rows(inputs['archive'], family)):
        total = ordinal + 1
        if ordinal % BLOCK == 0 and requested(output):
            return {'status': 'yielded', 'complete_source': False, 'sealed_blocks': blocks}
        # Resume authenticates immutable closed records; independent verify rebuilds them.
        if blocks < len(prefix):
            if ordinal % BLOCK == 0:
                saved = read_chunk(prefix[blocks])
                if saved['binding'] != bind or saved['start'] != ordinal:
                    raise ValueError('Closed source block binding changed')
                if len(saved['rows']) > BLOCK or any(r['ordinal'] != ordinal+i for i, r in enumerate(saved['rows'])):
                    raise ValueError('Closed source block order changed')
            if ordinal % BLOCK + 1 == len(saved['rows']):
                blocks += 1
            continue
        chunk.append(convert(raw, ordinal, family, salt, bind['constructed_fixture']))
        if len(chunk) == BLOCK:
            write_chunk(output / f'block-{blocks:06d}.json.gz', {'binding': bind, 'start': ordinal + 1-BLOCK, 'rows': chunk})
            blocks += 1; new += 1; chunk = []
            if config.get('max_new_blocks') is not None and new >= config['max_new_blocks']:
                return {'status': 'yielded', 'complete_source': False, 'sealed_blocks': blocks}
    if chunk:
        write_chunk(output / f'block-{blocks:06d}.json.gz', {'binding': bind, 'start': total-len(chunk), 'rows': chunk})
        blocks += 1
    if blocks != len(list(output.glob('block-*.json.gz'))):
        raise ValueError('Closed source suffix exceeds actual source')
    hits = Counter(); refused = Counter(); selected = {k: [] for k in markers.families(family)}; seen = set()
    for index in range(blocks):
        saved = read_chunk(output / f'block-{index:06d}.json.gz')
        for row in saved['rows']:
            if row['id'] in seen:
                raise ValueError('Duplicate canonical source record')
            seen.add(row['id'])
            if row.get('refused'):
                refused[row['refused']] += 1; continue
            for name, present in markers.presence(family, row['markers']).items():
                if present:
                    hits[name] += 1
                    rank = hashlib.sha256(f'{family}|{SEED}|{name}|{row["id"]}'.encode()).hexdigest()
                    selected[name].append((rank, row['id']))
                    selected[name] = sorted(selected[name])[:100]
    wanted = {item[1] for values in selected.values() for item in values}; texts = {}
    for ordinal, raw in enumerate(raw_rows(inputs['archive'], family)):
        if ordinal % BLOCK == 0 and requested(output):
            return {'status': 'yielded', 'complete_source': False, 'sealed_blocks': blocks}
        key = identity(salt, family, 'ordinal', str(ordinal)) if family == 'RF1' else identity(salt, family, 'utterance', raw['id']) if isinstance(raw.get('id'), str) and raw['id'] else None
        if key in wanted:
            texts[key] = raw['TXT'] if family == 'RF1' else markers.strip_quotes(raw['text'])
    sample = [{'family': name, 'id': key, 'rank': rank, 'text': texts[key]}
              for name in markers.families(family) for rank, key in selected[name]]
    summary = {'schema': 'RF-CP-SOURCE-SUMMARY-1', 'family': family, 'records': total,
        'expected_records': bind['expected_records'], 'unique_records': len(seen), 'refusals': dict(sorted(refused.items())),
        'family_hits': {k: hits[k] for k in markers.families(family)},
        'sample_sizes': {k: len(selected[k]) for k in markers.families(family)},
        'source_gate': total == bind['expected_records'] and len(seen) == total and sum(refused.values()) <= .01*total,
        'marker_gate': 'manual_review_pending', 'scientific_admission': False,
        'election_identity_qualified': False if family == 'RF1' else None,
        'record_kind': 'run', 'theory_tags': ['H15-T3' if family == 'RF1' else 'H15-T4'],
        'by_construction': bind['constructed_fixture']}
    write_equal(output / 'REVIEW_PRIVATE.json', sample)
    write_equal(output / 'ADJUDICATION_TEMPLATE.json', [{k:v for k,v in row.items() if k in ('family','id')} | {'correct': None} for row in sample])
    write_equal(output / 'SUMMARY.json', summary)
    write_equal(output / 'SOURCE_COMPLETE.json', {'complete_source': True, 'binding_sha256': sha(output / 'BINDING.json'),
        'summary_sha256': sha(output / 'SUMMARY.json'), 'private_review_sha256': sha(output / 'REVIEW_PRIVATE.json'),
        'blocks': {p.name: sha(p) for p in sorted(output.glob('block-*.json.gz'))}})
    return summary


def execute(output, inputs, config):
    return produce(output, inputs, config)


def verify(output, inputs, config):
    output = Path(output)
    if not (output / 'SOURCE_COMPLETE.json').is_file():
        raise ValueError('Cannot verify incomplete source')
    replay = output / 'independent-replay'
    result = produce(replay, inputs, config)
    if result.get('status') == 'yielded':
        return dict(result, verified=False)
    complete = json.loads((output / 'SOURCE_COMPLETE.json').read_text('utf8'))
    for name, expected in complete['blocks'].items():
        if sha(output / name) != expected or sha(replay / name) != expected:
            raise ValueError('Full independent source replay differs')
    for name in ('BINDING.json', 'SUMMARY.json', 'REVIEW_PRIVATE.json', 'ADJUDICATION_TEMPLATE.json', 'SOURCE_COMPLETE.json'):
        if (output / name).read_bytes() != (replay / name).read_bytes():
            raise ValueError('Independent source receipt differs')
    proof = {'verified': True, 'complete_source_and_markers_replayed': True, 'scientific_admission': False,
        'source_complete_sha256': sha(output / 'SOURCE_COMPLETE.json'), 'binding_sha256': sha(output / 'BINDING.json')}
    write_equal(output / 'SOURCE_VERIFIED.json', proof)
    return proof
