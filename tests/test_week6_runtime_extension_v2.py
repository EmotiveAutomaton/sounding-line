"""R18 constructed boundary checks; no live registry, process or scientific data.

DESIGN CHECK: same refusal under every scientific direction. New family totals
include fixtures and all attempts; live/unknown native readers and changed
receipts fail. Exact clock-only calendar compatibility is a narrow exception.
"""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import json
import pytest
from runners.drive.cards import week6_policy_v2 as original
from runners.drive.cards import week6_policy_extension_v2 as policy
from runners.drive.cards import week6_limits_extension_v2 as limits
from runners.drive.cards import week6_transition_extension_v2 as transition
from runners.drive.cards.batch_runtime import filehash


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value)+'\n', encoding='utf8')
    return path


def budget(root, key, family, cap, preparation=0, prior=0):
    evidence = put(root.parent/(key+'-evidence.json'), {'constructed':True})
    row = dict(campaign='S15-WEEK6', key=key, family=family, owner_reviewed=True,
        revision=1, previous_sha256=None, ceiling_cpu_seconds=cap,
        preparation_cpu_seconds=preparation, prior_campaign_cpu_seconds=prior,
        evidence_pins={str(evidence):filehash(evidence)})
    path = put(root/'_budgets'/f'{key}-r0001.json', row)
    return row, path


def terminal(root, name='old', family='IN', key='IN16', cpu=17, status='FAILED', runtime='week6-v2'):
    attempt = root/name
    plan = dict(campaign='S15-WEEK6', family=family, budget_key=key, max_cpu_seconds=100,
                accounting_runtime=runtime)
    put(attempt/'PLAN.json', plan); (attempt/'ATTEMPT.claim').touch()
    native = dict(pid=1234, created_ticks=99, executable='constructed-python')
    put(attempt/'OWNER.json', dict(native=native, plan_sha256=filehash(attempt/'PLAN.json')))
    put(attempt/(status+'.json'), dict(status=status, cpu_seconds=cpu))
    return attempt, native


def review_fixture(tmp_path, monkeypatch):
    root = tmp_path/'campaign'; root.mkdir()
    attempt, native = terminal(root)
    source = put(tmp_path/'source.json', {'constructed':True})
    monkeypatch.setattr(transition, 'REQUIRED_SOURCES', (source,))
    monkeypatch.setattr(transition, 'native_identity', lambda pid:None)
    monkeypatch.setattr(transition, 'check_process_census', lambda compatible, root:None)
    inventory = transition.legacy_inventory(root)
    filing = put(tmp_path/'filing.json', dict(full_write_through=True, accounting_reconciled=True,
        attempt_root=str(attempt), terminal_pins=inventory['old']['pins']))
    proof = dict(schema='WEEK6_R18_TRANSITION_REVIEW_V1', epoch=transition.EPOCH,
        campaign_root=str(root), owner_reviewed=True, full_write_through=True,
        at=policy.OPEN.isoformat(), legacy_launchers_retired_from_owner_workflow=True,
        source_pins={str(source.resolve()):filehash(source)}, legacy_inventory=inventory,
        baseline_budget_pins={}, compatible_calendars=[], pending_preparation={},
        filing_receipts={'old':{'path':str(filing), 'sha256':filehash(filing)}})
    path = put(tmp_path/'review.json', proof)
    return root, path, proof, native


@pytest.mark.parametrize('family,cap', [('KP',20000),('ES',100000),('MI',10000),('IP',20000),('EN',60000)])
def test_r18_family_caps_are_shared_and_original_caps_are_preserved(family, cap):
    assert policy.FAMILY_CEILINGS[family] == cap == limits.EXTENSION_FAMILY_CAPS[family]
    assert all(policy.FAMILY_CEILINGS[key] == value for key,value in original.FAMILY_CEILINGS.items())
    assert policy.CEILING == original.CEILING == 6_000_000
    assert (policy.OPEN,policy.FREEZE,policy.DRAIN,policy.ADDENDUM) == (original.OPEN,original.FREEZE,original.DRAIN,original.ADDENDUM)


