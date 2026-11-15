"""Constructed execute/verify source paths; no human source or native jobs."""
import gzip
import json
import numpy as np
import pytest

from runners.drive.cards import week6_la6_source_v1 as la
from runners.drive.cards import week6_la6_runner_v1 as runner
from runners.drive.cards import week6_dc1_source_v1 as dc
from runners.drive.cards import week6_dc1_runner_v1 as dc_runner
from runners.drive.cards import week5_qualification_io as io


def raw_act(meeting, name, start):
    return {'id': name, 'meeting': meeting, 'speaker': 'A', 'corpus': 'AMI',
            'act_type': 'statement', 'start': start, 'end': start + 1,
            'words': [{'kind': 'word', 'text': 'plain', 'start': start, 'end': start + .5}]}


def source_tree(tmp_path):
    root = tmp_path / 'original'; (root / 'output').mkdir(parents=True)
    acts = [raw_act(m, f'{m}-{i}', t) for m in ('M1', 'M2') for i, t in enumerate((0., 40.))]
    laughs = [{'meeting': m, 'speaker': 'B', 'start': 1., 'end': 1.5, 'label': 'vocal'} for m in ('M1', 'M2')]
    values = {'ACTS': acts, 'LAUGHS': laughs, 'METADATA': {m: {'corpus': 'AMI'} for m in ('M1', 'M2')}}
    pins = {}
    for name, value in values.items():
        path = root / 'output' / (name + '.json.gz')
        with gzip.open(path, 'wt', encoding='utf8') as stream:
            json.dump(value, stream)
        pins['output/' + path.name] = io.sha(path)
    io.write_json(root / 'COMPLETE.json', {'status': 'COMPLETE', 'fresh_process_verified': True, 'outputs': pins})
    return root


def test_all_utterances_including_first_survive_source_prepare_and_replay(tmp_path):
    root = source_tree(tmp_path); output = tmp_path / 'prepared'
    inputs = {'source_root': str(root)}; config = {'phase': 'LA6-prepare', 'max_new_meetings': 1}
    assert la.execute(output, inputs, config)['status'] == 'yielded'
    result = la.execute(output, inputs, config)
    assert result['all_original_utterances'] == 4 and result['matched_pairs'] == 2
    first = la.seal.read(output / 'meetings' / '00000.json')['all_utterance_features'][0]
    assert first['id'] == 'M1-0' and first['numeric'][1:4] == [0, 0., 0]
    assert la.verify(output, inputs, config)['status'] == 'yielded'
    assert la.verify(output, inputs, config)['verified']


def test_original_source_byte_mutation_fails_before_projection(tmp_path):
    root = source_tree(tmp_path)
    with (root / 'output' / 'ACTS.json.gz').open('ab') as stream:
        stream.write(b'changed')
    with pytest.raises(ValueError, match='source table changed'):
        la.load_source({'source_root': str(root)})


def test_runner_requires_exact_review_before_any_fit(tmp_path, monkeypatch):
    root = tmp_path / 'prepared'; root.mkdir()
    io.write_json(root / 'COMPLETE.json', {'fixture': True})
    review = tmp_path / 'review.json'; io.write_json(review, {'approved': True})
    monkeypatch.setattr(runner.seal, 'complete', lambda *args: (root, {}, {}))
    with pytest.raises(ValueError, match='Owner source/statistic review'):
        runner.load({'prepared_run': str(root), 'owner_review': str(review)})


def test_dc1_source_wrapper_retains_availability_hold_and_all_dispositions(tmp_path, monkeypatch):
    p = np.zeros((2, 30, 15)); p[:, :, 2] = 1; p[:, :, 3] = 4; p[:, :, 4] = -2
    p[:, :, 6] = np.arange(30) % 2; p[:, :, 7] = np.arange(30); p[:, :, 9] = np.nan
    p[:, [0, 2, 5, 7, 10, 12, 15, 17, 20, 22, 25, 29], 9] = 2
    data = {'plays': p, 'person': np.array([1, 2]), 'counter': np.array([1, 1])}
    monkeypatch.setattr(dc, 'load_parents', lambda inputs: (data, [1, 2], {'common_people': 2}, [1.] * 9, {'constructed': True}))
    monkeypatch.setattr(dc, 'BLOCK', 1)
    output = tmp_path / 'prepared'; config = {'phase': 'DC1-prepare', 'max_new_blocks': 1}
    assert dc.execute(output, {}, config)['status'] == 'yielded'
    result = dc.execute(output, {}, config)
    assert result['paired_occasions'] == 20 and result['all_rating_dispositions'] == 24
    assert not result['production_admitted'] and not result['human_outcome_fit']
    table = dc.seal.read(output / 'TABLE.json')
    assert set(table['offer_control_availability'].values()) == {'unknown_at_rating_time'}
    assert dc.verify(output, {}, config)['status'] == 'yielded'
    assert dc.verify(output, {}, config)['verified']


