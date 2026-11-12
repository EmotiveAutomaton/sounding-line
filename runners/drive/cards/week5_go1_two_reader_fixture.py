"""Constructed R4 comparison and actual producer/collector boundary fixture.

No corpus or language model is read. A deterministic constructed encoder stand-in
exercises the unchanged vector cache; existing encoder qualification remains a
separate requirement. Signed/null cases run all 2,000 paired author resamples.
"""
from pathlib import Path
import json
import re
import numpy as np
from . import week5_go1_two_reader as go


def rows():
    return [dict(repository='eips', type='Standards Track', category='Core',
                 document=f'constructed-{i}', author=f'author-{i}',
                 motivation=f'goal unique{i}', rest=f'body unique{i}') for i in range(60)]


def scores(roster, correct):
    value = np.zeros((len(roster), len(roster[0]['candidates'])))
    for i, row in enumerate(roster):
        truth = row['truth_position']
        value[i, truth if correct[i] else (truth + 1) % len(row['candidates'])] = 1.
    return value


def vectors(texts, manifest, cache=None, on_vector=None):
    if json.loads(Path(manifest).read_text('utf8')) != {'constructed_only': True}:
        raise ValueError('Constructed encoder manifest required')
    cache = {} if cache is None else dict(cache)
    for text in dict.fromkeys(texts):
        if text in cache:
            continue
        vector = np.zeros(384, dtype=np.float32)
        vector[int(re.search(r'unique(\d+)', text)[1])] = 1.
        cache[text] = vector
        if on_vector:
            on_vector(text, vector)
    return np.asarray([cache[text] for text in texts])


def seal_stage(root, reader):
    root = Path(root)
    go.io.write_json(root / 'PLAN.json', {'module': go.MODULE, 'config': {'phase': 'GO1-score', 'reader': reader}})
    go.io.write_json(root / 'VERIFIED.json', {'verified': True, 'constructed_fixture_internal': True})
    go.io.write_json(root / 'COMPLETE.json', {'status': 'COMPLETE', 'fresh_process_verified': True,
        'constructed_fixture_internal': True,
        'outputs': {p.relative_to(root).as_posix(): go.io.sha(p) for p in (root / 'output').rglob('*') if p.is_file()}})


def arithmetic():
    source = rows()
    allocation = go.core.allocate(source)
    low = np.arange(60) < 10
    high = np.arange(60) < 50
    cases = {}
    for label, a, b, expected in [('positive', low, high, 'supports'),
                                   ('negative', high, low, 'against'), ('exact-null', low, low, 'against')]:
        result, samples = go.compare(source, allocation, {'tfidf': scores(allocation, a), 'encoder': scores(allocation, b)}, 2000)
        if result['outcome'] != expected or len(samples) != 2000:
            raise AssertionError('Signed/exact-null full uncertainty gate failed')
        if label == 'exact-null' and (result['primary']['estimate'] != 0 or np.any(samples != 0)):
            raise AssertionError('Identical reader banks must produce exact zero')
        if result['primary']['sees'] != 2.8 * float(np.std(samples, ddof=1)):
            raise AssertionError('Amendment P must use the actual bootstrap SE')
        cases[label] = {'outcome': result['outcome'], 'draws': len(samples)}
    return cases


def execute(output, inputs, config):
    if inputs or config:
        raise ValueError('Only the complete constructed fixture is allowed')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    source = rows()
    documents = output / 'documents.json'
    manifest = output / 'encoder.json'
    go.io.write_json(documents, {'documents': source})
    go.io.write_json(manifest, {'constructed_only': True})
    args = {'documents': str(documents), 'encoder_manifest': str(manifest)}
    prepared = go.execute(output / 'preparation', args, {'phase': 'GO1-prepare'})
    if prepared['unique_encoder_texts'] != 120 or prepared['first_five_percent_texts'] != 6:
        raise AssertionError('Exact original encoder-work census differs')
    if go.verify(output / 'preparation', args, {'phase': 'GO1-prepare'}).get('verified') is not True:
        raise AssertionError('Source-only work census replay failed')
    original_embedding = go.original.readers.embeddings
    original_selected = go.original.reader_binding
    def no_selected_reader(*unused):
        raise AssertionError('R4 primary reached the forbidden AT2 dependency')
    go.original.readers.embeddings = vectors
    go.original.reader_binding = no_selected_reader
    try:
        allocation = go.core.allocate(source)
        for reader in ('tfidf', 'encoder'):
            root = output / reader
            cfg = {'phase': 'GO1-score', 'reader': reader, 'distractors': 49}
            if reader == 'encoder':
                partial = go.execute(root / 'output', args, {**cfg, 'max_new_texts': 1})
                if partial.get('status') != 'yielded':
                    raise AssertionError('Encoder prefix did not preserve its boundary')
            go.execute(root / 'output', args, cfg)
            if go.verify(root / 'output', args, cfg).get('verified') is not True:
                raise AssertionError('Full score replay failed')
            if json.loads((root / 'output/ALLOCATION.json').read_text('utf8'))['allocation'] != allocation:
                raise AssertionError('R4 changed the original roster/distractors')
            seal_stage(root, reader)
        args['readers'] = {name: str(output / name / 'output') for name in ('tfidf', 'encoder')}
        cfg = {'phase': 'GO1-collect', 'draws': 2000, 'distractors': 49}
        result = go.execute(output / 'collection', args, cfg)
        if not result['primary_ready'] or result['support_readers'] != ['encoder', 'tfidf']:
            raise AssertionError('Two-reader primary did not become complete')
        if go.verify(output / 'collection', args, cfg).get('verified') is not True:
            raise AssertionError('All primary draws failed to replay')
    finally:
        go.original.readers.embeddings = original_embedding
        go.original.reader_binding = original_selected
    report = {'constructed_only': True, 'actual_score_collect_verify_routes': True,
              'same_original_roster_distractors_authors': True, 'no_AT2_dependency': True,
              'encoder_pause_resume_and_full_replay': True, 'full_2000_draws_replayed': True,
              'cases': arithmetic(), 'actual_pretrained_encoder_run': False,
              'scope': 'R4 interface and statistic qualification; original encoder qualification remains required'}
    go.io.write_json(output / 'FIXTURE.json', report)
    return report


def verify(output, inputs, config):
    output = Path(output)
    actual = execute(output / 'independent-replay', inputs, config)
    if actual != json.loads((output / 'FIXTURE.json').read_text('utf8')):
        raise ValueError('Constructed R4 fixture independent replay differs')
    return {'verified': True, 'complete_constructed_R4_replay': True}
