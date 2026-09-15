"""Known-answer and provenance checks for the late cheap-control supplement."""
from copy import deepcopy
from dataclasses import asdict

import pytest

from . import earlier_baselines as runner, comparison_bank
from .contracts import digest
from .human_memory_checks import task, rows
from .ollama import write_new
from .revision_bank import finish


def earlier(row):
    value = deepcopy(row)
    value['evidence_view'] = 'earlier-artifacts'
    value['evidence']['earlier_drafts'] = ['Earlier permitted draft.']
    return value


def inputs(tmp_path):
    training, answers = rows('signal')
    training = [earlier(r) for r in training]
    evaluation = [earlier(asdict(task('reserved-short', 1))), earlier(asdict(task('reserved-long', 12)))]
    public = {'tasks': training}; labels = {'targets': answers}
    frozen = {'public_sha256': {'train': digest(public)},
              'evaluator_sha256': {'train': digest(labels)}, 'sources': {}}
    selected = {'training_frozen_sha256': digest(frozen),
                'public_sha256': {'evaluation': digest({'tasks': evaluation})}, 'selection_sources': {}}
    prepared, selection = tmp_path/'prepared', tmp_path/'selection'
    for name, value in [('FROZEN', frozen), ('train-public', public), ('train-evaluator', labels)]:
        write_new(prepared/(name+'.json'), value)
    write_new(selection/'FROZEN.json', selected)
    write_new(selection/'evaluation-public.json', {'tasks': evaluation})
    return prepared, selection, training, answers, evaluation


def test_signal_null_and_earlier_evidence_invariance(tmp_path):
    _, _, train, truth, evaluation = inputs(tmp_path)
    fit, pred = runner.forecasts(train, truth, evaluation)
    choices = [dict(r['choices']) for r in evaluation]
    assert [choices[i][pred['surface-features'][r['task_id']]['forecast']['choice']] for i,r in enumerate(evaluation)] == [runner.human_baselines.programs.DESCRIPTIONS[a] for a in ('accept','edit')]
    assert fit['models']['artifact']['prior'].count(0) == 2
    changed = deepcopy(evaluation)
    for row in changed:
        row['evidence']['earlier_drafts'] = ['Completely changed earlier evidence.']
        row['choices'] = tuple(reversed(row['choices']))
    _, other = runner.forecasts(train, truth, changed)
    for arm in runner.ARMS:
        for row in evaluation:
            assert pred[arm][row['task_id']]['forecast'] == other[arm][row['task_id']]['forecast']
    null, labels = rows('null')
    _, predicted = runner.forecasts([earlier(r) for r in null], labels, evaluation)
    assert all(abs(p-.25)<1e-12 for p in predicted['class-prior'][evaluation[0]['task_id']]['forecast']['probabilities'].values())


def test_no_target_access_replay_and_mutation(tmp_path, monkeypatch):
    prepared, selection, _, _, _ = inputs(tmp_path)
    original_read = runner.read
    def guarded(path):
        assert 'evaluation-evaluator' not in str(path)
        return original_read(path)
    monkeypatch.setattr(runner, 'read', guarded)
    result = runner.produce(prepared, selection, tmp_path/'control')
    assert runner.produce(prepared, selection, tmp_path/'control') == result
    path = prepared/'train-public.json'
    value = original_read(path); value['tasks'][0]['evidence']['document'] = 'changed'
    path.write_text(__import__('json').dumps(value), encoding='utf8')
    with pytest.raises(ValueError, match='frozen baseline data'):
        runner.produce(prepared, selection, tmp_path/'other')
    assert not (tmp_path/'other').exists()


def test_private_fields_and_training_overlap_refuse(tmp_path):
    _, _, train, truth, evaluation = inputs(tmp_path)
    evaluation[0]['evidence']['earlier_handling'] = ['edit']
    with pytest.raises(ValueError): runner.forecasts(train, truth, evaluation)
    with pytest.raises(ValueError, match='overlaps training'): runner.forecasts(train, truth, train[:1])


def test_whole_supplement_preserves_original_and_refuses_missing_row(tmp_path):
    prepared, selection, train, truth, evaluation = inputs(tmp_path)
    runner.produce(prepared, selection, tmp_path/'control')
    control = runner.read(tmp_path/'control/RESULT.json')
    baseline = control['predictions']['class-prior']
    answers = {r['task_id']: {'truth':r['choices'][0][0], 'group':'w'+str(i), 'dependencies':['p'], 'event':'e'+str(i)} for i,r in enumerate(evaluation)}
    cell = {'tasks':evaluation,'answers':answers,'predictions':{'R0':baseline},'population':'constructed',
            'contrasts':[],'costs':{'R0':{'model_calls':0}},'scope':'fixture'}
    bundle = {'schema':'stage10.comparison-bank.1','sources':{},'cells':[cell],'scope':'fixture'}
    write_new(tmp_path/'inputs/BUNDLE.json',bundle); finish(tmp_path/'inputs',digest(bundle))
    result = comparison_bank.analyze(bundle)
    write_new(tmp_path/'original/RESULT.json',result); finish(tmp_path/'original',digest(result))
    args = (tmp_path/'inputs',tmp_path/'original',tmp_path/'control',tmp_path/'supplement')
    receipt = runner.supplement(*args)
    assert runner.supplement(*args) == receipt
    revised = runner.read(tmp_path/'supplement/RESULT.json')['results'][0]
    assert revised['cells']['R0'] == result['results'][0]['cells']['R0']
    assert revised['paired']['R0 vs baseline-class-prior']['brier']['estimate'] == 0
    path = tmp_path/'control/RESULT.json'
    data = runner.read(path); data['predictions']['class-prior'].pop(evaluation[0]['task_id'])
    path.write_text(__import__('json').dumps(data),encoding='utf8')
    with pytest.raises(ValueError): runner.supplement(*args)
