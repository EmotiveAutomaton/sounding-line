"""Prospective known-answer and hostile dependence qualification, constructed only."""
import json
import os
from pathlib import Path
import numpy as np
from runners.drive.cards import week6_in14_person_v1 as person
from runners.drive.cards import week6_in14_person_fixture_v1 as fixture
from runners.drive.cards import week6_in14_math_v1 as carry


def test_shared_boundary_covariance_changes_correction_and_keeps_raw_ratio():
    observed = np.array([[1.5, 0., 0.], [0., 2., 1.], [0., 1., 2.]])
    sampling = np.array([[1., 0., 0.], [0., 1., 1.], [0., 1., 1.]])
    answer = person.corrected_moments(observed, sampling, .4 / np.sqrt(3))
    assert answer['half_diagnostic'] == 0
    assert np.isclose(answer['full_reliability'], 1 / 3)
    assert np.isclose(answer['adjusted_trait_relation'], .4)
    observed[1, 2] = observed[2, 1] = 1.8
    sampling[1, 2] = sampling[2, 1] = .2
    assert np.isclose(person.corrected_moments(observed, sampling)['half_diagnostic'], 1.6)
    observed[1, 1] = 1.
    assert person.corrected_moments(observed, sampling)['status'] == 'nonpositive_variance'


def test_whole_trajectory_boundary_and_independent_dense_covariance():
    frame, _ = fixture.world(.5, 'survey_measurement_ma1', writers=12)
    left = person.prepare(frame); right = person.prepare(frame, True)
    noise = person.nuisance(left, dict.fromkeys([p['writer'] for p in left], 1))
    for a, b in zip(left, right):
        assert a['failure'] is None and b['failure'] is None
        assert np.allclose(a['coefficients'], b['coefficients'], atol=1e-8, rtol=0)
        assert np.allclose(person.covariance(a, noise), person.covariance(b, noise, True), atol=1e-8, rtol=0)
    actual = person.evaluate(left); replay = person.evaluate(right, independent=True)
    assert np.allclose(actual['corrected_covariance'], replay['corrected_covariance'], atol=1e-8, rtol=0)
    rows = frame.loc[frame.prolific_id == 'w0']
    for t in range(3):
        assert np.array_equal(rows.loc[rows.raw_pair_ordinal == t, 'outcome'], rows.loc[rows.raw_pair_ordinal == t+1, 'baseline'])


def test_person_primary_population_and_rank_refusal():
    frame, _ = fixture.world(0., 'iid_innovations', writers=12)
    frame.loc[(frame.prolific_id == 'w0') & frame.raw_pair_ordinal.eq(0), 'gap_minutes'] = 20
    assert 'w0' not in {p['writer'] for p in person.prepare(frame)}
    assert 'w0' not in {p['prolific_id'] for p in carry.person_preparation(frame)}
    frame['baseline'] = 1.
    result = person.evaluate(person.prepare(frame))
    assert result['status'] == 'unsupported' and result['reason'] == 'person fit failure'


def test_raw_ordinal_gap_not_compressed():
    frame, _ = fixture.world(.5, 'iid_innovations', writers=12)
    frame = frame.loc[~(frame.prolific_id.eq('w1') & frame.raw_pair_ordinal.eq(3))]
    record = next(p for p in person.prepare(frame) if p['writer'] == 'w1')
    assert record['ordinals'].tolist() == [0, 1, 2, 4, 5, 6, 7]
    noise = {'phi': .4, 'feeling_correlation': np.eye(11)}
    covariance = person.covariance(record, noise)
    compressed = {**record, 'ordinals': np.arange(7)}
    assert not np.allclose(covariance, person.covariance(compressed, noise), atol=1e-10, rtol=0)


def test_frozen_all_nine_worlds_qualify_or_preserve_instrument_failure(tmp_path):
    report = fixture.calibration()
    destination = Path(os.environ.get('IN14_CALIBRATION_REPORT', str(tmp_path / 'CALIBRATION.json')))
    destination.write_bytes((json.dumps(report, indent=2, allow_nan=False) + '\n').encode())
    assert report['all_nine_worlds_retained']
    failed = [(w['family'], w['target'], w['estimate'].get('half_diagnostic'), w['estimate'].get('trait', {}).get('adjusted_relation')) for w in report['worlds'] if not w['passed']]
    assert report['qualified'], f'Instrument held; fixed world failures: {failed}'
