"""Supplement omitted earlier-draft cheap controls without changing old results.

DESIGN CHECK: Stage10 sections 7/9 and LESSONS3-5. Under the NULL, balanced
uninformative training gives uniform forecasts; a planted surface relation is
learned under the ALTERNATIVE. Predictions use training only. Changed sources,
incomplete rosters and changed saved outputs refuse in either case. This late
descriptive control does not become a preregistered confirmation or a new cohort.
"""
import argparse
import copy
from dataclasses import asdict
from pathlib import Path
import time

from . import comparison_bank, human_baselines
from .contracts import digest
from .earlier_programs import current_state
from .ollama import now, write_new
from .queue import read
from .reader import from_record
from .revision_bank import checked, finish, sha

ARMS = ('class-prior', 'surface-features', 'always-ignore')


def identity():
    paths = [Path(__file__), Path(__file__).with_name('earlier_programs.py')]
    return {**human_baselines.identity(), **{p.as_posix(): sha(p) for p in paths}}


def forecasts(training, answers, tasks):
    # Use precisely the earlier readers' training cohort, projected through the
    # existing current-state whitelist. Prior drafts add no feature to this
    # intentionally generic baseline. No fitted setting is selected on outcomes.
    projected = [asdict(current_state(from_record(row))) for row in training]
    fitted = human_baselines.fit(projected, answers)
    if {r['task_id'] for r in training} & {r['task_id'] for r in tasks}:
        raise ValueError('evaluation task overlaps training')
    predictions = {arm: {} for arm in ARMS}
    for row in tasks:
        task = from_record(row)
        for arm in ARMS:
            predictions[arm][task.task_id] = {
                'task_public': task.public(), 'status': 'VALID',
                'forecast': human_baselines.predict(current_state(task), fitted, arm)}
    return fitted, predictions


def produce(prepared, selection, output):
    started = time.perf_counter()
    sources = identity()

    def get(path):
        sources[path.as_posix()] = sha(path)
        return read(path)

    frozen = get(prepared / 'FROZEN.json')
    selected = get(selection / 'FROZEN.json')
    if selected['training_frozen_sha256'] != digest(frozen):
        raise ValueError('earlier selection training source differs')
    training = get(prepared / 'train-public.json')
    answers = get(prepared / 'train-evaluator.json')
    public = get(selection / 'evaluation-public.json')
    if (digest(training) != frozen['public_sha256']['train'] or
            digest(answers) != frozen['evaluator_sha256']['train'] or
            digest(public) != selected['public_sha256']['evaluation']):
        raise ValueError('frozen baseline data changed')
    sources.update(frozen['sources'])
    sources.update(frozen.get('source_files', {}))
    sources.update(selected['selection_sources'])
    for name, expected in sources.items():
        if sha(Path(name)) != expected:
            raise ValueError('baseline source changed: ' + name)
    fitted, predictions = forecasts(training['tasks'], answers['targets'], public['tasks'])
    result = {'sources': sources, 'fitted': fitted, 'predictions': predictions,
              'original_training_sha256': digest(training), 'model_calls': 0,
              'evaluation_outcomes_opened': False,
              'scope': 'Late descriptive controls; fixed original baseline recipe, earlier-reader training cohort, current draft/menu features only.'}
    if (output / 'COMPLETE.json').exists():
        checked(output)
        if read(output / 'RESULT.json') != result:
            raise ValueError('saved baseline result changed')
        return read(output / 'COMPLETE.json')
    output.mkdir(parents=True, exist_ok=False)
    write_new(output / 'RESULT.json', result)
    write_new(output / 'COST.json', {'wall_seconds': time.perf_counter() - started,
              'model_calls': 0, 'input_tokens': 0, 'output_tokens': 0,
              'scope': 'Shared CPU fit and all three controls; charge once, not per reused comparison.'})
    return finish(output, digest(result), {'scientific_verdict': False})


def supplement(original_inputs, original_result, baseline, output):
    for directory in (original_inputs, original_result, baseline):
        checked(directory)
    bundle = read(original_inputs / 'BUNDLE.json')
    old = read(original_result / 'RESULT.json')
    control = read(baseline / 'RESULT.json')
    sources = {**bundle['sources'], **control['sources']}
    for name, expected in sources.items():
        if sha(Path(name)) != expected:
            raise ValueError('original or control source changed: ' + name)
    if comparison_bank.analyze(bundle) != old:
        raise ValueError('original comparison does not reproduce')
    for directory in (original_inputs, original_result, baseline):
        for path in directory.rglob('*'):
            if path.is_file():
                sources[path.as_posix()] = sha(path)
    revised = copy.deepcopy(bundle)
    for cell in revised['cells']:
        ids = {row['task_id'] for row in cell['tasks']}
        model_arms = list(cell['predictions'])
        for arm in ARMS:
            predictions = control['predictions'][arm]
            if set(predictions) != ids:
                raise ValueError('baseline is not the exact complete comparison population')
            name = 'baseline-' + arm
            if name in cell['predictions']:
                raise ValueError('supplement would overwrite existing control')
            cell['predictions'][name] = predictions
            cell['costs'][name] = dict(model_calls=0, input_tokens=0, output_tokens=0,
                                       executor_evaluations=0, wall_seconds=0)
            cell['contrasts'].extend([[model, name] for model in model_arms])
        cell['scope'] += ' Late cheap controls share one separately recorded CPU fit; old reader results, exclusions and central contrasts are unchanged.'
    revised['sources'] = sources
    result = comparison_bank.analyze(revised)
    for before, after in zip(old['results'], result['results'], strict=True):
        for key in ('cells', 'paired', 'costs'):
            if any(after[key][k] != v for k, v in before[key].items()):
                raise ValueError('supplement changed an original result')
    if (output / 'COMPLETE.json').exists():
        checked(output)
        if read(output / 'RESULT.json') != result or read(output / 'BUNDLE.json') != revised:
            raise ValueError('saved supplement changed')
        return read(output / 'COMPLETE.json')
    output.mkdir(parents=True, exist_ok=False)
    write_new(output / 'BUNDLE.json', revised)
    write_new(output / 'RESULT.json', result)
    write_new(output / 'RECONCILIATION.json', {'at': now(), 'old_cells_unchanged': True,
              'old_contrasts_unchanged': True, 'shared_control_cpu_cost': read(baseline / 'COST.json'),
              'original_result_sha256': sha(original_result / 'RESULT.json'),
              'model_calls': 0, 'scope': control['scope']})
    return finish(output, digest(result), {'scientific_verdict': False})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['produce', 'supplement'])
    for name in ('prepared', 'selection', 'baseline', 'original-inputs', 'original-result', 'output'):
        parser.add_argument('--' + name, type=Path, required=name == 'output')
    args = parser.parse_args()
    if args.action == 'produce':
        produce(args.prepared, args.selection, args.output)
    else:
        supplement(args.original_inputs, args.original_result, args.baseline, args.output)
