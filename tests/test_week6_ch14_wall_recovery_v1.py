"""Constructed-only recovery transport tests; native counted qualification only."""
from pathlib import Path
import copy
import json
import pytest
from runners.drive.cards import week6_ch14_wall_recovery_v1 as recovery
from runners.drive.cards import week6_resume_v1 as resume
from runners.drive.cards import week6_policy_v1 as original_policy
from runners.drive.cards.batch_runtime import read, filehash
from runners.drive.cards.week5_resume import output_manifest
from test_week6_ch_riders_v3 import constructed_source


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding='utf8')


@pytest.fixture
def case(tmp_path, monkeypatch):
    monkeypatch.setattr(recovery, 'ROOT', tmp_path)
    monkeypatch.setattr(original_policy, 'ROOT', tmp_path)
    monkeypatch.setattr(recovery, 'is_same_live_process', lambda n: False)
    monkeypatch.setattr(resume, 'is_same_live_process', lambda n: False)
    inputs = constructed_source(tmp_path)
    config = dict(card='CH14', draws=3, constructed_fixture=True, max_new_draws=1)
    old = tmp_path/'failed'; output = old/'output'
    assert recovery.base.execute(output, inputs, config)['status'] == 'yielded'
    plan = dict(module=recovery.ORIGINAL, inputs=inputs, config=config,
                campaign='S15-WEEK6', family='CH', budget_key='CH14',
                max_cpu_seconds=100, max_wall_seconds=100,
                pins={x['path']: x['sha256'] for x in inputs.values()})
    write(old/'PLAN.json', plan)
    native = dict(pid=987654321, created_ticks=123456, executable='constructed.exe')
    write(old/'OWNER.json', dict(native=native, plan_sha256=filehash(old/'PLAN.json')))
    write(old/'EXECUTE_NATIVE.json', dict(native=native))
    write(old/'EXECUTE_JOB_USAGE.json', dict(cpu_seconds=50, includes_all_descendants_and_exited_processes=True))
    write(old/'FAILED.json', dict(status='FAILED', failure_class='cost', error=recovery.ERROR,
                                 accounting_reconciliation_required=False, wall_seconds=101, cpu_seconds=50))
    manifest = tmp_path/'recovery.json'
    spec = dict(version=1, kind='CH14_EXECUTE_WALL_RECOVERY', root=str(old),
                receipts={n:filehash(old/n) for n in recovery.RECEIPTS},
                output_manifest=output_manifest(output), checkpoint_draws=1)
    write(manifest, spec)
    new = tmp_path/'new'
    successor = copy.deepcopy(plan)
    successor['module'] = recovery.__name__
    successor['config']['max_new_draws'] = 3
    successor['inputs']['wall_recovery'] = dict(path=str(manifest), sha256=filehash(manifest))
    successor['pins'][str(manifest)] = filehash(manifest)
    write(new/'PLAN.json', successor)
    return dict(old=old, new=new, manifest=manifest, spec=spec, plan=successor, original=plan)


def call(c):
    return recovery.execute(c['new']/'output', c['plan']['inputs'], c['plan']['config'])


def test_wall_recovery_matches_uninterrupted_bank_and_full_fresh_replay(case, tmp_path):
    original = output_manifest(case['old']/'output')
    assert call(case)['status'] == 'complete'
    inputs = case['original']['inputs']; config = dict(case['plan']['config'])
    assert recovery.base.execute(tmp_path/'fresh/output', inputs, config)['status'] == 'complete'
    assert read(case['new']/'output/RIDER_CHECKPOINT.json') == read(tmp_path/'fresh/output/RIDER_CHECKPOINT.json')
    assert recovery.verify(case['new']/'output', case['plan']['inputs'], config)['verified'] is True
    assert output_manifest(case['old']/'output') == original
    assert (case['new']/'output/independent-0001/SCIENCE.json').exists()
    assert not (case['old']/'PAUSED.json').exists()


@pytest.mark.parametrize('name', sorted(recovery.RECEIPTS))
def test_wall_recovery_rejects_changed_original_receipt(case, name):
    with (case['old']/name).open('a', encoding='utf8') as out:out.write(' ')
    with pytest.raises(ValueError, match='Changed predecessor receipt'):call(case)


@pytest.mark.parametrize('which', ['failure_class','unreconciled','cpu_cap','short_wall','job_cpu','job_incomplete'])
def test_wall_recovery_refuses_non_wall_or_incomplete_accounting(case, which):
    name = 'EXECUTE_JOB_USAGE.json' if which.startswith('job_') else 'FAILED.json'
    value = read(case['old']/name)
    changes = {'failure_class':('failure_class','engineering'), 'unreconciled':('accounting_reconciliation_required',True),
               'cpu_cap':('cpu_seconds',100), 'short_wall':('wall_seconds',99),
               'job_cpu':('cpu_seconds',49), 'job_incomplete':('includes_all_descendants_and_exited_processes',False)}
    key, replacement = changes[which]; value[key] = replacement
    write(case['old']/name, value)
    case['spec']['receipts'][name] = filehash(case['old']/name)
    write(case['manifest'], case['spec'])
    case['plan']['inputs']['wall_recovery']['sha256'] = filehash(case['manifest'])
    case['plan']['pins'][str(case['manifest'])] = filehash(case['manifest'])
    write(case['new']/'PLAN.json', case['plan'])
    with pytest.raises(ValueError, match='Not an accounted execute wall failure'):call(case)


