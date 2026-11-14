"""Constructed checks only. Full 2,000-draw native qualification is separate."""
from copy import deepcopy
from pathlib import Path
import itertools
import math
import numpy as np
import pytest
from runners.drive.cards import week5_rf_analysis_v3 as analysis
from runners.drive.cards import week5_rf_consumer_fixture_v1 as fixture
from runners.drive.cards import week5_rf_qualified_v1 as qualified
from runners.drive.cards import week5_rf_cp_source_v1 as source
from runners.drive.cards import week5_rf_math_fixture_v2 as math_fixture
from runners.drive.cards import week5_rf_statistics_v2 as stats
from runners.drive.cards import week5_rf_prefix_v1 as prefix


@pytest.fixture(scope='module')
def prepared(tmp_path_factory):
    root = tmp_path_factory.mktemp('rf-source')
    spec = fixture.prepare(root, 'three-read')
    rows, mapping, support = qualified.load(spec['inputs'], spec['config'])
    return root, spec, rows, mapping, support


def test_actual_authored_source_to_primary_matches_original_kernel(prepared):
    _, _, raw, mapping, _ = prepared
    rows, support = qualified.ordered_elections(raw, mapping)
    assert len(rows) == 320 and support['counts']['candidate_clusters'] == 40
    result = analysis.primary(rows, reference=True)
    original = stats.election_losses(rows)
    assert abs(result['primary']-original['primary']) < 1e-10
    gap = result['mean_election_log_losses']['TWO-A']-result['mean_election_log_losses']['THREE']
    assert abs(gap-math_fixture.hand_margin()) < 1e-10
    assert all(row['early']['comments'] == 10 and row['early_support'] == .5 for row in rows)


def test_current_snap_null_ids_cannot_be_elections(prepared):
    _, _, rows, _, _ = prepared
    assert all(r['election'] is None and r['election_identity_qualified'] is False for r in rows.values())
    with pytest.raises(ValueError, match='explicit election assignment'):
        qualified.validate_assignments(rows, [{'comment_id': k, 'election_id': r['election']} for k, r in rows.items()])


def test_explicit_map_must_cover_source_exactly(prepared):
    _, _, rows, mapping, _ = prepared
    assignments = [{'comment_id': k, 'election_id': v} for k, v in mapping.items()]
    with pytest.raises(ValueError, match='cover every'):
        qualified.validate_assignments(rows, assignments[:-1], True)
    with pytest.raises(ValueError, match='Duplicate'):
        qualified.validate_assignments(rows, assignments+[assignments[0]], True)
    with pytest.raises(ValueError, match='salted'):
        qualified.validate_assignments(rows, assignments, False)


def test_missing_or_changed_native_qualification_refuses(prepared):
    _, spec, _, _, _ = prepared
    with pytest.raises(ValueError, match='identity changed'):
        qualified.load(spec['inputs'], dict(spec['config'], identity_native_complete_sha256='0'*64))
    with pytest.raises(ValueError, match='review changed'):
        qualified.load(spec['inputs'], dict(spec['config'], identity_review_sha256='0'*64))
    with pytest.raises(ValueError):
        qualified.load(spec['inputs'], dict(spec['config'], constructed_fixture=False))


def test_neutrals_stay_in_split_and_marker_denominator(prepared):
    _, _, raw, mapping, _ = prepared
    election = next(iter(mapping.values()))
    rows = {k: deepcopy(v) for k, v in raw.items() if mapping[k] == election}
    ordered = sorted(rows.values(), key=lambda r: r['ordinal'])
    ordered[0]['vote'] = 0
    ordered[-1]['vote'] = 0
    got, _ = qualified.ordered_elections(rows, {k: election for k in rows})
    assert got[0]['early']['comments'] == 10
    assert got[0]['early_support'] == 4/9
    assert got[0]['later_support']+got[0]['later_oppose'] == 19
    assert got[0]['later_neutral'] == 1


def test_below_floor_pooled_route_needs_no_five_candidate_folds():
    rows = math_fixture.planted_rows(candidates=3)
    value = analysis.evaluate(rows, reference=True)
    assert value['primary_fit']['mode'] == 'pooled_descriptive'
    result = analysis.summarize(value, [])['primary']
    assert result['status'] == 'below_floor_descriptive' and result['interval'] is None


