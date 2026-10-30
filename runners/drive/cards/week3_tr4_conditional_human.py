"""Guarded TR4.h1 human primary; no dispatch before full calibration landing.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 5-7 reread 2026-10-29. The conditional
NULL is within-cell order invariance; ALTERNATIVE predicts useful order. All
parent rows and gains must match, failed calibration refuses, and secondary
reliability remains the original unsupported quantity. No new scientific gate.
"""
from pathlib import Path
import time
import numpy as np
from . import week3_tr4_conditional as control
from . import week3_tr4_conditional_worlds as worlds
from .timing_census import read, filehash
from .timing_pmap_source import completed
from .timing_p6 import write_equal, progress

CONFIG = dict(mode='human', repetitions=200, bootstraps=2000)
INPUTS = {'source_completion','parent_completion','parent_landing','calibration_completion','calibration_landing'}


def load(inputs):
    if set(inputs) != INPUTS:
        raise ValueError('all exact parent/source/calibration bindings required')
    source = Path(inputs['source_completion'])
    census_path = source.parent/'output/CENSUS.json'
    completed(source, census_path)
    census = read(census_path)
    if not census['summary']['full_population']:
        raise ValueError('full original population required')
    parent = Path(inputs['parent_completion'])
    result_path = parent.parent/'output/RESULTS.json'
    completed(parent, result_path)
    parent_landing = read(inputs['parent_landing'])
    if (not parent_landing['full_write_through'] or parent_landing['id'] != 'S15-TR4-20261027'
            or parent_landing['completion_sha256'] != filehash(parent)):
        raise ValueError('original fully landed parent required')
    parent_binding_path = parent.parent/'output/BINDING.json'
    completed(parent, parent_binding_path)
    if read(parent_binding_path)['inputs']['source_completion'] != filehash(source):
        raise ValueError('source differs from original parent')
    calibration = Path(inputs['calibration_completion'])
    summary_path = calibration.parent/'output/SUMMARY.json'
    binding_path = calibration.parent/'output/BINDING.json'
    completed(calibration, summary_path)
    completed(calibration, binding_path)
    binding = read(binding_path)
    if binding['config'] != worlds.CONFIGS['main'] or binding['inputs']['parent_landing'] != filehash(inputs['parent_landing']):
        raise ValueError('different calibration or parent')
    summary = read(summary_path)
    gate = read(inputs['calibration_landing'])
    expected_gates = {'complete_matrix','stationary_size','prompt_nuisance_size',
                      'high_dose_sensitivity','complete_support'}
    expected_families = list(zip(worlds.FAMILIES, (32,32,8,8)))
    if (set(summary['gates']) != expected_gates
            or [(r['family'],r['worlds']) for r in summary['families']] != expected_families
            or not summary['calibration_pass'] or not all(summary['gates'].values())
            or not gate['full_write_through'] or not gate['admitted']
            or gate['completion_sha256'] != filehash(calibration)):
        raise ValueError('complete passing calibration and full landing required')
    return census, read(result_path)


def preserve_parent(result, parent):
    if result['retained'] != parent['retained'] or result['counts'] != parent['counts']:
        raise ValueError('original scored population differs')
    actual = {r['writer']:r for r in result['writer_losses']}
    original = {r['writer']:r for r in parent['writer_losses']}
    if actual.keys() != original.keys():
        raise ValueError('writer coverage differs')
    for writer, row in actual.items():
        old = original[writer]
        if row['sessions'] != old['sessions'] or not np.isclose(row['gain'], old['gain'], rtol=0, atol=1e-14):
            raise ValueError('original primary statistic changed')
        for model in ('whole','kalman'):
            if not np.isclose(row['losses'][model], old['losses'][model], rtol=0, atol=1e-14):
                raise ValueError('original forecast changed')
    return dict(primary_and_population_preserved=True,
                original_secondary_reliability_unchanged=True,
                original_parameters=parent['parameters'],
                original_six_model_writer_losses=parent['writer_losses'],
                original_reliability=parent['reliability'])


def run(output, inputs, config, verification=False):
    if config != CONFIG:
        raise ValueError('frozen full human configuration required')
    census, parent = load(inputs)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    started = time.process_time()
    def update(phase, done, total):
        if done % 20 == 0 or done == total:
            progress(output/'PROGRESS.json', dict(phase=('verify-' if verification else '')+phase, done=done,total=total))
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():
            raise InterruptedError('TR4.h1 human yields at reference boundary')
    result = control.analyze(census, config['repetitions'], config['bootstraps'], update)
    preserved = preserve_parent(result, parent)
    payloads = {'RESULTS.json':result, 'ORIGINAL_PRESERVED.json':preserved,
                'BINDING.json':dict(config=config, inputs={k:filehash(v) for k,v in inputs.items()})}
    for name, value in payloads.items():
        if verification:
            if read(output/name) != value:
                raise ValueError('complete conditional human replay differs')
        else:
            write_equal(output/name, value)
    if not verification and not (output/'TIMING.json').exists():
        write_equal(output/'TIMING.json', dict(cpu_seconds=time.process_time()-started))
    if verification:
        return dict(verified=True,complete_input_replay=True,primary_and_population_preserved=True,scientific_admission=False)
    return dict(status='complete', scientific_admission=False)


def execute(output, inputs, config): return run(output, inputs, config)
def verify(output, inputs, config): return run(output, inputs, config, True)
