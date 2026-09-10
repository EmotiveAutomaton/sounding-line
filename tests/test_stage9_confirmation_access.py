import copy
from pathlib import Path

import pytest

from runners.stage9 import confirmation_access as subject, common, launch
from runners.stage9.common import digest, file_hash, read, write
from runners.stage9.confirmation_statistics import CONTRACT


def fixture(tmp_path, monkeypatch):
    for module in (subject, common, launch):
        monkeypatch.setattr(module, 'REPO', tmp_path)
    monkeypatch.setattr(subject, 'ROOT', tmp_path)
    def inside(path):
        path = Path(path).resolve()
        if not path.is_relative_to(tmp_path) or path == tmp_path:
            raise ValueError('outside fixture')
        return path
    monkeypatch.setattr(subject, 'inside', inside)
    def pointer(name, value):
        path = tmp_path / name;write(path, value)
        return {'path': name, 'sha256': file_hash(path)}
    package = {'kind':'explicit pilot package'}
    reader = pointer('reader.json', package)
    allocation = pointer('allocation.json', [{'unit':u,'role':'reserve','content_sha256':digest(u)} for u in ('a','b','unused')])
    reserve = {u:{'input':pointer(u+'.json', {'unit':u,'private_target':'fixture'}),
                  'content_sha256':digest(u)} for u in ('a','b','unused')}
    packet = {'id':'candidate','analysis_contract':copy.deepcopy(CONTRACT),'reserve_units':['b','a'],
        'planning':{'planned_units':2,'discovery':{'seeds':[None]}},
        'candidate':{'target':'proper_log_score','reader_packages':[{'job':'reader','path':'reader.json'}],
                     'allocation':allocation},'reader_package_content_hashes':[digest(package)]}
    contract = {'adapter':'artifact-baselines-v1','resource':'cpu','reader':reader,'reserve':reserve,
        'contrast':{'left':{'view':'artifact','dose':7,'model':'population|cheap-8.0'},
                    'right':{'view':'artifact','dose':0,'model':'population|population'}}}
    frozen = {'packet':packet,'contract':contract,'scope':'pilot','freeze_complete_sha256':'a'*64,
              'claims_sha256':'b'*64,'manifest_sha256':'c'*64}
    return frozen,tmp_path/'private/confirmation-execution-pilots/one'


def test_contract_does_not_open_any_reserved_payload(tmp_path, monkeypatch):
    frozen,_=fixture(tmp_path,monkeypatch)
    original=Path.read_bytes
    def watched(path):
        assert path.name not in ('a.json','b.json','unused.json')
        return original(path)
    monkeypatch.setattr(Path,'read_bytes',watched)
    selected=subject.validate_contract(frozen['contract'],frozen['packet'])
    assert list(selected)==['b','a']


def test_only_selected_payloads_open_and_failed_access_remains_immutable(tmp_path, monkeypatch):
    frozen,directory=fixture(tmp_path,monkeypatch)
    # An unselected broken file is not read as part of this selected claim.
    (tmp_path/'unused.json').write_text('not JSON',encoding='utf-8')
    with pytest.raises(RuntimeError,match='simulated'):
        with subject.reservation(directory,frozen) as opened:
            assert list(opened['payloads'])==['b','a']
            assert (directory/'OPENED.json').exists()
            raise RuntimeError('simulated downstream failure')
    before=(directory/'OPENED.json').read_bytes()
    with subject.reservation(directory,frozen) as opened:
        assert opened['payloads']['a']['unit']=='a'
    assert (directory/'OPENED.json').read_bytes()==before
    changed=copy.deepcopy(frozen);changed['claims_sha256']='d'*64
    with pytest.raises(ValueError,match='frozen'):
        with subject.reservation(directory,changed):pass