@pytest.mark.parametrize('name', ['COMPLETE.json','PAUSED.json','VERIFY_NATIVE.json','VERIFIED.json'])
def test_wall_recovery_rejects_ambiguous_or_replay_stage(case, name):
    write(case['old']/name, {})
    with pytest.raises(ValueError, match='Ambiguous or replay-stage'):call(case)


@pytest.mark.parametrize('which', ['manifest','checkpoint','source','extra_output','nonempty_target'])
def test_wall_recovery_refuses_changed_or_extra_bytes(case, which):
    path = {'manifest':case['manifest'], 'checkpoint':case['old']/'output/RIDER_CHECKPOINT.json',
            'source':Path(case['original']['inputs']['histories']['path']),
            'extra_output':case['old']/'output/unexpected.txt',
            'nonempty_target':case['new']/'output/unexpected.txt'}[which]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('ab') as out:out.write(b' ')
    with pytest.raises((ValueError, RuntimeError)):call(case)


@pytest.mark.parametrize('which', ['input','config','budget','pin','draw_count','root_escape'])
def test_wall_recovery_refuses_changed_contract(case, which, tmp_path):
    p = case['plan']
    if which == 'input':p['inputs']['decisions']['sha256'] = '0'*64
    elif which == 'config':p['config']['draws'] = 4
    elif which == 'budget':p['budget_key'] = 'CH13'
    elif which == 'pin':p['pins'].pop(next(iter(case['original']['pins'])))
    else:
        if which == 'draw_count':case['spec']['checkpoint_draws'] = 2
        else:case['spec']['root'] = str(tmp_path.parent)
        write(case['manifest'], case['spec'])
        p['inputs']['wall_recovery']['sha256'] = filehash(case['manifest'])
        p['pins'][str(case['manifest'])] = filehash(case['manifest'])
    write(case['new']/'PLAN.json', p)
    with pytest.raises(ValueError):call(case)


def test_wall_recovery_refuses_live_predecessor(case, monkeypatch):
    monkeypatch.setattr(recovery, 'is_same_live_process', lambda n: True)
    with pytest.raises(ValueError, match='still live'):call(case)


def test_wall_recovery_refuses_copy_corruption(case, monkeypatch):
    def corrupt(source, destination):Path(destination).write_bytes(b'bad')
    monkeypatch.setattr(recovery.shutil, 'copyfile', corrupt)
    with pytest.raises(ValueError, match='copy mismatch'):call(case)


def test_later_real_pause_preserves_newer_checkpoint(case, tmp_path):
    case['plan']['config']['max_new_draws'] = 1
    write(case['new']/'PLAN.json', case['plan'])
    assert call(case)['status'] == 'yielded'
    assert len(read(case['new']/'output/RIDER_CHECKPOINT.json')['draws']) == 2
    write(case['new']/'PAUSED.json', dict(status='PAUSED', checkpoint_validation_required=True,
          checkpoint_outputs=output_manifest(case['new']/'output')))
    write(case['new']/'OWNER.json', dict(native=dict(pid=987654321), plan_sha256=filehash(case['new']/'PLAN.json')))
    later = tmp_path/'later'; plan = copy.deepcopy(case['plan'])
    plan['resume'] = dict(root=str(case['new']), plan_sha256=filehash(case['new']/'PLAN.json'),
                          paused_sha256=filehash(case['new']/'PAUSED.json'))
    write(later/'PLAN.json', plan)
    resume.copy_checkpoint(later, plan)
    saved = read(later/'output/RIDER_CHECKPOINT.json')['draws']
    assert recovery.execute(later/'output', plan['inputs'], plan['config'])['status'] == 'complete'
    assert read(later/'output/RIDER_CHECKPOINT.json')['draws'][:2] == saved
    assert recovery.verify(later/'output', plan['inputs'], plan['config'])['verified'] is True


def test_wall_recovery_rejects_duplicate_install_and_changed_origin(case):
    assert call(case)['status'] == 'complete'
    with pytest.raises(ValueError, match='must be empty'):call(case)
    write(case['new']/'output/RECOVERY_ORIGIN.json', {})
    with pytest.raises(ValueError, match='Changed recovery origin'):
        recovery.verify(case['new']/'output', case['plan']['inputs'], case['plan']['config'])
