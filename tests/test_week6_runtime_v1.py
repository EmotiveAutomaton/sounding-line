"""Constructed boundaries; no human inputs or production campaign dispatch."""
from datetime import timedelta
from pathlib import Path
import json
import pytest
from runners.drive.cards import week6_policy_v1 as p, week6_limits_v1 as limits, week6_resume_v1 as resume
from runners.drive import calendar_20261115_week6 as calendar


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf8', newline='\n')


@pytest.mark.parametrize('scenario', ['complete', 'execute_yield', 'verify_yield', 'verify_overcap', 'resource_yield'])
def test_native_literal_execution_replay_and_final_bounds(tmp_path, monkeypatch, scenario):
    """Real Windows children and shared leases; constructed admission clock/evidence."""
    import threading
    import time
    from runners.drive.cards import week6_runtime_v1 as runtime
    from runners.drive.cards import week6_runtime_fixture_v1 as fixture
    from runners.stage9.process_identity import is_same_live_process
    root, _, _, _, _, plan = setup(tmp_path, monkeypatch)
    attempt = root/scenario
    plan.update(module=fixture.__name__, inputs={'literal': [2, 3, 5]},
                config={'scenario': scenario}, max_output_bytes=4096)
    for module in (runtime, fixture):
        path = Path(module.__file__).resolve()
        plan['pins'][str(path)] = limits.filehash(path)
    put(attempt/'PLAN.json', plan)
    original_admission, original_available = p.admission, p.available
    monkeypatch.setattr(p, 'available', lambda plan, root=root, exclude=None: original_available(plan, root, exclude))
    monkeypatch.setattr(p, 'admission', lambda plan: original_admission(
        plan, at=p.OPEN+timedelta(minutes=1), budget_root=root))
    if scenario == 'resource_yield':
        monkeypatch.setattr(runtime, 'resource_snapshot', lambda: dict(
            ram_available_GiB=3, commit_headroom_GiB=5, disk_free_GiB=19))
    # Keep real occupancy, shared reservation, memory and disk guards.
    stopped = threading.Event()
    errors = []
    def monitor():
        try:
            while not stopped.is_set():
                if (attempt/'OWNER.json').is_file():
                    put(attempt/'MONITOR_READY.json', {'owner_sha256': limits.filehash(attempt/'OWNER.json')})
                    return
                time.sleep(.01)
        except Exception as exc:
            errors.append(exc)
    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()
    try:
        if scenario == 'verify_overcap':
            with pytest.raises(RuntimeError, match='output byte cap'):
                runtime.run(attempt)
            terminal = limits.read(attempt/'FAILED.json')
            assert terminal['failure_class'] == 'environment'
            assert not (attempt/'COMPLETE.json').exists()
        else:
            runtime.run(attempt)
            terminal = limits.read(attempt/('COMPLETE.json' if scenario == 'complete' else 'PAUSED.json'))
            if scenario == 'complete':
                assert limits.read(attempt/'VERIFIED.json')['sum'] == 10
                assert terminal['fresh_process_verified']
                assert all(limits.filehash(attempt/name) == pin for name,pin in terminal['outputs'].items())
            else:
                assert terminal['paused_operation'] == ('execute' if scenario == 'resource_yield' else scenario.split('_')[0])
                assert terminal['checkpoint_outputs']
                if scenario == 'resource_yield':
                    assert terminal['reason']['reason'] == 'resource_floor'
        usage = []
        identities = []
        for operation in ('EXECUTE', 'VERIFY'):
            path = attempt/(operation+'_JOB_USAGE.json')
            if path.exists():
                row = limits.read(path)
                assert row['includes_all_descendants_and_exited_processes'] and row['exit_code'] == 0
                usage.append(row['cpu_seconds'])
                native = limits.read(attempt/(operation+'_NATIVE.json'))['native']
                assert not is_same_live_process(native)
                identities.append((native['pid'], native['created_ticks']))
                env = limits.read(attempt/(operation+'_ENVIRONMENT.json'))
                assert env['threads'] == 2 and env['cuda_visible'] == ''
                assert all(pool['num_threads'] <= 2 for pool in env['pools'])
        assert len(identities) == len(set(identities))
        assert terminal['cpu_seconds'] == sum(usage)
        lease = Path(limits.read(attempt/'ADMISSION.json')['lease'])
        assert not lease.exists() or limits.read(lease).get('attempt_root') != str(attempt.resolve())
    finally:
        stopped.set()
        thread.join(timeout=2)
    assert not thread.is_alive() and not errors


