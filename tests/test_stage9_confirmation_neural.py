import copy
from contextlib import contextmanager
import math
from pathlib import Path

import pytest

from runners.stage9 import confirmation_neural as subject, confirmation_access as access, common, launch, revision_predictions
from runners.stage9.common import closure, digest, file_hash, read, write
from runners.stage9.confirmation_statistics import CONTRACT
from runners.stage9.confirmation_planning import unit_estimates


def rows():
    return [{'unit': u, 'target': 'next_recorded_event', 'truth': 'a', 'role': 'reserve', 'seed': s,
             'sides': {side: {'valid': True, 'evidence_sha256': digest([u, side]),
                              'probabilities': {'a': p, 'b': 1-p}}
                       for side, p in [('left', .8), ('right', .5)]}}
            for u in ('a', 'b') for s in subject.SEEDS]


def test_all_seeds_average_within_sources_and_null_stays_zero():
    data = rows()
    data[0]['sides']['left']['probabilities'] = {'a': .2, 'b': .8}
    outcome = subject.calculation_input(data, ['a', 'b'])
    summary = unit_estimates(outcome['paired_rows'], list(subject.SEEDS))
    assert summary['n_units'] == 2
    assert summary['values'] == pytest.approx([(math.log(.2/.5)+2*math.log(.8/.5))/3, math.log(.8/.5)])
    assert len(outcome['paired_rows']) == 6 and outcome['excluded_seeds'] == 0
    assert not outcome['scientific_confirmation']
    for row in data:
        row['sides']['right']['probabilities'] = row['sides']['left']['probabilities']
    assert all(r['difference'] == 0 for r in subject.calculation_input(data, ['a', 'b'])['paired_rows'])


@pytest.mark.parametrize('fault', ['missing_seed', 'duplicate_seed', 'extra_unit', 'missing_side', 'truth', 'evidence', 'support'])
def test_incomplete_or_substituted_grid_refuses(fault):
    data = rows()
    if fault == 'missing_seed': data.pop()
    elif fault == 'duplicate_seed': data[-1] = copy.deepcopy(data[-2])
    elif fault == 'extra_unit': data[-1]['unit'] = 'new'
    elif fault == 'missing_side': del data[-1]['sides']['right']
    elif fault == 'truth': data[-1]['truth'] = 'b'
    elif fault == 'evidence': data[-1]['sides']['left']['evidence_sha256'] = digest('different')
    else: data[-1]['sides']['right']['probabilities'] = {'a': 1.}
    with pytest.raises(ValueError): subject.calculation_input(data, ['a', 'b'])


@pytest.mark.parametrize('fault', ['failed', 'left_zero', 'right_zero', 'both_zero'])
def test_single_seed_failure_or_nonfinite_contrast_blocks_finite_subset(fault):
    data = rows()
    if fault == 'failed': data[-1]['sides']['left']['valid'] = False
    else:
        for side in ('left', 'right'):
            if fault in (side+'_zero', 'both_zero'):
                data[-1]['sides'][side]['probabilities'] = {'a': 0., 'b': 1.}
    result = subject.calculation_input(data, ['a', 'b'])
    assert result['calculation_status'] == 'NOT_RUN' and result['paired_rows'] is None
    assert result['assigned_units'] == 2 and result['excluded_seeds'] == 0
    assert result['limitations'][0]['seed'] == 9003


