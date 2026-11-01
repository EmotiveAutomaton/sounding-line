"""Complete D5 context eligibility; necessary support only, never a score.

DESIGN CHECK: LESSONS 3-5, CONTROLS 1-7 reread 2026-11-01.
NULL/ALTERNATIVE preserve every row, fixed candidate, role and saved draw.
Missing real or donor evidence is unsupported, malformed provenance is invalid,
otherwise support is complete. No redraw, mask change or scientific admission.
"""
from collections import Counter
from pathlib import Path
import time

from runners.stage14.common import read, filehash, freeze, atomic
from .timing_p6 import gzread, gzip_equal
from .timing_pmap_stats import split_sessions
from . import week3_d5_reference_plans as reference

CONFIG = dict(reference.CONFIG, card='D5-context-support')
CONSTRUCTED = dict(reference.CONSTRUCTED, card='D5-context-support')


def load(inputs, config):
    if config not in (CONFIG, CONSTRUCTED):
        raise ValueError('Frozen context-support configuration required')
    if set(inputs) != {'reference_complete'}:
        raise ValueError('Complete reference producer required')
    terminal = Path(inputs['reference_complete']).resolve()
    root = terminal.parent
    complete = read(terminal)
    if complete.get('status') != 'COMPLETE' or complete.get('fresh_process_verified') is not True:
        raise ValueError('Reference source is not independently complete')
    pins = {str(terminal): filehash(terminal)}

    def artifact(name):
        path = (root/name).resolve()
        path.relative_to(root)
        digest = filehash(path)
        if complete['outputs'].get(name) != digest:
            raise ValueError('Completed reference bytes differ')
        pins[str(path)] = digest
        return gzread(path) if path.suffix == '.gz' else read(path)

    plan = artifact('PLAN.json')
    expected = reference.CONFIG if config == CONFIG else reference.CONSTRUCTED
    if plan['module'] != reference.__name__ or plan['config'] != expected:
        raise ValueError('Wrong reference producer')
    binding = artifact('output/BINDING.json')
    if binding['config'] != expected:
        raise ValueError('Wrong reference binding')
    for name, digest in binding['inputs'].items():
        if filehash(name) != digest:
            raise ValueError('Reference ancestor changed')
        pins[name] = digest
    rows, folds, original_pins = reference.load(plan['inputs'], expected)
    if original_pins != binding['inputs']:
        raise ValueError('Reference ancestor identity differs')
    rows = sorted(rows, key=lambda r: r['session'])
    writers = sorted({r['writer'] for r in rows})
    halves, _ = split_sessions(rows)
    roster = sorted(halves)
    if (len(rows), len(writers), len(roster)) != (config['sessions'], config['writers'], config['candidates']):
        raise ValueError('Source census differs')
    if len({r['session'] for r in rows}) != len(rows) or set(folds) != set(writers) or set(folds.values()) != {0, 1, 2}:
        raise ValueError('Source identities or roles differ')
    source = artifact('output/SOURCE.json.gz')
    if source != dict(rows=rows, writer_folds=folds, original_writers=writers, candidates=roster):
        raise ValueError('Saved source reconstruction differs')
    if artifact('output/REAL_SUPPORT.json') != reference.layout(rows, roster):
        raise ValueError('Saved real support differs')
    banks = {name: artifact('output/'+name+'-BANK.json.gz') for name in ('literal', 'independent')}
    for bank in banks.values():
        if bank['sessions'] != [r['session'] for r in rows] or bank['writer_order'] != writers:
            raise ValueError('Reference bank identities differ')
        if len(bank['assignments']) != config['permutations'] or len(bank['missing_profile_writers']) != config['permutations']:
            raise ValueError('Complete reference bank required')
    return rows, folds, roster, banks, pins


def assignment_for(rows, folds, bank, index, seed, roles):
    encoded = bank['assignments'][index]
    writers = bank['writer_order']
    if len(encoded) != len(rows) or any(type(x) is not int or not 0 <= x < len(writers) for x in encoded):
        raise ValueError('Invalid saved assignment')
    assignment = {r['session']: writers[x] for r, x in zip(rows, encoded)}
    expected = reference.label_draw(rows, folds, index, seed, roles)
    if assignment != expected:
        raise ValueError('Saved assignment differs from frozen seed')
    if roles and any(folds[r['writer']] != folds[assignment[r['session']]] for r in rows):
        raise ValueError('Role overlap in reference assignment')
    return assignment


