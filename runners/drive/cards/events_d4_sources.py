"""D4 authenticated frozen correction vectors and strictly later choices."""
import gzip
import json
from collections import Counter
from pathlib import Path
import numpy as np
from .events_p5 import filehash, read, classify
from .menus_p4 import chronological_partitions, recipient_split

INPUTS = {'sessions', 'content_records', 'content_vectors', 'content_model', 'content_complete',
          'p5_index', 'p5_summary', 'p5_inputs', 'p5_completion'}


def bind_completed(completion, path):
    receipt = read(completion)
    if receipt.get('status') != 'COMPLETE' or not receipt.get('fresh_process_verified'):
        raise ValueError('P5 completion is not independently verified')
    relative = Path(path).resolve().relative_to(Path(completion).resolve().parent).as_posix()
    if receipt['outputs'].get(relative) != filehash(path):
        raise ValueError('P5 artifact is not bound by completion')


def source(inputs):
    if set(inputs) != INPUTS:
        raise ValueError('explicit D4 input set differs')
    for key in ('p5_index', 'p5_summary', 'p5_inputs'):
        bind_completed(inputs['p5_completion'], inputs[key])
    binding = read(inputs['p5_inputs'])
    for key in ('sessions', 'content_model'):
        if Path(binding['paths'][key]).resolve() != Path(inputs[key]).resolve() or binding['sha256'][key] != filehash(inputs[key]):
            raise ValueError('P5 session/model binding differs')
    content = read(inputs['content_complete'])
    if content.get('status') != 'COMPLETE':
        raise ValueError('CONTENT_V2 incomplete')
    for key in ('content_records', 'content_vectors', 'content_model'):
        matches = [digest for name, digest in content['outputs'].items() if Path(name).name == Path(inputs[key]).name]
        if matches != [filehash(inputs[key])]:
            raise ValueError('CONTENT_V2 binding differs')
    sessions, records, index = read(inputs['sessions']), read(inputs['content_records']), read(inputs['p5_index'])
    session_map = {s['session']: s for s in sessions}
    if len(session_map) != len(sessions) or len({s['session'] for s in index}) != len(index) or set(session_map) != {s['session'] for s in index}:
        raise ValueError('P5/source session coverage differs')
    if read(inputs['p5_summary'])['sessions'] != len(index):
        raise ValueError('P5 session census differs')
    menus = {r['key']: r for s in sessions for r in s['rows']}
    records_map = {r['key']: r for r in records}
    if len(menus) != sum(len(s['rows']) for s in sessions) or len(records_map) != len(records) or set(menus) != set(records_map):
        raise ValueError('CONTENT_V2 decision coverage differs')
    vectors = np.load(inputs['content_vectors'], mmap_mode='r', allow_pickle=False)
    if vectors.ndim != 2 or vectors.shape[1] != 384:
        raise ValueError('CONTENT_V2 dimensions differ')
    splits, excluded = chronological_partitions(sessions)
    return dict(sessions=session_map, records=records_map, vectors=vectors,
        index={s['session']: s for s in index}, splits=splits, excluded=excluded,
        p5_root=Path(inputs['p5_index']).parent)


def choices(sessions, records, vectors):
    rows, exclusions = [], []
    for session in sorted(sessions, key=lambda s: (s['timestamp'], s['session'])):
        for menu in sorted(session['rows'], key=lambda r: (r['open_at'], r['key'])):
            reason = None
            if menu['handling'] not in ('accept', 'edit'):
                reason = 'no selected choice for ' + menu['handling']
            elif len(menu['menu']) < 2:
                reason = 'fewer than two displayed options'
            selected = [i for i, text in enumerate(menu['menu']) if text == menu['inserted']]
            if reason is None and len(selected) != 1:
                reason = 'selected original option missing or ambiguous'
            if reason:
                exclusions.append(dict(session=session['session'], key=menu['key'], reason=reason))
                continue
            feature = records[menu['key']]
            if feature['writer'] != session['writer'] or feature['session'] != session['session'] or len(feature['options']) != len(menu['menu']):
                raise ValueError('choice/source identity differs')
            array = vectors[feature['options']]
            if not np.isfinite(array).all() or not np.allclose(np.linalg.norm(array, axis=1), 1, atol=1e-5, rtol=0):
                raise ValueError('invalid choice vectors')
            rows.append(dict(key=menu['key'], session=session['session'], writer=session['writer'],
                chosen=selected[0], options=feature['options'], handling=menu['handling'], open_at=menu['open_at']))
    return rows, exclusions