def test_old_readers_reject_new_preparation_even_without_a_plan(tmp_path):
    root = tmp_path/'campaign'; root.mkdir()
    budget(root,'KP1','KP',20000,preparation=100)
    with pytest.raises(ValueError, match='Unknown preparation family'):
        original.charges(root)
    assert policy.charges(root)['KP'] == 100


@pytest.mark.parametrize('status', ['COMPLETE','FAILED','PAUSED'])
def test_every_terminal_charge_and_supervision_is_retained(tmp_path,status):
    root = tmp_path/'campaign'; root.mkdir()
    budget(root,'IN16','IN',20000,preparation=100)
    budget(root,'KP1','KP',20000,preparation=200)
    terminal(root,'prior','IN','IN16',17,status)
    terminal(root,'new','KP','KP1',23,status,transition.EPOCH)
    charges=policy.charges(root)
    assert charges['IN']==147 and charges['KP']==253


def test_kp_three_cards_and_fixture_share_twenty_thousand(tmp_path):
    root=tmp_path/'campaign';root.mkdir()
    for key in ('KP1','KP2','KP3'):
        budget(root,key,'KP',20000,preparation=1000)
        terminal(root,key,'KP',key,5000,'COMPLETE',transition.EPOCH)
    assert policy.charges(root)['KP']==18090
    assert policy.remaining('KP',root)==1910


def test_prior_card_cost_and_cumulative_preparation_do_not_reset_or_double(tmp_path):
    root=tmp_path/'campaign';root.mkdir()
    row,path=budget(root,'IP1','IP',20000,preparation=100,prior=400)
    original_path=path
    row.update(revision=2,previous_sha256=filehash(path),preparation_cpu_seconds=150)
    path=put(root/'_budgets/IP1-r0002.json',row)
    terminal(root,'IP1','IP','IP1',50,'PAUSED',transition.EPOCH)
    plan=dict(family='IP',budget_key='IP1',budget_receipt=str(path),budget_receipt_sha256=filehash(path),pins={str(path.resolve()):filehash(path)})
    assert policy.charges(root)['IP']==230
    assert policy.available(plan,root)==19370
    assert original_path.exists()


def test_campaign_cap_includes_extension_costs(tmp_path):
    root=tmp_path/'campaign';root.mkdir()
    terminal(root,'retained','CH','CH1',5_999_900,'FAILED')
    terminal(root,'extension','KP','KP1',30,'FAILED',transition.EPOCH)
    assert policy.remaining('KP',root)==10


def test_budget_revisions_refuse_reduced_cost_or_increased_original_limit(tmp_path):
    root=tmp_path/'campaign';root.mkdir()
    row,path=budget(root,'KP1','KP',20000,preparation=100)
    nextrow=deepcopy(row);nextrow.update(revision=2,previous_sha256=filehash(path),preparation_cpu_seconds=99)
    with pytest.raises(ValueError,match='cannot decrease'):limits.validate_prospective_revision(root,nextrow)
    nextrow['preparation_cpu_seconds']=101;nextrow['ceiling_cpu_seconds']=20001
    with pytest.raises(ValueError,match='shared family'):limits.validate_prospective_revision(root,nextrow)
    nextrow['ceiling_cpu_seconds']=20000
    assert limits.validate_prospective_revision(root,nextrow)==nextrow


def test_original_s4_modes_remain_immutable_and_cannot_raise_family_cap(tmp_path):
    root=tmp_path/'campaign';root.mkdir()
    row,path=budget(root,'IP1','IP',20000)
    pin=next(iter(row['evidence_pins']))
    row.update(revision=2,previous_sha256=filehash(path),extension=dict(mode='s4_double',authority_paths=[pin],cost_evidence_paths=[pin]))
    limits.validate_prospective_revision(root,row)
    path=put(root/'_budgets/IP1-r0002.json',row)
    plan=dict(family='IP',budget_key='IP1',budget_receipt=str(path),budget_receipt_sha256=filehash(path),pins={str(path.resolve()):filehash(path)})
    assert limits.plan_budget(plan,root)['effective_ceiling_cpu_seconds']==40000
    assert policy.available(plan,root)==20000


