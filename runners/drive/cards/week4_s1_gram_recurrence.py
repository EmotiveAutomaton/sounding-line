"""Three-word S1 texture recurrence, preserving the original estimator.

DESIGN CHECK: LESSONS 3-5 and Week4 S1/G read 2026-11-02. NULL: identical
own/donor memberships give zero; ALTERNATIVE: own-only and donor-only templates
give opposite signed recurrence. Mixed lengths refuse instead of yielding a
false null. Known-answer source joins, repeated occurrences, sentence boundaries
and the original positive/null/reversed/nuisance/unidentifiable bank precede
human scoring. Original support, resampling and nuisance rules are unchanged.
"""
import hashlib
import json
import time
from functools import partial
from pathlib import Path
from types import FunctionType, SimpleNamespace

from threadpoolctl import threadpool_limits
from . import week4_s1_recurrence as original
from . import week4_s1_stats as stats
from .timing_census import filehash, read
from .timing_p6 import gzip_equal, gzread, write_equal
from .timing_pmap_source import completed


def configuration(mode):
    if mode not in ('constructed', 'full'):
        raise ValueError('Unknown three-word recurrence mode')
    return dict(card='S1-texture-gram-3-recurrence', mode=mode, seed=20261102,
                gram_words=3, descriptive=True, descendants=False)


def checked_recurrence(grams, own, donor):
    if any(len(g) != 3 for collection in (grams, own, donor) for g in collection):
        raise ValueError('Matching three-word target and history templates required')
    return stats.recurrence(grams, own, donor)


def rows_from_sources(output, inputs, verification):
    if set(inputs) != {'nuisance_completion'}:
        raise ValueError('Exact completed controls required')
    nc = Path(inputs['nuisance_completion'])
    hc = Path(read(nc.parent / 'PLAN.json')['inputs']['histories_completion'])
    wc = Path(read(hc.parent / 'PLAN.json')['inputs']['windows_completion'])
    if read(wc.parent / 'PLAN.json')['config'].get('gram_words') != 3:
        raise ValueError('Frozen source must use three-word templates')
    windows = wc.parent / 'output/WINDOWS.json.gz'
    completed(wc, windows)
    for session in gzread(windows):
        if any(len(g) != 3 for w in session['windows'] for g in w['grams']):
            raise ValueError('Source target template length differs')
    matched_stats = SimpleNamespace(**dict(vars(stats),
        history_grams=partial(stats.history_grams, n=3), recurrence=checked_recurrence))
    namespace = dict(vars(original), stats=matched_stats)
    consumer = FunctionType(original.rows_from_sources.__code__, namespace,
                            'rows_from_sources', original.rows_from_sources.__defaults__)
    return consumer(output, inputs, verification)