def test_one_writer_covers_the_whole_execution_and_altered_payload_refuses(tmp_path, monkeypatch):
    frozen,directory=fixture(tmp_path,monkeypatch)
    with subject.reservation(directory,frozen):
        with pytest.raises(RuntimeError,match='another writer'):
            with subject.reservation(directory,frozen):pass
    write(tmp_path/'a.json',{'unit':'substitute'})
    with pytest.raises(ValueError,match='payload changed'):
        with subject.reservation(directory,frozen):pass
    assert (directory/'OPENED.json').exists()


@pytest.mark.parametrize('fault',['reader','source_content','source_path','missing_unit','neural_seeds','route','resource'])
def test_contract_refuses_substitution_before_opening(tmp_path, monkeypatch, fault):
    frozen,directory=fixture(tmp_path,monkeypatch);c=frozen['contract'];p=frozen['packet']
    if fault=='reader':p['reader_package_content_hashes']=['f'*64]
    elif fault=='source_content':c['reserve']['a']['content_sha256']='f'*64
    elif fault=='source_path':c['reserve']['b']['input']=c['reserve']['a']['input']
    elif fault=='missing_unit':del c['reserve']['a']
    elif fault=='neural_seeds':p['planning']['discovery']['seeds']=[9001,9002,9003]
    elif fault=='route':c['contrast']['right']=copy.deepcopy(c['contrast']['left'])
    else:c['resource']='gpu'
    with pytest.raises(ValueError):
        with subject.reservation(directory,frozen):pass
    assert not (directory/'OPENED.json').exists()


def test_scientific_claim_requires_original_contract_and_canonical_output(tmp_path, monkeypatch):
    frozen,directory=fixture(tmp_path,monkeypatch)
    result={'selected':[frozen['packet']],'policy':{'candidates':{'candidate':{}}}}
    with pytest.raises(ValueError,match='predeclared'):
        subject.bind_contracts(copy.deepcopy(result),{},'scientific')
    bound=subject.bind_contracts(copy.deepcopy(result),{'confirmation_execution':{'candidate':frozen['contract']}},'scientific')
    assert bound['selected'][0]['execution_contract_sha256']==digest(frozen['contract'])
    frozen['scope']='scientific'
    with pytest.raises(ValueError,match='canonical'):
        with subject.reservation(directory,frozen):pass


def producer_fixture(tmp_path, monkeypatch):
    from runners.stage9 import confirmation_freeze
    frozen, directory = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(confirmation_freeze, 'REPO', tmp_path)
    monkeypatch.setattr(confirmation_freeze, 'inside', subject.inside)
    declaration = copy.deepcopy(frozen['contract'])
    declaration['reader'] = {'job': 'source', 'path': 'reader.json'}
    plan = {'jobs': [{'id': 'source', 'role': 'work', 'produces': 'source/COMPLETE.json'}],
            'confirmation_execution': {'candidate': declaration}}
    # The declaration exists before the producer: its output includes that exact
    # manifest digest, so putting this future output's hash in the plan is circular.
    write(tmp_path/'PLAN.json', plan)
    package = {'kind': 'future reader', 'manifest_sha256': digest(plan)}
    write(tmp_path/'reader.json', package)
    write(tmp_path/'source/COMPLETE.json', {'execution_complete': True,
        'outputs': common.closure([tmp_path/'reader.json'])})
    snapshot = {'source': {'status': 'COMPLETE',
                'produce_sha256': file_hash(tmp_path/'source/COMPLETE.json')}}
    frozen['packet']['candidate']['reader_packages'] = [{'job': 'source', 'path': 'reader.json'}]
    frozen['packet']['reader_package_content_hashes'] = [digest(package)]
    return frozen, directory, plan, snapshot


