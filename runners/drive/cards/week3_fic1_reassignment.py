"""FIC1 exact profile reconstruction under prompt-block writer reassignment.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 reread October 27.
NULL and ALTERNATIVE both require every original session exactly once, fixed
within-prompt label counts, recomputed whole-prompt halves, exact word quotas
and unchanged pooled feature operators. Identity assignment must reproduce the
sealed observed prefixes exactly. Missing halves and lengths remain explicit;
no redraw, score, probability, context-reference claim or scientific admission.
This bounded engineering timing pass is not the complete permutation test.
"""
from collections import Counter, defaultdict
from pathlib import Path
import time

import numpy as np
from threadpoolctl import threadpool_limits

from runners.stage14.common import read, filehash, freeze, atomic
from . import week3_fic1_prefixes as prefix
from . import week3_fic1_galleries_recovery as gallery
from .timing_p6 import gzread
from .timing_pmap_source import completed
from .timing_pmap_stats import split_sessions

CONFIG = dict(card='FIC1-reassignment-timing', schema=1, mode='timing',
              sessions=990, writers=24, word_limits=[500, 1000, 2000],
              permutations=1, seed=20261026)
CONSTRUCTED = dict(CONFIG, mode='constructed', sessions=24, writers=3,
                   word_limits=[2, 4, 8], permutations=2)


def labels_within_prompt(units, rng):
    blocks = defaultdict(list)
    for u in units:
        blocks[u['genre'], u['prompt']].append(u)
    out = {}
    for _, rows in sorted(blocks.items()):
        rows = sorted(rows, key=lambda r: r['session'])
        out.update((r['session'], str(w)) for r, w in
                   zip(rows, rng.permutation([r['writer'] for r in rows])))
    return out


def rebuild(units, rows, dictionary, limits, labels=None):
    """Reassign whole sessions, then reconstruct chronology and all prefixes."""
    ix = {u['session']: u for u in units}
    features = {r['session']: r for r in rows}
    if not units or len(ix) != len(units) or len(features) != len(rows) or set(ix) != set(features):
        raise ValueError('missing or duplicate source session')
    identity = {s: u['writer'] for s, u in ix.items()}
    labels = identity if labels is None else labels
    if set(labels) != set(ix):
        raise ValueError('assignment must cover every original session')
    original = Counter((u['genre'], u['prompt'], u['writer']) for u in units)
    assigned = Counter((u['genre'], u['prompt'], labels[u['session']]) for u in units)
    if assigned != original:
        raise ValueError('within-prompt label multiplicities changed')
    for u in units:
        r = features[u['session']]
        if any(r[k] != u[k] for k in ('writer', 'genre', 'prompt', 'timestamp', 'typed_words')):
            raise ValueError('feature and occurrence identities differ')
    writers = sorted(set(identity.values()))
    result = []; excluded = {}; used = []
    for genre in gallery.base.GENRES:
        selected = [u for u in units if u['genre'] == genre]
        halves, absent = split_sessions(selected, labels)
        excluded[genre] = absent
        for w in writers:
            if w not in halves:
                result.append(dict(writer=w, genre=genre, state='unsupported',
                                   reason='insufficient sessions or disjoint prompts',
                                   sessions=sorted(u['session'] for u in selected if labels[u['session']] == w)))
                continue
            for half, part in enumerate(halves[w]):
                ids = [u['session'] for u in part]
                used.extend(ids)
                result.append(dict(writer=w, genre=genre, half=half, state='prepared',
                    sessions=ids, full_typed_words=sum(u['typed_words'] for u in part),
                    levels={str(n) if n is not None else 'full': prefix.profile(part, n, dictionary)
                            for n in [*limits, None]},
                    final=gallery.base.pooled_final([features[s] for s in ids], dictionary)))
    omitted = [s for r in result if r['state'] == 'unsupported' for s in r['sessions']]
    if Counter(used + omitted) != Counter(ix.keys()):
        raise ValueError('reassignment lost or duplicated a source session')
    return dict(profiles=result, excluded=excluded, original_sessions=len(ix),
                assigned_sessions=len(used), unsupported_sessions=len(omitted),
                original_writers=writers, labels={s: labels[s] for s in sorted(labels)})