def test_fully_filed_exited_inventory_passes(tmp_path,monkeypatch):
    root,path,proof,native=review_fixture(tmp_path,monkeypatch)
    assert transition.require_transition(path,filehash(path),root)==proof


@pytest.mark.parametrize('condition', ['active','unknown','missing_terminal','changed_owner','extra_plan','missing_filing','changed_budget','missing_source'])
def test_legacy_transition_refuses_unproved_state(tmp_path,monkeypatch,condition):
    root,path,proof,native=review_fixture(tmp_path,monkeypatch)
    if condition=='active':monkeypatch.setattr(transition,'native_identity',lambda pid:native)
    elif condition=='unknown':
        def denied(pid):raise OSError('constructed inaccessible native identity')
        monkeypatch.setattr(transition,'native_identity',denied)
    elif condition=='missing_terminal':(root/'old/FAILED.json').unlink()
    elif condition=='changed_owner':put(root/'old/OWNER.json',dict(native=native,plan_sha256='wrong'))
    elif condition=='extra_plan':put(root/'unstarted/PLAN.json',dict(campaign='S15-WEEK6',accounting_runtime='week6-v1'))
    elif condition=='missing_filing':proof['filing_receipts']={}
    elif condition=='changed_budget':proof['baseline_budget_pins']={'absent-r0001.json':'0'*64}
    elif condition=='missing_source':proof['source_pins']={}
    put(path,proof)
    with pytest.raises((ValueError,RuntimeError,KeyError,OSError)):
        transition.require_transition(path,filehash(path),root)


def test_census_classifies_legacy_and_unknown_but_not_substring_spoof(tmp_path):
    assert transition.classify_process(['python','-m','runners.drive.cards.week6_runtime_v2'],str(tmp_path),tmp_path)=='legacy'
    assert transition.classify_process(['python','-m','runners.drive.cards.week6_runtime_extension_v2'],str(tmp_path),tmp_path)=='extension'
    assert transition.classify_process(['python','-c','print("week6_runtime_extension_v2")'],str(tmp_path),tmp_path)=='unknown_workspace'
    assert transition.classify_process(['python','other.py'],str(tmp_path.parent),tmp_path)=='outside_workspace'


def test_mi_fixtures_require_exact_source_manifest(tmp_path):
    manifest=put(tmp_path/'fixture.json',dict(kind='MIDUS_CONSTRUCTED_FIXTURE_V1',no_real_rows=True,mr1_refused=True,inputs={'invented':'fixture'},module='constructed.module'))
    plan=dict(family='MI',fixture_only=True,data_access='constructed-fixture-only',inputs={'invented':'fixture'},module='constructed.module',
              sealed_fixture_manifest={'path':str(manifest),'sha256':filehash(manifest)},pins={str(manifest.resolve()):filehash(manifest)})
    policy.sealed_fixture_contract(plan)
    for key,value in [('fixture_only',False),('data_access','real-MIDUS'),('inputs',{'source':'real-file'}),('module','other.module')]:
        altered=deepcopy(plan);altered[key]=value
        with pytest.raises(ValueError):policy.sealed_fixture_contract(altered)


def test_existing_policy_epoch_cannot_admit_an_extension_plan():
    with pytest.raises(ValueError):policy.runtime_contract({'accounting_runtime':'week6-v2'})
    with pytest.raises(ValueError):original.runtime_contract({'accounting_runtime':transition.EPOCH})
    policy.runtime_contract({'accounting_runtime':transition.EPOCH})


