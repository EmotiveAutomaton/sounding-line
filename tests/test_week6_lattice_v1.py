import copy
import pytest
from runners.drive.cards import week6_lattice_v1 as m


def register():
    return [dict(row=i, source='diary-'+str(i), source_group='diary-'+str(i),
                 direction=1, claims=['T1']) for i in range(1, 45)]


def row(i, interval=(.1, .3)):
    return dict(row=i, result_id='constructed-'+str(i), estimate=sum(interval)/2,
                interval=interval, valid_inference=True, verdict='constructed', limit='Fixture only')


def test_source_dependence_does_not_multiply_primary_votes():
    r = register()
    for x in r:
        x['source_group'] = 'one-source'
    out = m.aggregate(r, [row(i) for i in range(1, 45)])
    assert out['primary']['n'] == 1
    assert out['primary']['p'] == .5
    assert not out['primary']['passes']
    assert out['descriptive']['row_coin_tail'] < .05


def test_all_rows_remain_and_zero_boundary_is_undecided():
    out = m.aggregate(register(), [row(1, (0., .3)), row(2, (-.3, 0.)), row(3)])
    assert len(out['rows']) == 44
    assert out['primary']['n'] == 1
    assert out['rows'][43]['verdict'] == 'not run'


def test_source_tie_stays_in_denominator():
    r = register()
    r[0]['source_group'] = r[1]['source_group'] = 'same'
    out = m.aggregate(r, [row(1), row(2, (-.3, -.1))])
    assert out['primary']['n'] == 1 and out['primary']['k'] == 0
    assert out['primary']['sources'][0]['tie']


def test_midus_collapses_but_two_diaries_remain_separate():
    r = register()
    for i, wave in enumerate(('midus-2', 'midus-3')):
        r[i].update(source=wave, source_group='midus')
    r[2].update(source='0057', source_group='0057')
    r[3].update(source='0056', source_group='0056')
    out = m.aggregate(r, [row(i) for i in range(1, 5)])
    assert out['primary']['n'] == 3
    bad = copy.deepcopy(r); bad[1]['source_group'] = 'midus-3'
    with pytest.raises(ValueError): m.aggregate(bad, [])


def test_invalid_diagnostic_never_becomes_decided():
    r = row(1); r['valid_inference'] = False
    out = m.aggregate(register(), [r])
    assert out['primary']['n'] == 0 and out['primary']['p'] is None
    assert out['rows'][0]['estimate'] == r['estimate']


@pytest.mark.parametrize('rows', [[row(1), row(1)], [row(45)], [row(1, (.3, .1))]])
def test_bad_results_refused(rows):
    with pytest.raises(ValueError): m.aggregate(register(), rows)


def test_negative_prediction_and_exact_binomial():
    r = register(); r[0]['direction'] = -1
    out = m.aggregate(r, [row(1, (-.3, -.1)), *[row(i) for i in range(2, 7)]])
    assert out['primary']['k'] == 6 and out['primary']['p'] == 1/64
    assert out['primary']['passes'] is None  # No set verdict from an unfinished table.
    remaining = [dict(row=i, valid_inference=False, verdict='unsupported',
                      reason='Constructed support failure') for i in range(7, 45)]
    final = m.aggregate(r, [row(1, (-.3, -.1)), *[row(i) for i in range(2, 7)], *remaining])
    assert final['primary']['passes']


def test_optional_reference_preserves_correlated_columns():
    import numpy as np
    a = np.random.default_rng(1).normal(0, .1, 2000)
    block = dict(source_group='fixture', common_draw_bank_sha256='constructed',
                 draws=np.column_stack([a+.5, a+.5]), estimates=[.5, .5], directions=[1, 1])
    out = m.diary_reference([block])
    assert set(out['reference_counts']) <= {0, 2}
    assert out['observed_count'] == 2 and out['p'] < .05
    assert out == m.diary_reference([block])
    del block['common_draw_bank_sha256']
    with pytest.raises(ValueError): m.diary_reference([block])
