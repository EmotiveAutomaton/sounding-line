"""Known-answer money, clock, payload and ownership checks; no paid dispatch."""
from copy import deepcopy
import json
import os
from pathlib import Path
from types import SimpleNamespace
import zipfile

import pytest
from runners import gear3_campaign as campaign, gear3_round1 as controller, gear3_supplement as supplement
from runners.stage10 import gear3_bundle
from tests.test_gear3_controller import account

SPEC = Path('docs/archive/study-specs/GEAR_3_ROUND_1_2026-09-13.md')


def original(tmp_path):
    grant = supplement.authorization()
    ledger = campaign.CampaignLedger(tmp_path / 'ledger.json')
    ledger.enroll(controller.AUTHORITY, SPEC)
    parent = ledger.reserve(grant['original_invocation'], 'P',
        ['runners/gear3.py', 'round1', grant['original_bundle_sha256']],
        {'job_sha256': grant['original_job_sha256'], 'image': grant['image'], 'startup_seconds': 300},
        3000, 25, approval='constructed original pilot', now=100)
    ledger.transition(parent['invocation_id'], 'SUBMITTED', call_id='fixture')
    ledger.transition(parent['invocation_id'], 'FAILED', owner_ended=True, evidence={'fixture': True})
    args = dict(invocation=grant['invocation'], node='Reserve',
        command=['runners/gear3.py', 'round1', grant['bundle_sha256']],
        profile={'job_sha256': grant['job_sha256'], 'image': grant['image'], 'startup_seconds': 300},
        seconds=600, overhead_cents=25, approval=grant['owner_instruction'], now=5000,
        supplement_authorization=grant)
    return ledger, parent, args


def test_single_supplement_preserves_expired_original_and_full_cost(tmp_path):
    ledger, parent, args = original(tmp_path)
    before = json.loads(ledger.path.read_text())['runs'][0]
    row = ledger.reserve(**args)
    data = json.loads(ledger.path.read_text())
    assert data['runs'][0] == before and before['expires_at'] == 3100
    assert row['expires_at'] == 5600 and row['reserved_cents'] == row['booked_cents'] == 64
    assert row['recovery_of'] is None and sum(ledger.totals(data).values()) == 281
    assert ledger.reserve(**args)['existing_reservation'] is True
    with pytest.raises(ValueError):
        ledger.reserve(**{**args, 'invocation': 'renamed-second-supplement'})
    assert len(json.loads(ledger.path.read_text())['runs']) == 2
    ledger.transition(row['invocation_id'], 'SUBMITTED', call_id='supplement-fixture')
    ledger.transition(row['invocation_id'], 'FAILED', owner_ended=True, evidence={'fixture': True})
    with pytest.raises(ValueError, match='recovery of a recovery'):
        ledger.reserve('retry-supplement', 'Reserve', row['command'], row['profile'], 30, 0,
            approval='fixture', recovery_of=row['invocation_id'], now=5500)


@pytest.mark.parametrize('change', [
    {'supplement_authorization': None}, {'node': 'A'}, {'invocation': 'other'},
    {'seconds': 601}, {'overhead_cents': 26}, {'approval': 'unapproved wording'},
    {'command': ['different-payload']}, {'cache': True}, {'recovery_of': 'p-gpu-panel-v1'},
    {'profile': {'job_sha256': '0'*64}},
])
def test_changed_or_unapproved_supplement_refuses_before_booking(tmp_path, change):
    ledger, _, args = original(tmp_path)
    before = ledger.path.read_bytes()
    with pytest.raises(ValueError): ledger.reserve(**{**args, **change})
    assert json.loads(ledger.path.read_bytes()) == json.loads(before)


