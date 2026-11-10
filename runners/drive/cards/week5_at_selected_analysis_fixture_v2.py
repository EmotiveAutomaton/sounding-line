"""Constructed AT3/AT4 guarded-bank consumer replay; no model load.

DESIGN CHECK: LESSONS 3-5. Only explicit guarded collection/selection
identities change; all full statistical outputs and refusal controls remain."""
from pathlib import Path
import json
import shutil

from . import week5_at_analysis as original
from . import week5_at_selected_analysis_v2 as consumer
from .week5_at_source import authenticate
from .week5_at_scoring import ENGINE_MODELS
from .timing_census import read, filehash
from .timing_p6 import write_equal, progress


def refuse(call):
    try:
        call()
    except (ValueError, KeyError):
        return
    raise ValueError('Incompatible dependency condition was accepted')


def changed_selection(root, original_root, name, filename, change):
    """Mutate an explicitly constructed copy; original completed bytes stay intact."""
    target = root / name
    if not target.exists():
        shutil.copytree(original_root, target)
        path = target / filename
        value = change(read(path))
        path.write_text(json.dumps(value, sort_keys=True) + '\n', encoding='utf8')
        done = read(target / 'COMPLETE.json')
        done['outputs'][filename] = filehash(path)
        done['constructed_dependency_fixture'] = True
        done['not_a_production_runtime_admission'] = True
        (target / 'COMPLETE.json').write_text(json.dumps(done, sort_keys=True) + '\n', encoding='utf8')
    return target


def run(output, inputs, config, verifying=False):
    if set(inputs) != {'constructed_root'} or config:
        raise ValueError('Only the completed constructed collection fixture is accepted')
    prior = authenticate(inputs['constructed_root'])
    if read(prior / 'PLAN.json').get('module') != 'runners.drive.cards.week5_at_guarded_bank_fixture':
        raise ValueError('Human collections are excluded from this fixture')
    fixture = read(prior / 'output/FIXTURE.json')
    if not fixture.get('fixture_only') or fixture.get('native_human_model_admission') is not False:
        raise ValueError('Constructed source declaration is absent')
    source = prior / 'output/complete-bank'
    collection = source / 'collection'
    selection = source / 'selection'
    chosen = read(selection / 'output/RESULT.json')['selected_model']
    models = read(collection / 'output/SUMMARY.json')['models']
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    selected_inputs = dict(collection_root=str(collection), selection_root=str(selection))
    independent_inputs = dict(collection_root=str(collection))
    cases = []
    for card in ('AT3', 'AT4'):
        cases.append((card + '-primary', selected_inputs,
                      dict(card=card, model=chosen, draws=2000, reader_role='selected')))
    for i, model in enumerate(models):
        cases.append((f'AT3-model-{i:02d}', independent_inputs,
                      dict(card='AT3', model=model, draws=200, reader_role='completed_model', texture=True)))
    for i, model in enumerate(ENGINE_MODELS):
        cases.append((f'AT4-engine-{i}', independent_inputs,
                      dict(card='AT4', model=model, draws=200, reader_role='engine_texture', texture=True)))
    for position in ('sentence_start', 'inside'):
        cases.append(('AT3-' + position, selected_inputs,
                      dict(card='AT3', model=chosen, draws=200, reader_role='selected', texture=True, position=position)))
    cases.append(('AT3-residualized', selected_inputs,
                  dict(card='AT3', model=chosen, draws=200, reader_role='selected', texture=True, residualized=True)))
    for threshold in (.3, .7):
        cases.append((f'AT4-threshold-{threshold}', selected_inputs,
                      dict(card='AT4', model=chosen, draws=200, reader_role='selected', texture=True, threshold=threshold)))
    reports = []
    for name, args, cfg in cases:
        if (root / 'YIELD_REQUEST.json').exists():
            return dict(status='yielded', reason='sealed complete statistical-handler case')
        child = root / name
        (consumer.verify if verifying else consumer.execute)(child, args, cfg)
        original_config = consumer.configuration(cfg)
        oracle = root / ('oracle-' + name)
        (original.verify if verifying else original.execute)(
            oracle, dict(rows=str(collection / 'output/ROWS.json.gz')), original_config)
        if read(child / 'RESULT.json') != read(oracle / 'RESULT.json'):
            raise ValueError('Dependency wrapper changed the statistical result')
        reports.append(dict(case=name, result_sha256=filehash(child / 'RESULT.json'),
                            provenance_sha256=filehash(child / 'READER_PROVENANCE.json')))
        progress(root / 'PROGRESS.json', dict(phase='verify' if verifying else 'execute',
                                             complete=len(reports), total=len(cases)))
    primary = cases[0][2]
    other = next(m for m in models if m != chosen)
    refuse(lambda: consumer.prepare(selected_inputs, dict(primary, model=other)))
    refuse(lambda: consumer.prepare(independent_inputs, primary))
    refuse(lambda: consumer.prepare(selected_inputs, dict(primary, context_length=64)))
    refuse(lambda: consumer.prepare(independent_inputs, dict(primary, reader_role='completed_model')))
    nonengine = next(m for m in models if m not in ENGINE_MODELS)
    refuse(lambda: consumer.prepare(independent_inputs,
        dict(card='AT4', model=nonengine, reader_role='engine_texture', texture=True, draws=200)))
    refuse(lambda: consumer.prepare(selected_inputs, dict(primary, texture=True, draws=2000)))
    refuse(lambda: consumer.prepare(selected_inputs, dict(primary, genre='fixture', texture=False)))
    screened = changed_selection(root, selection, 'screened-selection', 'output/RESULT.json',
                                 lambda x: dict(x, screening_only=True))
    refuse(lambda: consumer.prepare(dict(selected_inputs, selection_root=str(screened)), primary))
    changed = changed_selection(root, selection, 'different-cohort-selection', 'output/READER_BINDING.json',
                                 lambda x: dict(x, complete_collection_sha256='changed'))
    refuse(lambda: consumer.prepare(dict(selected_inputs, selection_root=str(changed)), primary))
    result = dict(fixture_only=True, no_pretrained_model_load=True, prior_complete_sha256=filehash(prior / 'COMPLETE.json'),
                  full_2000_draw_AT3_AT4_original_outputs_equal=True, every_completed_model_AT3_texture=True,
                  both_independent_engine_AT4_textures=True, declared_position_residualized_threshold_textures=True,
                  original_AT3_surprisal_companion_preserved=True, wrong_reader_lane_cohort_context_screening_refused=True,
                  cases=reports)
    if verifying:
        if read(root / 'FIXTURE.json') != result:
            raise ValueError('Complete AT3/AT4 dependency fixture differs')
        return dict(verified=True, full_dependency_and_statistical_replay=True)
    write_equal(root / 'FIXTURE.json', result)
    return dict(status='complete', fixture_only=True)


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, True)
