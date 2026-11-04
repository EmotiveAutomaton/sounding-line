"""Declared S1 three/five-word skeleton templates; source preparation only.

DESIGN CHECK: LESSONS2-5 and Week4 S1/G read 2026-11-02. NULL and ALTERNATIVE
retain source boundaries, dictionary ranking, timing and window membership.
An independent enumerated known source checks every gram and multiplicity;
wrong length, cross-sentence grams or source/output mismatch refuse admission.
This module computes no recurrence effect and cannot license a claim.
"""
from pathlib import Path
from functools import partial
from types import FunctionType
from . import week4_typed_windows as original
from .week4_s1_dictionary_textures import fixture_inputs
from .timing_p6 import gzread
from .timing_census import read


def configuration(size, mode):
    if type(size) is not int or size not in (3, 5) or mode not in ('constructed', 'full'):
        raise ValueError('Only declared three/five-word skeleton templates')
    return dict(original.CONFIG, card=f'S1-texture-gram-{size}', gram_words=size,
                expected_sessions=1 if mode == 'constructed' else 1399,
                mode=mode, descriptive=True, descendants=False)


def window_implementation(size):
    configuration(size, 'constructed')
    namespace = dict(original.__dict__, skeleton_grams=partial(original.skeleton_grams, n=size))
    return FunctionType(original.session_windows.__code__, namespace, 'session_windows',
                        original.session_windows.__defaults__)


def run(output, inputs, config, verification=False):
    if config != configuration(config['gram_words'], config['mode']):
        raise ValueError('Frozen gram variant required')
    if config['mode'] == 'constructed':
        if inputs:
            raise ValueError('No human input in known source')
        inputs = fixture_inputs(output)
    namespace = dict(original.__dict__, CONFIG=config,
                     session_windows=window_implementation(config['gram_words']))
    implementation = FunctionType(original.run.__code__, namespace, 'run', original.run.__defaults__)
    result = implementation(output, inputs, config, verification)
    if config['mode'] == 'constructed':
        dictionary = read(Path(output) / 'FROZEN_DICTIONARY.json')['words']
        if dictionary != [f'w{i:03d}' for i in range(150)]:
            raise ValueError('Original dictionary changed')
        sessions = gzread(Path(output) / 'WINDOWS.json.gz')
        if len(sessions) != 1 or len(sessions[0]['windows']) != 50:
            raise ValueError('Original window membership changed')
        width = config['gram_words']
        for j, window in enumerate(sessions[0]['windows']):
            expected = []
            for start in range(8 - width + 1):
                indices = list(range(j * 8 + start, j * 8 + start + width))
                if min(indices) < 150:
                    expected.append([f'w{i:03d}' if i < 150 else '<content>' for i in indices])
            if window['grams'] != expected:
                raise ValueError('Known gram sequence or multiplicity differs')
    return result


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, True)
