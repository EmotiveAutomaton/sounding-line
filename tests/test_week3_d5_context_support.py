"""Explicit donor oracle, fixed populations and actual completed-source boundary."""
from copy import deepcopy
from pathlib import Path
import pytest
from runners.stage14.common import read, freeze, filehash
from runners.drive.cards.timing_p6 import gzread, gzip_equal
from runners.drive.cards import week3_d5_context_support as card
from tests.test_week3_d5_reference_plans import fixture


def oracle(rows, folds, roster, assignment, independent):
    # Deliberately search actual donor rows for each target; no count-table reuse.
    halves, excluded = card.split_sessions(rows, assignment)
    result = []
    for fold in range(3) if independent else [None]:
        gallery = [w for w in roster if fold is None or folds[w] != fold]
        probes = [w for w in roster if fold is None or folds[w] == (fold+1) % 3]
        channels = {}
        for ch in card.reference.CHANNELS:
            parts = card.reference.source.COMPONENTS[ch]
            missing_gallery = [w for w in gallery if any(not any(r['support'][c] for r in halves.get(w, [[], []])[1]) for c in parts)]
            eligible = {w: [r for r in halves.get(w, [[], []])[0] if all(r['support'][c] for c in parts)] for w in probes}
            requirements = [(w, r, c, 'gallery') for w in gallery for r in halves.get(w, [[], []])[1] for c in parts if r['support'][c]]
            requirements += [(w, r, c, 'probe') for w in probes for r in eligible[w] for c in parts]
            missing = []
            for w, r, c, side in requirements:
                donors = [d for d in rows if d['prompt'] == r['prompt'] and d['support'][c]
                          and (folds[assignment[d['session']]] == fold if independent else assignment[d['session']] != w)]
                if not donors: missing.append([r['session'], c, side])
            no_probe = [w for w in probes if not eligible[w]]
            channels[ch] = dict(missing_gallery_writers=missing_gallery, missing_probe_writers=no_probe,
                missing_context_terms=missing, required_context_terms=len(requirements),
                probe_sessions=sum(map(len, eligible.values())), supported=not (missing_gallery or no_probe or missing))
        result.append(dict(donor_fold=fold, gallery_writers=gallery, probe_writers=probes, channels=channels))
    return dict(rotations=result, split_excluded=excluded)


def producer(tmp_path):
    root = tmp_path/'reference'; root.mkdir()
    p = root/'FIXTURE.json'; freeze(p, fixture())
    inputs = dict(fixture=str(p))
    freeze(root/'PLAN.json', dict(module=card.reference.__name__, config=card.reference.CONSTRUCTED, inputs=inputs))
    card.reference.execute(root/'output', inputs, card.reference.CONSTRUCTED)
    card.reference.verify(root/'output', inputs, card.reference.CONSTRUCTED)
    freeze(root/'COMPLETE.json', dict(status='COMPLETE', fresh_process_verified=True,
        outputs={p.relative_to(root).as_posix(): filehash(p) for p in root.rglob('*') if p.is_file()}))
    return dict(reference_complete=str(root/'COMPLETE.json'))


def test_exact_donor_oracle_for_real_and_reassigned_missingness():
    f = fixture(); rows = f['rows']; folds = f['writer_folds']; roster = sorted(folds)
    for i, r in enumerate(rows):
        if i % 3 == 0: r['support']['rhythm'] = False
        if r['prompt'] == 'p1' and folds[r['writer']] == 0: r['support']['final'] = False
    for independent in (False, True):
        for index in (None, 0, 5):
            assignment = ({r['session']: r['writer'] for r in rows} if index is None else
                          card.reference.label_draw(rows, folds, index, 20261026, independent))
            assert card.inspect_support(rows, folds, roster, assignment, independent) == oracle(rows, folds, roster, assignment, independent)


def test_missing_donor_cannot_drop_target_or_change_gallery():
    f = fixture(); rows = f['rows']; folds = f['writer_folds']; roster = sorted(folds)
    baseline = card.inspect_support(rows, folds, roster, independent=True)['rotations'][0]
    for r in rows:
        if r['prompt'] == 'p1' and folds[r['writer']] == 0: r['support']['final'] = False
    state = card.inspect_support(rows, folds, roster, independent=True)['rotations'][0]
    before, after = baseline['channels']['final'], state['channels']['final']
    assert before['supported'] and not after['supported']
    assert before['required_context_terms'] == after['required_context_terms']
    assert before['probe_sessions'] == after['probe_sessions']
    assert not after['missing_gallery_writers'] and not after['missing_probe_writers']
    assert len(after['missing_context_terms']) == 4
    assert state['gallery_writers'] == baseline['gallery_writers']


