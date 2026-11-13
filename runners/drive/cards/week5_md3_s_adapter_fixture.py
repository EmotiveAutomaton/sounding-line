"""Constructed production-boundary proof, not a new mood calibration.

The actual production execute/verify authenticate a constructed complete parent
and projected source, then retain an unsupported zero-choice population. The
already completed v4 signed/null cases remain the numerical qualification.
"""
from pathlib import Path
import json
import numpy as np
from . import week5_md3_s_production as adapter
from . import week5_qualification_io as io


def prepare(root):
    root = Path(root)
    source = root / 'source'
    source.mkdir(parents=True, exist_ok=True)
    task = source / 'task.npz'
    with task.open('wb') as stream:
        np.savez_compressed(stream, first=np.zeros((2, 30, 15)))
    io.write_json(source / 'SOURCE.json', {'task_sha256': io.sha(task)})
    io.write_json(source / 'VERIFIED.json', {'verified': True, 'constructed_only': True})
    parent = root / 'parent'
    io.write_json(parent / 'PLAN.json', {'inputs': {'task': str(task)}})
    io.write_json(parent / 'output/RESULT.json', {
        'card': 'MD3', 'complete_computation': True,
        'primary': {'gamma': .65, 'standing_sd': 1., 'analysed_first_plays': 2},
        'constructed_only': True})
    io.write_json(parent / 'VERIFIED.json', {'verified': True, 'constructed_only': True})
    io.write_json(parent / 'COMPLETE.json', {
        'status': 'COMPLETE', 'fresh_process_verified': True,
        'outputs': {'output/RESULT.json': io.sha(parent / 'output/RESULT.json')}})
    return {'task': str(task), 'parent_run': str(parent)}


def execute(output, inputs, config):
    if inputs or config:
        raise ValueError('Constructed boundary fixture takes no external inputs')
    output = Path(output)
    args = prepare(output / 'constructed')
    cfg = {'phase': 'MD3.s', 'draws': 2000, 'max_wall_seconds': 30, 'max_new_draws': 300}
    old = (adapter.study.core.sha, adapter.study.core.save_json, adapter.study.save_fit)
    value = adapter.execute(str(output / 'production'), args, cfg)
    if value.get('status') != 'unsupported' or not value.get('no_directional_claim'):
        raise AssertionError('Zero-choice constructed population must stay unsupported')
    verified = adapter.verify(str(output / 'production'), args, cfg)
    if verified.get('verified') is not True:
        raise AssertionError('Actual production replay did not verify')
    if old != (adapter.study.core.sha, adapter.study.core.save_json, adapter.study.save_fit):
        raise AssertionError('Production adapter leaked a callable replacement')
    with adapter.compatibility():
        deps = adapter.study.dependencies()
        if not deps or any(len(v) != 64 for v in deps.values()):
            raise AssertionError('Internal __file__ path hashing failed')
        adapter.study.save_fit(output / 'array/POINT.npz', 'constructed', {'beta': np.array([1., 2.])})
    path = output / 'array/POINT.npz'
    seal = json.loads(path.with_suffix('.sha256.json').read_text('utf8'))
    if seal != {'binding': 'constructed', 'sha256': io.sha(path)}:
        raise AssertionError('Direct numerical publication seal differs')
    report = {'verified_boundary': True, 'actual_production_execute_verify': True,
              'constructed_parent_and_source': True, 'unsupported_not_null': True,
              'string_and_internal_file_paths': True, 'exact_publication_adapters': True,
              'full_signed_null_calibration_repeated': False, 'no_corpus': True}
    io.write_json(output / 'FIXTURE.json', report)
    return report


def verify(output, inputs, config):
    output = Path(output)
    actual = execute(output / 'independent-replay', inputs, config)
    if actual != json.loads((output / 'FIXTURE.json').read_text('utf8')):
        raise ValueError('Independent compatibility-boundary replay differs')
    return {'verified': True, 'complete_constructed_boundary_replayed': True}
