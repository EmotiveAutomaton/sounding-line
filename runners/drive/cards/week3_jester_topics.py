"""Text-only feature freeze for CA5.r; this worker has no ratings input.

DESIGN CHECK: LESSONS 3-5, CONTROLS 1-7. Reordering identical text rows must
not change features. Missing, duplicate, changed text and non-convergence fail.
This is representation preparation, not an empirical preference result.
"""
from pathlib import Path
from .timing_census import read, filehash
from .timing_p6 import write_equal
from .week3_jester_preference import text_features


def build(inputs, config):
    if set(inputs) != {'jester_texts'} or set(config) != {'source_sha256'}:
        raise ValueError('text-only inputs required')
    if filehash(inputs['jester_texts']) != config['source_sha256']:
        raise ValueError('text source changed')
    return dict(source_sha256=config['source_sha256'], **text_features(read(inputs['jester_texts'])))


def execute(output, inputs, config):
    result = build(inputs, config)
    write_equal(Path(output)/'TOPICS.json', result)
    return dict(texts=150, topics=8, scientific_admission=False, ratings_read=False)


def verify(output, inputs, config):
    if build(inputs, config) != read(Path(output)/'TOPICS.json'):
        raise ValueError('fresh complete feature replay differs')
    return dict(verified=True, complete_feature_replay=True, scientific_admission=False, ratings_read=False)