def constructed_sources(output):
    """Synthetic authenticated source chain, never a research completion receipt."""
    root = Path(output) / 'constructed_sources'
    p6, windows, histories, controls = (root / n for n in ('p6', 'windows', 'histories', 'controls'))
    records = []
    for i in range(1399):
        record = dict(session=f's{i}', writer='w0' if i < 2 else f'w{i}',
                      timestamp=i + 2, end_at=i + 2.5, prompt='synthetic', training_sequences=[])
        if i == 0:
            record['training_sequences'] = [['a', 'one', 'two'], ['the', 'three', 'four']]
        records.append(record)
    index = []
    for record in records:
        path = p6 / (record['session'] + '.json')
        write_equal(path, record)
        index.append(dict(file=path.name, sha256=filehash(path)))
    write_equal(p6 / 'INDEX.json', index)
    # Each score has an independently enumerated membership answer. A repeated
    # target occurrence changes weighting; histories remain presence sets.
    a = ['a', '<content>', '<content>']
    b = ['and', '<content>', '<content>']
    shared = ['the', '<content>', '<content>']
    target = [dict(start_ordinal=i, **{'class': 'flow' if i % 2 else 'hesitant'}, grams=g)
              for i, g in enumerate(([a], [b], [a, a, b], [shared]))]
    ledger = [dict(session=r['session'], writer=r['writer'], genre='creative',
                   windows=target if r['session'] == 's1' else []) for r in records]
    gzip_equal(windows / 'output/WINDOWS.json.gz', ledger)
    write_equal(windows / 'output/FROZEN_DICTIONARY.json', dict(words=['a', 'and', 'the']))
    write_equal(windows / 'PLAN.json', dict(config=dict(gram_words=3)))
    leaf = hashlib.sha256(b's1').hexdigest() + '.json.gz'
    gzip_equal(histories / 'output/sessions' / leaf,
               dict(proof=dict(supported=True, own_sessions=['s0']),
                    donor=[dict(training_sequences=[['and', 'five', 'six'], ['the', 'seven', 'eight']])]))
    write_equal(histories / 'PLAN.json', dict(inputs=dict(
        windows_completion=str(windows / 'COMPLETE.json'),
        p6_index=str(p6 / 'INDEX.json'), p6_completion=str(p6 / 'COMPLETE.json'))))
    gzip_equal(controls / 'output/sessions' / leaf, dict(writer='w0', rows=[
        dict(start_ordinal=i, nuisance=[float(i), 0.0]) for i in range(4)]))
    write_equal(controls / 'output/SUMMARY.json', dict(mode='full', supported_writers=1))
    write_equal(controls / 'PLAN.json', dict(inputs=dict(histories_completion=str(histories / 'COMPLETE.json'))))
    for folder in (p6, windows, histories, controls):
        files = {p.relative_to(folder).as_posix(): filehash(p) for p in sorted(folder.rglob('*'))
                 if p.is_file() and p.name != 'COMPLETE.json'}
        write_equal(folder / 'COMPLETE.json', dict(status='COMPLETE', fresh_process_verified=True,
                    constructed_fixture_only=True, outputs=files))
    return dict(nuisance_completion=str(controls / 'COMPLETE.json'))


def run(output, inputs, config, verification=False):
    if config != configuration(config['mode']):
        raise ValueError('Frozen three-word recurrence configuration required')
    if config['mode'] == 'full':
        namespace = dict(vars(original), configuration=configuration, rows_from_sources=rows_from_sources)
        consumer = FunctionType(original.run.__code__, namespace, 'run', original.run.__defaults__)
        return consumer(output, inputs, config, verification)
    if inputs:
        raise ValueError('No human input in constructed validation')
    start = time.process_time()
    with threadpool_limits(limits=1):
        checks = stats.known_checks()
        d = {'a', 'the'}
        assert stats.history_grams([['a', 'b', '.', 'the', 'c', 'd'], ['a', 'e']], d, n=3) == {
            ('the', '<content>', '<content>')}
        assert not stats.history_grams([['b', 'c', 'd']], d, n=3)
        source_inputs = constructed_sources(output)
        rows, census, bindings = rows_from_sources(Path(output) / 'known_source', source_inputs, verification)
        if [r['outcome'] for r in rows] != [1.0, -1.0, 1 / 3, 0.0]:
            raise ValueError('Known complete source recurrence differs')
        checks.update(three_word_source_join=True, repeated_target_occurrences=True,
                      own_and_donor_membership=True, identical_membership_zero=True,
                      source_and_sentence_boundaries=True, all_placeholder_exclusion=True)
        value = dict(known_checks=checks, source_census=census, source_bindings=bindings,
                     gram_words=3, scientific_effect_computed=False, constructed_only=True)
        dest = Path(output) / 'SUMMARY.json'
        if verification:
            if read(dest) != json.loads(json.dumps(value)):
                raise ValueError('Complete constructed recurrence replay differs')
        else:
            write_equal(dest, value)
    if not verification:
        write_equal(Path(output) / 'TIMING.json', dict(cpu_seconds=time.process_time() - start))
    return (dict(verified=True, complete_source_replay=True, complete_statistical_replay=True)
            if verification else dict(status='complete', scientific_admission=False))


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, True)
