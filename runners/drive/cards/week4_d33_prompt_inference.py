"""Unchanged D33 joint inference on authenticated prompt-excluded preparation.

DESIGN CHECK: LESSONS 3-5 and D33 control lessons read November 5. Fixed null,
positive and reverse worlds test arithmetic and signed inference; neither
support nor references depend on observed outcomes. All rows and draws remain.
Changed sources, incomplete replay and undefined fits never become positives.
"""
from pathlib import Path
import time
import numpy as np
from threadpoolctl import threadpool_limits

from . import timing_d33_supported_stats as stats
from . import week4_d33_prompt_source as source
from .timing_census import read, filehash
from .timing_p6 import gzread, write_equal, progress
from .timing_stats import sufficient
from .batch_runtime import check_files


def configuration(mode):
    if mode not in ('constructed', 'cost', 'full'):
        raise ValueError('Unknown inference mode')
    return dict(card='D33.pair-calibration-supported.m', schema=1, mode=mode,
                bootstrap_draws=2000, permutations=200, seed=20261018)


def fixture(beta):
    rng = np.random.default_rng(31)
    rows = []
    for wi in range(6):
        for j in range(32):
            own, donor, pop, length, freq, session = rng.normal(size=6)
            start, punct, screen = rng.integers(0, 2, size=3)
            y = (beta*own+.35*donor+.15*pop+.02*length-.03*freq+.1*start
                 -.05*punct+.04*screen+.12*session+wi*.15+rng.normal(scale=.12))
            rows.append(dict(writer=str(wi), session=f'w{wi}_s', index=j,
                own_surprise=float(own), donor_surprise=float(donor),
                original_personal_surprise=float(own*1.1), population_surprisal=float(pop),
                length=float(length), log_frequency=float(freq), sentence_start=int(start),
                after_punctuation=int(punct), on_screen=int(screen), session_surprisal=float(session),
                log_pause=float(y)))
    return rows


def dense_check(rows):
    x, y, writers = stats.design(rows)
    actual = stats.fit(sufficient(x, y, writers))
    v = np.eye(len(y))
    for writer in set(writers):
        ix = np.flatnonzero(writers == writer)
        v[np.ix_(ix, ix)] += actual['variance_ratio']
    weighted = np.linalg.solve(v, x)
    beta = np.linalg.solve(x.T@weighted, weighted.T@y)
    if not np.allclose([actual['coefficients'][n] for n in stats.NAMES], beta,
                       rtol=0, atol=1e-8):
        raise ValueError('Independent dense GLS disagrees')
    return actual


def check_known_interval(result, expected):
    if result.get('state') != 'complete':
        raise ValueError('Known signed uncertainty state not recovered')
    value = result['primary']['own']
    # The inherited classifier calls a positive point whose interval includes
    # zero "marginal". The null calibration checks coverage, not that point sign.
    valid = (value.get('ci_low', 1) <= 0 <= value.get('ci_high', -1)
             if expected == 'null' else value['state'] == expected)
    if not valid:
        raise ValueError('Known signed uncertainty state not recovered')


def load(inputs):
    if set(inputs) != {'source_completion', 'source_landing'}:
        raise ValueError('Exact prepared inputs required')
    root = Path(inputs['source_completion']).resolve().parent
    done, plan, landing = read(root/'COMPLETE.json'), read(root/'PLAN.json'), read(inputs['source_landing'])
    if (done['status'] != 'COMPLETE' or not done['fresh_process_verified']
            or plan['module'] != source.__name__ or plan['config'] != source.configuration('full')
            or not landing['full_write_through']
            or landing['id'] != 'OPS-S15-W4-D33-PROMPT-SOURCE-FULL-20261105'
            or landing['complete_sha256'] != filehash(root/'COMPLETE.json')
            or landing['plan_sha256'] != filehash(root/'PLAN.json')
            or not read(root/'VERIFIED.json')['complete_source_replay']):
        raise ValueError('Unverified prepared source')
    check_files(plan['pins'])
    for name, expected in done['outputs'].items():
        if filehash(root/name) != expected:
            raise ValueError('Prepared source changed: '+name)
    rows = gzread(root/'output/DESIGN.json.gz')
    roster, summary = read(root/'output/SUPPORTED_ROSTER.json'), read(root/'output/SUMMARY.json')
    keys = [tuple(k) for k in roster['retained_keys']]
    if (len(keys) != len(set(keys)) or len(rows) != len(keys)
            or {(r['session'], r['index']) for r in rows} != set(keys)
            or len(rows) != summary['prepared_rows']
            or len({r['writer'] for r in rows}) != summary['coverage']['retained_writers']):
        raise ValueError('Prepared roster mismatch')
    return rows, dict(coverage=summary['coverage'], source_summary=summary,
                      source_complete_sha256=filehash(root/'COMPLETE.json'))


