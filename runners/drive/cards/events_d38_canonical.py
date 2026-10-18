"""Canonical-choice successor, retaining D38's frozen primary and anchors.

DESIGN CHECK: LESSONS 3-5. Flat/planted/reversed changes retain zero/sign.
Canonical choice is authenticated against the original source, never the logged
index. Changed event/anchor support fails closed. Repeated within-writer/menu-size
outcomes test the reference; a biased reference cannot become a clean control.
The primary is a population mean, not writer identification: fake identification
is inapplicable. All writers, exclusions, 200 draws and fixed seeds are retained.
"""
import copy
import hashlib
import math
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

from . import events_d38 as original
from . import menus_canonical_selection as canonical
from .events_d4 import save, read_sealed, assert_close
from .events_d4_sources import bind_completed
from .menus_io import read, sha256, input_hashes, write
from runners.stage14.common import digest

CONFIG = dict(original.CONFIG, threads=1, permutations=200, permutation_seed=20261018)
INPUTS = original.INPUTS | {'selection_reader', 'selection_complete', 'visibility', 'original_complete'}


def canonicalize(sessions, records, visibility, audit):
    sessions = copy.deepcopy(sessions)
    proofs = []
    for session in sessions:
        for row in session['rows']:
            proof = audit.join(row)
            selected = row['handling'] in ('accept', 'edit')
            positions = proof['canonical_positions']
            if selected and (len(positions) != 1 or not proof['verified_insertion'] or not proof['canonical_usable']):
                raise ValueError('D38 canonical choice not uniquely supported')
            if selected and sum(text == row['inserted'] for text in row['menu']) != 1:
                raise ValueError('D38 original choice support changes')
            if not selected and positions:
                raise ValueError('D38 unselected row has a choice')
            indices = records[row['key']]['options']
            if len(indices) != len(row['menu']):
                raise ValueError('D38 offer coverage differs')
            for index, text in zip(indices, row['menu']):
                scope = visibility[index]
                if scope['role'] != 'suggestion' or scope['text_sha256'] != digest(text):
                    raise ValueError('D38 offer vector/text association differs')
            if selected:
                row['inserted'] = row['menu'][positions[0]]
            proofs.append({k: proof[k] for k in ('key', 'writer', 'session', 'ordinal',
                'canonical_positions', 'prepared_positions', 'index_status', 'canonical_sha256', 'raw_source_sha256')})
    return sessions, proofs


def load(inputs, config):
    if set(inputs) != INPUTS or config != CONFIG:
        raise ValueError('D38 canonical frozen contract differs')
    data = list(original.source({k: inputs[k] for k in original.INPUTS}))
    complete = read(inputs['content_complete'])
    path = Path(inputs['visibility'])
    relative = path.resolve().relative_to(Path(inputs['content_complete']).resolve().parent).as_posix()
    if complete['outputs'].get(relative) != sha256(path):
        raise ValueError('D38 visibility source changed')
    visibility = read(path)
    if len(visibility) != len(data[2]):
        raise ValueError('D38 visibility/vector coverage differs')
    data[0], proofs = canonicalize(data[0], data[1], visibility, canonical.load(inputs))
    root = Path(inputs['original_complete']).parent / 'output'
    bind_completed(inputs['original_complete'], root / 'BINDING.json')
    binding = read(root / 'BINDING.json')
    if binding['paths'] != {k: inputs[k] for k in original.INPUTS} or binding['config'] != original.CONFIG:
        raise ValueError('D38 original extraction binding differs')
    for filename, expected in binding['pins'].items():
        if sha256(filename) != expected:
            raise ValueError('D38 original source changed')
    bind_completed(inputs['original_complete'], root / 'WRITER_INDEX.json')
    entries = read_sealed(root / 'WRITER_INDEX.json')
    roster = sorted({s['writer'] for s in data[0]})
    if [r['writer'] for r in entries] != roster:
        raise ValueError('D38 original roster differs')
    saved = {}
    for entry in entries:
        path = root / entry['file']
        bind_completed(inputs['original_complete'], path)
        if sha256(path) != entry['sha256']:
            raise ValueError('D38 original writer changed')
        saved[entry['writer']] = read_sealed(path)
    return data, proofs, saved


def anchors(support, saved):
    old = {e['key']: e for e in saved['events']}
    if len(old) != len(saved['events']) or set(old) != {e['key'] for e in support['events']}:
        raise ValueError('D38 event support changed; no silent anchor substitution')
    for event in support['events']:
        prior = old[event['key']]
        if hashlib.sha256(event['text'].encode('utf8')).hexdigest() != prior['text_sha256']:
            raise ValueError('D38 deleted span changed')
        for field in ('session', 'phase', 'ordinal', 'source_span_ordinal', 'original_codepoints', 'deleted_codepoints'):
            if event[field] != prior[field]:
                raise ValueError('D38 event provenance changed')
        # Windows and offer sets must be identical; only selected outcomes may change.
        for phase in ('before', 'after'):
            strip = lambda rows: [{k:v for k,v in r.items() if k != 'chosen'} for r in rows]
            if strip(event['window'][phase]) != strip(prior['window'][phase]):
                raise ValueError('D38 temporal window changed')
    return [old[e['key']]['anchor'] for e in support['events']], [old[e['key']]['token_scope'] for e in support['events']]


