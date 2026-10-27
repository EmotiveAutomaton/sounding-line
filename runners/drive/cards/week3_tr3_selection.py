"""TR3 discovery selection; no held-out carryover outcome.

DESIGN CHECK: LESSONS 2-5 and relevant CONTROLS read 2026-10-27.
NULL: identical banks select nothing. ALTERNATIVE: a sufficiently recurrent
planted model-associated feature passes the analytic information threshold.
Sparse single-writer support cannot qualify. Missing bank support is explicit,
not a null. Identity, aggregate or replay mismatch refuses admission. Exhaustive
states: supported selection, empty/unsupported bank, or instrument failure.
"""
from collections import Counter, defaultdict
import hashlib
import math
from pathlib import Path
import time

from .timing_census import read, filehash
from .timing_pmap_source import completed
from .timing_p6 import gzread, write_equal, progress
from .week3_tr3_candidates import discovery_roster

FAMILIES = ('w1', 'w2', 'w3', 'p')


def checked_counts(counts):
    if not isinstance(counts, dict):
        raise ValueError('count mapping required')
    for key, value in counts.items():
        if (not isinstance(key, str) or ':' not in key or
                key.split(':', 1)[0] not in FAMILIES or not key.split(':', 1)[1] or
                type(value) is not int or value <= 0):
            raise ValueError('positive integer feature count required')
    return counts


def aggregate(rows, roster):
    by_id = {r['session']: r for r in rows}
    if len(by_id) != len(rows) or set(by_id) != {r['session'] for r in roster}:
        raise ValueError('count session population differs')
    counts = Counter(); support = Counter(); writers = defaultdict(set)
    for expected in roster:
        row = by_id[expected['session']]
        if expected['half'] != 'discovery' or any(row[k] != expected[k] for k in ('session', 'writer', 'prompt')):
            raise ValueError('discovery count identity differs')
        values = checked_counts(row['feature_counts'])
        counts.update(values); support.update(values.keys())
        for feature in values:
            writers[feature].add(row['writer'])
    return dict(counts=dict(counts), session_support=dict(support)), {
        feature: len(ids) for feature, ids in writers.items()}


