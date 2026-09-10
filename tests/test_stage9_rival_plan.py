"""Known-answer future-package binding and refusal checks; no training occurs."""
import copy
from pathlib import Path

import pytest

from runners.stage9 import common, queue, revision_predictions, rival_plan as subject
from runners.stage9.common import closure, digest, file_hash, read, write


def refresh_fixture_commit(tmp_path, declaration, plan, state, q, path, manifest):
    """Re-sign a constructed original queue, not a changed production receipt."""
    write(path, declaration)
    own, producer = plan['jobs'][1], plan['jobs'][0]
    own['arguments'][own['arguments'].index('--declaration-sha256') + 1] = file_hash(path)
    state['manifest_sha256'] = digest(plan)
    model_cell = digest({'manifest_sha256': digest(plan), 'job': producer})
    model = tmp_path / 'models'; identity = read(model / 'IDENTITY.json'); identity['cell_identity'] = model_cell
    done = read(model / 'COMPLETE.json'); done.update(cell_identity=model_cell, identity_sha256=digest(identity),
        role=producer['arguments'][producer['arguments'].index('--role') + 1])
    write(model / 'IDENTITY.json', identity); write(model / 'COMPLETE.json', done)
    execution = q / 'attempt/EXECUTION.json'; actual = read(execution); actual['cell_identity'] = model_cell; write(execution, actual)
    commit = read(q / 'commits/models.json'); commit.update(manifest_sha256=digest(plan), cell_identity=model_cell,
        produce_sha256=file_hash(model / 'COMPLETE.json'), execution_sha256=file_hash(execution))
    write(q / 'commits/models.json', commit); write(manifest, plan); write(q / 'MANIFEST.json', plan); write(q / 'STATUS.json', state)
    return digest({'manifest_sha256': digest(plan), 'job': own}), file_hash(path)


def fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(subject, 'REPO', tmp_path)
    monkeypatch.setattr(queue, 'REPO', tmp_path)
    monkeypatch.setattr(common, 'REPO', tmp_path)
    monkeypatch.setattr(revision_predictions, 'REPO', tmp_path)
    monkeypatch.setattr(subject, 'ROOT', tmp_path)
    def inside(path):
        path = Path(path).resolve()
        if not path.is_relative_to(tmp_path):
            raise ValueError('fixture path escapes its root')
        return path
    monkeypatch.setattr(subject, 'inside', inside)
    output = tmp_path / 'private/rival-plan-pilots/one'
    declaration_path = tmp_path / 'DECLARATION.json'
    manifest = tmp_path / 'PLAN.json'; q = tmp_path / 'queue'; model = tmp_path / 'models'
    producer = {'id': 'models', 'module': 'runners.stage9.artifact_models', 'role': 'work', 'resource': 'cpu',
                'arguments': ['--root', str(model), '--role', 'pilot'], 'produces': 'models/COMPLETE.json'}
    own = {'id': 'bind', 'module': subject.MODULE, 'role': 'work', 'resource': 'cpu', 'after': ['models'],
           'arguments': ['--output', str(output), '--declaration', str(declaration_path), '--manifest', str(manifest),
                         '--queue', str(q), '--scope', 'pilot'],
           'produces': 'private/rival-plan-pilots/one/COMPLETE.json'}
    required = ('source_bootstrap', 'common', 'process_identity', 'artifact_models')
    source = {f'runners/stage9/{name}.py': digest(name) for name in required}
    plan = {'kind': 'prelaunch_rehearsal', 'sources': {'files': source, 'sha256': digest(source)}, 'jobs': [producer, own]}
    state = {'manifest_sha256': digest(plan), 'jobs': {'models': {'status': 'COMPLETE'}}}
    model_cell = digest({'manifest_sha256': digest(plan), 'job': producer})
    identity = {'operation': 'artifact-model-training-v1', 'cell_identity': model_cell}
    done = {'cell_identity': model_cell, 'identity_sha256': digest(identity), 'role': 'pilot', 'accepted': True, 'training_only': True}
    write(model / 'IDENTITY.json', identity); write(model / 'COMPLETE.json', done)
    execution = q / 'attempt/EXECUTION.json'
    write(execution, {'returncode': 0, 'cell_identity': model_cell, 'loaded_project_sources': source})
    write(q / 'commits/models.json', {'manifest_sha256': digest(plan), 'cell_identity': model_cell,
          'produce_sha256': file_hash(model / 'COMPLETE.json'), 'execution_path': 'attempt/EXECUTION.json', 'execution_sha256': file_hash(execution)})
    models = {view: {view + '-l2-0.01': {}, view + '-l2-0.1': {}} for view in ('artifact', 'process_record')}
    observed = []
    def fitted(path, role):
        observed.append((path, role))
        return {'models': models, 'completion_sha256': file_hash(path / 'COMPLETE.json')}
    monkeypatch.setattr(subject, 'model_inputs', fitted)
    declaration = {'model_job': 'models', 'model_path': 'models/COMPLETE.json', 'role': 'pilot',
                   'queries': {view + '|dose0': [name + '|' + route for name in candidates for route in subject.ROUTES]
                               for view, candidates in models.items()}}
    write(declaration_path, declaration); write(manifest, plan); write(q / 'MANIFEST.json', plan); write(q / 'STATUS.json', state)
    cell = digest({'manifest_sha256': digest(plan), 'job': own})
    return declaration, plan, state, q, cell, observed, output, declaration_path, manifest