@pytest.mark.parametrize('condition', ['unknown-owner', 'changed-parent', 'changed-approval', 'reserve-exhausted', 'workspace-exhausted'])
def test_parent_and_budget_guards_still_apply(tmp_path, condition):
    ledger, _, args = original(tmp_path)
    if condition == 'changed-approval':
        args['supplement_authorization'] = {**args['supplement_authorization'], 'reservation_cap_cents': 100}
    elif condition == 'workspace-exhausted':
        def deny(*unused): raise ValueError('workspace allocation exhausted')
        args['reservation_guard'] = deny
    else:
        with ledger.transaction() as data:
            if condition == 'unknown-owner': data['runs'][0]['owner_ended'] = False
            elif condition == 'changed-parent': data['runs'][0]['command'][-1] = 'changed'
            else:
                data['runs'].append({'campaign_id': campaign.CAMPAIGN, 'invocation_id': 'old-reserve',
                    'node': 'Reserve', 'booked_cents': 950, 'status': 'FAILED', 'owner_ended': True})
    count = len(json.loads(ledger.path.read_text())['runs'])
    with pytest.raises(ValueError): ledger.reserve(**args)
    assert len(json.loads(ledger.path.read_text())['runs']) == count


def test_actual_approved_bundle_and_altered_request_refusal():
    source = os.environ.get('G3_CONTEXT_SUPPLEMENT_BUNDLE')
    if not source: pytest.skip('requires privately prepared, approved original context bundle')
    bundle = Path(source)
    job, checked = gear3_bundle.validate_input(bundle, Path.cwd(), Path(os.environ['G3_GHOST_ROOT']))
    grant = supplement.verify_payload(Path.cwd(), bundle, job)
    assert checked['archive_sha256'] == grant['bundle_sha256']
    with pytest.raises(ValueError): supplement.verify_payload(Path.cwd(), bundle, {**job, 'blocks': []})


@pytest.mark.parametrize('approved', [False, True])
def test_adapter_reaches_provider_only_after_exact_reservation(tmp_path, monkeypatch, approved):
    source = os.environ.get('G3_CONTEXT_SUPPLEMENT_BUNDLE')
    if not source: pytest.skip('requires privately prepared context bundle')
    ledger, _, reserve_args = original(tmp_path)
    root = tmp_path / 'repo'; root.mkdir()
    spec = root / SPEC; spec.parent.mkdir(parents=True); spec.write_bytes(SPEC.read_bytes())
    auth = root / supplement.AUTHORIZATION_PATH; auth.parent.mkdir(parents=True)
    auth.write_bytes(Path(supplement.AUTHORIZATION_PATH).read_bytes())
    account_path = tmp_path / 'account.json'; account(account_path)
    bundle = Path(source)
    with zipfile.ZipFile(bundle) as archive: job = json.loads(archive.read('JOB.json'))
    monkeypatch.setattr(controller, 'authoritative_ledger', lambda repo: ledger.path)
    monkeypatch.setattr(controller, 'provider_client', lambda account: (object(), {'workspace': 'fixture', 'workspace_id': 'fixture'}))
    monkeypatch.setattr(__import__('runners.gear3_runtime', fromlist=['validate_runtime']), 'validate_runtime', lambda: {'fixture': True})
    monkeypatch.setattr(gear3_bundle, 'validate_input', lambda *args: (job, {'archive_sha256': reserve_args['command'][-1]}))
    entered = []
    import modal
    def stop_before_any_cloud_object(*args):
        row = json.loads(ledger.path.read_text())['runs'][-1]
        assert row['reserved_cents'] == 64 and row['status'] == 'RESERVED'
        assert row['supplement_authorization'] == supplement.authorization()
        entered.append(True)
        raise RuntimeError('constructed provider boundary; no cloud allocation')
    monkeypatch.setattr(modal, 'App', stop_before_any_cloud_object)
    args = SimpleNamespace(account=account_path, bundle=bundle, node='Reserve',
        invocation=reserve_args['invocation'], seconds=600, startup_seconds=300, overhead_cents=25,
        approval=reserve_args['approval'], recovery_of=None, pilot=None, plan=None, context_supplement=approved)
    with pytest.raises(RuntimeError if approved else ValueError): controller.dispatch(root, args)
    assert bool(entered) == approved
    data = json.loads(ledger.path.read_text())
    if approved:
        assert data['runs'][-1]['status'] == 'UNKNOWN' and data['runs'][-1]['booked_cents'] == 64
    else: assert len(data['runs']) == 1
