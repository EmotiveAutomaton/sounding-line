"""Known request grids, failed calls and rehashed substitutions; no model calls."""
from pathlib import Path
import shutil
import pytest

from runners.stage9 import closure_purpose as subject, purpose_jobs, common, artifact_comparisons
from runners.stage9 import baseline_matrix_runtime, comparison_runtime, mark_runtime
from runners.stage9.common import closure, digest, read, write, file_hash
from runners.stage9.saved_replay import active, replaying
from tests.test_stage9_purpose_reader import bundle

ORIGINAL = common.REPO
RUNTIMES = (baseline_matrix_runtime, comparison_runtime, mark_runtime)


def fixture(tmp_path, monkeypatch, consumer='purpose', invalid=False):
    data = bundle(); query = data['evidence']; query['earlier'] = (query['earlier'] * 4)[:7]
    uniform = {a: 1 / len(query['support']) for a in query['support']}
    case = {'unit': 'fixture', 'role': 'pilot', 'target': query['support'][1], 'oracle': uniform,
            'realized': True, 'views': {'process_record': query},
            'private_factors': {'domain': 'text', 'purpose': 'first'}}
    package = {'library': {k: data[k] for k in ('candidates', 'prior', 'shared_groups')},
               'models': {'process_record': {'fixture': {}}},
               'types': {'process_record': {}}, 'completion_sha256': digest('fit')}
    for module in (subject, purpose_jobs, common, artifact_comparisons):
        monkeypatch.setattr(module, 'REPO', tmp_path)
    monkeypatch.setattr(purpose_jobs, 'ROOT', tmp_path)
    for module in (subject, purpose_jobs):
        monkeypatch.setattr(module, 'inside', lambda p: Path(p).resolve())
    monkeypatch.setattr(subject, 'verify_committed', lambda *a: None)
    monkeypatch.setattr(purpose_jobs, 'inputs', lambda *a: ([case], package, data['purpose_groups']))
    origins = {'runners/stage7/runtime.py'} | {p for runtime in RUNTIMES for p in runtime.SOURCES.values()}
    for p in origins:
        dest = tmp_path / p; dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ORIGINAL / p, dest)
    source = closure([tmp_path / p for p in sorted(origins)])
    directory = tmp_path / 'private' / (consumer + '-prediction-pilots') / 'fixture'
    cases = tmp_path / 'cases/CASES.json'; write(cases, [case]); write(cases.parent / 'COMPLETE.json', {})
    args = ['--root', str(directory), '--cases', str(cases), '--models', str(tmp_path / 'fit'),
            '--role', 'pilot', '--consumer', consumer]
    job = {'id': 'fixture', 'module': subject.MODULE, 'arguments': args, 'produces': str(directory / 'COMPLETE.json')}
    plan = {'sources': source, 'jobs': [job]}
    cell = digest({'manifest_sha256': digest(plan), 'job': job})
    identity, _, _, _, forecast = purpose_jobs.context(directory, cases, tmp_path / 'fit', 'pilot',
        cell=cell, source=source, consumer=consumer)
    write(directory / 'IDENTITY.json', identity)

    class Recorder:
        count = 0

        def checkpoint(self, path, inputs, invoke, *, resume_only=False):
            if path.exists():
                return read(path)['result']
            result = invoke(); write(path, {'input_sha256': digest(inputs), 'result': result})
            return result

        def request(self, evidence, task, root, sources, *, runtime):
            self.count += 1
            cap = root / digest({'call': self.count, 'evidence': evidence, 'task': task})[:16]
            for p, origin in sources.items():
                dest = cap / p; dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(tmp_path / origin, dest)
            (cap / 'reader/__init__.py').write_text('', encoding='utf-8')
            (cap / 'bootstrap.py').write_text(subject.BOOTSTRAP, encoding='utf-8', newline='\n')
            copied_files = {p.relative_to(cap).as_posix(): file_hash(p) for p in cap.rglob('*.py')}
            copied = {'files': copied_files, 'sha256': digest(copied_files), 'task_sha256': digest(task),
                      'evidence_sha256': digest(evidence), 'bootstrap_owner_sha256': source['files']['runners/stage7/runtime.py']}
            op = task['operation']; accepted = not invalid or op == 'baseline_matrix'
            prediction = {'valid': accepted}
            if op == 'baseline_matrix':
                prediction['predictions'] = {q: {m + '|' + r: uniform for m in evidence['models']
                    for r in ('population', 'brief', 'cheap-8.0', 'cheap-16.0', 'cheap-32.0')}
                    for q in evidence['evidences']}
            elif op == 'purpose_comparison':
                names = purpose_jobs.ORDINARY if evidence['mode'] == 'ordinary' else ('supplied',)
                prediction['predictions'] = {k: {'exact_within_declared_model': True, 'prediction': uniform} for k in names}
            elif op == 'numerical_proposals':
                prediction.update(candidates=evidence['candidates'], prior=evidence['prior'],
                    selected_candidates=len(evidence['candidates']), fixed_complete_catalogue=True)
            elif op == 'proposal_evaluation':
                prediction.update(pool_sha256=digest({k: evidence[k] for k in ('candidates', 'prior')}),
                    evidence_sha256=digest(evidence['evidence']), forecast={'prediction': uniform})
            else:
                raise AssertionError('undeclared synthetic operation')
            receipt = {'loaded_sources': {('reader' if p == 'reader/__init__.py' else p[:-3].replace('/', '.')): sha
                for p, sha in copied_files.items() if p.startswith('reader/')}}
            access = {'fixture': True}
            for name, value in [('evidence', evidence), ('task', task), ('out/prediction', prediction),
                                ('out/receipt', receipt), ('out/access', access)]:
                write(cap / (name + '.json'), value)
            write(root / 'closures' / (cap.name + '.json'), copied)
            return {'accepted': accepted, 'rc': 0 if accepted else 1, 'capsule': str(cap), 'prediction': prediction,
                    'receipt': receipt, 'access': access, 'copied_sources': copied,
                    'inputs_and_sources_unchanged': True, 'wall_s': .1}

    key = {'unit': case['unit']}
    with replaying(Recorder()):
        row = forecast(case, package, data['purpose_groups'], directory / 'calls' / digest(key)[:12])
    write(directory / 'units' / (digest(key) + '.json'),
          {'identity': digest(identity), 'key': key, 'complete': True, 'row': row})
    write(directory / 'PREDICTIONS.json', [row])
    done = {'identity_sha256': digest(identity), 'cell_identity': cell, 'source': source, 'role': 'pilot',
            'execution_complete': True, 'assigned_units': 1, 'completed_units': 1, 'gpu_seconds': 0,
            'cpu_scope': 'parent excludes restricted readers', 'scientific_promotion': False}
    def seal():
        done['outputs'] = closure([directory / n for n in ('PREDICTIONS.json', 'units', 'calls')])
        write(directory / 'COMPLETE.json', done)
    seal()
    return directory, job, plan, done, seal, case