def test_absent_three_read_case_is_not_an_empirical_null():
    rows = math_fixture.planted_rows()
    for row in rows:
        for counts in row['early']['reads'].values():
            for key in counts:
                counts[key] = 0
    value = analysis.evaluate(rows)
    assert value['primary_fit']['primary'] is None
    assert analysis.summarize(value, [])['primary']['status'] == 'design_cannot_test'


def test_candidate_weight_replay_preserves_all_elections():
    rows = math_fixture.planted_rows()
    for index in (0, 999, 1999):
        expected = stats.bootstrap_weights([r['candidate'] for r in rows], index)
        assert np.array_equal(expected, analysis.independent_weights(rows, index))
        assert all(len(set(expected[i:i+8])) == 1 for i in range(0, len(rows), 8))


def test_secondary_probability_truth_and_no_mutation():
    rows = []
    for i, bits in enumerate(itertools.product((0, 1), repeat=6)):
        reads = {k: {'for_comments': 4*bits[2*j], 'against_comments': 4*bits[2*j+1],
            'overlap_comments': 0, 'for_mentions': 4*bits[2*j], 'against_mentions': 4*bits[2*j+1]}
            for j, k in enumerate(stats.READS)}
        rows.append({'election': f'constructed-{i}', 'candidate': f'constructed-{i%20}', 'year': 2010,
            'early_support': .5, 'later_support': 2 if bits[3] else 3, 'later_oppose': 4 if bits[3] else 3,
            'early': {'comments': 20, 'reads': reads}})
    before = deepcopy(rows)
    value = analysis.against(rows)
    expected = .5*((1/(1+2**.25)-.5)+(1/(1+2**1.25)-1/3))
    assert abs(value['contrasts']['trust']-expected) < 1e-10
    assert max(abs(value['contrasts'][k]) for k in ('respect', 'liking')) < 1e-10
    assert value['common_feasible_elections'] == 64 and value['excluded_elections'] == 0
    assert rows == before


def test_unidentified_against_is_not_a_zero_cost():
    value = analysis.against(math_fixture.planted_rows())
    assert all(v is None for v in value['contrasts'].values())
    assert all('unidentified' in why for why in value['unsupported'].values())
    assert value['common_feasible_elections'] == 40 and value['excluded_elections'] == 280


def test_checkpoint_resume_and_changed_global_index_refusal(tmp_path, prepared):
    _, spec, _, _, _ = prepared
    config = dict(spec['config'], max_new_draw_blocks=1)
    out = tmp_path/'analysis'
    assert analysis.execute(out, spec['inputs'], config)['status'] == 'yielded'
    first = (out/'draw-0000.json').read_bytes()
    assert analysis.execute(out, spec['inputs'], config)['status'] == 'yielded'
    assert (out/'draw-0000.json').read_bytes() == first
    assert (out/'draw-0004.json').exists()
    assert not (out/'independent-replay').exists()
    with pytest.raises(ValueError, match='Incomplete'):
        analysis.verify(out, spec['inputs'], config)
    block = analysis.read(out/'draw-0000.json')
    block['indices'][0] = 999
    (out/'draw-0000.json').write_bytes(source.canonical(block))
    (out/'draw-0000.seal.json').write_bytes(source.canonical({'sha256': source.sha(out/'draw-0000.json')}))
    with pytest.raises(ValueError, match='global indices'):
        analysis.execute(out, spec['inputs'], config)


def test_ancestor_resource_signal_yields_before_source_work(tmp_path):
    root = tmp_path/'native'
    root.mkdir()
    (root/'YIELD_REQUEST.json').write_text('{}', encoding='utf8')
    result = analysis.execute(root/'output/world/analysis', {}, {})
    assert result['status'] == 'yielded'
    assert not (root/'output/world/analysis/BINDING.json').exists()


def test_first_cost_prefix_has_fresh_complete_replay_without_full_claim(tmp_path, prepared):
    _, spec, _, _, _ = prepared
    config = dict(spec['config'], prefix_draws=4)
    out = tmp_path/'prefix'
    assert prefix.execute(out, spec['inputs'], config)['status'] == 'complete'
    original = (out/'PREFIX.json').read_bytes()
    assert prefix.execute(out, spec['inputs'], config)['status'] == 'complete'
    assert (out/'PREFIX.json').read_bytes() == original
    assert prefix.verify(out, spec['inputs'], config)['verified'] is True
    assert not (out/'analysis/ANALYSIS_COMPLETE.json').exists()
    receipt = analysis.read(out/'PREFIX.json')
    assert receipt['completed_global_draws'] == 4 and receipt['scientific_admission'] is False
