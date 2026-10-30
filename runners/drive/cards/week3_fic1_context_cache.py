"""FIC1.h1: bounded memoization of the original context arithmetic.

DESIGN CHECK: LESSONS 3-5, CONTROLS 1-7 reread 2026-10-29.
NULL and ALTERNATIVE: complete canonical JSON must exactly equal the original
on both prompt-only and planted worlds. Any difference or omitted unsupported
value fails parity. No scientific scoring, gate change or human admission.
"""
from collections import Counter, OrderedDict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time

from threadpoolctl import threadpool_limits
from runners.stage14.common import read, freeze, filehash
from . import week3_fic1_context as original
from . import week3_fic1_consumer as consumer

CONFIG = dict(card='FIC1.h1-context-cache-native', schema=1, mode='constructed',
              draws=32, cache_entries=128, seed=20261026)
FIXTURE = dict(constructed=True, worlds=['prompt_only', 'writer_plant'])


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf8')


class ContextCache:
    """Instance-owned snapshot; no cache survives a different input/config."""
    def __init__(self, data, config, cache_entries=128):
        if type(cache_entries) is not int or not 1 <= cache_entries <= 128:
            raise ValueError('cache capacity must be an integer from 1 to 128')
        self._data = deepcopy(data)
        self._config = deepcopy(config)
        self._capacity = cache_entries
        self._cache = OrderedDict()
        self.hits = self.misses = 0
        self._units = {u['session']:u for u in self._data['units']}
        self._rows = {r['session']:r for r in self._data['rows']}
        if len(self._units) != len(data['units']) or len(self._rows) != len(data['rows']):
            raise ValueError('duplicate source session')
        self._folds = original.writer_folds(self._data['units'], config['seed'])
        observed = original.reconstruction.rebuild(self._data['units'], self._data['rows'],
                        self._data['dictionary'], config['word_limits'])
        self._rosters = original.support(observed['profiles'],
                                        [str(n) for n in config['word_limits']]+['full'])

    def _measure(self, sessions, final, quota):
        key = (tuple(sorted(sessions)), final, quota)
        if key in self._cache:
            self.hits += 1
            self._cache.move_to_end(key)
            return self._cache[key]
        self.misses += 1
        value = original.mean_measure([self._units[s] for s in key[0]], self._rows, final, quota)
        self._cache[key] = value
        if len(self._cache) > self._capacity:
            self._cache.popitem(last=False)
        return value

    def _profiles(self, rebuilt, donors=None):
        units, rows = self._units, self._rows
        labels = rebuilt['labels']; dictionary = self._data['dictionary']
        cache = {}; out = []
        if donors is not None and not set(donors) <= set(labels.values()):
            raise ValueError('unknown donor writer')
        for profile in rebuilt['profiles']:
            if donors is not None and profile['writer'] in donors:
                continue
            p = deepcopy(profile)
            if p['state'] != 'prepared':
                out.append(p); continue
            allowed = set(labels.values())-{p['writer']} if donors is None else set(donors)
            def measure(sid, final=False, quota=None):
                target = units[sid]
                key = (target['genre'], target['prompt'], tuple(sorted(allowed)), final, quota)
                if key not in cache:
                    sessions = [u['session'] for u in units.values()
                                if (u['genre'], u['prompt']) == key[:2] and labels[u['session']] in allowed]
                    cache[key] = self._measure(sessions, final, quota)
                return cache[key]
            for level in p['levels'].values():
                if level['state'] != 'prepared':
                    continue
                value = original.pool([(measure(m['session'], quota=None if m['whole_session']
                                              else m['typed_words']), m['typed_words'])
                                       for m in level['members']], dictionary)
                level['features'] = value
                if value is None:
                    level.update(state='unsupported', reason='missing complete context donor prompt')
            parts = [(measure(s, True), rows[s]['final_words']) for s in p['sessions']]
            final = original.pool(parts, dictionary) if all(n > 0 for _, n in parts) else None
            p['final']['features'] = final['style'] if final else [None]*(len(dictionary['words'])+len(dictionary['punctuation']))
            p['context_rule'] = 'equal-session sufficient measure per word; pooled before rates and medians'
            out.append(p)
        return out

    def prepare(self, labels=None):
        data, config = self._data, self._config
        units = data['units']; folds = self._folds
        labels = labels or {u['session']:u['writer'] for u in units}
        if set(labels) != set(self._units):
            raise ValueError('assignment population differs')
        if any(labels[u['session']] not in folds or folds[labels[u['session']]] != folds[u['writer']] for u in units):
            raise ValueError('assignment crosses frozen writer roles')
        rebuilt = original.reconstruction.rebuild(units, data['rows'], data['dictionary'], config['word_limits'], labels)
        rosters = self._rosters
        literal = self._profiles(rebuilt); rotations = []
        for f in range(3):
            donors = sorted(w for w in folds if folds[w] == f)
            rr = {name:[w for w in roster if folds[w] != f] for name, roster in rosters.items()}
            probes = {name:[w for w in roster if folds[w] == (f+1)%3] for name, roster in rosters.items()}
            actual = [p for p in rebuilt['profiles'] if p['writer'] not in donors]
            context = self._profiles(rebuilt, set(donors))
            rotations.append(dict(donor_fold=f, donors=donors, probes=probes, galleries=rr,
                observed=original.matrices(actual, rr), context=original.matrices(context, rr), context_profiles=context))
        for name, roster in rosters.items():
            if Counter(w for r in rotations for w in r['probes'][name]) != Counter(roster):
                raise ValueError('probe coverage differs')
        return dict(rosters=deepcopy(rosters), writer_folds=dict(folds), rotations=rotations,
                    literal_leave_writer_out=original.matrices(literal, rosters), literal_licenses_claim=False,
                    identification_computed=False, full_calibration_complete=False, scientific_admission=False)