def test_future_producer_binds_without_editing_manifest_or_opening_reserve(tmp_path, monkeypatch):
    frozen, _, plan, snapshot = producer_fixture(tmp_path, monkeypatch)
    before = (tmp_path/'PLAN.json').read_bytes()
    original = Path.read_bytes
    def guarded(path):
        assert path.name not in ('a.json', 'b.json', 'unused.json')
        return original(path)
    monkeypatch.setattr(Path, 'read_bytes', guarded)
    result = {'selected': [frozen['packet']], 'policy': {'candidates': {'candidate': {}}}}
    subject.bind_contracts(result, plan, 'scientific', snapshot=snapshot)
    context = {'plan': plan, 'review': result, 'upstream': snapshot,
               **{k: frozen[k] for k in ('freeze_complete_sha256', 'claims_sha256', 'manifest_sha256')}}
    monkeypatch.setattr(subject, 'frozen_review', lambda *args: context)
    actual = subject.frozen_claim(None, None, None, 'candidate', 'scientific')
    assert actual['contract']['reader'] == {'path': 'reader.json', 'sha256': file_hash(tmp_path/'reader.json')}
    assert result['selected'][0]['execution_declaration_sha256'] == digest(plan['confirmation_execution']['candidate'])
    assert result['selected'][0]['execution_contract_sha256'] == digest(actual['contract'])
    assert (tmp_path/'PLAN.json').read_bytes() == before and read(tmp_path/'PLAN.json') == plan
    result['selected'][0]['execution_declaration_sha256'] = 'f'*64
    with pytest.raises(ValueError, match='original frozen'):
        subject.frozen_claim(None, None, None, 'candidate', 'scientific')


@pytest.mark.parametrize('fault', ['snapshot', 'failed', 'running', 'uncommitted', 'changed', 'commit', 'closure', 'unknown'])
def test_future_producer_requires_actual_terminal_committed_bytes(tmp_path, monkeypatch, fault):
    _, _, plan, snapshot = producer_fixture(tmp_path, monkeypatch)
    contract = plan['confirmation_execution']['candidate']
    if fault == 'snapshot': snapshot = None
    elif fault in ('failed', 'running'): snapshot['source']['status'] = fault.upper()
    elif fault == 'uncommitted': contract['reader']['path'] = 'a.json'
    elif fault == 'changed': write(tmp_path/'reader.json', {'substitution': True})
    elif fault == 'commit': write(tmp_path/'source/COMPLETE.json', {'substitution': True})
    elif fault == 'closure': plan['jobs'][0]['role'] = 'closure'
    else: contract['reader']['job'] = 'unknown'
    with pytest.raises(ValueError):
        subject.resolve_contract(contract, plan, snapshot)


def test_neural_future_refs_resolve_both_identity_outputs_and_preserve_direct_fit(tmp_path, monkeypatch):
    _, _, plan, snapshot = producer_fixture(tmp_path, monkeypatch)
    output = {'job': 'source', 'path': 'reader.json'}
    contract = {'adapter': 'neural-choice-v1', 'readers': {'9001': {
        'training': {'path': 'source/COMPLETE.json', 'sha256': snapshot['source']['produce_sha256']},
        'package': output, 'forecasts': {'left': output, 'right': output}}},
        'reserve': {'never_opened': {'input': {'job': 'invalid-reserve-producer', 'path': 'absent'}}}}
    resolved = subject.resolve_contract(contract, plan, snapshot)
    item = resolved['readers']['9001']
    assert item['training']['sha256'] == snapshot['source']['produce_sha256']
    assert all(p['sha256'] == file_hash(tmp_path/'reader.json') for p in [item['package'], *item['forecasts'].values()])
    assert resolved['reserve'] == contract['reserve']
    assert contract['readers']['9001']['training']['sha256'] == snapshot['source']['produce_sha256']