def test_literal_exclusion_and_fixed_candidate_failure():
    f = fixture(); rows = f['rows']; folds = f['writer_folds']; roster = sorted(folds)
    for r in rows:
        if r['prompt'] == 'p0' and r['writer'] != 'w0': r['support']['final'] = False
    ch = card.inspect_support(rows, folds, roster)['rotations'][0]['channels']['final']
    assert ['w0p0', 'final', 'probe'] in ch['missing_context_terms'] and not ch['supported']
    for r in rows:
        if r['writer'] == 'w0': r['support']['final'] = False
    state = card.inspect_support(rows, folds, roster)['rotations'][0]
    assert state['gallery_writers'] == roster
    assert state['channels']['final']['missing_gallery_writers'] == ['w0']
    assert state['channels']['final']['missing_probe_writers'] == ['w0']


def test_role_overlap_and_incomplete_boolean_support_refuse():
    f = fixture(); rows = f['rows']; folds = f['writer_folds']; roster = sorted(folds)
    assignment = {r['session']: r['writer'] for r in rows}; assignment['w0p0'] = 'w1'
    with pytest.raises(ValueError, match='Role overlap'):
        card.inspect_support(rows, folds, roster, assignment, True)
    rows[0]['support']['final'] = 1
    with pytest.raises(ValueError, match='boolean support'): card.inspect_support(rows, folds, roster)


def test_actual_handler_complete_replay_reentry_and_yield(tmp_path):
    inputs = producer(tmp_path); out = tmp_path/'out'
    assert card.execute(out, inputs, card.CONSTRUCTED)['status'] == 'complete'
    before = {p.name: p.read_bytes() for p in out.iterdir() if p.name != 'PROGRESS.json'}
    assert card.verify(out, inputs, card.CONSTRUCTED)['full_fresh_context_support_replay']
    card.execute(out, inputs, card.CONSTRUCTED)
    assert before == {p.name: p.read_bytes() for p in out.iterdir() if p.name != 'PROGRESS.json'}
    summary = read(out/'SUMMARY.json')
    assert not summary['scientific_admission'] and not summary['effect_computed']
    for name in ('literal', 'independent'):
        assert len(gzread(out/(name+'-CONTEXT_SUPPORT.json.gz'))) == 24
        assert summary['unsupported_reference_draws'][name]['human1024'] == 24
        assert summary['unsupported_reference_draws'][name]['final'] == 0
    pause = tmp_path/'pause'; pause.mkdir(); freeze(pause/'YIELD_REQUEST.json', {})
    assert card.execute(pause, inputs, card.CONSTRUCTED)['status'] == 'yielded'
    assert not (pause/'SUMMARY.json').exists()


def test_frozen_assignment_and_context_output_tamper_refuse(tmp_path):
    inputs = producer(tmp_path); rows, folds, roster, banks, _ = card.load(inputs, card.CONSTRUCTED)
    bank = deepcopy(banks['literal']); bank['assignments'][0][0] = 99
    with pytest.raises(ValueError, match='Invalid saved assignment'):
        card.assignment_for(rows, folds, bank, 0, 20261026, False)
    bank = deepcopy(banks['literal']); bank['assignments'][0][0] = (bank['assignments'][0][0]+1) % 6
    with pytest.raises(ValueError, match='frozen seed'):
        card.assignment_for(rows, folds, bank, 0, 20261026, False)
    out = tmp_path/'out'; card.execute(out, inputs, card.CONSTRUCTED)
    p = out/'REAL_CONTEXT_SUPPORT.json.gz'; state = gzread(p); state['literal']['rotations'][0]['channels']['final']['supported'] = False
    p.unlink(); gzip_equal(p, state)
    with pytest.raises(ValueError, match='replay differs'): card.verify(out, inputs, card.CONSTRUCTED)


def test_actual_full_producer_and_changed_source_refusal(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    terminal = repo/'results/phase_2_4_stage_15/raw/drive-week3-20261025/D5-reference-plans/COMPLETE.json'
    rows, folds, roster, banks, pins = card.load(dict(reference_complete=str(terminal)), card.CONFIG)
    assert len(rows) == 1399 and len(folds) == 61 and len(roster) == 45 and len(pins) > 2800
    for name in ('literal', 'independent'):
        assert len(banks[name]['assignments']) == 1000
        card.assignment_for(rows, folds, banks[name], 0, 20261026, name == 'independent')
    freeze(tmp_path/'COMPLETE.json', read(terminal))
    plan = read(terminal.parent/'PLAN.json'); plan['module'] = 'wrong'
    freeze(tmp_path/'PLAN.json', plan)
    with pytest.raises(ValueError, match='reference bytes'):
        card.load(dict(reference_complete=str(tmp_path/'COMPLETE.json')), card.CONFIG)