def contract_fixture(tmp_path, monkeypatch):
    for module in (subject, access, common, launch, revision_predictions): monkeypatch.setattr(module, 'REPO', tmp_path)
    monkeypatch.setattr(access, 'ROOT', tmp_path)
    def inside(path):
        path = Path(path).resolve()
        if not path.is_relative_to(tmp_path) or path == tmp_path: raise ValueError('outside fixture')
        return path
    monkeypatch.setattr(access, 'inside', inside)
    def pointer(name, value):
        path = tmp_path / name
        write(path, value)
        return {'path': name, 'sha256': file_hash(path)}
    readers, packages, hashes, bindings, forecasts = {}, [], [], {}, {}
    contrast = {'left': 'artifact_choice', 'right': 'process_choice'}
    for seed in subject.SEEDS:
        training = pointer(f'fit/{seed}/COMPLETE.json', {'seed': seed})
        pointer(f'fit/{seed}/IDENTITY.json', {'seed': seed, 'family': 'qwen'})
        pointer(f'fit/{seed}/SCIENTIFIC_INPUT.json', {'recipe': 'original_expert'})
        identities = {}
        forecasts[str(seed)] = {}
        for side in contrast:
            job = f'forecast-{seed}-{side}'
            identities[side] = pointer(f'{job}/IDENTITY.json', {'scope': 'scientific', 'role': 'discovery',
                'operation': contrast[side], 'package_kind': 'fitted', 'family': 'qwen',
                'training_complete_sha256': training['sha256'], 'adapter_sha256': digest(seed),
                'units': ['discovery-a', 'discovery-b'], 'cases_complete_sha256': digest('discovery-cases')})
            forecasts[str(seed)][side] = {'job': job, 'path': f'{job}/PREDICTIONS.json'}
        package = {**subject.BASES['qwen'], 'adapter_sha256': digest(seed), 'precision': 'float16', 'device': 'cuda',
            'batch_size': 4, 'max_context': 4096, 'max_support': 128, 'max_new_tokens': 32,
            'generation': {'requested': {'do_sample': False}}}
        package_pointer = pointer(f'forecast-{seed}-left/PACKAGE.json', package)
        pointer(f'forecast-{seed}-right/PACKAGE.json', package)
        readers[str(seed)] = {'training': training, 'forecasts': identities, 'package': package_pointer}
        packages.append({'job': f'forecast-{seed}-left', 'path': package_pointer['path']})
        hashes.append(digest(package))
        bindings[str(seed)] = {'forecast_identity': {'job': f'forecast-{seed}-left', 'path': identities['left']['path']}}
    def training_package(directory, family, scope):
        assert family == 'qwen' and scope == 'scientific'
        seed = int(directory.name)
        return directory/'weights', digest(seed), file_hash(directory/'COMPLETE.json')
    monkeypatch.setattr(subject, 'training_package', training_package)
    allocation = pointer('allocation.json', [{'unit': u, 'role': 'reserve', 'content_sha256': digest(u)} for u in ('a','b','unused')])
    reserve = {u: {'input': pointer('reserve/'+u+'.json', {'private': 'sealed fixture', 'unit': u}),
                   'content_sha256': digest(u)} for u in ('a','b','unused')}
    packet = {'id': 'claim', 'analysis_contract': copy.deepcopy(CONTRACT), 'reserve_units': ['b','a'],
        'planning': {'planned_units': 2, 'discovery': {'seeds': list(subject.SEEDS)}},
        'candidate': {'target': 'proper_log_score', 'reader_packages': packages, 'seed_evidence': bindings,
                      'seed_forecasts': forecasts, 'allocation': allocation}, 'reader_package_content_hashes': hashes}
    contract = {'adapter': 'neural-choice-v1', 'resource': 'gpu', 'readers': readers, 'reserve': reserve, 'contrast': contrast}
    return contract, packet


def test_three_seed_contract_never_opens_reserved_payloads(tmp_path, monkeypatch):
    contract, packet = contract_fixture(tmp_path, monkeypatch)
    original = Path.read_bytes
    def guarded(path):
        assert path.parent.name != 'reserve'
        return original(path)
    monkeypatch.setattr(Path, 'read_bytes', guarded)
    assert list(access.validate_contract(contract, packet)) == ['b', 'a']


@pytest.mark.parametrize('fault', ['seed', 'fit', 'package', 'right_fit', 'right_view', 'right_units', 'recipe', 'precision', 'duplicate_reader', 'right_package'])
def test_seed_package_or_paired_discovery_substitution_refuses_before_open(tmp_path, monkeypatch, fault):
    contract, packet = contract_fixture(tmp_path, monkeypatch)
    item = contract['readers']['9003']
    if fault == 'seed': del contract['readers']['9003']
    elif fault == 'fit': item['training'] = contract['readers']['9001']['training']
    elif fault == 'package': item['package'] = contract['readers']['9001']['package']
    elif fault == 'duplicate_reader': packet['candidate']['reader_packages'][-1] = packet['candidate']['reader_packages'][0]
    elif fault == 'recipe': write(tmp_path/'fit/9003/SCIENTIFIC_INPUT.json', {'recipe': 'both_expert'})
    elif fault == 'right_package': write(tmp_path/'forecast-9003-right/PACKAGE.json', {'changed': True})
    else:
        pointer = item['package'] if fault == 'precision' else item['forecasts']['right']
        path = tmp_path / pointer['path']; value = read(path)
        if fault == 'right_fit': value['training_complete_sha256'] = digest('other-fit')
        elif fault == 'right_view': value['operation'] = 'artifact_choice'
        elif fault == 'right_units': value['units'] = ['different-source']
        else: value['precision'] = 'float32'
        write(path, value); pointer['sha256'] = file_hash(path)
        if fault == 'precision': packet['reader_package_content_hashes'][-1] = digest(value)
    with pytest.raises(ValueError): access.validate_contract(contract, packet)
    assert not list(tmp_path.rglob('OPENED.json'))


