"""Complete known protocol grids and destructive substitutions; no reader calls."""
import copy

import pytest

from runners.stage9 import analysis_plan_contracts as subject


def menu(view, extras=()):
    return [view + '-l2-' + penalty + '|' + route for penalty in ('0.01', '0.1')
            for route in ('population', 'brief', 'cheap-8.0', 'cheap-16.0', 'cheap-32.0')] + list(extras)


def selection(contract):
    entry = contract == 'familiarity-entry-v1'
    grouped = contract in ('familiarity-v1', 'familiarity-entry-v1')
    groups = {}; queries = {}
    if contract == 'ambiguity-v1':
        queries = {q: ['inferred', 'committed', 'uniform' if q.startswith('history_') else 'population'] for q in (
            'history_artifact', 'history_after', 'history_record', 'future_old', 'future_changed', 'future_record')}
    elif contract == 'familiarity-v1':
        for view, offset in (('artifact', 0), ('process_record', 4)):
            for kind in ('recognition', 'future'):
                groups[view + '|' + kind] = {'questions': ['q' + str(i) + '|' + kind for i in range(offset, offset + 4)],
                    'eligible': ['prior', 'surface-8.0', 'surface-16.0', 'surface-32.0'] if kind == 'recognition'
                    else menu(view, ('program_prior', 'assume_different'))}
    else:
        for view in ('artifact', 'process_record'):
            if contract == 'constraint-v1':
                queries.update({view + '|' + free + '|' + limit: menu(view, ('program_prior',))
                    for free in ('expanded', 'restricted') for limit in ('loose', 'tight')})
                continue
            keys = [view + '|' + strategy + '|' + str(budget)
                    for strategy in ('affordance', 'anomaly', 'entropy', 'full_scan', 'future_prediction', 'model_information', 'random', 'signature')
                    for budget in ((0, 1, 3) if entry else (0, 1, 3, 7))]
            keys += [view + '|future-stop-' + str(c) + '|stopped' for c in (.05, .2)]
            if entry:
                for q in keys:
                    for familiar in ('familiar', 'unfamiliar'):
                        for expected in ('expected', 'unexpected'):
                            condition = familiar + '|' + expected
                            groups[condition + '::' + q] = {'query': q, 'conditions': [condition], 'eligible': menu(view)}
            else:
                queries.update({q: menu(view) for q in keys})
    return {'operation': 'select', 'role': 'pilot', 'package_sha256': None,
            'contrasts': [], 'groups' if grouped else 'queries': groups if grouped else queries}


def evaluation(contract):
    selected = selection(contract); grouped = 'groups' in selected
    contrasts = []
    for key, value in selected['groups' if grouped else 'queries'].items():
        if contract == 'familiarity-v1':
            side = {'questions': value['questions']}
        elif contract == 'familiarity-entry-v1':
            side = {'conditions': value['conditions'], 'query': value['query']}
        else:
            side = {'query': key}
        contrasts.append({'id': key, 'card': {'ambiguity-v1': 'M05', 'constraint-v1': 'M06', 'selection-v1': 'S02'}.get(contract, 'T02'),
            'left': {**side, 'model': 'inferred'}, 'right': {**side, 'selected_for': key},
            'threshold': .05, 'strata': ['domain', 'purpose'], 'required_controls': ['complete declared grid'],
            'meaning': 'Known protocol fixture, no measured scientific effect.'})
    return {'operation': 'evaluate', 'role': 'pilot', 'package_sha256': None,
            'contrasts': contrasts, 'groups' if grouped else 'queries': {}}


@pytest.mark.parametrize('contract,count', [('ambiguity-v1', 6), ('constraint-v1', 8), ('selection-v1', 68), ('familiarity-v1', 4), ('familiarity-entry-v1', 208)])
def test_complete_existing_selection_and_evaluation_protocol_preserves_definitions(contract, count):
    for template in (selection(contract), evaluation(contract)):
        before = copy.deepcopy(template)
        assert subject.validate(template, contract, 'pilot') == before and template == before
        assert len(template.get('groups', template.get('queries'))) == (count if template['operation'] == 'select' else 0)


@pytest.mark.parametrize('contract', subject.CONTRACTS)
@pytest.mark.parametrize('fault', ['missing_question', 'missing_rival', 'duplicate_rival', 'replacement', 'discovery_selection'])
def test_selection_never_omits_a_condition_or_chooses_an_easier_rival(contract, fault):
    template = selection(contract); groups = template.get('groups'); chosen = groups if groups is not None else template['queries']
    if fault == 'missing_question': chosen.pop(next(iter(chosen)))
    elif fault == 'discovery_selection': template['role'] = 'discovery'
    else:
        names = next(iter(chosen.values())); names = names['eligible'] if groups is not None else names
        if fault == 'missing_rival': names.pop()
        elif fault == 'duplicate_rival': names.append(names[0])
        else: names[0] = 'untrained-easier-rival'
    with pytest.raises(ValueError): subject.validate(template, contract, template['role'])


@pytest.mark.parametrize('contract', subject.CONTRACTS)
@pytest.mark.parametrize('fault', ['missing_grid', 'prebound', 'empty_controls', 'threshold', 'development_evaluation', 'duplicate_contrast'])
def test_evaluation_requires_complete_declared_scope_and_comparisons(contract, fault):
    template = evaluation(contract)
    if fault == 'missing_grid': template['contrasts'].pop()
    elif fault == 'prebound': template['package_sha256'] = '0' * 64
    elif fault == 'empty_controls': template['contrasts'][0]['required_controls'] = []
    elif fault == 'threshold': template['contrasts'][0]['threshold'] = .01
    elif fault == 'development_evaluation': template['role'] = 'development'
    else: template['contrasts'].append(copy.deepcopy(template['contrasts'][0]))
    with pytest.raises(ValueError): subject.validate(template, contract, template['role'])


def test_group_meaning_and_distinct_history_targets_cannot_be_relabelled():
    t = selection('familiarity-v1'); t['groups']['artifact|recognition']['questions'] = ['q4|recognition']
    with pytest.raises(ValueError): subject.validate(t, 'familiarity-v1', 'pilot')
    t = selection('familiarity-entry-v1'); first = next(iter(t['groups'].values())); first['conditions'] = ['unfamiliar|expected', 'familiar|expected']
    with pytest.raises(ValueError): subject.validate(t, 'familiarity-entry-v1', 'pilot')
    t = evaluation('ambiguity-v1'); t['contrasts'][0]['right']['query'] = 'future_changed'
    with pytest.raises(ValueError): subject.validate(t, 'ambiguity-v1', 'pilot')


def test_fitted_menu_is_checked_against_actual_package_not_only_nominal_names():
    t = selection('constraint-v1')
    package = {'models': {'artifact': {'artifact-l2-0.01': {}}, 'process_record': {'process_record-l2-0.01': {}}}}
    with pytest.raises(ValueError): subject.validate(t, 'constraint-v1', 'pilot', package=package)


@pytest.mark.parametrize('query,substitute', [('history_artifact', 'population'), ('future_changed', 'uniform')])
def test_history_uniform_and_future_population_are_distinct_rivals(query, substitute):
    t = selection('ambiguity-v1')
    assert t['queries']['history_artifact'] == ['inferred', 'committed', 'uniform']
    assert t['queries']['future_changed'] == ['inferred', 'committed', 'population']
    t['queries'][query][-1] = substitute
    with pytest.raises(ValueError): subject.validate(t, 'ambiguity-v1', 'pilot')
