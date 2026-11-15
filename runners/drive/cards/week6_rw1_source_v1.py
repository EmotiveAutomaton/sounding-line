"""Pinned RW1 source projection and independent marker-receipt preparation.

DESIGN CHECK: LESSONS 2,3. No outcome association, vocabulary learning or model
fit occurs here. Only long text and the five commissioned ratings are imported.
The source-row key is salted. Blank annotation forms are not annotations.
"""
from pathlib import Path
import csv
import hashlib
import hmac
import io as streams
import json
import math
import re
import time

import pandas as pd

from . import week6_rw1_intake_v1 as marker
from . import week5_engine_export_io as seal
from . import week5_qualification_io as io

MODULE = 'runners.drive.cards.week6_rw1_source_v1'
REVISION = '7324d50869578589a47781bc1d26123ca48e27c8'
GIT_BLOB = '1fc84fa83c893391ad0e9a5663082f3210518ea5'
SOURCE_URL = ('https://raw.githubusercontent.com/ben-aaron188/covid19worry/'
              + REVISION + '/data_phase_1/files/meta/rwwd_full.csv')
OSF_DECLARED_SHA256 = 'ff47e3e7860f4c63be356fa7eec6be6587422fef1ec1e94f28b1be8d33c4d7dd'
COLUMNS = ('text_long', 'worry', 'anxiety', 'fear', 'relaxation', 'sadness')
NOTICE_PINS = {
    'README.md': '2fd310e4c1e0a6dc51617e032d906cbc03fa355030223698e8e391a535ba3b26',
    'LICENSE': '3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986',
    'OSF_NODE_METADATA.json': 'f1f3acb649cd71bedb5ceb848202925cf85871df542e11833259df963512e219',
    'OSF_LICENSE_METADATA.json': '8d71e017c62bb83ba853725a35cd04b7c9d74e48779c605ff8e1bdc186976e9b',
}
SEMANTIC = {'population': 'original first-wave 2500 source rows', 'text': 'long only',
            'sentence_rule': 'punctuation-followed-by-whitespace-or-linebreak-v1',
            'sample': 'lowest SHA256 RW1-marker|20261107|opaque-sentence-id; no outcome or marker filtering',
            'sample_size': 200, 'marker_revision': 0}
BOUNDARY = re.compile(r"[.!?]+[\"'\u201d\u2019\)\]]*(?=\s|$)|\r\n|[\r\n]")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def private_output(path):
    path = Path(path).resolve()
    repo = Path(__file__).resolve().parents[3]
    allowed = (repo / '.agent-state', repo / 'corpora/store/external',
               repo / 'results/phase_2_4_stage_15/raw')
    if not any(path.is_relative_to(root.resolve()) for root in allowed):
        raise ValueError('RW1 participant material requires an ignored local output root')
    return path


def load_source(inputs):
    if set(inputs) != {'source_file', 'notice_directory', 'identity_salt'}:
        raise ValueError('Exact local source, author notices and campaign salt required')
    path = Path(inputs['source_file'])
    if path.is_symlink() or not 0 < path.stat().st_size <= 8 * 1024**2:
        raise ValueError('Source symlink or byte bound refused')
    raw = path.read_bytes()
    blob = hashlib.sha1(('blob ' + str(len(raw)) + '\0').encode() + raw).hexdigest()
    source_hash = hashlib.sha256(raw).hexdigest()
    if blob != GIT_BLOB or source_hash != OSF_DECLARED_SHA256:
        raise ValueError('Pinned original author Git blob or SHA-256 differs')
    notices = Path(inputs['notice_directory'])
    for name, expected in NOTICE_PINS.items():
        item = notices / name
        if item.is_symlink() or io.sha(item) != expected:
            raise ValueError('Pinned author source/license notice differs')
    salt = Path(inputs['identity_salt']).read_bytes()
    if len(salt) < 32:
        raise ValueError('At least 32 campaign salt bytes required')
    header = next(csv.reader(streams.StringIO(raw.splitlines()[0].decode('utf-8-sig'))))
    if len(header) != len(set(header)) or not set(COLUMNS).issubset(header):
        raise ValueError('Original header is duplicated or lacks allowed fields')
    # usecols is fixed: extra fields are not imported into the data frame.
    table = pd.read_csv(streams.BytesIO(raw), usecols=list(COLUMNS), dtype=str,
                        keep_default_na=False, na_filter=False, encoding='utf-8-sig')
    if set(table.columns) != set(COLUMNS) or len(table) != 2500:
        raise ValueError('Original first-wave schema or source-row count differs')
    identity = {'source_url': SOURCE_URL, 'revision': REVISION, 'git_blob': blob,
                'source_sha256': source_hash, 'bytes': len(raw), 'notices': NOTICE_PINS,
                'matches_OSF_declared_sha256': source_hash == OSF_DECLARED_SHA256,
                'salt_sha256': hashlib.sha256(salt).hexdigest(),
                'module_sha256': io.sha(__file__), 'marker_sha256': io.sha(marker.__file__),
                'pandas_version': pd.__version__, 'imported_columns': list(COLUMNS)}
    return table, salt, identity


