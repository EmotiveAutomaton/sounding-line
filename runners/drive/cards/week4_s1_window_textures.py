"""Declared S1 five/twelve-word source variants, with no recurrence outcome.

DESIGN CHECK: LESSONS 2-5 and the original S1 construction reviewed November 2.
Under null and alternative, only length changes; future flags never select words.
Known exact windows, breaks, predecessor gaps and sentence-local grams retain
their answers. Unsupported lengths or altered outputs refuse. Descriptive only,
no parent-claim upgrade or descendants; full nuisance and effect work is separate.
"""
from pathlib import Path
from types import FunctionType
from . import week4_typed_windows as original
from .timing_p6 import write_equal
from .timing_census import read


def configuration(size, mode):
    if type(size) is not int or size not in (5, 12) or mode not in ('constructed', 'full'):
        raise ValueError('Only declared five/twelve-word scopes are allowed')
    return dict(original.CONFIG, card='S1-texture-window-'+str(size),
                window_words=size, mode=mode, descriptive=True, descendants=False)


def fixture(size):
    words = [dict(index=i, ordinal=2*i+1, completed_ordinal=2*i+2,
        is_word=True, token='the', previous_typed_token_index=i-1 if i else None,
        sentence_start=i % size == 0, length=3, seconds=float(i), revised=False)
        for i in range(9*size)]
    intervals = [dict(ordinal=w['ordinal'], onset=True, stop=i % size == 0,
        fast=.2 if i % size == 0 else .95-(i//size)*.1, interval_seconds=1.)
        for i, w in enumerate(words)]
    return words, intervals


def known(size):
    words, intervals = fixture(size)
    windows, counts = original.session_windows(dict(words=words), intervals, {'the'}, size)
    support = original.classify([dict(writer='fixture', windows=windows)])
    assert [w['indices'] for w in windows] == [list(range(i, i+size)) for i in range(0, 9*size, size)]
    assert support['fixture']['classes'] == {'flow': 3, 'middle': 3, 'hesitant': 3}
    assert all(len(w['grams']) == size-3 for w in windows)
    return dict(size=size, windows=windows, counts=counts, support=support,
                scientific_effect_computed=False)


def run(output, inputs, config, verification=False):
    if config != configuration(config['window_words'], config['mode']):
        raise ValueError('Frozen texture configuration required')
    if config['mode'] == 'constructed':
        if inputs:
            raise ValueError('No human input in constructed validation')
        value = known(config['window_words'])
        path = Path(output)/'SUMMARY.json'
        if verification:
            if read(path) != value:
                raise ValueError('Complete texture replay differs')
            return dict(verified=True, complete_source_replay=True)
        write_equal(path, value)
        return dict(status='complete', scientific_admission=False)
    implementation = FunctionType(original.run.__code__,
        dict(original.__dict__, CONFIG=config), 'run', original.run.__defaults__)
    return implementation(output, inputs, config, verification)


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, True)
