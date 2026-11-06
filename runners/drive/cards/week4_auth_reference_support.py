"""Finite AUTH cache-support audit; never reads human scores.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 4-7 reread November 5.
NULL/ALTERNATIVE alike require every requested pair for exact cache reuse.
A missing requested pair disproves this route's completeness; zero missing in
one draw cannot license the full reference or any scientific inference.
"""
from collections import Counter
from pathlib import Path

from runners.stage14.common import read, filehash, digest
from .timing_p6 import write_equal
from . import week4_auth_pairs as pairs
from . import week3_identification_crossfit as roles


def configuration(mode):
    if mode not in ('constructed', 'full'):
        raise ValueError('fixed mode')
    return dict(mode=mode, seed=20261102, fold_seed=20261026, assignment_index=0,
                allocation=dict(pairs.configuration(mode),
                    **({'writers': 6, 'blocks_per_genre': 48} if mode == 'constructed' else {})))


def fixture():
    return [dict(session=f'{g}-{w}-{p}', writer=str(w), genre=g,
                 prompt=f'{g}-{p}', source_exact=True,
                 typed=dict(text=f'Constructed {g} writer{w} prompt{p}.', payload_words=4))
            for g in pairs.GENRES for w in range(6) for p in range(8)]


def check_assignment(sessions, folds, labels):
    by = {r['session']: r for r in sessions}
    if len(by) != len(sessions) or set(labels) != set(by):
        raise ValueError('session coverage')
    if set(folds) != {r['writer'] for r in sessions}:
        raise ValueError('writer fold coverage')
    original = Counter((r['genre'], r['prompt'], r['writer']) for r in sessions)
    changed = Counter((r['genre'], r['prompt'], labels[r['session']]) for r in sessions)
    if original != changed:
        raise ValueError('prompt/genre label counts changed')
    if any(folds[r['writer']] != folds[labels[r['session']]] for r in sessions):
        raise ValueError('role membership changed')
    return [dict(r, writer=labels[r['session']]) for r in sessions]


def coverage(requested, cached):
    ids = [r['pair_id'] for r in requested]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate requested pair')
    missing = sorted(set(ids) - set(cached))
    return dict(requested=len(ids), available=len(ids) - len(missing),
                missing=len(missing), all_requested_present=not missing), missing


def audit(sessions, saved, selection, config):
    original, rebuilt_selection, _ = pairs.draw(sessions, config['allocation'])
    if original != saved or rebuilt_selection != selection:
        raise ValueError('identity reconstruction changed')
    ids = {r['pair_id'] for r in original}
    excluded = selection['calibration'] + selection['fresh']
    if len(excluded) != len(set(excluded)) or not set(excluded) <= ids:
        raise ValueError('invalid excluded calibration bank')
    metadata = [{k: r[k] for k in ('session', 'writer', 'genre', 'prompt')} for r in sessions]
    folds = roles.writer_folds(metadata, config['fold_seed'])
    labels = roles.role_assignment(metadata, folds, config['assignment_index'], config['seed'])
    changed = check_assignment(sessions, folds, labels)
    private = dict(folds=folds, assignment=labels, reference_pair_ids=[], missing_optimistic=[], missing_main=[])
    common = dict(sessions=len(sessions), writers=len(folds), original_pairs=len(original),
                  excluded_pairs=len(excluded), eligible_main_pairs=len(ids-set(excluded)),
                  assignment_index=config['assignment_index'], assignment_sha256=digest(labels),
                  changed_session_labels=sum(labels[r['session']] != r['writer'] for r in sessions),
                  human_scores_used=False, scientific_admission=False, context_control_admission=False,
                  full_reference_validated=False, identity_reconstruction_verified=True)
    try:
        reference, _, _ = pairs.draw(changed, config['allocation'])
    except ValueError as error:
        return dict(common, disposition='reconstruction_unsupported', reason=str(error)), private
    optimistic, absent = coverage(reference, ids)
    main, main_absent = coverage(reference, ids-set(excluded))
    private.update(reference_pair_ids=sorted(r['pair_id'] for r in reference),
                   missing_optimistic=absent, missing_main=main_absent)
    by_genre = {}
    for genre in pairs.GENRES:
        selected = [r for r in reference if r['genre'] == genre]
        by_genre[genre] = dict(optimistic=coverage(selected, ids)[0], main=coverage(selected, ids-set(excluded))[0])
    state = 'missing_cached_pairs' if absent else 'single_draw_covered_full_reference_untested'
    return dict(common, disposition=state, optimistic=optimistic, main=main, by_genre=by_genre), private


def load(inputs, config):
    if config['mode'] == 'constructed':
        if inputs:
            raise ValueError('no external constructed inputs')
        sessions = fixture()
        saved, selection, _ = pairs.draw(sessions, config['allocation'])
        return sessions, saved, selection
    if set(inputs) != {'pairs_root', 'pairs_landing'}:
        raise ValueError('fixed pair source')
    root = Path(inputs['pairs_root']); landed = read(inputs['pairs_landing'])
    complete = read(root/'COMPLETE.json')
    if not complete['fresh_process_verified'] or not landed['full_write_through'] or landed['complete_sha256'] != filehash(root/'COMPLETE.json'):
        raise ValueError('unlanded pair source')
    for name in ('PLAN.json', 'output/PRIVATE_PAIRS.json', 'output/SELECTION.json'):
        if filehash(root/name) != complete['outputs'][name]:
            raise ValueError('pair source changed')
    plan = read(root/'PLAN.json')
    if plan['config'] != config['allocation']:
        raise ValueError('allocation configuration changed')
    return pairs.load(plan['inputs']), read(root/'output/PRIVATE_PAIRS.json'), read(root/'output/SELECTION.json')


def run(output, inputs, config, verification=False):
    if config != configuration(config['mode']):
        raise ValueError('fixed audit configuration')
    sessions, saved, selection = load(inputs, config)
    if verification:
        sessions = list(reversed(sessions))
    summary, private = audit(sessions, saved, selection, config)
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    for name, value in [('SUMMARY.json', summary), ('PRIVATE_WITNESSES.json', private)]:
        if verification:
            if read(output/name) != value:
                raise ValueError('complete fresh support replay differs')
        else:
            write_equal(output/name, value)
    return dict(verified=True, complete_support_replay=True, scientific_admission=False)


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, True)
