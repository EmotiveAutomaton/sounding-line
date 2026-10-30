"""D5 fixed-population gallery support, before identification or length selection.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 reread 2026-10-29.
Under NULL and ALTERNATIVE every original writer/session remains in the census.
Whole prompts never cross a writer's halves. Missing evidence cannot remove a
candidate silently. Independent context donors exclude all scored writers in
their rotation. Known boundary, missing-support and source-tamper cases must
pass. These are necessary support checks, never scientific admission gates.
"""
from collections import Counter, defaultdict
from bisect import bisect_right
from pathlib import Path
import math
import numpy as np

from runners.stage14.common import read, filehash, freeze
from .timing_p6 import gzread, gzip_equal
from .timing_pmap_stats import split_sessions
from . import week3_d5_features as words
from . import week3_d5_character_features as chars

CONFIG = dict(card='D5-gallery-support', schema=1, mode='full', sessions=1399, writers=61, seed=20261026)
CONSTRUCTED = dict(CONFIG, mode='constructed', sessions=32, writers=8)
EDGES = (0., .25, .5, .75, 1.)
COMPONENTS = {'final': ('final',), 'selection': ('selection',), 'rhythm': ('rhythm',),
              'process': ('selection', 'rhythm'),
              **{'human'+str(n): ('human'+str(n),) for n in words.LENGTHS}}


def share_bin(value):
    if value is None: return 'missing'
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError('Invalid recorded model share')
    return str(min(3, bisect_right(EDGES, value)-1))


def available(values):
    if not isinstance(values, list) or not values: raise ValueError('Explicit nonempty feature vector required')
    if any(v is not None and (type(v) not in (int, float) or not math.isfinite(v)) for v in values):
        raise ValueError('Nonfinite feature supplied')
    return any(v is not None for v in values)


def join(word, character):
    keys = ('session', 'writer', 'prompt', 'timestamp', 'model_share', 'model_share_missing_reason')
    if any(word[k] != character[k] for k in keys): raise ValueError('Feature identities differ')
    if not math.isfinite(word['timestamp']): raise ValueError('Invalid session date')
    support = {'selection': available(word['process']['selection']),
               'rhythm': available(word['process']['rhythm'])}
    def char_support(value):
        if set(value['opportunities']) != {'2', '3', '4'}: raise ValueError('Character orders differ')
        if any(type(n) is not int or n < 0 for n in value['opportunities'].values()):
            raise ValueError('Invalid character opportunity count')
        return all(n > 0 for n in value['opportunities'].values())
    support['final'] = char_support(character['final'])
    if any(word[k]['words'] != character[k]['words'] for k in ('final', 'human')):
        raise ValueError('Word and character lengths differ')
    for n in words.LENGTHS:
        a, b = word['human_prefixes'][str(n)], character['human_prefixes'][str(n)]
        if a['supported'] != b['supported']: raise ValueError('Prefix support differs')
        if a['supported'] and (a['words'] != n or b['words'] != n):
            raise ValueError('Prefix is not its declared word length')
        support['human'+str(n)] = bool(a['supported'] and char_support(b))
    return dict(**{k:word[k] for k in keys}, share_bin=share_bin(word['model_share']), support=support)


def load(inputs, config):
    if config not in (CONFIG, CONSTRUCTED): raise ValueError('Frozen support configuration required')
    if config == CONSTRUCTED:
        if set(inputs) != {'fixture'}: raise ValueError('Constructed fixture required')
        fixture = read(inputs['fixture'])
        if fixture.get('constructed') is not True: raise ValueError('Constructed scope required')
        return fixture['rows'], {str(Path(inputs['fixture']).resolve()): filehash(inputs['fixture'])}
    if set(inputs) != {'word_complete', 'character_complete'}: raise ValueError('Both completed feature channels required')
    sources = {}; bindings = {}; ancestors = []
    for key, module in [('word_complete', words), ('character_complete', chars)]:
        terminal = Path(inputs[key]).resolve(); root = terminal.parent; complete = read(terminal)
        if complete.get('status') != 'COMPLETE' or complete.get('fresh_process_verified') is not True:
            raise ValueError('Feature source is not independently complete')
        bindings[str(terminal)] = filehash(terminal)
        def artifact(relative):
            p = (root/relative).resolve(); p.relative_to(root)
            h = filehash(p)
            if complete['outputs'].get(relative) != h: raise ValueError('Completed feature bytes differ')
            bindings[str(p)] = h
            return gzread(p) if p.suffix == '.gz' else read(p)
        plan = artifact('PLAN.json')
        if plan['module'] != module.__name__ or plan['config'] != module.CONFIG:
            raise ValueError('Wrong complete feature producer')
        ancestors.append({k: str(Path(v).resolve()) for k, v in plan['inputs'].items()})
        summary = artifact('output/SUMMARY.json')
        if not summary['all_sessions_retained'] or summary['sessions'] != config['sessions'] or summary['writers'] != config['writers']:
            raise ValueError('Full feature census required')
        units = {}
        for item in artifact('output/FEATURE_INDEX.json'):
            relative = 'output/'+item['file']; unit = artifact(relative)
            if bindings[str((root/relative).resolve())] != item['sha256'] or any(unit[k] != item[k] for k in ('session', 'writer')):
                raise ValueError('Feature index differs')
            if unit['session'] in units: raise ValueError('Duplicate feature session')
            units[unit['session']] = unit
        sources[key] = units
    if ancestors[0] != ancestors[1]: raise ValueError('Feature source ancestors differ')
    a, b = sources['word_complete'], sources['character_complete']
    if set(a) != set(b): raise ValueError('Channel populations differ')
    return [join(a[s], b[s]) for s in sorted(a)], bindings