def verify_observed(result, profiles, prefixes):
    key = lambda r: (r['writer'], r['genre'], r['half'])
    if any(r['state'] != 'prepared' for r in result['profiles']):
        raise ValueError('observed source unexpectedly lost profile support')
    actual = {key(r): r for r in result['profiles']}
    groups = {key(r): r for r in profiles}; saved = {key(r): r for r in prefixes}
    if len(groups) != len(profiles) or len(saved) != len(prefixes) or set(actual) != set(groups) or set(actual) != set(saved):
        raise ValueError('observed profile census differs')
    for k, r in actual.items():
        if r['sessions'] != groups[k]['sessions'] or r['full_typed_words'] != groups[k]['full_typed_words'] or r['levels'] != saved[k]['levels']:
            raise ValueError('observed reconstruction differs from sealed prefixes')


def load(inputs, config):
    if config == CONSTRUCTED:
        if set(inputs) != {'fixture'}:
            raise ValueError('explicit constructed fixture required')
        p = Path(inputs['fixture']).resolve()
        return read(p), {str(p): filehash(p)}
    if config != CONFIG:
        raise ValueError('fixed complete-source timing configuration required')
    data, bindings = gallery.load(inputs, gallery.CONFIG)
    terminal = Path(inputs['prefix_completion']).resolve()
    def artifact(rel):
        path = terminal.parent / rel
        completed(terminal, path); bindings[str(path)] = filehash(path)
        return gzread(path) if path.suffix == '.gz' else read(path)
    index = artifact('output/SESSION_INDEX.json'); units = []
    for item in index:
        u = artifact('output/' + item['file'])
        if u['session'] != item['session'] or bindings[str(terminal.parent / 'output' / item['file'])] != item['sha256']:
            raise ValueError('occurrence index differs')
        units.append(u)
    return dict(data, units=units), bindings


def run(output, inputs, config, verification=False):
    if config not in (CONFIG, CONSTRUCTED):
        raise ValueError('fixed timing configuration required')
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    start = time.process_time()
    data, bindings = load(inputs, config)
    loaded = time.process_time() - start
    if len(data['units']) != config['sessions'] or len({u['writer'] for u in data['units']}) != config['writers']:
        raise ValueError('complete source population differs')
    def retain(name, value):
        path = output / name
        if verification:
            if read(path) != value:
                raise ValueError('complete reassignment replay differs: ' + name)
        else:
            freeze(path, value)
    with threadpool_limits(limits=1):
        observed = rebuild(data['units'], data['rows'], data['dictionary'], config['word_limits'])
        verify_observed(observed, data['profiles'], data['prefixes'])
        retain('OBSERVED_RECONSTRUCTION.json', observed)
        observed_cpu = time.process_time() - start - loaded
        rng = np.random.default_rng(config['seed']); costs = []
        for i in range(config['permutations']):
            tick = time.process_time()
            labels = labels_within_prompt(data['units'], rng)
            result = rebuild(data['units'], data['rows'], data['dictionary'], config['word_limits'], labels)
            retain(f'REASSIGNMENT_{i:04}.json', result)
            costs.append(time.process_time() - tick)
            atomic(output / 'PROGRESS.json', dict(phase='verify-reassignment' if verification else 'reassignment',
                   done=i+1, total=config['permutations']))
            if (output.parent / 'STOP').exists() or (output / 'YIELD_REQUEST.json').exists():
                raise InterruptedError('yield after complete reassignment reconstruction')
    summary = dict(card=config['card'], constructed=config['mode']=='constructed',
        sessions=config['sessions'], writers=config['writers'],
        observed_prefixes_identical=True, complete_session_accounting=True,
        permutations_rebuilt=config['permutations'], identification_computed=False,
        context_reference_computed=False, full_calibration_complete=False,
        scientific_admission=False, complete_permutation_test=False)
    retain('SUMMARY.json', summary)
    retain('BINDING.json', dict(config=config, inputs=bindings))
    cost = output / ('VERIFY_COST.json' if verification else 'EXECUTE_COST.json')
    if not cost.exists():
        freeze(cost, dict(load_cpu_seconds=loaded, observed_cpu_seconds=observed_cpu,
                         permutation_cpu_seconds=costs, total_cpu_seconds=time.process_time()-start))
    if verification:
        return dict(verified=True, complete_input_replay=True, all_reassignments_recomputed=True,
                    observed_prefixes_identical=True)
    return dict(status='complete', scientific_admission=False)


def execute(output, inputs, config): return run(output, inputs, config)
def verify(output, inputs, config): return run(output, inputs, config, True)