def test_complete_actual_commit_binds_checksum_and_preserves_fixed_menu(tmp_path, monkeypatch):
    declaration, plan, state, q, cell, observed, *_ = fixture(tmp_path, monkeypatch)
    before = copy.deepcopy(declaration)
    actual, binding = subject.resolve(declaration, plan, state, q, cell, 'pilot')
    assert actual == {'operation': 'select', 'role': 'pilot', 'queries': declaration['queries'],
                      'contrasts': [], 'package_sha256': file_hash(tmp_path / 'models/COMPLETE.json')}
    assert binding['model_job'] == 'models' and binding['model_complete_sha256'] == actual['package_sha256']
    assert observed == [(tmp_path / 'models', 'pilot')] and declaration == before


@pytest.mark.parametrize('fault', ['running', 'failed', 'missing_dependency', 'wrong_module', 'different_path', 'wrong_cell', 'scope', 'role', 'changed_completion', 'changed_execution'])
def test_unfinished_or_substituted_producer_refuses_before_package_loading(tmp_path, monkeypatch, fault):
    declaration, plan, state, q, cell, observed, *_ = fixture(tmp_path, monkeypatch)
    if fault in ('running', 'failed'): state['jobs']['models']['status'] = fault.upper()
    elif fault == 'missing_dependency': plan['jobs'][1]['after'] = []
    elif fault == 'wrong_module': plan['jobs'][0]['module'] = 'runners.stage9.other'
    elif fault == 'different_path': declaration['model_path'] = 'replacement/COMPLETE.json'
    elif fault == 'scope': plan['kind'] = 'science'
    elif fault == 'role': declaration['role'] = 'discovery'
    elif fault == 'changed_completion': write(tmp_path / 'models/COMPLETE.json', {'substituted': True})
    elif fault == 'changed_execution': write(q / 'attempt/EXECUTION.json', {'substituted': True})
    state['manifest_sha256'] = digest(plan)
    cell = '0' * 64 if fault == 'wrong_cell' else digest({'manifest_sha256': digest(plan), 'job': plan['jobs'][1]})
    with pytest.raises(ValueError): subject.resolve(declaration, plan, state, q, cell, 'pilot')
    assert observed == []


@pytest.mark.parametrize('fault', ['omitted', 'duplicate', 'replacement', 'unsupported_view', 'unsupported_dose', 'empty'])
def test_changed_eligible_menu_cannot_silently_choose_an_easier_rival(tmp_path, monkeypatch, fault):
    declaration, plan, state, q, cell, *_ = fixture(tmp_path, monkeypatch)
    names = declaration['queries']['artifact|dose0']
    if fault == 'omitted': names.pop()
    elif fault == 'duplicate': names.append(names[0])
    elif fault == 'replacement': names[0] = 'untrained|population'
    elif fault == 'empty': declaration['queries'] = {}
    else:
        key = 'hidden|dose0' if fault == 'unsupported_view' else 'artifact|dose2'
        declaration['queries'][key] = declaration['queries'].pop('artifact|dose0')
    with pytest.raises(ValueError): subject.resolve(declaration, plan, state, q, cell, 'pilot')


