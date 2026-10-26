"""Complete Jester source/support census for commissioned CA5.r; no effect test.

DESIGN CHECK: LESSONS sections 3-5 reread 2026-10-26. Null and alternative
ratings have identical admission. Preserve every approved complete record,
signed values, exact zeros and missingness. Authenticate predecessor outputs
and inputs; reject gaps, duplicate chunks, altered receipts and invalid values.
Both-half availability is reported, never used to drop people. Fresh verification
rebuilds every aggregate from the full original chunk inventory. No demographic,
harm-category or independent-quality information is invented; no claim licensed.
"""
from pathlib import Path
import json
import hashlib
import numpy as np
from .timing_census import read, filehash
from .timing_p6 import write_equal


INPUTS = {'source_complete', 'source_plan', 'jester_texts'}
CARD = 'CA5.r-input-support'


def checked_path(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or path == root.resolve():
        raise ValueError('source path escapes root')
    return path


def census(inputs, config):
    if set(inputs) != INPUTS or set(config) != {'mode', 'expected_rows'}:
        raise ValueError('exact support inputs/config required')
    if config['mode'] not in {'corpus', 'constructed'} or type(config['expected_rows']) is not int or config['expected_rows'] < 1:
        raise ValueError('invalid source mode/count')
    if config['mode'] == 'corpus' and config['expected_rows'] != 50691:
        raise ValueError('whole approved population required')
    root = Path(inputs['source_complete']).resolve().parent
    if Path(inputs['source_plan']).resolve() != root/'PLAN.json':
        raise ValueError('mixed predecessor roots')
    complete, plan = read(inputs['source_complete']), read(inputs['source_plan'])
    if (complete.get('status') != 'COMPLETE' or complete.get('fresh_process_verified') is not True
            or complete.get('card') != 'Jester2plus-complete-records'
            or plan.get('module') != 'runners.drive.cards.timing_jester_complete_records'
            or plan.get('config') != dict(card='Jester2plus-complete-records', rows_per_chunk=1024)):
        raise ValueError('unadmitted predecessor')
    if Path(plan['inputs']['jester_texts']).resolve() != Path(inputs['jester_texts']).resolve():
        raise ValueError('different text source')
    bindings = {str(Path(p).resolve()): h for p, h in plan['pins'].items()}
    for p, h in bindings.items():
        if filehash(p) != h:
            raise ValueError('changed predecessor input')
    if bindings.get(str(Path(inputs['jester_texts']).resolve())) != filehash(inputs['jester_texts']):
        raise ValueError('unpinned texts')
    for rel, h in complete['outputs'].items():
        p = checked_path(root, rel)
        if filehash(p) != h:
            raise ValueError('changed predecessor output')
        bindings[str(p)] = h
    out = root/'output'
    def admitted(rel):
        p = checked_path(out, rel)
        if complete['outputs'].get(p.relative_to(root).as_posix()) != filehash(p):
            raise ValueError('unsealed source artifact')
        return p
    ix = read(admitted('RATINGS_INDEX.json'))
    if {k: ix.get(k) for k in ('schema', 'dtype', 'missing', 'joke_ids', 'rows')} != dict(
            schema=1, dtype='float64', missing='NaN', joke_ids=list(range(1, 151)), rows=config['expected_rows']):
        raise ValueError('source dimensions/semantics differ')
    texts = read(inputs['jester_texts'])
    if (not isinstance(texts, list) or len(texts) != 150
            or sorted(x['joke_id'] for x in texts) != list(range(1, 151))
            or any(not isinstance(x['text'], str) or not x['text'].strip() for x in texts)):
        raise ValueError('complete unique joke texts required')
    quarantine = read(admitted('QUARANTINE.json'))
    if quarantine.get('numeric_cells') != 123 or quarantine.get('blank_cells') != 28:
        raise ValueError('original partial-record gap missing')
    observed = np.zeros(150, dtype=np.int64)
    row_hist = np.zeros(151, dtype=np.int64)
    half_hist = np.zeros((76, 76), dtype=np.int64)
    signed = dict(negative=0, zero=0, positive=0, missing=0)
    offset = 0
    seen = set()
    values_hash = hashlib.sha256()
    for number, unit in enumerate(ix['chunks']):
        if (unit['file'] in seen or unit['rater_offset'] != offset or unit['rows'] <= 0
                or unit['file'] != f'chunks/{number:04}.npy'
                or unit['receipt'] != f'chunks/{number:04}.json'):
            raise ValueError('nonconsecutive/duplicate source chunk')
        seen.add(unit['file'])
        path = admitted(unit['file']); receipt = read(admitted(unit['receipt']))
        expected_unit = {k: v for k, v in unit.items() if k not in {'file', 'receipt'}}
        if (receipt['sha256'] != filehash(path) or receipt['unit'] != expected_unit
                or receipt['input_binding_sha256'] != filehash(admitted('INPUT_BINDING.json'))):
            raise ValueError('chunk receipt mismatch')
        a = np.load(path, allow_pickle=False)
        if a.dtype != np.dtype('float64') or a.shape != (unit['rows'], 150):
            raise ValueError('invalid array dimensions/type')
        finite = np.isfinite(a)
        if np.isinf(a).any() or np.any(np.abs(a[finite]) > 10):
            raise ValueError('invalid rating or unconverted sentinel')
        observed += finite.sum(0)
        row_hist += np.bincount(finite.sum(1), minlength=151)
        left, right = finite[:, ::2].sum(1), finite[:, 1::2].sum(1)
        np.add.at(half_hist, (left, right), 1)
        for key, mask in [('negative', a < 0), ('zero', a == 0), ('positive', a > 0), ('missing', ~finite)]:
            signed[key] += int(mask.sum())
        values_hash.update(path.read_bytes())
        offset += len(a)
    if offset != ix['rows'] or set(p.relative_to(out).as_posix() for p in (out/'chunks').glob('*.npy')) != seen:
        raise ValueError('incomplete/extraneous source inventory')
    if config['mode'] == 'corpus' and (row_hist[0] or np.count_nonzero(observed) != 140):
        raise ValueError('approved corpus support identity differs')
    summary = dict(card=CARD, mode=config['mode'], population_records=offset, original_partial_records=1,
        joke_texts=150, observed_items=int(np.count_nonzero(observed)), per_item_observed=observed.tolist(),
        ratings_per_record_histogram=row_hist.tolist(), odd_even_observed_count_histogram=half_hist.tolist(),
        records_with_both_item_halves=int(half_hist[1:, 1:].sum()), signed_value_counts=signed,
        source_values_sha256=values_hash.hexdigest(), all_rows_retained=True, imputed_values=0,
        demographics_available=False, harm_categories_available=False,
        original_full_population_gap_retained=True, scientific_admission=False,
        scope='Input support only. Split is numeric item identity, not chronological order. No feature selection or recurrence statistic.')
    bindings.update({str(Path(p).resolve()): filehash(p) for p in inputs.values()})
    return summary, bindings


def execute(output, inputs, config):
    summary, bindings = census(inputs, config)
    write_equal(Path(output)/'SOURCE_SUPPORT.json', summary)
    write_equal(Path(output)/'SOURCE_BINDINGS.json', bindings)
    return dict(card=CARD, population_records=summary['population_records'], scientific_admission=False)


def verify(output, inputs, config):
    summary, bindings = census(inputs, config)
    if summary != read(Path(output)/'SOURCE_SUPPORT.json') or bindings != read(Path(output)/'SOURCE_BINDINGS.json'):
        raise ValueError('fresh complete source census differs')
    return dict(verified=True, complete_source_replay=True, population_records=summary['population_records'], scientific_admission=False)