@pytest.mark.parametrize('consumer', ['purpose', 'proposal'])
@pytest.mark.parametrize('invalid', [False, True])
def test_actual_dispatch_and_runtime_constructors_reconstruct_read_only(tmp_path, monkeypatch, consumer, invalid):
    directory, job, plan, _, _, _ = fixture(tmp_path, monkeypatch, consumer, invalid)
    def forbidden(*a, **kw):
        raise AssertionError('reader or output writer executed during replay')
    for runtime in RUNTIMES:
        monkeypatch.setattr(runtime, 'run_capsule', forbidden)
        monkeypatch.setattr(runtime, 'write', forbidden)
    monkeypatch.setattr(purpose_jobs, 'writer', forbidden)
    monkeypatch.setattr(purpose_jobs, 'Units', forbidden)
    before = closure([tmp_path]); result = subject.inspect_completed(job, plan, tmp_path)
    assert closure([tmp_path]) == before and active() is None
    assert result['units'] == 1 and bool(result['invalid_calls_retained']) == invalid
    assert result['calls'] == (7 if consumer == 'purpose' else 4 if invalid else 10)
    assert result['new_reader_calls'] == result['new_reserve_openings'] == 0
    assert result['scientific_admission'] is False


@pytest.mark.parametrize('fault', ['identity', 'source', 'truth', 'hidden_input', 'signature', 'task',
    'access', 'prediction', 'missing_prediction', 'missing_receipt', 'copied', 'copy_closure',
    'boolean', 'invalidity', 'missing_call', 'extra_call', 'extra_capsule', 'unit', 'unit_boolean',
    'missing_unit', 'extra_unit', 'export', 'counts', 'promoted'])