def test_handler_preserves_reentry_and_refuses_rehashed_plan_substitution(tmp_path, monkeypatch):
    declaration, plan, state, q, cell, observed, output, declaration_path, manifest = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(subject, 'cell_identity', lambda: cell)
    # The fixture supplies deliberately synthetic compiled metadata; only this
    # fixture bypasses whole-repository source/manifest admission, never production.
    monkeypatch.setattr(subject, 'validate_manifest', lambda p: None)
    monkeypatch.setattr(subject, 'verify_sources', lambda s: None)
    monkeypatch.setattr(subject, 'sources', lambda: closure([declaration_path]))
    done = subject.run(output, declaration_path, manifest, q, 'pilot')
    assert done['execution_complete'] and done['predictions_or_scores_computed'] is False
    first = closure([output])
    assert subject.run(output, declaration_path, manifest, q, 'pilot') == done
    assert closure([output]) == first
    selected = read(output / 'SELECTION_PLAN.json'); selected['package_sha256'] = '0' * 64
    write(output / 'SELECTION_PLAN.json', selected)
    # Even refreshing a plain output checksum cannot change the resolved package.
    done['outputs'] = closure([output / 'IDENTITY.json', output / 'SELECTION_PLAN.json'])
    write(output / 'COMPLETE.json', done)
    with pytest.raises(ValueError, match='does not reconstruct'):
        subject.run(output, declaration_path, manifest, q, 'pilot')


def evaluation_fixture(tmp_path, monkeypatch):
    declaration, plan, state, q, cell, observed, output, declaration_path, manifest = fixture(tmp_path, monkeypatch)
    declaration.pop('queries')
    declaration['template'] = {
        'operation': 'evaluate', 'role': 'pilot', 'queries': {}, 'package_sha256': None,
        'contrasts': [{'id': 'prospective', 'card': 'M03',
            'left': {'query': 'process_record|dose7', 'model': 'purpose_inferred'},
            'right': {'query': 'process_record|dose7', 'selected_for': 'process_record|dose7'},
            'threshold': .05, 'strata': ['domain'], 'required_controls': ['wrong_purpose'],
            'meaning': 'Held-out purpose inference against the independently selected complete ordinary menu.'}]}
    write(declaration_path, declaration)
    sha = file_hash(declaration_path)
    output = tmp_path / 'private/evaluation-plan-pilots/one'
    own = plan['jobs'][1]
    own['arguments'][1] = str(output)
    own['arguments'] += ['--declaration-sha256', sha]
    own['produces'] = 'private/evaluation-plan-pilots/one/COMPLETE.json'
    state['manifest_sha256'] = digest(plan)
    producer = plan['jobs'][0]; model_cell = digest({'manifest_sha256': digest(plan), 'job': producer})
    model = tmp_path / 'models'; identity = read(model / 'IDENTITY.json'); identity['cell_identity'] = model_cell
    done = read(model / 'COMPLETE.json'); done.update(cell_identity=model_cell, identity_sha256=digest(identity))
    write(model / 'IDENTITY.json', identity); write(model / 'COMPLETE.json', done)
    execution = q / 'attempt/EXECUTION.json'; actual = read(execution); actual['cell_identity'] = model_cell; write(execution, actual)
    commit = read(q / 'commits/models.json'); commit.update(manifest_sha256=digest(plan), cell_identity=model_cell,
        produce_sha256=file_hash(model / 'COMPLETE.json'), execution_sha256=file_hash(execution))
    write(q / 'commits/models.json', commit); write(manifest, plan); write(q / 'MANIFEST.json', plan); write(q / 'STATUS.json', state)
    cell = digest({'manifest_sha256': digest(plan), 'job': own})
    return declaration, plan, state, q, cell, observed, output, declaration_path, manifest, sha


def paired_fixture(tmp_path, monkeypatch):
    declaration, plan, state, q, _, observed, _, path, manifest, _ = evaluation_fixture(tmp_path, monkeypatch)
    template = declaration.pop('template')
    template.pop('operation'); template.pop('queries')
    template['contrasts'] = [{'id': 'goal-minus-difficulty', 'card': 'T03',
        'left': {'query': 'process_record|goal', 'model': 'inferred_changed', 'baseline': 'inferred_stale'},
        'right': {'query': 'process_record|harder', 'model': 'inferred_changed', 'baseline': 'inferred_stale'},
        'threshold': .05, 'strata': ['domain', 'purpose'],
        'required_controls': ['paired-base-units', 'distinct-actual-targets'],
        'meaning': 'Difference of prospective gains under goal change and unchanged-goal difficulty.'}]
    declaration['paired_template'] = template
    output = tmp_path / 'private/paired-plan-pilots/one'
    own = plan['jobs'][1]; own['arguments'][1] = str(output)
    own['produces'] = 'private/paired-plan-pilots/one/COMPLETE.json'
    cell, sha = refresh_fixture_commit(tmp_path, declaration, plan, state, q, path, manifest)
    return declaration, plan, state, q, cell, observed, output, path, manifest, sha