def training_producer_fixture(tmp_path, monkeypatch):
    from runners.stage9 import training_jobs
    _, _, plan, snapshot = producer_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(training_jobs, 'ROOT', tmp_path)
    job = {'id': 'fit', 'role': 'work', 'module': 'runners.stage9.training_jobs',
           'produces': 'training-summary.json', 'arguments': ['fit', '--family', 'qwen',
           '--recipe', 'original_expert', '--seed', '9001']}
    plan['jobs'].append(job)
    output = {'job': 'source', 'path': 'reader.json'}
    contract = {'adapter': 'neural-choice-v1', 'readers': {'9001': {
        'training': {'job': 'fit', 'path': 'training-summary.json'},
        'package': output, 'forecasts': {'left': output, 'right': output}}}, 'reserve': {}}
    plan['confirmation_execution'] = {'candidate': contract}
    cell = digest({'manifest_sha256': digest(plan), 'job': job})
    directory = training_jobs.training_root('qwen', 'original_expert', 9001)
    identity = {'family': 'qwen', 'seed': 9001, 'split': 'training'}
    inputs = {'cell_identity': cell, 'family': 'qwen', 'recipe': 'original_expert', 'seed': 9001}
    done = {'identity_sha256': digest(identity), 'selected_checkpoint_sha256': digest('fixture-checkpoint')}
    for name,value in [('IDENTITY',identity),('SCIENTIFIC_INPUT',inputs),('COMPLETE',done)]:
        write(directory/(name+'.json'),value)
    wrapper = {'cell_identity': cell, 'full_validation_retained': True, 'family': 'qwen',
        'recipe': 'original_expert', 'seed': 9001, 'training_root': directory.relative_to(tmp_path).as_posix(),
        'training_complete_sha256': file_hash(directory/'COMPLETE.json'),
        'input_sha256': digest(inputs), 'selected_checkpoint_sha256': done['selected_checkpoint_sha256']}
    write(tmp_path/'training-summary.json',wrapper)
    snapshot['fit'] = {'status': 'COMPLETE', 'produce_sha256': file_hash(tmp_path/'training-summary.json')}
    return plan,snapshot,directory,wrapper


def test_future_fit_resolves_original_summary_to_canonical_training_bytes(tmp_path, monkeypatch):
    plan,snapshot,directory,_ = training_producer_fixture(tmp_path, monkeypatch)
    declaration = copy.deepcopy(plan['confirmation_execution']['candidate'])
    resolved = subject.resolve_contract(declaration,plan,snapshot)
    assert resolved['readers']['9001']['training'] == {
        'path': (directory/'COMPLETE.json').relative_to(tmp_path).as_posix(),
        'sha256': file_hash(directory/'COMPLETE.json')}
    assert declaration == plan['confirmation_execution']['candidate']


@pytest.mark.parametrize('fault', ['seed', 'root', 'cell', 'validation', 'fit_hash', 'input', 'checkpoint', 'fit_identity', 'pilot'])
def test_future_fit_rejects_rebound_summary_or_checkpoint_even_with_new_commit_hash(tmp_path, monkeypatch, fault):
    plan,snapshot,directory,wrapper = training_producer_fixture(tmp_path, monkeypatch)
    if fault == 'seed': wrapper['seed'] = 9002
    elif fault == 'root': wrapper['training_root'] = 'another-fit'
    elif fault == 'cell': wrapper['cell_identity'] = 'f'*64
    elif fault == 'validation': wrapper['full_validation_retained'] = False
    elif fault == 'fit_hash': wrapper['training_complete_sha256'] = 'f'*64
    elif fault == 'input':
        inputs=read(directory/'SCIENTIFIC_INPUT.json');inputs['cell_identity']='f'*64
        write(directory/'SCIENTIFIC_INPUT.json',inputs);wrapper['input_sha256']=digest(inputs)
    elif fault == 'checkpoint': wrapper['selected_checkpoint_sha256'] = 'f'*64
    elif fault == 'fit_identity':
        identity=read(directory/'IDENTITY.json');identity['split']='pilot';write(directory/'IDENTITY.json',identity)
        done=read(directory/'COMPLETE.json');done['identity_sha256']=digest(identity);write(directory/'COMPLETE.json',done)
        wrapper['training_complete_sha256']=file_hash(directory/'COMPLETE.json')
    else: plan['confirmation_execution']['candidate']['adapter']='neural-choice-rehearsal-v1'
    write(tmp_path/'training-summary.json',wrapper)
    snapshot['fit']['produce_sha256']=file_hash(tmp_path/'training-summary.json')
    with pytest.raises(ValueError):
        subject.resolve_contract(plan['confirmation_execution']['candidate'],plan,snapshot)