def setup(tmp, monkeypatch):
    old, root = tmp/'predecessor', tmp/'new'
    root.mkdir()
    job = old/'prior'
    put(job/'PLAN.json', dict(campaign='S15-WEEK5', family='IN', max_cpu_seconds=100))
    (job/'ATTEMPT.claim').touch()
    native = dict(pid=123, created_ticks=456, executable='constructed')
    put(job/'OWNER.json', dict(native=native, plan_sha256=limits.filehash(job/'PLAN.json')))
    put(job/'PAUSED.json', dict(cpu_seconds=17, status='PAUSED'))
    report = tmp/'final-drain.json'
    put(report, dict(id='OPS-S15-W5-FINAL-DRAIN-FIXTURE', full_write_through=True))
    proof = tmp/'DRAIN_REVIEW.json'
    put(proof, dict(at=p.OPEN.isoformat(), owner_reviewed=True, all_native_exits_verified=True,
        full_write_through=True, predecessor_root=str(old), terminal_inventory=limits.predecessor_inventory(old),
        exited_native_identities={'prior': native}, final_drain_receipt=str(report), final_drain_receipt_sha256=limits.filehash(report)))
    monkeypatch.setattr(limits, 'PREDECESSOR', old)
    monkeypatch.setattr(limits, 'DRAIN_REVIEW', proof)
    evidence = tmp/'accounting-evidence.json'
    put(evidence, dict(constructed=True, prior_cpu=400, preparation_cpu=100))
    budget = root/'_budgets/IN13-r0001.json'
    put(budget, dict(campaign='S15-WEEK6', key='IN13', family='IN', owner_reviewed=True,
        revision=1, previous_sha256=None, ceiling_cpu_seconds=20000,
        prior_campaign_cpu_seconds=400, preparation_cpu_seconds=100,
        evidence_pins={str(evidence): limits.filehash(evidence)}))
    plan = dict(campaign='S15-WEEK6', family='IN', card='constructed', accounting_runtime='week6-v1',
        budget_key='IN13', budget_receipt=str(budget), budget_receipt_sha256=limits.filehash(budget),
        numerical_threads=2, paid=False, gpu=False, ollama=False,
        premortem=dict(case_and_check='constructed known answer', smaller_route='preserve original evidence'),
        max_cpu_seconds=100, max_wall_seconds=60, forecast_cpu_seconds=100, projected_peak_ram_GiB=2,
        fixture_passed=True, reviewed_design_commit='constructed',
        pins={str(path): limits.filehash(path) for path in (budget, proof, report)})
    return root, job, proof, report, budget, plan


def admit(root, plan, **kwargs):
    args=dict(at=p.OPEN+timedelta(minutes=1), resources=dict(ram_available_GiB=24, commit_headroom_GiB=32, disk_free_GiB=99),
        budget_root=root, lock_path=root/'shared.lock', occupied=[], logical=24)
    args.update(kwargs)
    return p.admission(plan, **args)


def test_approved_clock_ceiling_and_shared_slots_preserve_old():
    from runners.drive.cards import week5_policy_v3 as old
    assert p.OPEN == old.DRAIN
    assert p.FREEZE.isoformat() == '2026-11-23T04:00:00+00:00'
    assert p.DRAIN.isoformat() == '2026-11-23T06:00:00+00:00'
    assert p.ADDENDUM.isoformat() == '2026-11-23T07:00:00+00:00'
    assert p.CEILING == 6000000 and p.FAMILY_CEILINGS['IN'] == 200000 and p.FAMILY_CEILINGS['RW'] == 20000
    assert {k:v for k,v in p.FAMILY_CEILINGS.items() if k not in {'IN','RW'}} == {k:v for k,v in old.FAMILY_CEILINGS.items() if k != 'IN'}
    assert (p.OLD_SLOTS,p.NEW_SLOTS,p.SHARED_LOCK)==(old.OLD_SLOTS,old.NEW_SLOTS,old.SHARED_LOCK)
    assert old.FREEZE.isoformat() == '2026-11-16T04:00:00+00:00'