def test_repeat_projection_preserves_both_references_without_changing_recent():
    p = np.zeros((2, 30, 15)); p[:, :, 2] = 1; p[:, :, 3] = 4; p[:, :, 4] = -2
    p[:, :, 6] = np.arange(30) % 2; p[:, :, 7] = np.arange(30); p[:, :, 9] = np.nan
    p[:, [0, 2, 5, 7, 10, 12, 15, 17, 20, 22, 25, 29], 9] = 2
    data = {'plays': p, 'person': np.array([1, 1]), 'counter': np.array([1, 2]), '_dc1_earlier_reference': {1: 50.}}
    block = dc.project_block(data, [1], [1.] * 9)
    start = block['repeat_rows']['play_start']; earlier = block['repeat_rows']['best_observed_earlier_score']
    assert len(start) == len(earlier) == 10 and len(block['repeat_dispositions']) == 24
    assert start[0]['attempt'] == earlier[0]['attempt'] == 2
    assert start[0]['x'][dc.math.RECENT] == earlier[0]['x'][dc.math.RECENT]
    assert start[0]['x'][dc.math.LEVEL] == 3 and earlier[0]['x'][dc.math.BELOW] == -47
    assert len(block['person_source_arrays']) == 1


def test_TR1_fit_support_never_selects_the_prospective_roster_or_bridges_failed_pairs():
    p = np.zeros((6, 30, 15)); p[:, :, 2] = 1; p[:, :, 3] = 4; p[:, :, 4] = -2
    p[:, :, 6] = 1; p[:, :, 7] = np.arange(30); p[:, :, 9] = np.nan
    p[:, [0, 2, 5, 7, 10, 12, 15, 17, 20, 22, 25, 29], 9] = 2
    # Person 2's only middle play is unsupported. Valid endpoints must not form
    # a new consecutive pair; person 1 retains two supported consecutive pairs.
    p[4, :, 7] = 1
    data = {'plays': p, 'person': np.repeat([1, 2], 3), 'counter': np.tile([1, 2, 3], 2),
            'repeat_eligible': np.ones(6, bool)}
    people, supported, audit = dc.tr1_membership(data)
    assert people.tolist() == [1, 2]
    assert supported.tolist() == [1]
    assert audit['source_eligible']['people'] == 2
    assert audit['supported_analysis']['people_in_supported_pairs'] == 1
    assert audit['supported_analysis']['unsupported_pairs'] == 2


def test_dc1_runner_refuses_unresolved_offer_control_review(tmp_path, monkeypatch):
    root = tmp_path / 'prepared'; root.mkdir(); io.write_json(root / 'COMPLETE.json', {'fixture': True})
    review = dc_runner.review_contract(io.sha(root / 'COMPLETE.json'))
    review['offer_controls_known_at_rating_time'][dc.math.TERMS[0]] = False
    path = tmp_path / 'review.json'; io.write_json(path, review)
    monkeypatch.setattr(dc_runner.seal, 'complete', lambda *args: (root, {}, {}))
    with pytest.raises(ValueError, match='every next-offer availability'):
        dc_runner.load({'prepared_run': str(root), 'owner_review': str(path)})


def test_la6_runner_frozen_point_draws_match_array_ruler():
    rows = []
    for meeting in range(20):
        for label in (0, 1):
            for ordinal in range(15):
                rows.append({'meeting': str(meeting), 'id': f'{label}-{ordinal}', 'label': label,
                             'act_type': 'marked' if ordinal < (5 if label else 3) else 'base', 'numeric': [0.] * 9})
    base = runner.point(rows)
    one = runner.one_draw(rows, base, 0)
    assert one == runner.one_draw(rows, base, 0)
    for include in (True, False):
        assert base[str(include)]['auc'] == pytest.approx(17 / 30)
        assert one[str(include)]['auc'] == pytest.approx(17 / 30)
    summary = runner.summarize(base, [one] * 2000, 20)
    assert summary['with_laugh_history']['status'] == 'degenerate, descriptive'
    assert summary['with_laugh_history']['outcome'] is None


def test_dc1_runner_checkpoint_resumes_at_next_whole_person_draw(tmp_path, monkeypatch):
    rng = np.random.default_rng(23); x = rng.normal(size=(100, 9)); people = np.repeat(np.arange(5), 20)
    y = rng.integers(0, 2, 100); rating = rng.normal(size=100)
    rows = [{'x': a.tolist(), 'rating': float(b), 'choice': int(c), 'person': int(p)}
            for a, b, c, p in zip(x, rating, y, people, strict=True)]
    table = {'rows': rows, 'repeat_rows': {'play_start': [], 'best_observed_earlier_score': []},
             'person_source_arrays': [], 'source_identity': {}}
    monkeypatch.setattr(dc_runner, 'load', lambda inputs: (table, {'constructed': True}))
    output = tmp_path / 'analysis'; config = {'phase': 'DC1', 'max_new_draws': 1}
    assert dc_runner.execute(output, {}, config)['completed'] == 1
    assert dc_runner.execute(output, {}, config)['completed'] == 2
    state = dc_runner.seal.read(output / 'primary_first_play' / 'DRAWS.json')
    stats = dc.math.sufficient_statistics(x, rating, y, people)
    assert state['draws'] == [dc.math.bootstrap_draw(stats, 0), dc.math.bootstrap_draw(stats, 1)]