def test_budget_writer_checks_transition_before_mutation(tmp_path,monkeypatch):
    from runners.drive import week6_launch_extension_v2 as launcher
    from contextlib import nullcontext
    from runners.drive.cards import batch_runtime_v8 as kernel
    monkeypatch.setattr(launcher.policy,'ROOT',tmp_path)
    monkeypatch.setattr(kernel,'admission_lock',lambda *args:nullcontext())
    def refuse(*args,**kwargs):raise RuntimeError('constructed live legacy reader')
    monkeypatch.setattr(transition,'require_transition',refuse)
    with pytest.raises(RuntimeError,match='legacy reader'):
        launcher.freeze_budget({'family':'KP'},'unwritten-review','0'*64)
    assert not (tmp_path/'_budgets').exists()


def test_exact_calendar_compatibility_and_source_change_refusal(tmp_path,monkeypatch):
    source=tmp_path/'calendar.py';source.write_text('# constructed exact clock-only source\n')
    monkeypatch.setattr(transition,'CALENDAR',source);monkeypatch.setattr(transition,'CALENDAR_SHA256',filehash(source))
    monkeypatch.setattr(transition,'REPO',tmp_path)
    root=tmp_path/'calendar';plan=put(root/'PLAN.json',dict(calendar_only=True,research_dispatch=False,campaign='S15-WEEK6-calendar',pins={str(source):filehash(source)}))
    native={'pid':1,'created_ticks':2,'executable':'constructed'}
    owner=put(root/'OWNER.json',dict(native=native,plan_sha256=filehash(plan)))
    record={'root':str(root),'plan_sha256':filehash(plan),'owner_sha256':filehash(owner),'native':native}
    assert transition.calendar_compatibility(record)==native
    source.write_text('# altered budget-reading calendar\n')
    with pytest.raises(ValueError,match='calendar source'):transition.calendar_compatibility(record)


def test_inherited_charge_and_native_execution_bodies_are_unchanged():
    import inspect
    from runners.drive.cards import week6_runtime_v2 as old_runtime
    from runners.drive.cards import week6_runtime_extension_v2 as new_runtime
    for name in ('charges','remaining','available','shared_reservation','memory_reserve','yield_reason'):
        assert inspect.getsource(getattr(policy,name)) == inspect.getsource(getattr(original,name))
    for name in ('run','failure_charge'):
        assert inspect.getsource(getattr(old_runtime,name)) == inspect.getsource(getattr(new_runtime,name))
    old_path=Path(old_runtime.__file__).with_name('tr2_b2_archive_runtime_v1.py')
    new_path=Path(old_runtime.__file__).with_name('tr2_b2_archive_runtime_extension_v2.py')
    expected=old_path.read_text(encoding='utf8').replace(
        'from runners.drive.cards import week6_policy_v1 as policy',
        'from runners.drive.cards import week6_policy_extension_v2 as policy').replace(
        'from runners.drive.cards import week6_runtime_v1 as inherited',
        'from runners.drive.cards import week6_runtime_extension_v2 as inherited')
    assert new_path.read_text(encoding='utf8')==expected


def test_plan_guard_runs_under_mutex_before_new_plan_write(tmp_path,monkeypatch):
    from contextlib import contextmanager
    from runners.drive import week6_launch_extension_v2 as launcher
    from runners.drive.cards import batch_runtime_v8 as kernel
    state={'held':False}
    @contextmanager
    def mutex(*args):
        state['held']=True
        try:yield
        finally:state['held']=False
    def refuse(plan):
        assert state['held']
        raise RuntimeError('constructed legacy refusal under mutex')
    monkeypatch.setattr(kernel,'admission_lock',mutex)
    monkeypatch.setattr(launcher.policy,'ROOT',tmp_path)
    monkeypatch.setattr(launcher,'review',lambda plan:None)
    monkeypatch.setattr(launcher.policy,'admission',refuse)
    with pytest.raises(RuntimeError,match='under mutex'):
        launcher.freeze_plan(tmp_path/'new',{})
    assert not (tmp_path/'new').exists() and state['held'] is False