def sentence_spans(text):
    """Frozen transparent splitter; offsets select exact original Unicode text.

    Abbreviations can split at a period. No inferred abbreviation model, length
    filter, semantic selection or outcome-dependent repair enters this version.
    """
    if not isinstance(text, str):
        raise ValueError('Original long text must be a string')
    starts, last = [], 0
    for match in BOUNDARY.finditer(text):
        starts.append((last, match.end())); last = match.end()
    starts.append((last, len(text)))
    result = []
    for start, end in starts:
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        if end > start:
            result.append((start, end))
    return result


def person_record(values, ordinal, salt, source_hash):
    if set(values) != set(COLUMNS):
        raise ValueError('Projection received a nonallowlisted field')
    person = hmac.new(salt, f'RW1|{source_hash}|{ordinal}'.encode(), hashlib.sha256).hexdigest()
    text = values['text_long']
    if not isinstance(text, str):
        raise ValueError('Long text must retain its original string')
    ratings, reasons = {}, []
    for field in COLUMNS[1:]:
        value = str(values[field]).strip()
        if not value:
            ratings[field] = None; reasons.append('missing_' + field); continue
        try:
            number = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError('Non-numeric commissioned rating') from error
        if not math.isfinite(number) or not number.is_integer() or not 1 <= number <= 9:
            raise ValueError('Commissioned rating outside its original integer scale')
        ratings[field] = int(number)
    spans = sentence_spans(text)
    if not spans:
        reasons.append('empty_long_text')
    sentences = []
    for start, end in spans:
        key = hmac.new(salt, f'RW1-sentence|{person}|{start}|{end}'.encode(), hashlib.sha256).hexdigest()
        sentences.append({'id': key, 'start': start, 'end': end, 'text': text[start:end]})
    return {'person': person, 'source_row': ordinal, 'text_long': text, 'ratings': ratings,
            'sentences': sentences, 'dispositions': reasons}


def sample_sentences(records):
    candidates = [dict(sentence, person=row['person']) for row in records for sentence in row['sentences']]
    if len(candidates) < 200 or len({s['id'] for s in candidates}) != len(candidates):
        raise ValueError('Two hundred distinct source sentences required')
    candidates.sort(key=lambda s: (hashlib.sha256(('RW1-marker|20261107|' + s['id']).encode()).hexdigest(), s['id']))
    sample = candidates[:200]
    return sample, marker.manifest_digest(sample)


def annotation_form(sample, binding, kind):
    if kind not in ('hand', 'list'):
        raise ValueError('Hand or list form required')
    return {'kind': kind, 'builder_id': None, 'manifest_sha256': binding,
            'guidance': ('Judge whether the sentence expresses a first-person intention or planned action; '
                         'judge meaning without consulting automatic labels.' if kind == 'hand'
                         else 'Apply the pinned literal marker list only after sealing the hand form.'),
            'marker_version': marker.VERSION, 'marker_sha256': io.sha(marker.__file__),
            'revision': 0, 'independently_annotated': False, 'provenance_sha256': None,
            'hand_receipt_sha256': None, 'automatic_labels_seen_before_hand_seal': None,
            'annotations': [{'id': s['id'], 'text': s['text'], 'label': None} for s in sample]}


