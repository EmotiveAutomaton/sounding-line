"""S6 fixed-writer population-conflict features; no scientific fit.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 reread 2026-11-04.
NULL/ALTERNATIVE: the same twenty writers and every retained onset survive.
Entropy is zero for one possible continuation and increases with competition;
negative top-two margin increases toward a tie. Sparse evaluation must match
enumerating the original full vocabulary. Changed sources, missing keys or a
different original target probability refuse. No new model or future context.
"""
from collections import defaultdict
import math
from pathlib import Path
import time
import numpy as np
from runners.stage14.common import atomic, digest
from . import week3_d33_spec as parent
from .timing_p6 import KneserNey, gzread, gzip_equal, read, write_equal
from .timing_pmap_source import completed, bound_record


def configuration(mode):
    if mode not in ('constructed', 'cost', 'full'):
        raise ValueError('Unknown source mode')
    return dict(card='W4-S6-source', mode=mode, seed=20261102, writers=20)


def selection(rows):
    writers = sorted({r['writer'] for r in rows})
    if len(writers) < 20:
        raise ValueError('Twenty-writer floor unavailable')
    chosen = sorted(np.random.default_rng(20261102).permutation(writers).tolist()[:20])
    return dict(seed=20261102, population_writers=len(writers), selected_writers=chosen,
                sample_writers=20, selection='whole supported writers; no outcome or genre selection')


class Conflict:
    """Exact sparse interpolation, with the original scalar scorer as oracle."""
    def __init__(self, model):
        self.model = model
        self.base = {w: model.continuations[w]/model.total_types for w in sorted(model.vocabulary)}
        self.base_entropy = -math.fsum(p*math.log(p) for p in self.base.values() if p)
        self.base_order = sorted(self.base, key=lambda w: (-self.base[w], w))
        self.lower, self.three = defaultdict(dict), defaultdict(dict)
        for (b, w), n in model.lower.items():
            self.lower[b][w] = max(n-model.discount, 0)/model.lower_total[b]
        for (a, b, w), n in model.three.items():
            self.three[(a, b)][w] = max(n-model.discount, 0)/model.context_total[(a, b)]
        self.cache = {}

    def __call__(self, context):
        m = self.model
        key = tuple(['<s>']*max(0, 2-len(context))+[m.lookup(w) for w in context[-2:]])
        if key in self.cache:
            return dict(self.cache[key])
        a, b = key
        l2 = m.discount*m.lower_types[b]/m.lower_total[b] if m.lower_total[b] else 1.
        l3 = m.discount*m.context_types[key]/m.context_total[key] if m.context_total[key] else 1.
        scale = l2*l3
        deltas = {w: l3*p for w, p in self.lower[b].items()}
        for w, p in self.three[key].items():
            deltas[w] = deltas.get(w, 0.)+p
        # Sum entropy of the scaled base once, then replace only changed cells.
        terms = [scale*self.base_entropy-scale*math.log(scale)]
        top = []
        for w in sorted(deltas):
            old, p = scale*self.base[w], scale*self.base[w]+deltas[w]
            terms.append((old*math.log(old) if old else 0.)-(p*math.log(p) if p else 0.))
            top.append(p)
        untouched = 0
        for w in self.base_order:
            if w not in deltas:
                top.append(scale*self.base[w]); untouched += 1
                if untouched == 2:
                    break
        total = scale+math.fsum(deltas.values())
        entropy = math.fsum(terms)
        first, second = sorted(top, reverse=True)[:2]
        if abs(total-1.) > 1e-10 or entropy < -1e-10 or not 0 <= second <= first <= 1:
            raise ValueError('Invalid original conditional distribution')
        value = dict(entropy=max(0., entropy), top_two_margin=first-second,
                     negative_margin=second-first, total_probability=total)
        self.cache[key] = value
        return dict(value)


def dense(model, context):
    values = sorted((model.score(w, context) for w in sorted(model.vocabulary)), reverse=True)
    return dict(entropy=-math.fsum(p*math.log(p) for p in values if p),
                top_two_margin=values[0]-values[1], negative_margin=values[1]-values[0],
                total_probability=math.fsum(values))


def known_answers():
    sequences = [['a', 'b', 'a', 'c'], ['a', 'b', 'd'], ['z'], ['b', 'c', 'b']]*3
    model = KneserNey(sequences); fast = Conflict(model)
    contexts = [[], ['a'], ['a', 'b'], ['z', 'missing'], ['missing'], ['c', 'b']]
    maximum = 0.
    for context in contexts:
        x, y = fast(context), dense(model, context)
        maximum = max(maximum, *(abs(x[k]-y[k]) for k in x))
    if maximum > 2e-12:
        raise ValueError('Sparse conditional entropy/margin differs from scalar model')
    rows = [dict(writer=f'w{i:02}', log_pause=i) for i in range(30)]
    selected = selection(rows)
    if selected != selection([dict(r, log_pause=-999) for r in reversed(rows)]):
        raise ValueError('Writer selection depends on outcomes or order')
    return dict(scalar_contexts=len(contexts), maximum_absolute_error=maximum,
                selection_invariant=True, verified=True)