def permutation_values(unit, menus, vectors, config):
    eligible = [e for e in unit['events'] if e['primary']['eligible']]
    phases = {e['phase'] for e in eligible}
    if phases != {'early', 'late'}:
        return None
    values = []
    for index in range(config['permutations']):
        shuffled = original.shuffle_choices(menus, unit['writer'], config['permutation_seed'] + index)
        buckets = defaultdict(list)
        for event in eligible:
            score = original.gradient(event['window'], event['anchor'], vectors, shuffled)
            if not score['eligible']:
                raise ValueError('D38 permutation changed outcome-independent support')
            buckets[(event['phase'], event['session'])].append(score['gradient'])
        means = {phase: np.mean([np.mean(v) for (p,s),v in sorted(buckets.items()) if p == phase])
                 for phase in ('early', 'late')}
        values.append(float(means['late'] - means['early']))
    return values


def writer_unit(writer, data, saved, config):
    support = original.writer_support(writer, *data, config)
    anchor, scopes = anchors(support, saved)
    unit = original.score_writer(support, anchor, scopes, data[2])
    menus = []
    for session in data[0]:
        if session['writer'] != writer:
            continue
        for row in session['rows']:
            menu, reason = original.eligible_menu(row, data[1][row['key']], data[2])
            if reason is None:
                menus.append(menu)
    unit['permutation_values'] = permutation_values(unit, menus, data[2], config)
    return unit


def summarize(units, proofs, config):
    result = original.summarize(units, config)
    values = [u['permutation_values'] for u in units if u['permutation_values'] is not None]
    if not values:
        raise ValueError('D38 no paired supported writers')
    reference = np.asarray(values).mean(axis=0)
    if len(reference) != config['permutations'] or not np.isfinite(reference).all():
        raise ValueError('D38 incomplete permutation reference')
    mean, sd = float(reference.mean()), float(reference.std(ddof=1))
    result.update(card='D38-canonical', canonical_successor=True,
        source_audit=dict(decisions=len(proofs), changed=sum(p['index_status']=='proven_disjoint_choice' for p in proofs)),
        repeated_outcome_control=dict(draws=reference.tolist(), mean=mean, sd=sd,
            bias_flag=abs(mean) > .25 * sd, permutation_seed=config['permutation_seed'],
            method='Within writer and offered-menu size; fixed eligibility and equal event/session/half/writer weights'),
        fake_writer_control='Not applicable: population mean early-late contrast, no writer-identification claim',
        anchor_policy='Authenticated unchanged original deleted-span embeddings reused; no encoder refit',
        original_preserved=True)
    return result


def execute(output, inputs, config):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    if (output/'SUMMARY.json').exists():
        raise ValueError('Completed canonical D38 is immutable')
    with threadpool_limits(limits=1):
        started = time.monotonic()
        data, proofs, saved = load(inputs, config)
        save(output/'BINDING.json', dict(inputs=input_hashes(inputs), config=config))
        save(output/'SOURCE_CHOICE_AUDIT.json', proofs)
        units = []; roster = sorted(saved)
        for i, writer in enumerate(roster, 1):
            path = output/'writers'/(hashlib.sha256(writer.encode()).hexdigest()[:24]+'.json')
            if original.sealed(path):
                unit = read_sealed(path)
            else:
                if (output/'YIELD_REQUEST.json').exists():
                    return dict(status='yielded', writers_saved=len(units), writers_total=len(roster))
                unit = writer_unit(writer, data, saved[writer], config)
                save(path, unit)
            units.append(unit)
            if i >= max(1, math.ceil(.1*len(roster))) and not (output/'FIRST_TENTH.json').exists():
                write(output/'FIRST_TENTH.json', dict(completed_writers=i,total_writers=len(roster),
                    projected_seconds=2*(time.monotonic()-started)*len(roster)/i, includes_fresh_verification=True))
        report = summarize(units, proofs, config)
        save(output/'SUMMARY.json', report)
        return report


def verify(output, inputs, config):
    output = Path(output)
    with threadpool_limits(limits=1):
        data, proofs, saved = load(inputs, config)
        assert_close(read_sealed(output/'BINDING.json'), dict(inputs=input_hashes(inputs), config=config))
        assert_close(read_sealed(output/'SOURCE_CHOICE_AUDIT.json'), proofs)
        units = []
        for writer in sorted(saved):
            unit = writer_unit(writer, data, saved[writer], config)
            path = output/'writers'/(hashlib.sha256(writer.encode()).hexdigest()[:24]+'.json')
            assert_close(read_sealed(path), unit); units.append(unit)
        report = summarize(units, proofs, config)
        assert_close(read_sealed(output/'SUMMARY.json'), report)
    return dict(verified=True, fresh_source_replay=True, all_200_permutations_recomputed=True,
                original_primary_retained=True, scientific_admission=False)