def test_paired_binding_preserves_both_conditions_and_consumer_plan_shape(tmp_path, monkeypatch):
    declaration, plan, state, q, cell, observed, *_ = paired_fixture(tmp_path, monkeypatch)
    before = copy.deepcopy(declaration)
    actual, binding = subject.resolve(declaration, plan, state, q, cell, 'pilot')
    assert actual == {**before['paired_template'], 'package_sha256': file_hash(tmp_path / 'models/COMPLETE.json')}
    assert set(actual) == {'role', 'contrasts', 'package_sha256'}
    assert declaration == before and observed == [(tmp_path / 'models', 'pilot')]
    assert binding['model_complete_sha256'] == actual['package_sha256']


@pytest.mark.parametrize('fault', ['ordinary_template', 'both_templates', 'prebound', 'development',
    'selected_baseline', 'missing_baseline', 'empty_baseline', 'query_menu', 'task_contract',
    'empty_controls', 'duplicate_controls', 'duplicate_id', 'threshold', 'running', 'changed_execution'])
def test_paired_binding_refuses_changed_question_or_producer_before_model_load(tmp_path, monkeypatch, fault):
    declaration, plan, state, q, cell, observed, *_ = paired_fixture(tmp_path, monkeypatch)
    template = declaration['paired_template']; contrast = template['contrasts'][0]
    if fault == 'ordinary_template': declaration['template'] = declaration.pop('paired_template')
    elif fault == 'both_templates': declaration['template'] = copy.deepcopy(template)
    elif fault == 'prebound': template['package_sha256'] = '0' * 64
    elif fault == 'development': template['role'] = declaration['role'] = 'development'
    elif fault == 'selected_baseline': contrast['right']['selected_for'] = contrast['right'].pop('baseline')
    elif fault == 'missing_baseline': del contrast['left']['baseline']
    elif fault == 'empty_baseline': contrast['left']['baseline'] = ' '
    elif fault == 'query_menu': template['queries'] = {}
    elif fault == 'task_contract': declaration['query_contract'] = 'goal-change-v1'
    elif fault == 'empty_controls': contrast['required_controls'] = []
    elif fault == 'duplicate_controls': contrast['required_controls'] *= 2
    elif fault == 'duplicate_id': template['contrasts'].append(copy.deepcopy(contrast))
    elif fault == 'threshold': contrast['threshold'] = .01
    elif fault == 'running': state['jobs']['models']['status'] = 'RUNNING'
    elif fault == 'changed_execution': write(q / 'attempt/EXECUTION.json', {'substitution': True})
    with pytest.raises(ValueError): subject.resolve(declaration, plan, state, q, cell, 'pilot')
    assert observed == []


def test_paired_handler_requires_original_checksum_namespace_and_byte_stable_reentry(tmp_path, monkeypatch):
    declaration, plan, state, q, cell, observed, output, path, manifest, sha = paired_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(subject, 'cell_identity', lambda: cell)
    monkeypatch.setattr(subject, 'validate_manifest', lambda p: None)
    monkeypatch.setattr(subject, 'verify_sources', lambda s: None)
    monkeypatch.setattr(subject, 'sources', lambda: closure([manifest]))
    with pytest.raises(ValueError, match='frozen checksum'): subject.run(output, path, manifest, q, 'pilot')
    with pytest.raises(ValueError, match='output scope'):
        subject.run(tmp_path / 'private/evaluation-plan-pilots/one', path, manifest, q, 'pilot', declaration_sha256=sha)
    assert observed == []
    done = subject.run(output, path, manifest, q, 'pilot', declaration_sha256=sha); before = closure([output])
    assert subject.run(output, path, manifest, q, 'pilot', declaration_sha256=sha) == done
    assert before == closure([output]) and done['predictions_or_scores_computed'] is False
    assert read(output / 'PAIRED_PLAN.json') == {**declaration['paired_template'], 'package_sha256': file_hash(tmp_path / 'models/COMPLETE.json')}
    observed.clear(); declaration['paired_template']['contrasts'][0]['left']['baseline'] = 'easier'
    write(path, declaration)
    with pytest.raises(ValueError, match='frozen checksum'):
        subject.run(output, path, manifest, q, 'pilot', declaration_sha256=sha)
    with pytest.raises(ValueError, match='original queue argument'):
        subject.run(output, path, manifest, q, 'pilot', declaration_sha256=file_hash(path))
    assert observed == [] and before == closure([output])