def prepare(rows, config):
    rows = sorted(rows, key=lambda r:r['session']); writers = sorted({r['writer'] for r in rows})
    if len(rows) != config['sessions'] or len({r['session'] for r in rows}) != len(rows) or len(writers) != config['writers']:
        raise ValueError('Full session/writer census differs')
    for r in rows:
        if share_bin(r['model_share']) != r['share_bin'] or set(r['support']) != set(COMPONENTS)-{'process'}:
            raise ValueError('Invalid support metadata')
        if any(type(v) is not bool for v in r['support'].values()): raise ValueError('Support must be explicit')
    halves, excluded = split_sessions(rows)
    folds = {str(w):i % 3 for i, w in enumerate(np.random.default_rng(config['seed']).permutation(writers))}
    detail = {}; summary = {}
    for channel, components in COMPONENTS.items():
        profiles = {}; literal_missing = {}; rotations = []
        for w in writers:
            parts = halves.get(w, [[], []])
            profiles[w] = [{part:[r['session'] for r in rr if r['support'][part]] for part in components} for rr in parts]
            if {r['prompt'] for r in parts[0]} & {r['prompt'] for r in parts[1]}: raise ValueError('Whole prompt leaked')
        supported = [w for w in writers if all(all(part[c] for c in components) for part in profiles[w])]
        for r in rows:
            missing = [c for c in components if not any(d['prompt'] == r['prompt'] and d['writer'] != r['writer'] and d['support'][c] for d in rows)]
            if missing: literal_missing[r['session']] = missing
        for f in range(3):
            donors = [r for r in rows if folds[r['writer']] == f]
            gallery = [w for w in writers if folds[w] != f]
            probes = [w for w in writers if folds[w] == (f+1) % 3]
            missing = {}
            donor_support = defaultdict(set)
            for d in donors:
                for c in components:
                    if d['support'][c]: donor_support[d['prompt']].add(c)
            for r in rows:
                if r['writer'] not in gallery: continue
                absent = [c for c in components if c not in donor_support[r['prompt']]]
                if absent: missing[r['session']] = absent
            rotations.append(dict(donor_writers=[w for w in writers if folds[w] == f], gallery_writers=gallery,
                probe_writers=probes, missing_context_sessions=missing))
        detail[channel] = dict(component_sessions=profiles, supported_writers=supported,
            missing_literal_context_sessions=literal_missing, independent_rotations=rotations)
        summary[channel] = dict(profile_supported_writers=len(supported), full_original_gallery_supported=len(supported)==len(writers),
            literal_missing_context_sessions=len(literal_missing), independent_missing_context_sessions=[len(x['missing_context_sessions']) for x in rotations],
            independent_gallery_sizes=[len(x['gallery_writers']) for x in rotations],
            support_is_necessary_not_scientific_admission=True)
    bins = {str(i):0 for i in range(4)}; bins['missing'] = 0; bins.update(Counter(r['share_bin'] for r in rows))
    result = dict(sessions=len(rows), writers=len(writers), all_sessions_retained=True,
        split_supported_writers=len(halves), excluded_from_split=len(excluded), model_share_bins=bins,
        bin_edges=list(EDGES), bins_left_closed_right_open_except_final=True, channels=summary,
        source_only=True, effect_computed=False, scientific_admission=False,
        scope='Necessary fixed-population gallery and context support only; no selected subset or text length')
    return result, dict(rows=rows, writer_folds=folds, halves={w:[[r['session'] for r in rr] for rr in h] for w,h in halves.items()},
        split_exclusions=excluded, channels=detail, original_gallery=writers)


def compute(output, inputs, config, verification=False):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    rows, bindings = load(inputs, config); summary, detail = prepare(rows, config)
    values = {'BINDING.json':dict(config=config, inputs=bindings), 'SUMMARY.json':summary, 'GALLERIES.json.gz':detail}
    for name, value in values.items():
        p = output/name
        if verification:
            if (gzread(p) if p.suffix == '.gz' else read(p)) != value: raise ValueError('Fresh complete support replay differs')
        elif p.suffix == '.gz': gzip_equal(p, value)
        else: freeze(p, value)
    return dict(verified=True, full_fresh_support_replay=True, source_only=True) if verification else dict(status='complete', source_only=True)


def execute(output, inputs, config): return compute(output, inputs, config)
def verify(output, inputs, config): return compute(output, inputs, config, True)