def test_rehashed_substitution_or_omission_refuses(tmp_path, monkeypatch, fault):
    directory, job, plan, done, seal, case = fixture(tmp_path, monkeypatch)
    call_path = next(p for p in (directory / 'calls').rglob('*.json') if 'input_sha256' in read(p))
    call = read(call_path); cap = Path(call['result']['capsule'])
    if fault == 'identity':
        value = read(directory / 'IDENTITY.json'); value['role'] = 'reserve'; write(directory / 'IDENTITY.json', value)
    elif fault == 'source':
        plan['sources']['files']['runners/stage7/runtime.py'] = digest('changed')
    elif fault == 'truth':
        case['target'] = 'changed'
    elif fault == 'hidden_input':
        case['private_factors']['purpose'] = 'second'
    elif fault == 'signature':
        call['input_sha256'] = digest('changed'); write(call_path, call)
    elif fault in ('task', 'access', 'prediction'):
        write(cap / (('' if fault == 'task' else 'out/') + fault + '.json'), {'changed': True})
    elif fault in ('missing_prediction', 'missing_receipt'):
        (cap / 'out' / (fault.removeprefix('missing_') + '.json')).unlink()
    elif fault == 'copied':
        p = cap / 'reader/worker.py'; p.write_text('changed', encoding='utf-8')
        call['result']['copied_sources']['files']['reader/worker.py'] = file_hash(p)
        call['result']['copied_sources']['sha256'] = digest(call['result']['copied_sources']['files']); write(call_path, call)
    elif fault == 'copy_closure':
        write(cap.parent / 'closures' / (cap.name + '.json'), {})
    elif fault in ('boolean', 'invalidity'):
        call['result']['accepted'] = 1 if fault == 'boolean' else False; write(call_path, call)
    elif fault == 'missing_call':
        call_path.unlink()
    elif fault == 'extra_call':
        write(directory / 'calls/extra.json', call)
    elif fault == 'extra_capsule':
        write(cap.parent / 'extra/evidence.json', {})
    elif fault in ('unit', 'unit_boolean'):
        p = next((directory / 'units').glob('*.json')); value = read(p)
        if fault == 'unit': value['row']['truth'] = 'changed'
        else: value['complete'] = 1
        write(p, value)
    elif fault == 'missing_unit':
        next((directory / 'units').glob('*.json')).unlink()
    elif fault == 'extra_unit':
        write(directory / 'units/extra.json', {})
    elif fault == 'export':
        write(directory / 'PREDICTIONS.json', [])
    elif fault == 'counts':
        done['completed_units'] = 2
    elif fault == 'promoted':
        done['scientific_promotion'] = True
    seal()
    with pytest.raises((ValueError, FileNotFoundError)):
        subject.inspect_completed(job, plan, tmp_path)
    assert active() is None