def run_bank(output, rows, config, verifying, cost=False):
    root = Path(output)/('verify-inference' if verifying else 'inference')
    seen = []
    def checkpoint(item):
        seen.append(item['blocks'])
        progress(Path(output)/'PROGRESS.json', dict(phase='verify-inference' if verifying else 'inference',
                                                   blocks=item['blocks'], total=10))
        return cost or (Path(output)/'YIELD_REQUEST.json').exists()
    value = stats.run(rows, draws=config['bootstrap_draws'], permutations=config['permutations'],
                      seed=config['seed'], checkpoint=root, checkpoint_callback=checkpoint)
    if cost:
        if value != dict(status='yielded', completed_blocks=1, total_blocks=10) or seen != [1]:
            raise ValueError('Cost block incomplete: '+str(value.get('reason')))
    elif value.get('status') == 'yielded':
        return value
    if value.get('state') == 'complete' or cost:
        blocks = 1 if cost else 10
        for index in range(blocks):
            name = f'block-{index:02}.json'
            block = read(root/name)
            if len(block['samples']) != 200 or len(block['controls']) != 20:
                raise ValueError('Incomplete fixed inference bank')
            if verifying and block != read(Path(output)/'inference'/name):
                raise ValueError('Fresh inference block differs')
    return value


def one_pass(output, inputs, config, verifying=False, loader=load):
    if config != configuration(config.get('mode')):
        raise ValueError('Frozen inference configuration required')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    def store(name, value):
        if verifying:
            if read(output/name) != value:
                raise ValueError('Complete inference replay differs: '+name)
        else:
            write_equal(output/name, value)
    store('INPUTS.json', dict(config=config, inputs={k:filehash(v) for k,v in inputs.items()}))
    start = time.process_time()
    with threadpool_limits(limits=1):
        if config['mode'] == 'constructed':
            if inputs:
                raise ValueError('No external constructed inputs')
            results = {}
            for name, beta, expected in [('null', 0., 'null'), ('positive', .8, 'positive'), ('negative', -.8, 'negative')]:
                rows = fixture(beta)
                point = dense_check(rows)
                if abs(point['own']-beta) >= .04:
                    raise ValueError('Known coefficient not recovered')
                result = run_bank(output/name, rows, config, verifying)
                if result.get('status') == 'yielded':
                    return result
                check_known_interval(result, expected)
                results[name] = result
            store('CONSTRUCTED.json', results)
            store('SUMMARY.json', dict(constructed=True, signed_worlds=3, dense_arithmetic_verified=True,
                                      complete_banks=True, scientific_admission=False))
        else:
            rows, meta = loader(inputs)
            source_cpu = time.process_time()-start
            inference_start = time.process_time()
            result = run_bank(output, rows, config, verifying, cost=config['mode'] == 'cost')
            inference_cpu = time.process_time()-inference_start
            if config['mode'] == 'cost':
                store('PROBE.json', dict(mode='cost-only', blocks=1, paired_writer_draws=200,
                                        draws_per_control=20, source=meta, scientific_admission=False))
            elif result.get('status') == 'yielded':
                return result
            else:
                store('SUMMARY.json', dict(card=config['card'], source=meta, statistics=result,
                    descriptive=True, original_full_population_question='open',
                    scope='Prompt-excluded histories on the separately supported pair2 population; no isolated cross-population prompt-removal effect',
                    no_descendants=True))
            write_equal(output/('VERIFY_TIMING.json' if verifying else 'EXECUTE_TIMING.json'),
                        dict(source_cpu_seconds=source_cpu, inference_cpu_seconds=inference_cpu))
    return dict(verified=True, full_fresh_inference_replay=True, mode=config['mode'],
                scientific_admission=False)


def execute(output, inputs, config):
    return one_pass(output, inputs, config)


def verify(output, inputs, config):
    return one_pass(output, inputs, config, True)