@pytest.mark.parametrize('producer_role', ['training', 'pilot'])
def test_scientific_paired_binding_uses_only_actual_training_package(tmp_path, monkeypatch, producer_role):
    declaration, plan, state, q, _, observed, output, path, manifest, _ = paired_fixture(tmp_path, monkeypatch)
    plan['kind'] = 'science'; declaration['role'] = declaration['paired_template']['role'] = 'discovery'
    plan['jobs'][0]['arguments'][-1] = producer_role
    cell, _ = refresh_fixture_commit(tmp_path, declaration, plan, state, q, path, manifest)
    if producer_role == 'pilot':
        with pytest.raises(ValueError, match='wrong scope'):
            subject.resolve(declaration, plan, state, q, cell, 'scientific')
        assert observed == []
    else:
        actual, _ = subject.resolve(declaration, plan, state, q, cell, 'scientific')
        assert actual['role'] == 'discovery' and set(actual) == {'role', 'package_sha256', 'contrasts'}
        assert observed == [(tmp_path / 'models', 'discovery')]


@pytest.mark.parametrize('kind,contract,expected', [
    ('queries', None, 'bind-selection'), ('template', None, 'bind-evaluation'),
    ('paired_template', None, 'bind-paired'),
    ('queries', 'goal-change-v1', 'bind-selection-goal-change-v1')])
def test_launch_rehearsal_distinguishes_materializer_operations(tmp_path, monkeypatch, kind, contract, expected):
    from runners.stage9 import launch
    monkeypatch.setattr(launch, 'REPO', tmp_path)
    path = tmp_path / 'declaration.json'; declaration = {kind: {}}
    if contract: declaration['query_contract'] = contract
    write(path, declaration)
    job = {'module': subject.MODULE, 'arguments': ['--declaration', str(path), '--declaration-sha256', file_hash(path)]}
    assert launch.handler_operation(job) == (subject.MODULE, expected, None, None)
    if kind != 'queries' or contract:
        write(path, {**declaration, 'substituted': True})
        with pytest.raises(ValueError, match='checksum changed'): launch.handler_operation(job)


def consumer_fixture(tmp_path, monkeypatch, contract, operation):
    from tests.test_stage9_analysis_plan_contracts import selection, evaluation
    declaration, plan, state, q, _, observed, _, path, manifest, _ = evaluation_fixture(tmp_path, monkeypatch)
    declaration.pop('template'); declaration['analysis_contract'] = contract
    declaration['analysis_template'] = selection(contract) if operation == 'select' else evaluation(contract)
    output = tmp_path / 'private/consumer-plan-pilots/one'; own = plan['jobs'][1]
    own['arguments'][1] = str(output); own['produces'] = 'private/consumer-plan-pilots/one/COMPLETE.json'
    cell, sha = refresh_fixture_commit(tmp_path, declaration, plan, state, q, path, manifest)
    return declaration, plan, state, q, cell, observed, output, path, manifest, sha


@pytest.mark.parametrize('contract', ['ambiguity-v1', 'constraint-v1', 'selection-v1', 'familiarity-v1', 'familiarity-entry-v1'])
@pytest.mark.parametrize('operation', ['select', 'evaluate'])
def test_consumer_handler_preserves_full_template_and_refuses_rehashed_replacement(tmp_path, monkeypatch, contract, operation):
    from runners.stage9 import launch
    d, plan, state, q, cell, observed, output, path, manifest, sha = consumer_fixture(tmp_path, monkeypatch, contract, operation)
    monkeypatch.setattr(subject, 'cell_identity', lambda: cell)
    monkeypatch.setattr(subject, 'validate_manifest', lambda p: None)
    monkeypatch.setattr(subject, 'verify_sources', lambda s: None)
    monkeypatch.setattr(subject, 'sources', lambda: closure([manifest]))
    monkeypatch.setattr(launch, 'REPO', tmp_path)
    assert launch.handler_operation(plan['jobs'][1])[1] == 'bind-consumer-' + contract + '-' + operation
    done = subject.run(output, path, manifest, q, 'pilot', declaration_sha256=sha)
    before = closure([output]); filename = 'SELECTION_PLAN.json' if operation == 'select' else 'EVALUATION_PLAN.json'
    assert read(output / filename) == {**d['analysis_template'], 'package_sha256': file_hash(tmp_path / 'models/COMPLETE.json')}
    assert done['predictions_or_scores_computed'] is False
    assert subject.run(output, path, manifest, q, 'pilot', declaration_sha256=sha) == done and closure([output]) == before
    observed.clear(); d['analysis_template']['role'] = 'discovery'; write(path, d)
    with pytest.raises(ValueError, match='frozen checksum'):
        subject.run(output, path, manifest, q, 'pilot', declaration_sha256=sha)
    with pytest.raises(ValueError, match='original queue argument'):
        subject.run(output, path, manifest, q, 'pilot', declaration_sha256=file_hash(path))
    assert observed == [] and closure([output]) == before


