"""Known-answer checks; no real evaluation labels or model calls.

DESIGN CHECK: LESSONS3-5/CONTROLS1-6. Equal forecasts must tie, a planted
prediction improves both scores, missing/zero support stays explicit, and
replicated observations cannot change equal-writer weights or dependencies.
"""
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import math

from . import comparison as measure, human_baselines as baseline
from .contracts import canonical, digest
from .human_memory_checks import task, rows as training_rows
from .ollama import now, write_new
from .reader import from_record


def run(output):
    checks = []
    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)
    def refuse(name, call):
        try:
            call()
        except ValueError:
            checks.append(name)
        else:
            raise AssertionError(name)
    t = task(100, 1); ids = [k for k, _ in t.choices]; truth = ids[0]
    def forecast(probabilities, choice=truth):
        return dict(choice=choice, probabilities=dict(zip(ids, probabilities)),
                    explanation='constructed', insufficient_evidence=False)
    uniform = forecast([.25]*4)
    good = forecast([1.,0.,0.,0.])
    bad = forecast([0.,1.,0.,0.])
    u = measure.score(t, truth, 'VALID', uniform)
    check('known uniform Brier and log loss', u['brier'] == .375 and u['log_loss'] == math.log(4))
    check('perfect prediction has zero loss', measure.score(t, truth, 'VALID', good)['brier'] == 0)
    check('zero support remains infinite', measure.score(t, truth, 'VALID', bad)['log_loss'] == 'infinite')
    invalid = measure.score(t, truth, 'INVALID', None)
    check('invalid is worst system loss, no invented proper score', invalid['brier_system'] == 1 and invalid['log_loss'] is None)
    refuse('invalid substitution refused', lambda: measure.score(t, truth, 'INVALID', uniform))
    refuse('probability normalization is not implicit', lambda: measure.score(t, truth, 'VALID', forecast([.5]*4)))
    contrary = measure.score(t, truth, 'VALID', forecast([1.,0.,0.,0.], ids[1]))
    check('generated choice and executed probabilities are separate', contrary['generated_correct'] == 0 and contrary['probability_correct'] == 1)
    check('probability ties receive fractional accuracy', u['probability_correct'] == .25)
    tasks = [replace(t, task_id=digest(['comparison', i])[:32]) for i in range(4)]
    answers = {q.task_id: dict(truth=truth, group='writer'+str(i//2), event='event'+str(i), dependencies=['shared-prompt']) for i,q in enumerate(tasks)}
    def cell(f):
        predictions = {q.task_id: dict(task_public=q.public(), status='VALID', forecast=f) for q in tasks}
        return measure.cell(tasks, answers, predictions, 'constructed evaluation')
    initial = cell(uniform); perfect = cell(good); impossible = cell(bad)
    check('shared prompt forms one connected component', initial['summary']['dependency_components'] == 1)
    delta = measure.paired(perfect, initial)
    check('positive paired Brier has known direction', delta['brier']['estimate'] == .375)
    check('positive paired log benefit is known', delta['finite_log']['estimate'] == math.log(4))
    check('identical forecasts have zero paired benefit', measure.paired(initial, initial)['brier']['estimate'] == 0)
    check('two infinities are never subtracted', measure.paired(impossible, impossible)['finite_log']['estimate'] is None)
    check('one component gets no population interval', delta['brier']['leave_one_component_out_range'] is None and 'bootstrap_percentile_95' not in delta['brier'])
    check('writer replication does not change weight', measure.balanced([dict(group='a', x=1)]*10+[dict(group='b',x=0)], 'x') == .5)
    swapped = deepcopy(initial); swapped['rows'].reverse()
    check('row order does not affect pairing', measure.paired(initial, swapped)['brier']['estimate'] == 0)
    altered = deepcopy(initial); altered['rows'][0]['truth'] = ids[1]
    refuse('paired targets cannot differ', lambda: measure.paired(initial, altered))
    altered = deepcopy(initial); altered['rows'][0]['public']['evidence']['document'] += ' new'
    refuse('paired evidence cannot differ', lambda: measure.paired(initial, altered))
    predictions = {q.task_id: dict(task_public=q.public(), status='VALID', forecast=uniform) for q in tasks}
    refuse('missing attempted row refused', lambda: measure.cell(tasks, answers, {k:v for k,v in predictions.items() if k != tasks[0].task_id}, 'x'))
    repeated = deepcopy(answers); repeated[tasks[1].task_id]['event'] = repeated[tasks[0].task_id]['event']
    refuse('duplicate source event refused', lambda: measure.cell(tasks, repeated, predictions, 'x'))
    refuse('mixed views refused', lambda: measure.cell([replace(tasks[0], evidence_view='process-record')]+tasks[1:], answers, predictions, 'x'))
    bridge = [dict(group='a',dependencies=['p']),dict(group='b',dependencies=['p','q']),dict(group='c',dependencies=['q'])]
    check('dependencies connect transitively', len(set(measure.components(bridge).values())) == 1)
    null = [dict(group=str(i), component=str(i), x=0.) for i in range(10)]
    check('constant-null bootstrap is exactly zero', measure.uncertainty(null, 'x')['bootstrap_percentile_95'] == [0,0])
    calibration = measure.calibration([dict(group='a', valid=True, confidence=.5, generated_correct=int(i%2)) for i in range(8)], 'confidence', 'generated_correct')
    check('balanced known calibration is exact', calibration['expected_calibration_error'] == 0)

    train, labels = training_rows('signal')
    fitted = baseline.fit(train, labels)
    short = task('new-short',1); long = task('new-long',12)
    chosen = lambda q: dict(q.choices)[baseline.predict(q, fitted, 'surface-features')['choice']]
    check('planted feature relation learned', chosen(short) == baseline.programs.DESCRIPTIONS['accept'] and chosen(long) == baseline.programs.DESCRIPTIONS['edit'])
    null_train, null_labels = training_rows('null')
    null_fit = baseline.fit(null_train, null_labels)
    check('balanced uninformative features stay uniform', all(abs(p-.25)<1e-12 for p in baseline.predict(short, null_fit, 'surface-features')['probabilities'].values()))
    check('training prior retains missing classes', fitted['models']['artifact']['prior'].count(0) == 2)
    check('always-ignore is an explicit constant', dict(short.choices)[baseline.predict(short, fitted, 'always-ignore')['choice']] == baseline.programs.DESCRIPTIONS['ignore'])
    check('option reorder cannot change semantic baseline', baseline.predict(replace(short, choices=tuple(reversed(short.choices))), fitted, 'surface-features')['probabilities'] == baseline.predict(short, fitted, 'surface-features')['probabilities'])
    check('repeated words count as word length', baseline.vector(task('repeat',12))[0] == math.log1p(12))
    check('surface baseline does not read personal history', baseline.vector(replace(short, evidence_view='process-record', evidence={**short.evidence,'earlier_handling':['edit']})) == baseline.vector(short))
    with TemporaryDirectory(prefix='s10-comparison-', dir=output.parent) as temporary:
        root = Path(temporary); prepared = root/'source'; prepared.mkdir()
        public = dict(train={'tasks':train}, development={'tasks':[asdict(short)]}, evaluation={'tasks':[asdict(long)]})
        targets = {'targets':labels}
        frozen = dict(public_sha256={k:digest(v) for k,v in public.items()}, evaluator_sha256={'train':digest(targets)})
        for phase, value in public.items():
            write_new(prepared/(phase+'-public.json'), value)
        write_new(prepared/'train-evaluator.json', targets); write_new(prepared/'FROZEN.json', frozen)
        original_read = baseline.read
        def guarded(path):
            if path.name in {'development-evaluator.json','evaluation-evaluator.json'}:
                raise AssertionError('baseline opened nontraining target')
            return original_read(path)
        with patch.object(baseline, 'read', guarded):
            first = baseline.run(prepared, root/'producer')
            check('whole baseline producer and replay avoid evaluation answers', baseline.run(prepared, root/'producer') == first and first['predictions'] == 8)
        result_path = root/'producer/RESULT.json'; original = result_path.read_bytes()
        changed = original_read(result_path); changed['predictions'][0]['forecast']['explanation'] = 'corrupted'
        result_path.write_text(canonical(changed), encoding='utf8')
        refuse('changed saved baseline output refused', lambda: baseline.run(prepared, root/'producer'))
        result_path.write_bytes(original)
        changed = deepcopy(public['train']); changed['tasks'][0]['evidence']['document'] = 'corrupted'
        (prepared/'train-public.json').write_text(canonical(changed), encoding='utf8')
        refuse('changed training evidence refused', lambda: baseline.run(prepared, root/'producer'))
    result = dict(at=now(), status='PASS', checks=checks, model_calls=0, real_evaluation_answers_opened=False,
                  sources={**baseline.identity(), 'runners/stage10/comparison.py': __import__('hashlib').sha256(Path(measure.__file__).read_bytes()).hexdigest()},
                  scope='known-answer comparison and cheap baseline apparatus; no scientific result')
    write_new(output/'COMPLETE.json', result)
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    result = run(parser.parse_args().output)
    print('PASS', len(result['checks']), 'known-answer checks; zero model calls')