def corrections(saved, vectors, decisions):
    """Classify before examining outcomes; exact P5 split, no threshold rescue."""
    rows, units, exclusions = [], [], []
    audit = Counter()
    for edit in sorted(saved['edits'], key=lambda e: e['ordinal']):
        audit['all'] += 1
        before, after = vectors[edit['before_vector']], vectors[edit['after_vector']]
        rebuilt = classify(edit['before'], edit['after'], before, after, edit['finite_verbs_before'], edit['finite_verbs_after'])
        if rebuilt != {k: edit[k] for k in rebuilt}:
            raise ValueError('frozen P5 deterministic split differs')
        reason, key = None, None
        if edit['split'] == 'excluded':
            reason = 'outside both deterministic classes'
        elif edit['origin'] == 'model':
            if any(n > 0 for origin, n in edit['deleted_origin_counts'].items() if origin != 'accepted'):
                reason = 'mixed changed-span provenance'
            elif len(edit['accepted_owners_touched']) != 1:
                reason = 'multiple accepted owners'
            else:
                owner = edit['accepted_owners_touched'][0]
                decision = decisions.get(owner)
                if decision is None or owner >= edit['ordinal']:
                    reason = 'missing or nonpreceding exact accepted owner'
                elif decision['handling'] != 'edit':
                    reason = 'linked model span not accepted-then-edited'
                else:
                    key = decision['key']
        elif edit['origin'] == 'own':
            if edit['accepted_owners_touched'] or not edit['deleted_origin_counts'] or set(edit['deleted_origin_counts']) != {'typed'}:
                reason = 'own text lacks exclusive typed changed-span provenance'
        else:
            reason = 'unsupported correction origin'
        delta = np.asarray(after, float) - np.asarray(before, float)
        norm = float(np.linalg.norm(delta))
        if not np.isfinite(delta).all():
            raise ValueError('nonfinite correction delta')
        if reason is None and norm <= 1e-12:
            reason = 'zero embedding delta'
        if reason:
            audit[reason] += 1
            exclusions.append(dict(session=saved['session'], ordinal=edit['ordinal'], reason=reason,
                                   origin=edit['origin'], split=edit['split']))
            continue
        audit[edit['origin'] + '_' + edit['split']] += 1
        rows.append(dict(session=saved['session'], ordinal=edit['ordinal'], origin=edit['origin'],
            split=edit['split'], key=key, before_vector=edit['before_vector'], after_vector=edit['after_vector']))
        units.append(delta / norm)
    return rows, np.asarray(units, float).reshape((-1, 384)), exclusions, dict(audit)


def writer_data(writer, source_data, config):
    partition = recipient_split(writer, source_data['splits'])
    own = partition['own_train']
    metadata = dict(writer=writer, partition={name: [s['session'] for s in partition[name]]
        for name in ('own_train', 'calibration', 'test')}, cutoff=partition['cutoff'], test_cutoff=partition['test_cutoff'],
        excluded_future_training=partition['excluded_future_training'],
        excluded_overlapping_calibration=partition['excluded_overlapping_calibration'], exclusion=partition['reason'])
    if partition['reason']:
        return dict(**metadata, corrections=[], correction_exclusions=[], audit={}, source_pins={},
                    calibration=[], test=[], choice_exclusions=[], support={}), np.empty((0, 384))
    rows, blocks, excluded, pins, audit = [], [], [], {}, Counter()
    for session in own:
        entry = source_data['index'][session['session']]
        root = source_data['p5_root']
        for name, digest in (('file', 'sha256'), ('vectors', 'vectors_sha256')):
            path = (root / entry[name]).resolve()
            path.relative_to(root.resolve())
            if filehash(path) != entry[digest]:
                raise ValueError('P5 training checkpoint changed')
            pins[str(path)] = entry[digest]
        with gzip.open(root / entry['file'], 'rt', encoding='utf8') as f:
            saved = json.load(f)
        if any(saved[k] != session[k] for k in ('writer', 'session', 'timestamp', 'end_at')):
            raise ValueError('P5 training session identity differs')
        vectors = np.load(root / entry['vectors'], allow_pickle=False)
        decisions = {r['ordinal']: r for r in session['rows']}
        if len(decisions) != len(session['rows']):
            raise ValueError('ambiguous accepted-owner ordinal')
        rr, uu, ee, aa = corrections(saved, vectors, decisions)
        rows.extend(rr); blocks.append(uu); excluded.extend(ee); audit.update(aa)
    units = np.concatenate(blocks) if blocks else np.empty((0, 384))
    calibration, excluded_cal = choices(partition['calibration'], source_data['records'], source_data['vectors'])
    test, excluded_test = choices(partition['test'], source_data['records'], source_data['vectors'])
    support = {}
    for origin in ('model', 'own'):
        support[origin] = {}
        for split in ('content', 'housekeeping'):
            indices = [i for i, r in enumerate(rows) if r['origin'] == origin and r['split'] == split]
            sessions = sorted({rows[i]['session'] for i in indices})
            support[origin][split] = dict(indices=indices, corrections=len(indices), sessions=sessions,
                eligible=len(indices) >= config['minimum_corrections'] and len(sessions) >= config['minimum_training_sessions'])
    if not all(support['model'][s]['eligible'] for s in support['model']):
        metadata['exclusion'] = 'fewer than five corrections or two training sessions in either model class'
    elif not calibration or not test:
        metadata['exclusion'] = 'empty eligible calibration or test choices'
    return dict(**metadata, corrections=rows, correction_exclusions=excluded, audit=dict(audit), source_pins=pins,
                calibration=calibration, test=test, choice_exclusions=excluded_cal + excluded_test, support=support), units