def bounded(output, began, seconds):
    return time.monotonic() - began >= seconds or any((p / 'YIELD_REQUEST.json').exists() for p in [output, *output.parents[:3]])


def prepare(output, inputs, config):
    if set(config) - {'phase', 'max_new_blocks', 'max_wall_seconds'} or config.get('phase') != 'RW1-source':
        raise ValueError('Exact RW1 source phase required')
    limit, seconds = config.get('max_new_blocks', 4), float(config.get('max_wall_seconds', 600))
    if type(limit) is not int or limit <= 0 or not math.isfinite(seconds) or not 0 < seconds <= 1200:
        raise ValueError('Positive bounded source quantum required')
    table, salt, identity = load_source(inputs)
    binding = digest({'identity': identity, 'semantic': SEMANTIC})
    state = seal.state(output / 'STATE.json', binding, {'blocks': []})
    blocks = (len(table) + 127) // 128
    if state['blocks'] != list(range(len(state['blocks']))) or len(state['blocks']) > blocks:
        raise ValueError('Source checkpoint order differs')
    began, added = time.monotonic(), 0
    for ordinal in range(blocks):
        path = output / 'people' / f'{ordinal:05d}.json'
        if ordinal < len(state['blocks']):
            seal.state(path, binding, {}); continue
        if added >= limit or bounded(output, began, seconds):
            return {'status': 'yielded', 'verified': False, 'phase': 'RW1-source',
                    'completed': ordinal, 'total': blocks}
        start = ordinal * 128
        rows = [person_record(row, start + i, salt, identity['source_sha256'])
                for i, row in enumerate(table.iloc[start:start + 128].to_dict('records'))]
        seal.checkpoint(path, {'binding': binding, 'ordinal': ordinal, 'records': rows})
        state['blocks'].append(ordinal); seal.checkpoint(output / 'STATE.json', state); added += 1
    records = []
    for ordinal in range(blocks):
        block = seal.state(output / 'people' / f'{ordinal:05d}.json', binding, {})
        if block['ordinal'] != ordinal:
            raise ValueError('Source block identity differs')
        records.extend(block['records'])
    if [r['source_row'] for r in records] != list(range(len(table))):
        raise ValueError('Every original person must survive projection')
    sample, sample_binding = sample_sentences(records)
    payloads = {'RECORDS.json': {'source_identity': identity, 'records': records},
                'SAMPLE.json': {'manifest_sha256': sample_binding, 'semantic': SEMANTIC, 'sentences': sample},
                'HAND_FORM.json': annotation_form(sample, sample_binding, 'hand'),
                'LIST_FORM.json': annotation_form(sample, sample_binding, 'list')}
    for name, value in payloads.items():
        seal.checkpoint(output / name, value)
    return {'card': 'RW1-source', 'record_kind': 'run', 'theory_tags': [], 'activation': [],
            'by_construction': False, 'complete_preparation': True, 'people': len(records),
            'source_sentences': sum(len(r['sentences']) for r in records), 'sample_sentences': 200,
            'source_identity': identity, 'sample_manifest_sha256': sample_binding,
            'files': {name: io.sha(output / name) for name in payloads},
            'independent_annotations_complete': False, 'production_admitted': False,
            'human_outcomes_computed': False}