@pytest.mark.parametrize('operation', ['select', 'evaluate'])
@pytest.mark.parametrize('producer_role', ['training', 'pilot'])
def test_scientific_consumer_role_and_original_training_producer_stay_separate(tmp_path, monkeypatch, operation, producer_role):
    d, plan, state, q, _, observed, _, path, manifest, _ = consumer_fixture(tmp_path, monkeypatch, 'familiarity-v1', operation)
    plan['kind'] = 'science'; d['role'] = d['analysis_template']['role'] = 'development' if operation == 'select' else 'discovery'
    plan['jobs'][0]['arguments'][-1] = producer_role
    cell, _ = refresh_fixture_commit(tmp_path, d, plan, state, q, path, manifest)
    if producer_role == 'pilot':
        with pytest.raises(ValueError, match='wrong scope'): subject.resolve(d, plan, state, q, cell, 'scientific')
        assert observed == []
    else:
        bound, _ = subject.resolve(d, plan, state, q, cell, 'scientific')
        assert bound['operation'] == operation and bound['role'] == d['role']
        assert observed == [(tmp_path / 'models', d['role'])]


def test_evaluation_binds_only_actual_package_preserving_all_declared_contrasts(tmp_path, monkeypatch):
    declaration, plan, state, q, cell, observed, *_ = evaluation_fixture(tmp_path, monkeypatch)
    before = copy.deepcopy(declaration)
    actual, binding = subject.resolve(declaration, plan, state, q, cell, 'pilot')
    assert actual == {**before['template'], 'package_sha256': file_hash(tmp_path / 'models/COMPLETE.json')}
    assert declaration == before and observed == [(tmp_path / 'models', 'pilot')]
    assert binding['model_complete_sha256'] == actual['package_sha256']


@pytest.mark.parametrize('fault', ['running', 'failed', 'wrong_role', 'pilot_as_science', 'changed_completion', 'changed_execution'])
def test_evaluation_preserves_original_training_producer_guards(tmp_path, monkeypatch, fault):
    declaration, plan, state, q, cell, observed, *_ = evaluation_fixture(tmp_path, monkeypatch)
    if fault in ('running', 'failed'): state['jobs']['models']['status'] = fault.upper()
    elif fault == 'wrong_role': declaration['role'] = 'development'
    elif fault == 'pilot_as_science': plan['kind'] = 'science'
    elif fault == 'changed_completion': write(tmp_path / 'models/COMPLETE.json', {'substituted': True})
    elif fault == 'changed_execution': write(q / 'attempt/EXECUTION.json', {'substituted': True})
    with pytest.raises(ValueError): subject.resolve(declaration, plan, state, q, cell, 'pilot')
    assert observed == []


@pytest.mark.parametrize('fault', ['prebound_package', 'selection', 'development', 'query_menu', 'empty',
    'duplicate', 'threshold', 'no_meaning', 'missing_control_field', 'ambiguous_side', 'duplicate_stratum'])
def test_evaluation_refuses_undeclared_or_repurposed_template_before_loading_model(tmp_path, monkeypatch, fault):
    declaration, plan, state, q, cell, observed, *_ = evaluation_fixture(tmp_path, monkeypatch)
    template = declaration['template']; contrast = template['contrasts'][0]
    if fault == 'prebound_package': template['package_sha256'] = '0' * 64
    elif fault == 'selection': template['operation'] = 'select'
    elif fault == 'development': template['role'] = 'development'
    elif fault == 'query_menu': template['queries'] = {'process_record|dose7': ['easier_rival']}
    elif fault == 'empty': template['contrasts'] = []
    elif fault == 'duplicate': template['contrasts'].append(copy.deepcopy(contrast))
    elif fault == 'threshold': contrast['threshold'] = 0
    elif fault == 'no_meaning': contrast['meaning'] = ' '
    elif fault == 'missing_control_field': del contrast['required_controls']
    elif fault == 'ambiguous_side': contrast['right']['model'] = 'arbitrary'
    elif fault == 'duplicate_stratum': contrast['strata'].append('domain')
    with pytest.raises(ValueError): subject.resolve(declaration, plan, state, q, cell, 'pilot')
    assert observed == []