def test_drain_and_inclusive_prior_preparation_costs(tmp_path,monkeypatch):
    root,_,_,_,_,plan=setup(tmp_path,monkeypatch)
    assert p.charges(root)['IN']==100
    assert admit(root,plan)['remaining_cpu_seconds']==19470
    assert p.available(plan,root)==19500
    put(root/'unstarted/PLAN.json',plan)
    assert p.available(plan,root)==19500
    (root/'unstarted/ATTEMPT.claim').touch()
    put(root/'unstarted/FAILED.json',dict(cpu_seconds=17))
    assert p.charges(root)['IN']==147
    assert p.available(plan,root)==19453


@pytest.mark.parametrize('defect',['early','freeze','missing_review','unfiled','exit_unproved','native_mismatch','new_attempt','terminal_changed','ambiguous','owner_binding','calendar_only','missing_pin'])
def test_drain_is_evidence_not_just_time(tmp_path,monkeypatch,defect):
    root,job,proof,report,_,plan=setup(tmp_path,monkeypatch)
    options={}
    if defect=='early':options['at']=p.OPEN-timedelta(seconds=1)
    elif defect=='freeze':options['at']=p.FREEZE
    elif defect=='missing_review':proof.unlink()
    elif defect in {'unfiled','exit_unproved','native_mismatch'}:
        value=limits.read(proof)
        if defect=='unfiled':value['full_write_through']=False
        if defect=='exit_unproved':value['all_native_exits_verified']=False
        if defect=='native_mismatch':value['exited_native_identities']={}
        put(proof,value);plan['pins'][str(proof)]=limits.filehash(proof)
    elif defect=='new_attempt':
        other=job.parent/'new';put(other/'PLAN.json',dict(campaign='S15-WEEK5'));(other/'ATTEMPT.claim').touch()
    elif defect=='terminal_changed':put(job/'PAUSED.json',dict(cpu_seconds=18,status='PAUSED'))
    elif defect=='ambiguous':put(job/'COMPLETE.json',dict(cpu_seconds=17))
    elif defect=='owner_binding':put(job/'OWNER.json',dict(native={},plan_sha256='wrong'))
    elif defect=='calendar_only':
        put(report,dict(event='FINAL_DRAIN_RECONCILIATION',owner_action_required=True))
        value=limits.read(proof);value['final_drain_receipt_sha256']=limits.filehash(report);put(proof,value)
        plan['pins'].update({str(proof):limits.filehash(proof),str(report):limits.filehash(report)})
    elif defect=='missing_pin':plan['pins'].pop(str(proof))
    with pytest.raises((RuntimeError,ValueError,FileNotFoundError)):admit(root,plan,**options)


@pytest.mark.parametrize('defect',['ceiling','prior','lower_preparation','ancestry','dropped_evidence','missing_revision'])
def test_budget_revisions_never_reset_original_cost(tmp_path,monkeypatch,defect):
    root,_,_,_,budget,plan=setup(tmp_path,monkeypatch)
    value=limits.read(budget);value.update(revision=2,previous_sha256=limits.filehash(budget),preparation_cpu_seconds=150)
    if defect=='ceiling':value['ceiling_cpu_seconds']=40000
    if defect=='prior':value['prior_campaign_cpu_seconds']=0
    if defect=='lower_preparation':value['preparation_cpu_seconds']=99
    if defect=='ancestry':value['previous_sha256']='bad'
    if defect=='dropped_evidence':value['evidence_pins']={}
    if defect=='missing_revision':value['revision']=3
    put(root/f"_budgets/IN13-r{value['revision']:04d}.json",value)
    with pytest.raises(ValueError):p.available(plan,root)