def compare_world(kind, draws=32):
    data = consumer.world(kind); config = consumer.CONFIG
    t = time.process_time(); cached = ContextCache(data, config)
    build = time.process_time()-t
    sequence = [None] + list(range(draws)) + [0, None]
    receipts = []; timings = dict(build=build, original=0., cached=0.)
    for index in sequence:
        labels = (original.role_assignment(data['units'], cached._folds, index, config['seed'])
                  if index is not None else None)
        t = time.process_time(); expected = original.prepare(data, config, labels)
        timings['original'] += time.process_time()-t
        t = time.process_time(); actual = cached.prepare(labels)
        timings['cached'] += time.process_time()-t
        a, b = canonical(expected), canonical(actual)
        if a != b:
            raise ValueError('complete cached context differs from original')
        receipts.append(dict(draw=index, original_sha256=hashlib.sha256(a).hexdigest(),
                             cached_sha256=hashlib.sha256(b).hexdigest()))
    return dict(world=kind, receipts=receipts, exact_parity=True, cache_hits=cached.hits,
                cache_misses=cached.misses, scientific_admission=False), timings


def run(output, inputs, config, verification=False):
    if config != CONFIG or set(inputs) != {'fixture'} or read(inputs['fixture']) != FIXTURE:
        raise ValueError('fixed constructed-only parity handler; human mode refused')
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    results = []; timings = {}
    with threadpool_limits(limits=1):
        for kind in FIXTURE['worlds']:
            result, timing = compare_world(kind, config['draws'])
            results.append(result); timings[kind] = timing
    summary = dict(card=config['card'], constructed=True, complete_context_parity=True,
                   worlds=results, corpus_parity_verified=False, full_pipeline_calibration_complete=False,
                   human_identification_computed=False, scientific_admission=False)
    for name, value in [('SUMMARY.json', summary), ('BINDING.json', dict(config=config, fixture_sha256=filehash(inputs['fixture'])))]:
        if verification:
            if read(output/name) != value:
                raise ValueError('fresh native context parity replay differs')
        else:
            freeze(output/name, value)
    freeze(output/('VERIFY_TIMING.json' if verification else 'TIMING.json'), timings)
    return dict(verified=True, complete_context_parity=True) if verification else dict(status='complete', scientific_admission=False)


def execute(output, inputs, config): return run(output, inputs, config)
def verify(output, inputs, config): return run(output, inputs, config, True)