def deciles(rows):
    """Ties use their exact cumulative rank interval midpoint; bins 0..9."""
    for family in FAMILIES:
        ordered = sorted((r for r in rows if r['family'] == family),
                         key=lambda r: (r['pooled_count'], r['feature']))
        start = 0; size = len(ordered)
        while start < size:
            stop = start + 1
            while stop < size and ordered[stop]['pooled_count'] == ordered[start]['pooled_count']:
                stop += 1
            decile = min(9, 10 * (start + stop) // (2 * size))
            for row in ordered[start:stop]:
                row['frequency_decile'] = decile
            start = stop


def select(model, human, writer_support):
    mc = checked_counts(model['counts']); hc = checked_counts(human['counts'])
    selected = []; families = {}
    vocabulary = sorted(set(mc) | set(hc))
    for family in FAMILIES:
        names = [f for f in vocabulary if f.split(':', 1)[0] == family]
        mt = sum(mc.get(f, 0) for f in names); ht = sum(hc.get(f, 0) for f in names)
        families[family] = dict(vocabulary=len(names), model_total=mt, human_total=ht,
                                supported=bool(mt and ht), selected=0)
        if not mt or not ht:
            continue
        for feature in names:
            m = mc.get(feature, 0); h = hc.get(feature, 0)
            # Exact integer ratio test for Jeffreys-smoothed probabilities.
            ratio_passes = (2*m+1)*(2*ht+len(names)) >= 2*(2*h+1)*(2*mt+len(names))
            if (m < 10 or model['session_support'].get(feature, 0) < 5 or
                    writer_support.get(feature, 0) < 5 or not ratio_passes):
                continue
            pm = (m+.5)/(mt+.5*len(names)); ph = (h+.5)/(ht+.5*len(names))
            selected.append(dict(feature=feature, family=family, model_count=m, human_count=h,
                pooled_count=m+h, model_sessions=model['session_support'][feature],
                model_writers=writer_support[feature], model_probability=pm, human_probability=ph,
                model_pmi=math.log(2*pm/(pm+ph))))
            families[family]['selected'] += 1
    deciles(selected)
    return dict(features=sorted(selected, key=lambda r: r['feature']), families=families,
                selection_rule='Jeffreys within-family equal-prior PMI >= log(4/3); model count >=10, sessions >=5, writers >=5; no top-k',
                frequency_rule='Within selected family, pooled discovery count tied-midrank deciles')


def run(output, inputs, config, verification=False):
    mode = config.get('mode')
    if config != dict(mode=mode, seed=20261026) or mode not in ('constructed', 'full'):
        raise ValueError('frozen selection configuration required')
    output = Path(output); output.mkdir(parents=True, exist_ok=True); started = time.process_time()
    if mode == 'constructed':
        if set(inputs) != {'fixture'}:
            raise ValueError('fixture required')
        fixture = read(inputs['fixture']); census = fixture['census']; split = fixture['split']
        parents = None
    else:
        if set(inputs) != {'exposure_completion', 'model_completion', 'human_completion'}:
            raise ValueError('exact completed parents required')
        source = Path(inputs['exposure_completion']).parent
        for name in ('CENSUS.json', 'WB1_WRITER_SPLIT.json'):
            completed(inputs['exposure_completion'], source/'output'/name)
        census = read(source/'output/CENSUS.json'); split = read(source/'output/WB1_WRITER_SPLIT.json')
        parents = {bank: Path(inputs[bank+'_completion']).parent for bank in ('model', 'human')}
    roster = discovery_roster(census, split, mode == 'full'); banks = {}; supports = {}; bindings = {}
    for bank, filename in (('model', 'CANDIDATES.json'), ('human', 'COUNTS.json')):
        rows = []; hashes = []
        for i, expected in enumerate(roster):
            sid = expected['session']
            if parents is None:
                row = fixture[bank]['sessions'][sid]; source_hash = None
            else:
                path = parents[bank]/'output/sessions'/(hashlib.sha256(sid.encode()).hexdigest()+'.json.gz')
                completed(inputs[bank+'_completion'], path); source_hash = filehash(path); row = gzread(path)
            rows.append(row); hashes.append(dict(session=sid, source_sha256=source_hash))
            progress(output/'PROGRESS.json', dict(phase=bank+'-discovery-validation', done=i+1, total=len(roster)))
            if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():
                raise InterruptedError('selection yield at session boundary')
        actual, writers = aggregate(rows, roster)
        if parents is None:
            declared = fixture[bank]['aggregate']
        else:
            path = parents[bank]/'output'/filename
            completed(inputs[bank+'_completion'], path); declared = read(path)
        if actual != declared:
            raise ValueError('discovery aggregate differs from complete sessions')
        banks[bank] = actual; supports[bank] = writers; bindings[bank] = hashes
    selection = select(banks['model'], banks['human'], supports['model'])
    summary = dict(sessions=len(roster), writers=len({r['writer'] for r in roster}),
        selected_features=len(selection['features']), families=selection['families'],
        test_payloads_read=0, constructed=mode == 'constructed', scientific_admission=False,
        disposition='selected' if selection['features'] else 'unsupported-empty-selection',
        scope='Frozen discovery feature selection only; carryover and matching uncomputed')
    payloads = {'SELECTION.json': selection, 'SUMMARY.json': summary,
        'BINDING.json': dict(config=config, inputs={k:filehash(v) for k,v in inputs.items()}, units=bindings)}
    for name, value in payloads.items():
        if verification:
            if read(output/name) != value:
                raise ValueError('selection replay differs')
        else:
            write_equal(output/name, value)
    if verification:
        return dict(verified=True, complete_selection_replay=True, scientific_admission=False)
    if not (output/'TIMING.json').exists():
        write_equal(output/'TIMING.json', dict(cpu_seconds=time.process_time()-started))
    return dict(status='complete', summary=summary, scientific_admission=False)


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, True)