def load(inputs):
    if set(inputs) != {'parent_completion', 'parent_landing', 'p6_completion', 'p6_index'}:
        raise ValueError('Exact completed sources required')
    rows, _ = parent.load({k: inputs[k] for k in ('parent_completion', 'parent_landing')})
    # Bind P6 to the actual ancestral D33 plan, not just an arbitrary completed model.
    original = read(Path(inputs['parent_completion']).parent/'PLAN.json')
    prior = read(Path(original['inputs']['prior_completion']).parent/'PLAN.json')
    for k in ('p6_completion', 'p6_index'):
        if Path(prior['inputs'][k]).resolve() != Path(inputs[k]).resolve():
            raise ValueError('Different population model ancestry')
    completed(inputs['p6_completion'], inputs['p6_index'])
    index = read(inputs['p6_index'])
    records = [bound_record(inputs['p6_index'], r) for r in index]
    if len({r['session'] for r in records}) != len(records):
        raise ValueError('Duplicate P6 session')
    for r, i in zip(records, index):
        if (r['session'], r['writer']) != (i['session'], i['writer']):
            raise ValueError('P6 record identity changed')
    return rows, records


def features(rows, records, chosen, output):
    lookup = {r['session']: r for r in records}
    training = defaultdict(list)
    for record in records:
        training[record['writer']].extend(record['training_sequences'])
    result = []
    for wi, writer in enumerate(chosen):
        model = KneserNey([s for w in sorted(training) if w != writer for s in training[w]])
        conflict = Conflict(model)
        for row in rows:
            if row['writer'] != writer:
                continue
            source = lookup[row['session']]
            word = source['words'][row['index']]
            if source['writer'] != writer or word['index'] != row['index']:
                raise ValueError('Source onset identity differs')
            p = model.score(word['token'], word['context'])
            if p != word['population_probability'] or not math.isclose(-math.log(p), row['population_surprisal'], abs_tol=1e-12):
                raise ValueError('Original population probability differs')
            result.append(dict(row, **conflict(word['context'])))
        atomic(Path(output)/'PROGRESS.json', dict(phase='population_conflict', done=wi+1, total=len(chosen)))
    expected = {(r['session'], r['index']) for r in rows if r['writer'] in chosen}
    if len(result) != len(expected) or {(r['session'], r['index']) for r in result} != expected:
        raise ValueError('Conflict extraction changed retained support')
    return sorted(result, key=lambda r: (r['writer'], r['session'], r['index']))


def one_pass(output, inputs, config, verifying=False):
    if config != configuration(config.get('mode')):
        raise ValueError('Frozen configuration required')
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    start = time.process_time()
    if config['mode'] == 'constructed':
        if inputs:
            raise ValueError('Constructed validation accepts no human data')
        summary = known_answers()
    else:
        rows, records = load(inputs); manifest = selection(rows)
        chosen = manifest['selected_writers']
        if config['mode'] == 'cost':
            chosen = chosen[:2]  # Fixed lexical first tenth of the frozen sample.
        manifest = dict(manifest, processed_writers=chosen, cost_only=config['mode']=='cost')
        if verifying:
            if read(output/'SELECTION.json') != manifest:
                raise ValueError('Frozen writer selection differs')
        else:
            write_equal(output/'SELECTION.json', manifest)
        source_cpu = time.process_time()-start
        value = features(rows, records, chosen, output)
        if verifying:
            if gzread(output/'PRIVATE_DESIGN.json.gz') != value:
                raise ValueError('Full fresh conflict reconstruction differs')
        else:
            gzip_equal(output/'PRIVATE_DESIGN.json.gz', value)
        summary = dict(writers=len(chosen), population_writers=manifest['population_writers'],
                       words=len(value), keys_sha256=digest([[r['session'], r['index']] for r in value]),
                       scoring=False, scope='frozen supported-writer sample',
                       model='original P6 leave-writer-out population trigram; complete vocabulary',
                       direction='higher entropy and less negative top-two margin mean greater conflict')
        timing = dict(source_cpu_seconds=source_cpu, features_cpu_seconds=time.process_time()-start-source_cpu)
        write_equal(output/('VERIFY_TIMING.json' if verifying else 'EXECUTE_TIMING.json'), timing)
        if verifying and config['mode']=='cost':
            old = read(output/'EXECUTE_TIMING.json')
            forecast = 6*(max(old['source_cpu_seconds'], timing['source_cpu_seconds'])+
                          10*max(old['features_cpu_seconds'], timing['features_cpu_seconds']))
            write_equal(output/'FORECAST.json', dict(full_source_cpu_seconds=forecast,
                        safety_factor=3, includes_fresh_replay=True, analysis_admitted=False))
    if verifying:
        if read(output/'SUMMARY.json') != summary:
            raise ValueError('Source summary differs on replay')
    else:
        write_equal(output/'SUMMARY.json', summary)
    return dict(verified=True, full_fresh_replay=True, scientific_fit=False) if verifying else summary


def execute(output, inputs, config):
    return one_pass(output, inputs, config)


def verify(output, inputs, config):
    return one_pass(output, inputs, config, True)
