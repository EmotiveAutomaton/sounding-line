"""Numerical-only CH7 qualification on three independently generated worlds.

DESIGN CHECK: LESSONS 3-5. Full 2000-player bootstraps and twenty complete
history nulls are required per native case; known null/floor/ladder gates are
unchanged. Independent formulas check fits, every bootstrap and null recurrence.
No raw-source requalification, human data or engine is involved.
"""
from pathlib import Path
import json
import sqlite3
import numpy as np
from . import week5_ch7_math_v3 as m
from . import week5_ch7_reference_v1 as reference
from . import week5_ch7_fixture_v1 as old_fixture
from . import week5_sg1_carried_v3 as consumer
from . import week5_sg1_source_v1 as sg1
from .week5_ch_source import digest, write_json

CASES = {'null': (0.,0.,'mixed'), 'floor': (-.16,0.,'floor'), 'ladder': (-.16,-.16,'ladder')}


def database(path, world):
    # Only a local, explicitly constructed table. No source admission is claimed.
    old_fixture.database(path, world)
    with sqlite3.connect(path) as con:
        con.execute('INSERT INTO settings VALUES(?,?)',('adapter_sha256',digest(sg1.__file__)))


def independent_comparison(world, science, draws=2000):
    data = [m.player_data(games) for games in world.values()]
    blocks = [d['rows'] for d in data]
    stats = m.sufficient_blocks(blocks)
    expected_point = reference.dense_fit(blocks,'recent',stats['kept'])
    np.testing.assert_allclose(science['primary']['point']['coefficients'],expected_point,atol=1e-9,rtol=1e-9)
    xx, xy, _ = reference.raw_statistics(blocks,'recent',stats['kept'])
    rng = np.random.default_rng(m.SEED)
    expected = []
    for _ in range(draws):
        indices = rng.integers(0,len(blocks),len(blocks))
        multiplicities = [sum(indices == i) for i in range(len(blocks))]
        beta = reference.weighted_fit(xx,xy,multiplicities)
        expected.append(abs(beta[0])-abs(beta[1]))
    interval, se = reference.interval(expected)
    np.testing.assert_allclose(science['primary']['interval'],interval,atol=1e-9,rtol=1e-9)
    np.testing.assert_allclose(science['primary']['bootstrap_se'],se,atol=1e-10,rtol=1e-9)
    fits = [m.fit_null(d) for d in data]
    nulls = []
    for draw in range(20):
        simulated = []
        for person, (datum, fit) in enumerate(zip(data,fits)):
            seed = np.random.SeedSequence([m.SEED,811,draw,person])
            expected_rows = reference.simulate(datum['trace'],fit,seed)
            actual_rows = m.simulate(datum,fit,np.random.SeedSequence([m.SEED,811,draw,person]))
            np.testing.assert_allclose(actual_rows,expected_rows,atol=1e-9,rtol=1e-11,equal_nan=True)
            simulated.append(expected_rows)
        s = m.sufficient_blocks(simulated)
        a,b,_ = reference.raw_statistics(simulated,'recent',s['kept'])
        beta = reference.weighted_fit(a,b,np.ones(len(simulated),int))
        nulls.append(abs(beta[0])-abs(beta[1]))
    expected_bar = max(.1*science['observed_stop_probability'],
                       2*sum(abs(v) for v in nulls)/20+3*reference.interval(nulls)[1])
    np.testing.assert_allclose(science['working_bar'],expected_bar,atol=1e-9,rtol=1e-9)
    return dict(full_bootstrap_draws=draws,full_null_histories=20,
        independent_dense_point=True,independent_raw_sum_bootstrap=True,
        independent_scalar_history_recurrence=True,independent_bar=True)


def execute(output, inputs, config):
    if inputs or set(config) != {'constructed_fixture','case'} or config['constructed_fixture'] is not True or config['case'] not in CASES:
        raise ValueError('Frozen constructed numerical case required')
    output = Path(output)
    output.mkdir(parents=True,exist_ok=True)
    left,right,shape = CASES[config['case']]
    world,truth = reference.histories(left=left,right=right)
    path = output/'PRIVATE_CONSTRUCTED_HISTORY.sqlite'
    database(path,world)
    source = {'histories':dict(path=str(path),sha256=digest(path))}
    controls = dict(card='CH7',constructed_fixture=True,draws=2000,null_draws=20,floor=8)
    if consumer.execute(output/'analysis',source,controls)['status'] != 'complete':
        raise AssertionError('Constructed CH7 handler did not complete')
    science = json.loads((output/'analysis/SCIENCE.json').read_text())
    beta = science['primary']['point']['coefficients']
    if max(abs(beta[0]-left),abs(beta[1]-right)) > .05:
        raise AssertionError('Frozen planted slopes not recovered')
    if science['null']['completed'] != 20 or science['null']['invalid'] or science['null']['mean_absolute_contrast'] > .05:
        raise AssertionError('Complete null histories did not remove reference effect')
    if science['primary']['invalid_draws'] or science['pattern'] != shape:
        raise AssertionError('Frozen uncertainty/joint-shape gate failed')
    if config['case'] == 'null' and science['verdict'] != 'against':
        raise AssertionError('Null world failed original inside-band gate')
    evidence = independent_comparison(world,science)
    write_json(output/'QUALIFICATION.json',dict(passed=True,case=config['case'],truth=truth,
        evidence=evidence,record_kind='run',by_construction=True,theory_tags=['H12-T6'],
        activation=[],constructed_fixture=True,raw_source_requalified=False,
        production_admitted=False,science_sha256=digest(output/'analysis/SCIENCE.json')))
    return dict(status='complete',constructed_fixture=True)


def verify(output, inputs, config):
    output = Path(output)
    fresh = output/'independent_native'
    execute(fresh,inputs,config)
    for relative in ('analysis/SCIENCE.json','QUALIFICATION.json'):
        if digest(output/relative) != digest(fresh/relative):
            raise ValueError('Fresh complete numerical qualification differs')
    return dict(verified=True,full_constructed_generation_and_formulas_replayed=True,
                raw_source_requalified=False)