def test_failed_and_unrun_dispositions_do_not_open_inputs(tmp_path, monkeypatch):
    def forbidden(*a): raise AssertionError('uncompleted operation opened')
    monkeypatch.setattr(subject, 'inspect_completed', forbidden)
    checked = []; monkeypatch.setattr(subject, 'verify_disposition', lambda q, j, s: checked.append(s['status']))
    jobs = {k: {'module': subject.MODULE} for k in ('failed', 'unrun')}
    state = {k: {'status': s, 'reason': 'original refusal', 'disposition_sha256': digest(s)}
             for k, s in [('failed', 'FAILED'), ('unrun', 'NOT_RUN')]}
    write(tmp_path / 'STATUS.json', {'jobs': state})
    assert subject.queue_audits({}, tmp_path, jobs)['jobs'] == state
    assert checked == ['FAILED', 'NOT_RUN']


def test_replay_context_refuses_nesting_and_restores_on_error():
    assert active() is None
    handler = object()
    with pytest.raises(ValueError), replaying(handler):
        assert active() is handler
        with replaying(object()): pass
    assert active() is None


@pytest.mark.parametrize('sha,count', subject.HISTORICAL_COMPARISON.items())
def test_only_exact_reviewed_historical_source_maps_are_accepted(sha, count):
    mapping = comparison_runtime.SOURCES
    excluded = {'reader/' + name + '.py' for name in subject.ADDITIONS[count:]}
    expected = {p: origin for p, origin in mapping.items() if p not in excluded}
    original = {'files': {origin: digest(origin) for origin in expected.values()}}
    original['files']['runners/stage9/comparison_runtime.py'] = sha
    assert subject.source_map(mapping, original, 'comparison_runtime') == {p: digest(origin) for p, origin in expected.items()}
    original['files'].pop(next(iter(expected.values())))
    with pytest.raises(ValueError):
        subject.source_map(mapping, original, 'comparison_runtime')


def test_unknown_partial_runtime_map_refuses():
    original = {'files': {'runners/stage9/comparison_runtime.py': digest('unknown')}}
    with pytest.raises(ValueError, match='unreviewed historical'):
        subject.source_map(comparison_runtime.SOURCES, original, 'comparison_runtime')


def test_scope_compatibility_changes_only_reviewed_sentence_under_exact_source():
    original = {'files': {'runners/stage9/selection_jobs.py': subject.SELECTION_SCOPE_SOURCE}}
    row = {'scope': subject.CURRENT_SELECTION_SCOPE, 'costs': [{'valid': False}], 'rows': {}}
    adjusted = subject.original_annotation(row, original, 'selection')
    assert adjusted == {**row, 'scope': subject.ORIGINAL_SELECTION_SCOPE}
    assert row['scope'] == subject.CURRENT_SELECTION_SCOPE
    assert subject.original_annotation(row, {'files': {}}, 'selection') == row
    assert subject.original_annotation(row, original, 'familiarity-entry') == row
    with pytest.raises(ValueError):
        subject.original_annotation({**row, 'scope': 'changed'}, original, 'selection')


def test_original_purpose_identity_renames_only_exact_reviewed_field():
    source = {'files': {'runners/stage9/purpose_jobs.py': subject.PURPOSE_IDENTITY_SOURCE}}
    identity = {'budget_per_evaluation_call': 800000, 'selected_units': ['one'], 'role': 'pilot'}
    assert subject.original_identity(identity, source, 'purpose') == {
        'budget_per_purpose_call': 800000, 'selected_units': ['one'], 'role': 'pilot'}
    assert identity['budget_per_evaluation_call'] == 800000
    assert subject.original_identity(identity, {'files': {}}, 'purpose') == identity


def test_original_identity_protocol_refuses_other_consumer_or_changed_budget():
    source = {'files': {'runners/stage9/purpose_jobs.py': subject.PURPOSE_IDENTITY_SOURCE}}
    with pytest.raises(ValueError):
        subject.original_identity({'budget_per_evaluation_call': 800000}, source, 'proposal')
    for value in (800001, 800000., True, None):
        with pytest.raises(ValueError):
            subject.original_identity({'budget_per_evaluation_call': value}, source, 'purpose')