def test_evaluation_actual_handler_pins_original_template_and_reconstructs_reentry(tmp_path, monkeypatch):
    declaration, plan, state, q, cell, observed, output, path, manifest, sha = evaluation_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(subject, 'cell_identity', lambda: cell)
    monkeypatch.setattr(subject, 'validate_manifest', lambda p: None)
    monkeypatch.setattr(subject, 'verify_sources', lambda s: None)
    monkeypatch.setattr(subject, 'sources', lambda: closure([manifest]))
    done = subject.run(output, path, manifest, q, 'pilot', declaration_sha256=sha)
    before = closure([output])
    assert subject.run(output, path, manifest, q, 'pilot', declaration_sha256=sha) == done
    assert closure([output]) == before and done['predictions_or_scores_computed'] is False
    bound = read(output / 'EVALUATION_PLAN.json')
    assert bound == {**declaration['template'], 'package_sha256': file_hash(tmp_path / 'models/COMPLETE.json')}
    observed.clear()
    declaration['template']['contrasts'][0]['left']['model'] = 'substituted_after_lock'
    write(path, declaration)
    with pytest.raises(ValueError, match='frozen checksum'):
        subject.run(output, path, manifest, q, 'pilot', declaration_sha256=sha)
    with pytest.raises(ValueError, match='original queue argument'):
        subject.run(output, path, manifest, q, 'pilot', declaration_sha256=file_hash(path))
    assert observed == [] and closure([output]) == before


def test_evaluation_requires_checksum_and_original_invocation_path(tmp_path, monkeypatch):
    declaration, plan, state, q, cell, observed, output, path, manifest, sha = evaluation_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(subject, 'cell_identity', lambda: cell)
    monkeypatch.setattr(subject, 'validate_manifest', lambda p: None)
    monkeypatch.setattr(subject, 'verify_sources', lambda s: None)
    with pytest.raises(ValueError, match='frozen checksum'):
        subject.run(output, path, manifest, q, 'pilot')
    replacement = tmp_path / 'REPLACEMENT.json'; write(replacement, declaration)
    with pytest.raises(ValueError, match='original queue arguments'):
        subject.run(output, replacement, manifest, q, 'pilot', declaration_sha256=sha)
    assert observed == [] and not output.exists()


@pytest.mark.parametrize('producer_role', ['training', 'pilot'])
def test_scientific_discovery_binding_requires_training_scope_even_with_valid_commit(tmp_path, monkeypatch, producer_role):
    declaration, plan, state, q, cell, observed, *_ = evaluation_fixture(tmp_path, monkeypatch)
    plan['kind'] = 'science'; declaration['role'] = declaration['template']['role'] = 'discovery'
    producer = plan['jobs'][0]; producer['arguments'][-1] = producer_role
    state['manifest_sha256'] = digest(plan)
    model_cell = digest({'manifest_sha256': digest(plan), 'job': producer})
    model = tmp_path / 'models'; identity = read(model / 'IDENTITY.json'); identity['cell_identity'] = model_cell
    done = read(model / 'COMPLETE.json'); done.update(cell_identity=model_cell, identity_sha256=digest(identity), role=producer_role)
    write(model / 'IDENTITY.json', identity); write(model / 'COMPLETE.json', done)
    execution = q / 'attempt/EXECUTION.json'; actual = read(execution); actual['cell_identity'] = model_cell; write(execution, actual)
    commit = read(q / 'commits/models.json'); commit.update(manifest_sha256=digest(plan), cell_identity=model_cell,
        produce_sha256=file_hash(model / 'COMPLETE.json'), execution_sha256=file_hash(execution))
    write(q / 'commits/models.json', commit)
    cell = digest({'manifest_sha256': digest(plan), 'job': plan['jobs'][1]})
    if producer_role == 'pilot':
        with pytest.raises(ValueError, match='wrong scope'):
            subject.resolve(declaration, plan, state, q, cell, 'scientific')
        assert observed == []
    else:
        actual, _ = subject.resolve(declaration, plan, state, q, cell, 'scientific')
        assert actual['role'] == 'discovery' and actual['operation'] == 'evaluate'
        assert observed == [(model, 'discovery')]


def task_declaration(declaration, contract):
    declaration = copy.deepcopy(declaration); declaration['query_contract'] = contract
    queries, population = subject.QUERY_CONTRACTS[contract]
    names = ([population, 'cheap-8.0', 'cheap-16.0', 'cheap-32.0'] if population else
             declaration['queries']['process_record|dose0'])
    declaration['queries'] = {query: list(names) for query in queries}
    return declaration


@pytest.mark.parametrize('contract,queries,names', [
    ('library-withdrawn-v1', {'process_record|withdrawn'}, None),
    ('goal-change-v1', {'process_record|goal'}, {'population_changed', 'cheap-8.0', 'cheap-16.0', 'cheap-32.0'}),
    ('unchanged-goal-harder-v1', {'process_record|harder'}, {'population_changed', 'cheap-8.0', 'cheap-16.0', 'cheap-32.0'}),
    ('context-report-v1', {'process_record|true', 'process_record|false', 'process_record|redundant'},
     {'population_cued', 'cheap-8.0', 'cheap-16.0', 'cheap-32.0'}),
])
def test_task_contract_preserves_its_actual_query_and_full_rival_menu(tmp_path, monkeypatch, contract, queries, names):
    declaration, plan, state, q, cell, observed, *_ = fixture(tmp_path, monkeypatch)
    ordinary = set(declaration['queries']['process_record|dose0'])
    declaration = task_declaration(declaration, contract);before = copy.deepcopy(declaration)
    bound, _ = subject.resolve(declaration, plan, state, q, cell, 'pilot')
    assert set(bound['queries']) == queries and declaration == before
    assert all(set(menu) == (ordinary if names is None else names) for menu in bound['queries'].values())
    assert bound['operation'] == 'select' and bound['role'] == 'pilot' and observed == [(tmp_path / 'models', 'pilot')]


