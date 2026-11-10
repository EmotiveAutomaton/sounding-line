"""AT3/AT4 dependency authentication with unchanged statistical kernels.

DESIGN CHECK: LESSONS 3--5. A selected-reader primary must consume the exact
complete AT2 selection and score collection. Explicit per-reader textures may
consume a completed model bank independently; neither route selects a reader.
"""
from pathlib import Path

from . import week5_at_analysis as original
from . import week5_at_collect_v4 as collector
from .week5_at_source import authenticate
from .week5_at_selection import selected_reader
from .week5_at_scoring import ENGINE_MODELS, digest
from .week5_at_scoring_v4 import NUMERICAL_SPEC
from .timing_census import read, filehash
from .timing_p6 import write_equal


def complete_plan(path, module):
    root = authenticate(path)
    plan = read(root / 'PLAN.json')
    if plan.get('module') != module:
        raise ValueError('Unexpected completed dependency handler')
    if read(root / 'COMPLETE.json')['outputs'].get('PLAN.json') != filehash(root / 'PLAN.json'):
        raise ValueError('Dependency plan is not authenticated')
    return root, plan


def configuration(config):
    allowed = {'card', 'model', 'draws', 'reader_role', 'texture', 'precision_followup',
               'context', 'context_length', 'genre', 'position', 'residualized',
               'outcome', 'threshold'}
    if set(config) - allowed or config.get('card') not in ('AT3', 'AT4'):
        raise ValueError('Registered AT3/AT4 configuration required')
    role = config.get('reader_role')
    texture = config.get('texture', False)
    precision = config.get('precision_followup', False)
    if not isinstance(texture, bool) or not isinstance(precision, bool):
        raise ValueError('Explicit boolean analysis lane required')
    if role not in ('selected', 'completed_model', 'engine_texture'):
        raise ValueError('Explicit reader dependency role required')
    if (role == 'completed_model' and config['card'] != 'AT3') or (
            role == 'engine_texture' and (config['card'] != 'AT4' or config.get('model') not in ENGINE_MODELS)):
        raise ValueError('Independent reader role differs from declared grid')
    if role != 'selected' and not texture:
        raise ValueError('Independent completed-reader analysis is texture only')
    if config.get('context', 'final') != 'final' or config.get('context_length', 1024) != 1024:
        raise ValueError('AT3/AT4 require the declared final-context 1024-token scores')
    if config.get('outcome', 'log_pause') != 'log_pause':
        raise ValueError('AT3/AT4 outcome differs from declared grid')
    if config.get('position') not in (None, 'sentence_start', 'inside'):
        raise ValueError('Undeclared word-position texture')
    if config.get('threshold', .5) not in (.3, .5, .7):
        raise ValueError('Undeclared fluency threshold')
    if config['card'] == 'AT3' and 'threshold' in config:
        raise ValueError('AT3 has no classification threshold')
    if config['card'] == 'AT4' and (config.get('position') or config.get('residualized')):
        raise ValueError('AT4 has no residualized-entropy or position texture')
    if not texture and (config.get('genre') or config.get('position') or config.get('residualized')
                        or config.get('threshold', .5) != .5 or precision):
        raise ValueError('Primary cannot inherit a texture condition')
    expected_draws = 2000 if not texture or precision else 200
    if config.get('draws') != expected_draws:
        raise ValueError('Declared lane uncertainty count required')
    return {k: v for k, v in config.items() if k not in ('reader_role', 'texture', 'precision_followup')}


def prepare(inputs, config):
    analysis_config = configuration(config)
    role = config['reader_role']
    expected_inputs = {'collection_root', 'selection_root'} if role == 'selected' else {'collection_root'}
    if set(inputs) != expected_inputs:
        raise ValueError('Exact dependency inputs required for the reader role')
    root, plan = complete_plan(inputs['collection_root'], 'runners.drive.cards.week5_at_collect_v4')
    if read(root / 'output/NUMERICAL_SPEC.json') != NUMERICAL_SPEC:
        raise ValueError('Completed collection numerical specification differs')
    if (plan['config'].get('context', 'final') != 'final' or
            plan['config'].get('context_length', 1024) != 1024):
        raise ValueError('Completed collection context differs')
    collector.validate(plan['inputs'], plan['config'])
    bank = read(plan['inputs']['bank_manifest'])
    model = config.get('model')
    if model not in bank or model not in read(root / 'output/SUMMARY.json')['models']:
        raise ValueError('Requested reader is not completely collected')
    manifests = [read(read(Path(p) / 'PLAN.json')['inputs']['model_manifest']) for p in bank[model].values()]
    if not manifests or len({digest(m) for m in manifests}) != 1:
        raise ValueError('Completed reader manifest is not unique')
    manifest = manifests[0]
    provenance = dict(reader_role=role, texture=config.get('texture', False),
                      precision_followup=config.get('precision_followup', False), model=model,
                      revision=manifest['revision'], manifest_sha256=digest(manifest),
                      numerical_spec=NUMERICAL_SPEC, context='final', context_length=1024,
                      collection_complete_sha256=filehash(root / 'COMPLETE.json'))
    if role == 'selected':
        selection, selection_plan = complete_plan(inputs['selection_root'], 'runners.drive.cards.week5_at_analysis_v3')
        selected_collection = Path(selection_plan['inputs']['collection_root']).resolve()
        if selected_collection != root.resolve():
            raise ValueError('Selected reader refers to another score collection')
        binding = selected_reader(selection, manifest)
        if (binding.get('complete_collection_sha256') != provenance['collection_complete_sha256'] or
                binding.get('context') != 'final' or binding.get('context_length') != 1024):
            raise ValueError('Selected reader cohort or context differs')
        provenance['selection_complete_sha256'] = filehash(selection / 'COMPLETE.json')
    return root, analysis_config, provenance


def run(output, inputs, config, verifying=False):
    output = Path(output)
    if (output / 'YIELD_REQUEST.json').exists():
        return dict(status='yielded', reason='before complete bounded AT statistical consumer')
    root, analysis_config, provenance = prepare(inputs, config)
    result = (original.verify if verifying else original.execute)(
        output, dict(rows=str(root / 'output/ROWS.json.gz')), analysis_config)
    if verifying:
        if read(output / 'READER_PROVENANCE.json') != provenance:
            raise ValueError('Completed reader dependency replay differs')
    else:
        write_equal(output / 'READER_PROVENANCE.json', provenance)
    return result


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, True)