@pytest.mark.parametrize('interrupted', [False, True])
@pytest.mark.parametrize('scope', ['scientific', 'pilot'])
def test_actual_dispatch_path_keeps_every_seed_and_reentry_never_reopens_service(tmp_path, monkeypatch, interrupted, scope):
    # Synthetic transport and source fixtures exercise the installed orchestration.
    # They do not impersonate actual scientific fits or reserve acceptance.
    contract, packet = (rehearsal_contract_fixture if scope == 'pilot' else contract_fixture)(tmp_path, monkeypatch)
    directory = tmp_path/'execution'
    payloads = {u: {'unit': u, 'role': 'pilot' if scope == 'pilot' else 'reserve', 'target': 'a', 'sources': u} for u in packet['reserve_units']}
    frozen = {'packet': packet, 'contract': contract, 'scope': scope,
              'freeze_complete_sha256': digest('freeze'), 'claims_sha256': digest('claims')}
    monkeypatch.setattr(subject, 'frozen_claim', lambda *args: frozen)
    @contextmanager
    def reserved(*args):
        write(directory/'OPENED.json', {'fixture': True})
        yield {'packet': packet, 'contract': contract, 'payloads': payloads, 'identity': {'fixture': True}}
    monkeypatch.setattr(subject, 'reservation', reserved)
    monkeypatch.setattr(subject, 'validate_cases', lambda c, r: None)
    monkeypatch.setattr(subject, 'cell_identity', lambda: digest('cell'))
    monkeypatch.setattr(subject, 'sources', lambda: {'files': {}, 'sha256': digest({})})
    monkeypatch.setattr(subject, 'choice_input', lambda c, op: {'prefix': c['unit']+op, 'options': {'a': ' a', 'b': ' b'}})
    monkeypatch.setattr(subject, 'audit_execution', lambda r: None)
    opened, calls = [], []
    @contextmanager
    def service(path, config):
        seed = int(Path(config['adapter']).parent.name)
        opened.append(seed)
        yield {'identity': checked_package(seed), 'endpoint': 'fixture'}, 'fixture-token'
    def checked_package(seed): return read(tmp_path/contract['readers'][str(None if scope == 'pilot' else seed)]['package']['path'])
    monkeypatch.setattr(subject, 'resident', service)
    def execute(evidence, task, endpoint, token, root):
        calls.append(copy.deepcopy(evidence))
        if interrupted and len(calls) == (3 if scope == 'pilot' else 6):
            raise RuntimeError('fixture interruption in the second seed')
        return {'accepted': True, 'prediction': {'probs': {'a': .8 if 'artifact' in evidence['prefix'] else .5,
                                                          'b': .2 if 'artifact' in evidence['prefix'] else .5}}}
    monkeypatch.setattr(subject, 'execute', execute)
    def checkpoint(path, inputs, invoke, resume_only=False):
        if path.exists():
            saved = read(path); assert saved['inputs'] == inputs; return saved['result']
        assert not resume_only
        result = invoke(); write(path, {'inputs': inputs, 'result': result}); return result
    monkeypatch.setattr(subject, 'checkpoint_call', checkpoint)
    def finish(work, identity, started, cpu, files, **extra):
        done = {'execution_complete': True, 'identity_sha256': digest(identity),
                'outputs': closure([work/'IDENTITY.json', work/'PREDICTIONS.json', work/'OUTCOME.json', work/'units', work/'calls']), **extra}
        write(work/'COMPLETE.json', done); return done
    monkeypatch.setattr(subject, 'finish', finish)
    if interrupted:
        with pytest.raises(RuntimeError, match='fixture interruption'):
            subject.run(directory, None, None, None, 'claim', scope)
        assert len(list((directory/'work/units').glob('*.json'))) == (1 if scope == 'pilot' else 2)
        partial = closure([directory/'work/units', directory/'work/calls'])
        assert not (directory/'work/COMPLETE.json').exists()
    result = subject.run(directory, None, None, None, 'claim', scope)
    expected_opens = ([9001, 9001] if interrupted else [9001]) if scope == 'pilot' else ([9001, 9002, 9002, 9003] if interrupted else list(subject.SEEDS))
    expected_calls = (5 if interrupted else 4) if scope == 'pilot' else (13 if interrupted else 12)
    assert opened == expected_opens and len(calls) == expected_calls
    if interrupted:
        assert all(file_hash(tmp_path/p) == sha for p,sha in partial['files'].items())
    assert result['completed_units'] == 2 and result['training_seeds'] == list(subject.seed_grid(scope))
    before = closure([directory])
    assert subject.run(directory, None, None, None, 'claim', scope) == result
    assert closure([directory]) == before and opened == expected_opens and len(calls) == expected_calls
    assert len(read(directory/'work/PREDICTIONS.json')) == (2 if scope == 'pilot' else 6)