@pytest.mark.parametrize('fault', ['unknown', 'missing_treatment', 'wrong_query', 'omitted_rival', 'duplicate_rival', 'wrong_population', 'discovery_selection'])
def test_task_contract_cannot_omit_conditions_or_substitute_the_ordinary_comparison(tmp_path, monkeypatch, fault):
    declaration, plan, state, q, cell, *_ = fixture(tmp_path, monkeypatch)
    declaration = task_declaration(declaration, 'context-report-v1')
    if fault == 'unknown': declaration['query_contract'] = 'arbitrary-task'
    elif fault == 'missing_treatment': del declaration['queries']['process_record|redundant']
    elif fault == 'wrong_query': declaration['queries']['process_record|dose7'] = declaration['queries'].pop('process_record|true')
    elif fault == 'omitted_rival': declaration['queries']['process_record|true'].pop()
    elif fault == 'duplicate_rival': declaration['queries']['process_record|true'].append('population_cued')
    elif fault == 'wrong_population': declaration['queries']['process_record|true'][0] = 'population_changed'
    elif fault == 'discovery_selection': declaration['role'] = 'discovery'
    with pytest.raises(ValueError): subject.resolve(declaration, plan, state, q, cell, 'pilot')


def test_task_contract_handler_requires_original_checksum_and_reenters_immutably(tmp_path, monkeypatch):
    declaration, plan, state, q, cell, observed, output, path, manifest = fixture(tmp_path, monkeypatch)
    declaration = task_declaration(declaration, 'goal-change-v1');write(path, declaration);sha = file_hash(path)
    plan['jobs'][1]['arguments'] += ['--declaration-sha256', sha]
    state['manifest_sha256'] = digest(plan);producer = plan['jobs'][0]
    model_cell = digest({'manifest_sha256': digest(plan), 'job': producer});model = tmp_path / 'models'
    identity = read(model / 'IDENTITY.json');identity['cell_identity'] = model_cell
    done = read(model / 'COMPLETE.json');done.update(cell_identity=model_cell, identity_sha256=digest(identity))
    write(model / 'IDENTITY.json', identity);write(model / 'COMPLETE.json', done)
    execution = q / 'attempt/EXECUTION.json';actual = read(execution);actual['cell_identity'] = model_cell;write(execution, actual)
    commit = read(q / 'commits/models.json');commit.update(manifest_sha256=digest(plan), cell_identity=model_cell,
        produce_sha256=file_hash(model / 'COMPLETE.json'), execution_sha256=file_hash(execution))
    write(q / 'commits/models.json', commit);write(manifest, plan);write(q / 'MANIFEST.json', plan);write(q / 'STATUS.json', state)
    cell = digest({'manifest_sha256': digest(plan), 'job': plan['jobs'][1]})
    monkeypatch.setattr(subject, 'cell_identity', lambda: cell)
    monkeypatch.setattr(subject, 'validate_manifest', lambda p: None)
    monkeypatch.setattr(subject, 'verify_sources', lambda s: None)
    monkeypatch.setattr(subject, 'sources', lambda: closure([manifest]))
    with pytest.raises(ValueError, match='frozen checksum'): subject.run(output, path, manifest, q, 'pilot')
    assert observed == [] and not output.exists()
    done = subject.run(output, path, manifest, q, 'pilot', declaration_sha256=sha);before = closure([output])
    assert subject.run(output, path, manifest, q, 'pilot', declaration_sha256=sha) == done and closure([output]) == before
    assert read(output / 'SELECTION_PLAN.json')['queries'] == declaration['queries']
    observed.clear();declaration['query_contract'] = 'unchanged-goal-harder-v1'
    declaration['queries']['process_record|harder'] = declaration['queries'].pop('process_record|goal');write(path, declaration)
    with pytest.raises(ValueError, match='original queue argument'):
        subject.run(output, path, manifest, q, 'pilot', declaration_sha256=file_hash(path))
    assert observed == [] and closure([output]) == before