def inspect_support(rows, folds, roster, assignment=None, independent=False):
    assignment = assignment or {r['session']: r['writer'] for r in rows}
    if set(assignment) != {r['session'] for r in rows} or not set(assignment.values()) <= set(folds):
        raise ValueError('Complete assigned source required')
    if independent and any(folds[r['writer']] != folds[assignment[r['session']]] for r in rows):
        raise ValueError('Role overlap in reference assignment')
    components = sorted({c for cs in reference.source.COMPONENTS.values() for c in cs})
    total, by_writer, by_fold = Counter(), Counter(), Counter()
    for r in rows:
        if set(r['support']) != set(components) or any(type(v) is not bool for v in r['support'].values()):
            raise ValueError('Explicit complete boolean support required')
        writer = assignment[r['session']]
        for component in components:
            if r['support'][component]:
                total[r['prompt'], component] += 1
                by_writer[r['prompt'], component, writer] += 1
                by_fold[r['prompt'], component, folds[writer]] += 1
    halves, excluded = split_sessions(rows, assignment)
    rotations = []
    for fold in range(3) if independent else [None]:
        gallery = [w for w in roster if fold is None or folds[w] != fold]
        probes = [w for w in roster if fold is None or folds[w] == (fold+1) % 3]
        if len(gallery) < 2 or not probes or not set(probes) <= set(gallery):
            raise ValueError('Fixed rotation cannot form a comparison')
        channels = {}
        for channel in reference.CHANNELS:
            required = reference.source.COMPONENTS[channel]
            missing_gallery, missing_probes, missing_terms = [], [], []
            probe_sessions = terms = 0
            for writer in gallery:
                parts = halves.get(writer, [[], []])
                if not all(any(r['support'][c] for r in parts[1]) for c in required):
                    missing_gallery.append(writer)
                for r in parts[1]:
                    for component in required:
                        if r['support'][component]:
                            terms += 1
                            donors = (by_fold[r['prompt'], component, fold] if independent else
                                      total[r['prompt'], component]-by_writer[r['prompt'], component, writer])
                            if not donors: missing_terms.append([r['session'], component, 'gallery'])
            for writer in probes:
                eligible = [r for r in halves.get(writer, [[], []])[0] if all(r['support'][c] for c in required)]
                if not eligible: missing_probes.append(writer)
                probe_sessions += len(eligible)
                for r in eligible:
                    for component in required:
                        terms += 1
                        donors = (by_fold[r['prompt'], component, fold] if independent else
                                  total[r['prompt'], component]-by_writer[r['prompt'], component, writer])
                        if not donors: missing_terms.append([r['session'], component, 'probe'])
            channels[channel] = dict(missing_gallery_writers=missing_gallery,
                missing_probe_writers=missing_probes, missing_context_terms=missing_terms,
                required_context_terms=terms, probe_sessions=probe_sessions,
                supported=not (missing_gallery or missing_probes or missing_terms))
        rotations.append(dict(donor_fold=fold, gallery_writers=gallery, probe_writers=probes, channels=channels))
    return dict(rotations=rotations, split_excluded=excluded)


def compute(output, inputs, config, verification=False):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    started = time.process_time()
    rows, folds, roster, banks, pins = load(inputs, config)

    def retain(name, value):
        path = output/name
        if verification:
            if (gzread(path) if path.suffix == '.gz' else read(path)) != value:
                raise ValueError('Fresh context support replay differs')
        elif path.suffix == '.gz': gzip_equal(path, value)
        else: freeze(path, value)

    retain('BINDING.json', dict(config=config, inputs=pins))
    real = {name: inspect_support(rows, folds, roster, independent=(name == 'independent'))
            for name in banks}
    retain('REAL_CONTEXT_SUPPORT.json.gz', real)
    total = 2*config['permutations']; done = 0; invalid = {}
    for name, bank in banks.items():
        records = []; counts = Counter({ch: 0 for ch in reference.CHANNELS})
        for index in range(config['permutations']):
            assignment = assignment_for(rows, folds, bank, index, config['seed'], name == 'independent')
            old = reference.layout(rows, roster, assignment)['missing_profile_writers']
            if {ch: v for ch, v in old.items() if v} != bank['missing_profile_writers'][index]:
                raise ValueError('Saved fixed-gallery support differs')
            state = inspect_support(rows, folds, roster, assignment, name == 'independent')
            records.append(state)
            counts.update(ch for ch in reference.CHANNELS if any(not r['channels'][ch]['supported'] for r in state['rotations']))
            done += 1
            if done % 12 == 0 or done == total:
                atomic(output/'PROGRESS.json', dict(phase='verify' if verification else 'execute', done=done, total=total))
            if (output/'YIELD_REQUEST.json').exists() or (output.parent/'STOP').exists():
                raise InterruptedError('Context-support boundary yield')
            if not verification and done == max(1, config['permutations']//10) and not (output/'FIRST_TENTH.json').exists():
                freeze(output/'FIRST_TENTH.json', dict(projected_cpu_seconds=max(.001, 4*(time.process_time()-started)*total/done), scope='Complete context support, both passes times two; no scientific admission'))
        retain(name+'-CONTEXT_SUPPORT.json.gz', records)
        invalid[name] = dict(counts)
    retain('SUMMARY.json', dict(sessions=len(rows), writers=len(folds), candidate_writers=len(roster),
        source_only=True, effect_computed=False, scientific_admission=False, all_draws_retained=True,
        permutations_per_bank=config['permutations'], unsupported_reference_draws=invalid,
        unsupported_real_channels={name: [ch for ch in reference.CHANNELS if any(not r['channels'][ch]['supported'] for r in state['rotations'])] for name, state in real.items()},
        scope='Necessary context-source support only; numerical validity and scientific calibration remain required'))
    return dict(verified=True, full_fresh_context_support_replay=True, source_only=True) if verification else dict(status='complete', source_only=True)


def execute(output, inputs, config):
    try: return compute(output, inputs, config)
    except InterruptedError: return dict(status='yielded', source_only=True)


def verify(output, inputs, config):
    return compute(output, inputs, config, True)