def discovery_fixture():
    from runners.stage9.generation_pilot import original_world
    from runners.stage9.series_cases import prepare_case
    from runners.stage9.neural_operations import unit_result
    world = original_world('S9GEN|essay|pilot|original|reader|3')
    case = {**prepare_case(world, [], 3, 'pilot'), 'source_worlds': [world]}
    assert case['realized']
    def call(evidence, arguments, index):
        return {'accepted': True, 'prediction': {'probs': {k: 1/len(evidence['options']) for k in evidence['options']}}}
    return case, {op: unit_result(case, op, call) for op in subject.OPERATIONS}


def test_actual_constructor_and_operation_export_feed_existing_b01_without_rescoring():
    from runners.stage9.confirmation_freeze import paired_rows
    case, units = discovery_fixture()
    left = subject.discovery_forecasts([case], [units['artifact_choice']], 'artifact_choice')
    right = subject.discovery_forecasts([case], [units['process_choice']], 'process_choice')
    layout = {k: [k] for k in ('unit','target','truth','probabilities','valid')}
    for seed in subject.SEEDS:
        assert paired_rows(left, right, layout, layout, seed) == [
            {'unit': case['unit'], 'target': 'next_recorded_event', 'seed': seed, 'difference': 0.}]


@pytest.mark.parametrize('fault', ['target', 'input', 'source', 'missing'])
def test_discovery_export_cannot_relabel_or_subset_original_units(fault):
    case, units = discovery_fixture()
    unit = units['artifact_choice']
    if fault == 'target': unit['result']['target'] = 'invented'
    elif fault == 'input': unit['result']['input_sha256'] = digest('other')
    elif fault == 'source': unit['case_sha256'] = digest('other')
    with pytest.raises(ValueError):
        subject.discovery_forecasts([case], [] if fault == 'missing' else [unit], 'artifact_choice')


def test_failed_discovery_call_is_exported_and_b01_refuses_the_claim():
    from runners.stage9.confirmation_freeze import paired_rows
    case, units = discovery_fixture()
    units['artifact_choice']['result']['call'] = {'accepted': False, 'prediction': None}
    left = subject.discovery_forecasts([case], [units['artifact_choice']], 'artifact_choice')
    right = subject.discovery_forecasts([case], [units['process_choice']], 'process_choice')
    assert len(left) == 1 and not left[0]['valid'] and left[0]['probabilities'] is None
    layout = {k: [k] for k in ('unit','target','truth','probabilities','valid')}
    with pytest.raises(ValueError, match='failed assigned forecast'):
        paired_rows(left, right, layout, layout, 9001)


