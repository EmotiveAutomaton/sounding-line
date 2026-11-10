"""Prepared counted real-encoder check of the constructed Wikipedia boundary."""
from pathlib import Path
import numpy as np
from . import week5_bk_t2_wiki_features as feature
from .week5_bk_t2_features import dictionary, lexical
from .week5_go_readers import embeddings
from .timing_p6 import gzip_equal, gzread, write_equal
from .timing_census import filehash, read


def run(output, inputs, config, verification=False):
    if config != dict(constructed_fixture=True) or set(inputs) != {'dictionary_completion', 'encoder_manifest'}:
        raise ValueError('Only the constructed feature boundary is executable here')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    words, word_hash = dictionary(inputs['dictionary_completion'])
    a, removed = feature.units(0, 'An ordinary first sentence. A [[Target|revised]] final sentence.<ref>Removed source.</ref>')
    b, _ = feature.units(1, 'An ordinary first sentence. A revised final sentence.')
    rows = a+b
    if len(a) != 2 or [r['text'] for r in a] != [r['text'] for r in b] or removed.get('dropped_ref') != 1:
        raise ValueError('Constructed prose equivalence failed before encoding')
    def check(text, vector):
        if (output/'YIELD_REQUEST.json').exists():
            raise InterruptedError('Owner feature-fixture request')
    try:
        result = feature.encode(rows, words, inputs['encoder_manifest'], check)
        # The independent direct path must execute every actual encoder forward.
        direct = embeddings([r['text'] for r in rows], inputs['encoder_manifest'], on_vector=check)
    except InterruptedError:
        return dict(status='yielded', reason='restart complete short constructed encoder fixture in fresh output')
    for row, got, vector in zip(rows, result, direct):
        baseline, full = lexical(row['text'], row['position'], words)
        if baseline != got['baseline'] or not np.allclose(full+vector.tolist(), got['features'], atol=1e-7, rtol=0):
            raise ValueError('Feature bridge differs from original CoAuthor lexical/encoder path')
    poisoned = dict(rows[0], outcome=1, edit_count=10, writer='constructed metadata')
    try:feature.validate([poisoned])
    except ValueError:pass
    else:raise AssertionError('Outcome/history metadata crossed feature boundary')
    summary = dict(constructed=True, rows=len(rows), unique_texts=len({r['text'] for r in rows}),
                   actual_encoder_forwards=True, original_feature_equivalence=True,
                   outcome_metadata_refused=True, human_execution=False,
                   dictionary_sha256=word_hash, encoder_manifest_sha256=filehash(inputs['encoder_manifest']),
                   dimensions=len(result[0]['features']))
    if verification:
        old = gzread(output/'PRIVATE_CONSTRUCTED_FEATURES.json.gz')
        if summary != read(output/'FIXTURE.json') or len(old) != len(result):
            raise ValueError('Complete feature-boundary replay coverage differs')
        for x, y in zip(old, result):
            if ({k:v for k,v in x.items() if k != 'features'} != {k:v for k,v in y.items() if k != 'features'}
                    or not np.allclose(x['features'], y['features'], atol=1e-7, rtol=0)):
                raise ValueError('Fresh constructed encoder replay differs')
        return dict(verified=True, all_encoder_forwards_recomputed=True)
    gzip_equal(output/'PRIVATE_CONSTRUCTED_FEATURES.json.gz', result)
    write_equal(output/'FIXTURE.json', summary)
    return dict(status='complete')


def execute(output, inputs, config):return run(output, inputs, config)
def verify(output, inputs, config):return run(output, inputs, config, True)