def read_form(path, sample, binding, kind):
    path = Path(path)
    if path.is_symlink() or io.sha(path) != seal.read(path.with_suffix('.seal.json'))['sha256']:
        raise ValueError('Annotation file is not sealed')
    form = seal.read(path)
    if (form.get('kind') != kind or form.get('manifest_sha256') != binding
            or form.get('marker_sha256') != io.sha(marker.__file__)
            or form.get('marker_version') != marker.VERSION or form.get('revision') != 0):
        raise ValueError('Annotation source or marker pin differs')
    rows = form.get('annotations', [])
    if [(r.get('id'), r.get('text')) for r in rows] != [(s['id'], s['text']) for s in sample]:
        raise ValueError('Ordered annotation sentences differ')
    if any(type(r.get('label')) is not bool for r in rows):
        raise ValueError('Every sentence needs an actual boolean annotation')
    if not form.get('provenance_sha256') or form.get('independently_annotated') is not True:
        raise ValueError('Actual independent annotation provenance required')
    if kind == 'hand' and form.get('automatic_labels_seen_before_hand_seal') is not False:
        raise ValueError('Hand annotations must precede automatic list exposure')
    return form, io.sha(path)


def review_markers(inputs, config):
    expected = {'prepared_run', 'builder_a_hand', 'builder_a_list', 'builder_b_hand', 'builder_b_list'}
    if set(inputs) != expected or config != {'phase': 'RW1-marker-review'}:
        raise ValueError('Exact original source and two builders hand/list files required')
    root, _, _ = seal.complete(inputs['prepared_run'], MODULE)
    result = seal.read(root / 'output/RESULT.json')
    if result.get('complete_preparation') is not True or result.get('card') != 'RW1-source':
        raise ValueError('Complete RW1 source preparation required')
    if (result['source_identity']['marker_sha256'] != io.sha(marker.__file__)
            or result['source_identity']['module_sha256'] != io.sha(__file__)):
        raise ValueError('Source marker implementation changed')
    sample = seal.read(root / 'output/SAMPLE.json')['sentences']
    binding = marker.manifest_digest(sample)
    if binding != result['sample_manifest_sha256']:
        raise ValueError('Prepared sample differs')
    receipts, form_hashes = [], {}
    for prefix in ('builder_a', 'builder_b'):
        hand, hand_hash = read_form(inputs[prefix + '_hand'], sample, binding, 'hand')
        listed, list_hash = read_form(inputs[prefix + '_list'], sample, binding, 'list')
        if hand['builder_id'] != listed['builder_id'] or listed.get('hand_receipt_sha256') != hand_hash:
            raise ValueError('Each builder must bind the previously sealed hand form')
        form_hashes[prefix] = {'hand': hand_hash, 'list': list_hash}
        receipts.append({'builder_id': hand['builder_id'], 'manifest_sha256': binding,
            'marker_version': marker.VERSION, 'revision': 0, 'independently_annotated': True,
            'provenance_sha256': digest({'hand': hand['provenance_sha256'], 'list': listed['provenance_sha256'],
                                        'files': form_hashes[prefix]}),
            'annotations': [{'id': s['id'], 'by_hand': h['label'], 'by_list': l['label']}
                for s, h, l in zip(sample, hand['annotations'], listed['annotations'], strict=True)]})
    return {'card': 'RW1-marker-review', 'record_kind': 'run', 'theory_tags': [],
            'by_construction': False, 'activation': [], 'form_sha256': form_hashes,
            'prepared_complete_sha256': io.sha(root / 'COMPLETE.json'),
            **marker.qualification(sample, *receipts)}


def operation(output, inputs, config):
    output = private_output(output); output.mkdir(parents=True, exist_ok=True)
    began = time.process_time()
    result = review_markers(inputs, config) if config.get('phase') == 'RW1-marker-review' else prepare(output, inputs, config)
    if result.get('status') != 'yielded':
        io.write_json(output / 'RESULT.json', result)
    io.write_json(output / 'COST.json', {'process_CPU_seconds': time.process_time() - began,
                                       'scope': 'invocation only; native/source/replay accounting remains external'})
    return result


def execute(output, inputs, config):
    return operation(output, inputs, config)


def verify(output, inputs, config):
    output = private_output(output)
    result = operation(output / 'independent-replay', inputs, config)
    if result.get('status') == 'yielded':
        return result
    if seal.read(output / 'RESULT.json') != result:
        raise ValueError('Full source/marker receipt replay differs')
    return {'verified': True, 'complete_source_or_annotation_receipt_replay': True,
            'independence_still_requires_owner_provenance_review': True, 'human_outcomes_computed': False}