def rehearsal_contract_fixture(tmp_path, monkeypatch):
    contract, packet = contract_fixture(tmp_path, monkeypatch)
    item = contract['readers']['9001']
    contract.update(adapter='neural-choice-rehearsal-v1', readers={'None': item})
    packet['planning']['discovery']['seeds'] = [None]
    packet['candidate']['reader_packages'] = packet['candidate']['reader_packages'][:1]
    packet['reader_package_content_hashes'] = packet['reader_package_content_hashes'][:1]
    packet['candidate']['seed_evidence'] = {}
    packet['candidate']['seed_forecasts'] = {'None': packet['candidate']['seed_forecasts']['9001']}
    for pointer in item['forecasts'].values():
        path = tmp_path / pointer['path']; identity = read(path)
        identity.update(scope='pilot', role='pilot')
        write(path, identity); pointer['sha256'] = file_hash(path)
    def training(directory, family, scope):
        assert scope == 'pilot' and family == 'qwen'
        return directory / 'weights', digest(9001), file_hash(directory / 'COMPLETE.json')
    monkeypatch.setattr(subject, 'training_package', training)
    return contract, packet


def test_discarded_reader_contract_keeps_no_scientific_seed_claim(tmp_path, monkeypatch):
    contract, packet = rehearsal_contract_fixture(tmp_path, monkeypatch)
    before = closure([tmp_path / 'reserve'])
    subject.validate_rehearsal_contract(contract, packet)
    assert access.validate_contract(contract, packet) == {u: contract['reserve'][u] for u in packet['reserve_units']}
    assert closure([tmp_path / 'reserve']) == before
    with pytest.raises(ValueError): subject.validate_reader_contract(contract, packet)


@pytest.mark.parametrize('fault', ['seed_claim', 'scientific_forecast', 'changed_fit', 'wrong_view',
    'another_package', 'changed_pair', 'incomplete_fit', 'service_settings'])
def test_rehearsal_contract_cannot_borrow_another_reader_or_claim_training_seeds(tmp_path, monkeypatch, fault):
    contract, packet = rehearsal_contract_fixture(tmp_path, monkeypatch)
    item = contract['readers']['None']
    if fault == 'seed_claim': packet['planning']['discovery']['seeds'] = [9001, 9002, 9003]
    elif fault == 'incomplete_fit':
        def refuse(*args): raise ValueError('actual discarded fit incomplete')
        monkeypatch.setattr(subject, 'training_package', refuse)
    elif fault in ('another_package', 'service_settings'):
        path = tmp_path / item['package']['path']; package = read(path)
        package['adapter_sha256' if fault == 'another_package' else 'max_context'] = 'wrong'
        write(path, package); item['package']['sha256'] = file_hash(path)
    else:
        pointer = item['forecasts']['right']; path = tmp_path / pointer['path']; value = read(path)
        field, replacement = {'scientific_forecast': ('role', 'discovery'), 'changed_fit': ('training_complete_sha256', 'wrong'),
                              'wrong_view': ('operation', 'artifact_choice'), 'changed_pair': ('units', ['different'])}[fault]
        value[field] = replacement; write(path, value); pointer['sha256'] = file_hash(path)
    with pytest.raises(ValueError): subject.validate_rehearsal_contract(contract, packet)


@pytest.mark.parametrize('boundary', ['bind', 'reservation'])
def test_discarded_contract_refuses_scientific_access_before_reading(tmp_path, monkeypatch, boundary):
    contract = {'adapter': 'neural-choice-rehearsal-v1'}
    def forbidden(*args): raise AssertionError('must refuse before reader validation or source access')
    monkeypatch.setattr(access, 'validate_contract', forbidden)
    if boundary == 'bind':
        with pytest.raises(ValueError, match='discarded'):
            access.bind_contracts({'policy': {'candidates': ['c']}, 'selected': [{'id': 'c'}]},
                                 {'confirmation_execution': {'c': contract}}, 'scientific')
    else:
        with pytest.raises(ValueError, match='discarded'):
            with access.reservation(tmp_path, {'packet': {'id': 'c'}, 'contract': contract, 'scope': 'scientific'}):
                raise AssertionError('scientific reserve opened')


def test_rehearsal_grid_is_explicit_and_cannot_substitute_for_scientific_seeds():
    data = [{**r, 'seed': None, 'role': 'pilot'} for r in rows() if r['seed'] == 9001]
    result = subject.calculation_input(data, ['a', 'b'], scope='pilot')
    assert result['calculation_status'] == 'READY' and all(r['seed'] is None for r in result['paired_rows'])
    with pytest.raises(ValueError): subject.calculation_input(data, ['a', 'b'])
    with pytest.raises(ValueError): subject.calculation_input(rows(), ['a', 'b'], scope='pilot')
    with pytest.raises(ValueError): subject.seed_grid('unspecified')