def test_cumulative_preparation_charged_once_and_across_old_plan(tmp_path,monkeypatch):
    root,_,_,_,budget,plan=setup(tmp_path,monkeypatch)
    value=limits.read(budget);value.update(revision=2,previous_sha256=limits.filehash(budget),preparation_cpu_seconds=150)
    put(root/'_budgets/IN13-r0002.json',value)
    assert p.charges(root)['IN']==150 and p.available(plan,root)==19450


@pytest.mark.parametrize('resource',['ram_available_GiB','commit_headroom_GiB','disk_free_GiB'])
def test_resource_guards(tmp_path,monkeypatch,resource):
    root,_,_,_,_,plan=setup(tmp_path,monkeypatch)
    resources=dict(ram_available_GiB=24,commit_headroom_GiB=32,disk_free_GiB=99);resources[resource]=0
    with pytest.raises(RuntimeError,match='floor'):admit(root,plan,resources=resources)
    assert p.yield_reason(root,plan,resources)=='resource_floor'


def test_eight_slots_and_paid_gpu_refuse(tmp_path,monkeypatch):
    root,_,_,_,_,plan=setup(tmp_path,monkeypatch)
    with pytest.raises(RuntimeError,match='occupied'):admit(root,plan,occupied=[root/str(i) for i in range(8)])
    for key in ('paid','gpu','ollama'):
        with pytest.raises(ValueError,match='CPU-only'):admit(root,{**plan,key:True})


def test_calendar_preserves_wake_config_and_emits_once(tmp_path):
    cfg=tmp_path/'watch.json';root=tmp_path/'calendar'
    put(cfg,dict(wake_mode='events_and_idle',fallback_seconds=14400,single_pending_wake=True,other='retained'))
    before=cfg.read_bytes()
    assert calendar.tick(root,cfg,p.OPEN-timedelta(seconds=1))==[]
    assert calendar.tick(root,cfg,p.OPEN)==['START_GATE_REVIEW_DUE']
    calendar.tick(root,cfg,p.ADDENDUM)
    saved={x.name:x.read_bytes() for x in root.iterdir()}
    assert len(saved)==10 and all(not json.loads(v)['research_admitted'] for v in saved.values())
    assert calendar.tick(root,cfg,p.ADDENDUM+timedelta(hours=1))==[]
    assert before==cfg.read_bytes() and saved=={x.name:x.read_bytes() for x in root.iterdir()}


def test_same_campaign_resume_preserves_both_workspaces(tmp_path,monkeypatch):
    monkeypatch.setattr(p,'ROOT',tmp_path)
    monkeypatch.setattr(resume,'is_same_live_process',lambda _:False)
    old,new=tmp_path/'old',tmp_path/'new';source=tmp_path/'fixed';source.write_text('constructed')
    plan=dict(module='runners.drive.cards.week6_in14_v1',campaign='S15-WEEK6',family='IN',budget_key='IN14',
        inputs={'source':str(source)},config=dict(draws=2000,max_new_draws=1),pins={str(source):limits.filehash(source)})
    put(old/'PLAN.json',plan);put(old/'OWNER.json',dict(native={},plan_sha256=limits.filehash(old/'PLAN.json')))
    put(old/'output/progress.json',dict(draws=1));put(old/'output/independent-replay/progress.json',dict(draws=0))
    manifest=resume.output_manifest(old/'output')
    put(old/'PAUSED.json',dict(status='PAUSED',checkpoint_validation_required=True,checkpoint_outputs=manifest))
    successor={**plan,'config':dict(draws=2000,max_new_draws=100),
        'resume':dict(root=str(old),plan_sha256=limits.filehash(old/'PLAN.json'),paused_sha256=limits.filehash(old/'PAUSED.json'))}
    assert resume.copy_checkpoint(new,successor)['copied']==manifest
    assert resume.output_manifest(old/'output')==resume.output_manifest(new/'output')==manifest
    for key,value in [('budget_key','OTHER'),('campaign','S15-WEEK5')]:
        with pytest.raises(ValueError):resume.copy_checkpoint(tmp_path/key,{**successor,key:value})
    with pytest.raises(ValueError):resume.copy_checkpoint(tmp_path/'changed',{**successor,'config':dict(draws=2001)})
