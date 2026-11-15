"""Frozen B01-B25 constructed budget boundaries; no human or live campaign inputs.

The command-line helper at the end runs only this file's literal native cases
in temporary campaign/lease namespaces. Production child/resume code is reused.
"""
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import ast
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import os
import threading
import time
import pytest
from runners.drive.cards import week6_limits_v1 as l1, week6_policy_v1 as p1
from runners.drive.cards import week6_limits_v2 as limits, week6_policy_v2 as p
from runners.drive.cards import week6_runtime_v1 as r1, week6_runtime_v2 as runtime
from runners.drive.cards import week6_resume_v1 as resume
from runners.drive.cards.batch_runtime import filehash, read, release_slot
from runners.stage9.process_identity import native_identity, is_same_live_process

ORIGINAL_PINS = {'runners/drive/cards/week6_limits_v1.py': '8ff3038d8023a0aa2dd1d18f8ac6adb616de847b567d71cf22937e748e0a483b', 'runners/drive/cards/week6_policy_v1.py': 'b5a7d22533c495f1bf0e5254bc7fd521c2166979bc06e558acd2fadb425e46a3', 'runners/drive/cards/week6_runtime_v1.py': 'a20fe994e70ce59a62e00953c44534f2acfcbd47b149f1c7ef2e30cba1eaf92b', 'runners/drive/cards/week6_child_v1.py': '339546a95b38c1a932272ff45a9e8707b2ddad23b610d85e82f2dd793ba3c07a', 'runners/drive/cards/week6_resume_v1.py': 'ff2e085228e31414bb3cefe6d61c132d7a0e050e0426775c3e7f4d80b1f55980', 'runners/drive/week6_launch_v1.py': 'b7b245edfa443656e078b86d99a3276889fa52ec1860281eecdec98526090625', 'runners/drive/calendar_20261115_week6.py': '24f88b9ec7dfef045e6f04f1d7e754ea6af73b997e10296e73af9c7ba72211fa', 'tests/test_week6_runtime_v1.py': '31553bd4758f25a90a1af2f3dc7f7e6691722151dd647c27d4fad37da5566594', 'runners/drive/cards/week5_policy_v3.py': '1b53094c787d90749e0b2a4a59434ea9496ddbdcc1dd68aeb27487a43eacaff0'}


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2)+'\n').encode())


def setup(tmp, monkeypatch, family='IN', key='IN13'):
    tmp.mkdir(parents=True, exist_ok=True)
    old, root = tmp/'predecessor', tmp/'campaign'
    root.mkdir()
    # Pure controls never inspect the live counted-slot namespaces.
    monkeypatch.setattr(p, 'lease_paths', lambda: [])
    job = old/'prior'
    put(job/'PLAN.json', dict(campaign='S15-WEEK5', family='IN', max_cpu_seconds=100))
    (job/'ATTEMPT.claim').touch()
    native = dict(pid=123, created_ticks=456, executable='constructed')
    put(job/'OWNER.json', dict(native=native, plan_sha256=filehash(job/'PLAN.json')))
    put(job/'PAUSED.json', dict(cpu_seconds=17, status='PAUSED'))
    report, proof = tmp/'final-drain.json', tmp/'DRAIN_REVIEW.json'
    put(report, dict(id='OPS-S15-W5-FINAL-DRAIN-FIXTURE', full_write_through=True))
    put(proof, dict(at=p.OPEN.isoformat(), owner_reviewed=True, all_native_exits_verified=True,
        full_write_through=True, predecessor_root=str(old), terminal_inventory=limits.predecessor_inventory(old),
        exited_native_identities={'prior': native}, final_drain_receipt=str(report), final_drain_receipt_sha256=filehash(report)))
    for module in (limits, l1):
        monkeypatch.setattr(module, 'PREDECESSOR', old)
        monkeypatch.setattr(module, 'DRAIN_REVIEW', proof)
    evidence = {}
    for name in ('authority', 'cost', 'checkpoint'):
        path = tmp/(name+'.json')
        put(path, dict(constructed=True, kind=name, literal=[2, 3, 5]))
        evidence[str(path)] = filehash(path)
    budget = root/f'_budgets/{key}-r0001.json'
    put(budget, dict(campaign='S15-WEEK6', key=key, family=family, owner_reviewed=True,
        revision=1, previous_sha256=None, ceiling_cpu_seconds=20000,
        prior_campaign_cpu_seconds=400, preparation_cpu_seconds=100, evidence_pins=evidence))
    plan = dict(campaign='S15-WEEK6', family=family, card='constructed', accounting_runtime='week6-v2',
        budget_key=key, budget_receipt=str(budget), budget_receipt_sha256=filehash(budget),
        numerical_threads=2, paid=False, gpu=False, ollama=False,
        premortem=dict(case_and_check='constructed known answer', smaller_route='retain original evidence'),
        max_cpu_seconds=100, max_wall_seconds=45, forecast_cpu_seconds=100, projected_peak_ram_GiB=2,
        fixture_passed=True, reviewed_design_commit='constructed',
        pins={str(path): filehash(path) for path in (budget, proof, report)})
    return dict(tmp=tmp, root=root, old=old, proof=proof, report=report, budget=budget, plan=plan)


def append(ctx, mode='s4_double', prep=None, mutate=None):
    prior = ctx['budget']
    row = read(prior)
    row.update(revision=row['revision']+1, previous_sha256=filehash(prior))
    if prep is not None:
        row['preparation_cpu_seconds'] = prep
    if mode == 'original':
        row.pop('extension', None)
    else:
        row['extension'] = dict(mode=mode, authority_paths=[str(ctx['tmp']/'authority.json')],
            cost_evidence_paths=[str(ctx['tmp']/'cost.json')])
        if mode == 'lb_idle_family':
            row['extension']['checkpoint_evidence_paths'] = [str(ctx['tmp']/'checkpoint.json')]
    if mutate:
        mutate(row)
    path = ctx['root']/f"_budgets/{row['key']}-r{row['revision']:04d}.json"
    put(path, row)
    ctx['budget'] = path
    return path


def bind(ctx, path=None, plan=None):
    plan = deepcopy(plan or ctx['plan'])
    path = path or ctx['budget']
    plan.update(budget_receipt=str(path), budget_receipt_sha256=filehash(path))
    plan['pins'][str(path)] = filehash(path)
    return plan


def doubled(tmp, monkeypatch):
    ctx = setup(tmp, monkeypatch)
    append(ctx, prep=150)
    ctx['plan'] = bind(ctx)
    return ctx


def lb(tmp, monkeypatch, **kwargs):
    ctx = setup(tmp, monkeypatch, **kwargs)
    append(ctx, prep=150)
    append(ctx, 'lb_idle_family')
    ctx['plan'] = bind(ctx)
    return ctx


RESOURCES = dict(ram_available_GiB=32, commit_headroom_GiB=32, disk_free_GiB=99)


def admit(ctx, plan=None, **kwargs):
    args = dict(at=p.OPEN+timedelta(minutes=1), resources=RESOURCES,
        budget_root=ctx['root'], lock_path=ctx['tmp']/'shared.lock', occupied=[], logical=24)
    args.update(kwargs)
    return p.admission(plan or ctx['plan'], **args)


def attempt(ctx, name, terminal=None, cpu=17, claim=True, **changes):
    root = ctx['root']/name
    plan = {**ctx['plan'], **changes}
    put(root/'PLAN.json', plan)
    if claim:
        (root/'ATTEMPT.claim').touch()
    if terminal:
        put(root/(terminal+'.json'), dict(cpu_seconds=cpu))
    return root


def fixed_clock(monkeypatch):
    stamp = p.OPEN+timedelta(minutes=1)
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return stamp if tz else stamp.replace(tzinfo=None)
    monkeypatch.setattr(p, 'datetime', Clock)
    return stamp


def local_claim(ctx, monkeypatch):
    old, new = ctx['tmp']/'slots-old', ctx['tmp']/'slots-new'
    old.mkdir(exist_ok=True)
    new.mkdir(exist_ok=True)
    monkeypatch.setattr(p, 'OLD_SLOTS', old)
    monkeypatch.setattr(p, 'NEW_SLOTS', new)
    original_admission = p.admission
    monkeypatch.setattr(p, 'lease_paths', lambda: sorted(old.glob('slot-*.json'))+sorted(new.glob('slot-*.json')))
    monkeypatch.setattr(p, 'admission', lambda plan: original_admission(plan,
        at=p.OPEN+timedelta(minutes=1), resources=RESOURCES, logical=24,
        budget_root=ctx['root'], lock_path=ctx['tmp']/'shared.lock'))
    return old, new


def occupy(banks, indices):
    for index in indices:
        path = banks[int(index >= 4)]/f'slot-{index}.json'
        put(path, dict(native=native_identity(), projected_peak_ram_GiB=1,
            card='constructed-occupant', attempt_root=str(path.parent/'constructed')))


def test_b01_base_arithmetic(tmp_path, monkeypatch):
    ctx = setup(tmp_path, monkeypatch)
    assert p.available(ctx['plan'], ctx['root']) == 19500
    assert p.charges(ctx['root'])['IN'] == 100


def test_b02_single_doubling_arithmetic(tmp_path, monkeypatch):
    ctx = setup(tmp_path, monkeypatch)
    append(ctx)
    plan = bind(ctx)
    assert p.available(plan, ctx['root']) == 39500
    budget = limits.plan_budget(plan, ctx['root'])
    assert budget['ceiling_cpu_seconds'] == 20000
    assert budget['effective_ceiling_cpu_seconds'] == 40000


def test_b03_cumulative_preparation_once(tmp_path, monkeypatch):
    ctx = doubled(tmp_path, monkeypatch)
    assert p.charges(ctx['root'])['IN'] == 150
    assert p.available(ctx['plan'], ctx['root']) == 39450


def test_b04_old_plan_never_auto_promoted(tmp_path, monkeypatch):
    ctx = setup(tmp_path, monkeypatch)
    append(ctx, prep=150)
    assert p.available(ctx['plan'], ctx['root']) == 19450
    assert p1.available(ctx['plan'], ctx['root']) == 19450
    assert l1.budgets(ctx['root'])['IN13']['extension']['mode'] == 's4_double'


def test_b05_doubled_plan_never_auto_lb(tmp_path, monkeypatch):
    ctx = doubled(tmp_path, monkeypatch)
    append(ctx, 'lb_idle_family', prep=175)
    assert p.available(ctx['plan'], ctx['root']) == 39425
    assert p.available(bind(ctx), ctx['root']) == 199825
    assert limits.plan_budget(ctx['plan'], ctx['root'])['allowance_mode'] == 's4_double'


def test_b06_original_identity_and_ancestry(tmp_path, monkeypatch):
    defects = {
        'key': lambda r: r.update(key='OTHER'),
        'family': lambda r: r.update(family='MD'),
        'ceiling': lambda r: r.update(ceiling_cpu_seconds=40000),
        'prior': lambda r: r.update(prior_campaign_cpu_seconds=0),
        'missing_revision': lambda r: r.update(revision=3),
        'ancestry': lambda r: r.update(previous_sha256='bad'),
        'dropped_evidence': lambda r: r['evidence_pins'].pop(next(iter(r['evidence_pins']))),
        'lower_prep': lambda r: r.update(preparation_cpu_seconds=99),
    }
    for name, defect in defects.items():
        ctx = setup(tmp_path/name, monkeypatch)
        append(ctx, mutate=defect)
        with pytest.raises(ValueError):
            p.available(ctx['plan'], ctx['root'])


def test_b07_strict_extension_schema(tmp_path, monkeypatch):
    defects = {
        'unknown': lambda r: r['extension'].update(mode='triple'),
        'unreviewed': lambda r: r.update(owner_reviewed=False),
        'authority': lambda r: r['extension'].pop('authority_paths'),
        'cost': lambda r: r['extension'].pop('cost_evidence_paths'),
        'unbound': lambda r: r['extension'].update(authority_paths=['not-pinned']),
        'empty': lambda r: r['extension'].update(cost_evidence_paths=[]),
        'string': lambda r: r['extension'].update(authority_paths='not-a-list'),
        'multiplier': lambda r: r['extension'].update(multiplier=2),
        'null': lambda r: r.update(extension=None),
    }
    for name, defect in defects.items():
        ctx = setup(tmp_path/name, monkeypatch)
        append(ctx, mutate=defect)
        with pytest.raises(ValueError):
            limits.budgets(ctx['root'])
    ctx = doubled(tmp_path/'checkpoint', monkeypatch)
    append(ctx, 'lb_idle_family', mutate=lambda r: r['extension'].pop('checkpoint_evidence_paths'))
    with pytest.raises(ValueError):
        limits.budgets(ctx['root'])
    ctx = setup(tmp_path/'first-extension', monkeypatch)
    row = read(ctx['budget'])
    row['extension'] = dict(mode='s4_double', authority_paths=[str(ctx['tmp']/'authority.json')],
        cost_evidence_paths=[str(ctx['tmp']/'cost.json')])
    put(ctx['budget'], row)
    with pytest.raises(ValueError, match='begin'):
        limits.budgets(ctx['root'])


def test_b08_only_one_doubling_and_forward_modes(tmp_path, monkeypatch):
    ctx = doubled(tmp_path/'same', monkeypatch)
    append(ctx)
    append(ctx)
    assert limits.plan_budget(bind(ctx), ctx['root'])['effective_ceiling_cpu_seconds'] == 40000
    for name, first, second in [('skip', 'original', 'lb_idle_family'),
            ('back', 's4_double', 'original'), ('lb-back', 'lb_idle_family', 's4_double')]:
        ctx = setup(tmp_path/name, monkeypatch)
        if first != 'original':
            append(ctx)
        if first == 'lb_idle_family':
            append(ctx, first)
        append(ctx, second)
        with pytest.raises(ValueError, match='ancestry'):
            limits.budgets(ctx['root'])
    ctx = setup(tmp_path/'overflow', monkeypatch, key='OTHER')
    row = read(ctx['budget']); row['ceiling_cpu_seconds'] = 1e308; put(ctx['budget'], row)
    append(ctx)
    with pytest.raises(ValueError, match='accounting'):
        limits.budgets(ctx['root'])


def test_b09_prior_campaign_not_rebooked(tmp_path, monkeypatch):
    ctx = doubled(tmp_path, monkeypatch)
    assert read(ctx['old']/'prior/PAUSED.json')['cpu_seconds'] == 17
    assert sum(p.charges(ctx['root']).values()) == 150
    assert p.available(ctx['plan'], ctx['root']) == 40000-400-150


def test_b10_failed_and_paused_attempts_remain_charged(tmp_path, monkeypatch):
    for terminal in ('FAILED', 'PAUSED'):
        ctx = doubled(tmp_path/terminal, monkeypatch)
        attempt(ctx, 'old-attempt', terminal)
        assert p.charges(ctx['root'])['IN'] == 197
        assert p.available(ctx['plan'], ctx['root']) == 39403


def test_b11_unclaimed_and_nested_cost_not_double_charged(tmp_path, monkeypatch):
    ctx = doubled(tmp_path, monkeypatch)
    attempt(ctx, 'unclaimed', claim=False, max_cpu_seconds=10000)
    done = attempt(ctx, 'done', 'COMPLETE')
    put(done/'output/COST_PREFIX.json', dict(cpu_seconds=999999))
    assert p.charges(ctx['root'])['IN'] == 197


def test_b12_fresh_active_envelope(tmp_path, monkeypatch):
    ctx = doubled(tmp_path, monkeypatch)
    stamp = fixed_clock(monkeypatch)
    running = attempt(ctx, 'active')
    put(running/'BUDGET_PROGRESS.json', dict(cpu_seconds=10, at=(stamp-timedelta(seconds=1)).isoformat()))
    assert p.charges(ctx['root'])['IN'] == 196
    assert p.available(ctx['plan'], ctx['root']) == 39404


def test_b13_stale_and_unknown_active_reserve_cap(tmp_path, monkeypatch):
    for stale in (False, True):
        ctx = doubled(tmp_path/str(stale), monkeypatch)
        stamp = fixed_clock(monkeypatch)
        running = attempt(ctx, 'active', max_cpu_seconds=123)
        if stale:
            put(running/'BUDGET_PROGRESS.json', dict(cpu_seconds=100, at=(stamp-timedelta(seconds=16)).isoformat()))
        assert p.charges(ctx['root'])['IN'] == 303
        assert p.available(ctx['plan'], ctx['root']) == 39297


def test_b14_ambiguous_or_missing_accounting_never_zero(tmp_path, monkeypatch):
    ctx = doubled(tmp_path/'ambiguous', monkeypatch)
    done = attempt(ctx, 'done', 'FAILED')
    put(done/'PAUSED.json', dict(cpu_seconds=17))
    with pytest.raises(ValueError, match='Ambiguous'):
        p.charges(ctx['root'])
    ctx = doubled(tmp_path/'future', monkeypatch)
    stamp = fixed_clock(monkeypatch)
    running = attempt(ctx, 'active')
    put(running/'BUDGET_PROGRESS.json', dict(cpu_seconds=1, at=(stamp+timedelta(seconds=1)).isoformat()))
    with pytest.raises(ValueError, match='future'):
        p.charges(ctx['root'])
    monkeypatch.setattr(p, 'READ_DELAYS', ())
    assert runtime.failure_charge(ctx['root'], ctx['plan'], ['execute'], 3) == (100, True)
    ctx = doubled(tmp_path/'unreadable', monkeypatch)
    original = limits.check_files
    def unavailable(_):
        raise PermissionError('constructed accounting access refusal')
    monkeypatch.setattr(limits, 'check_files', unavailable)
    with pytest.raises(PermissionError):
        p.available(ctx['plan'], ctx['root'])
    monkeypatch.setattr(limits, 'check_files', original)


def test_b15_exclude_current_attempt_never_excludes_preparation(tmp_path, monkeypatch):
    ctx = doubled(tmp_path, monkeypatch)
    stamp = fixed_clock(monkeypatch)
    attempt(ctx, 'peer', 'PAUSED')
    current = attempt(ctx, 'current')
    put(current/'BUDGET_PROGRESS.json', dict(cpu_seconds=10, at=stamp.isoformat()))
    assert p.charges(ctx['root'], exclude=current)['IN'] == 197
    room = p.available(ctx['plan'], ctx['root'], exclude=current)
    assert room == 39403
    assert room-(10+30) == 39363
    assert p.available(ctx['plan'], ctx['root']) == room-44


def test_b16_lb_still_obeys_family_and_campaign(tmp_path, monkeypatch):
    ctx = lb(tmp_path, monkeypatch)
    attempt(ctx, 'past-doubling', 'COMPLETE', cpu=40000)
    monkeypatch.setattr(p, 'FAMILY_CEILINGS', {**p.FAMILY_CEILINGS, 'IN': 50000})
    monkeypatch.setattr(p, 'CEILING', 100000)
    assert p.available(ctx['plan'], ctx['root']) == 9820
    monkeypatch.setattr(p, 'CEILING', 41000)
    assert p.available(ctx['plan'], ctx['root']) == 820
    monkeypatch.setattr(p, 'CEILING', 40180)
    assert p.available(ctx['plan'], ctx['root']) == 0
    budget = limits.plan_budget(ctx['plan'], ctx['root'])
    assert budget['ceiling_cpu_seconds'] == 20000 and budget['prior_campaign_cpu_seconds'] == 400
    assert budget['effective_ceiling_cpu_seconds'] is None


def test_b17_idle_capacity_shared_reservation_and_bk_bank(tmp_path, monkeypatch):
    ctx = lb(tmp_path/'general', monkeypatch)
    with pytest.raises(RuntimeError, match='occupied'):
        admit(ctx, occupied=[ctx['tmp']/str(i) for i in range(8)])
    stamp = p.OPEN+timedelta(minutes=1)
    put(ctx['tmp']/'shared.lock', dict(created_at=p.OPEN.isoformat(), expires_at=(p.OPEN+timedelta(hours=1)).isoformat()))
    with pytest.raises(RuntimeError, match='occupied'):
        admit(ctx, occupied=[ctx['tmp']/str(i) for i in range(7)], at=stamp)
    (ctx['tmp']/'shared.lock').unlink()
    with monkeypatch.context() as scoped:
        banks = local_claim(ctx, scoped)
        occupy(banks, range(7))
        lease, receipt = runtime.claim(ctx['root']/'new', ctx['plan'])
        try:
            assert receipt['idle_slots_before_claim'] == 1
            assert receipt['allowance_mode'] == 'lb_idle_family'
        finally:
            release_slot(*lease)
    ctx = lb(tmp_path/'bk', monkeypatch, family='BK', key='FIXTURE-BK')
    banks = local_claim(ctx, monkeypatch)
    occupy(banks, range(4))
    with pytest.raises(RuntimeError, match='No free counted slot'):
        runtime.claim(ctx['root']/'new', ctx['plan'])
    assert not list(banks[1].glob('slot-*.json'))


def test_b18_review_to_claim_race_rechecks_under_mutex(tmp_path, monkeypatch):
    ctx = lb(tmp_path, monkeypatch)
    banks = local_claim(ctx, monkeypatch)
    occupy(banks, range(7))
    assert p.admission(ctx['plan'])['idle_slots_before_claim'] == 1
    saved = {str(x): x.read_bytes() for x in p.lease_paths()}
    original_lock, original_admission = runtime.kernel.admission_lock, p.admission
    state = {'locked': False, 'checked': False}
    @contextmanager
    def mutex(path):
        with original_lock(path):
            state['locked'] = True
            occupy(banks, [7])
            try:
                yield
            finally:
                state['locked'] = False
    def checked(plan):
        assert state['locked']
        state['checked'] = True
        return original_admission(plan)
    monkeypatch.setattr(runtime.kernel, 'admission_lock', mutex)
    monkeypatch.setattr(p, 'admission', checked)
    with pytest.raises(RuntimeError, match='occupied'):
        runtime.claim(ctx['root']/'new', ctx['plan'])
    assert state['checked'] and all(Path(path).read_bytes() == content for path, content in saved.items())


def test_b19_finite_checkpoint_quantum_and_pinned_evidence(tmp_path, monkeypatch):
    ctx = lb(tmp_path, monkeypatch)
    receipt = admit(ctx)
    assert receipt['cumulative_card_cpu_seconds'] == 550
    assert receipt['original_ceiling_cpu_seconds'] == 20000
    assert receipt['budget_receipt_sha256'] == filehash(ctx['budget'])
    assert receipt['remaining_cpu_seconds'] == 199820
    for field in ('max_cpu_seconds', 'max_wall_seconds', 'projected_peak_ram_GiB'):
        for value in (0, -1, float('inf'), float('nan')):
            with pytest.raises(ValueError):
                admit(ctx, {**ctx['plan'], field: value})
    (ctx['tmp']/'checkpoint.json').write_bytes(b'changed')
    with pytest.raises(ValueError):
        admit(ctx)


def test_b20_owned_quantum_keeps_slot_next_dispatch_rechecks(tmp_path, monkeypatch):
    ctx = lb(tmp_path, monkeypatch)
    banks = local_claim(ctx, monkeypatch)
    lease, _ = runtime.claim(ctx['root']/'owned', ctx['plan'])
    own_index = int(lease[0].stem.split('-')[1])
    try:
        occupy(banks, [i for i in range(8) if i != own_index])
        assert p.available(ctx['plan'], ctx['root'], exclude=ctx['root']/'owned') == 199850
        assert p.yield_reason(ctx['root']/'owned', ctx['plan'], RESOURCES) is None
        assert read(lease[0]) == lease[1]
        with pytest.raises(RuntimeError, match='occupied'):
            runtime.claim(ctx['root']/'next', ctx['plan'])
    finally:
        release_slot(*lease)
    assert p.admission(ctx['plan'])['idle_slots_before_claim'] == 1


def test_b21_v1_compatibility_and_immutable_pins(tmp_path, monkeypatch):
    ctx = lb(tmp_path, monkeypatch)
    assert l1.budgets(ctx['root'])['IN13']['extension']['mode'] == 'lb_idle_family'
    assert p1.charges(ctx['root'])['IN'] == 150
    assert p1.available(ctx['plan'], ctx['root']) == 19450
    for name, digest in ORIGINAL_PINS.items():
        assert filehash(REPO/name) == digest, name


def resume_setup(tmp, monkeypatch):
    monkeypatch.setattr(p1, 'ROOT', tmp)
    monkeypatch.setattr(resume, 'is_same_live_process', lambda _: False)
    old = tmp/'old'
    source = tmp/'fixed'; source.parent.mkdir(parents=True, exist_ok=True); source.write_bytes(b'literal')
    plan = dict(module='runners.drive.cards.week6_budget_fixture_v2', campaign='S15-WEEK6', family='IN',
        budget_key='IN13', accounting_runtime='week6-v1', inputs={'literal': [2, 3, 5]},
        config={'max_new_draws': 1}, pins={str(source): filehash(source)})
    put(old/'PLAN.json', plan)
    put(old/'OWNER.json', dict(native={}, plan_sha256=filehash(old/'PLAN.json')))
    put(old/'output/CHECKPOINT.json', [2])
    manifest = resume.output_manifest(old/'output')
    put(old/'PAUSED.json', dict(status='PAUSED', checkpoint_validation_required=True, checkpoint_outputs=manifest))
    successor = {**plan, 'accounting_runtime': 'week6-v2', 'config': {'max_new_draws': 2},
        'resume': dict(root=str(old), plan_sha256=filehash(old/'PLAN.json'), paused_sha256=filehash(old/'PAUSED.json'))}
    return old, successor, manifest


def test_b22_resume_identity_receipts_science_and_manifest(tmp_path, monkeypatch):
    old, successor, manifest = resume_setup(tmp_path/'valid', monkeypatch)
    assert resume.copy_checkpoint(old.parent/'new', successor)['copied'] == manifest
    assert resume.output_manifest(old/'output') == resume.output_manifest(old.parent/'new/output') == manifest
    for defect in ('key', 'science', 'pin', 'live', 'manifest', 'receipt'):
        old, successor, _ = resume_setup(tmp_path/defect, monkeypatch)
        if defect == 'key': successor['budget_key'] = 'OTHER'
        if defect == 'science': successor['inputs'] = {'literal': [2, 3, 6]}
        if defect == 'pin': successor['pins'] = {}
        if defect == 'live': monkeypatch.setattr(resume, 'is_same_live_process', lambda _: True)
        if defect == 'manifest': put(old/'output/CHECKPOINT.json', [3])
        if defect == 'receipt': successor['resume']['paused_sha256'] = 'bad'
        with pytest.raises(ValueError):
            resume.copy_checkpoint(old.parent/'new', successor)


def native_plan(ctx, version, module, config, predecessor=None):
    plan = bind(ctx, plan=predecessor)
    plan.update(accounting_runtime='week6-'+version, module=module,
        inputs={'literal': [2, 3, 5]}, config=config, max_output_bytes=65536)
    names = ['runners/drive/cards/week6_child_v1.py', 'runners/drive/cards/week6_resume_v1.py',
        'runners/drive/cards/week6_runtime_fixture_v1.py', 'runners/drive/cards/week6_budget_fixture_v2.py',
        'tests/test_week6_budget_v2.py']
    for kind in ('limits', 'policy', 'runtime'):
        names.append(f'runners/drive/cards/week6_{kind}_{version}.py')
    for name in names:
        path = (REPO/name).resolve(); plan['pins'][str(path)] = filehash(path)
    return plan


def run_native(ctx, name, version, plan):
    from runners.drive.native_job import ContainedProcess
    root = ctx['root']/name
    put(root/'PLAN.json', plan)
    command = [sys.executable, '-X', 'utf8', '-B', str(Path(__file__).resolve()),
        'supervisor', version, str(root), str(ctx['tmp'])]
    env = os.environ.copy()
    for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        env[key] = '2'
    started = time.monotonic()
    with ContainedProcess(command, REPO, root/'driver.stdout.txt', root/'driver.stderr.txt', env) as child:
        while child.poll() is None:
            if time.monotonic()-started > 60:
                pytest.fail('Constructed native supervisor exceeded sixty seconds')
            time.sleep(.05)
        assert child.poll() == 0, (root/'driver.stderr.txt').read_text()
    assert not is_same_live_process(read(root/'OWNER.json')['native'])
    terminal = read(root/('PAUSED.json' if (root/'PAUSED.json').exists() else 'COMPLETE.json'))
    measured = []
    for operation in ('EXECUTE', 'VERIFY'):
        path = root/(operation+'_JOB_USAGE.json')
        if path.exists():
            usage = read(path)
            assert usage['includes_all_descendants_and_exited_processes'] and usage['exit_code'] == 0
            measured.append(usage['cpu_seconds'])
            assert not is_same_live_process(read(root/(operation+'_NATIVE.json'))['native'])
            environment = read(root/(operation+'_ENVIRONMENT.json'))
            assert environment['threads'] == 2 and environment['cuda_visible'] == ''
            assert all(pool['num_threads'] <= 2 for pool in environment['pools'])
    assert terminal['cpu_seconds'] == sum(measured)
    assert not Path(read(root/'ADMISSION.json')['lease']).exists()
    assert not (root/'FAILED.json').exists()
    return root, terminal


def test_b23_native_literal_complete(tmp_path, monkeypatch):
    ctx = doubled(tmp_path, monkeypatch)
    plan = native_plan(ctx, 'v2', 'runners.drive.cards.week6_runtime_fixture_v1', {'scenario': 'complete'})
    root, terminal = run_native(ctx, 'complete', 'v2', plan)
    assert read(root/'VERIFIED.json')['sum'] == 10 and terminal['fresh_process_verified']
    admission = read(root/'ADMISSION.json')
    assert admission['allowance_mode'] == 's4_double' and admission['idle_slots_before_claim'] == 8
    assert admission['cumulative_preparation_cpu_seconds'] == 150
    assert all(filehash(root/name) == pin for name, pin in terminal['outputs'].items())


def test_b24_native_v1_pause_v2_continuation(tmp_path, monkeypatch):
    ctx = setup(tmp_path, monkeypatch)
    original = native_plan(ctx, 'v1', 'runners.drive.cards.week6_budget_fixture_v2', {'max_new_draws': 1})
    old, paused = run_native(ctx, 'old', 'v1', original)
    original_bytes = (old/'PLAN.json').read_bytes()
    original_checkpoint = (old/'output/CHECKPOINT.json').read_bytes()
    assert paused['status'] == 'PAUSED' and read(old/'output/CHECKPOINT.json') == [2]
    append(ctx, prep=150)
    append(ctx, 'lb_idle_family')
    plan = native_plan(ctx, 'v2', original['module'], {'max_new_draws': 2}, original)
    plan['resume'] = dict(root=str(old), plan_sha256=filehash(old/'PLAN.json'), paused_sha256=filehash(old/'PAUSED.json'))
    new, terminal = run_native(ctx, 'new', 'v2', plan)
    assert read(new/'RESUMED_FROM.json')['copied'] == paused['checkpoint_outputs']
    assert read(new/'RESUMED_FROM.json')['adapter'] == 'week6_resume_v1'
    assert read(new/'VERIFIED.json')['sum'] == 10 and terminal['fresh_process_verified']
    assert original_bytes == (old/'PLAN.json').read_bytes()
    assert original_checkpoint == (old/'output/CHECKPOINT.json').read_bytes()
    assert all(plan['pins'].get(path) == pin for path, pin in original['pins'].items())
    assert p.charges(ctx['root'])['IN'] == 150+paused['cpu_seconds']+terminal['cpu_seconds']+60
    assert read(new/'ADMISSION.json')['allowance_mode'] == 'lb_idle_family'


def test_b25_preserved_global_boundaries(tmp_path, monkeypatch):
    ctx = setup(tmp_path, monkeypatch)
    for name in ('OPEN', 'FREEZE', 'DRAIN', 'ADDENDUM', 'CEILING', 'FAMILY_CEILINGS', 'OLD_SLOTS', 'NEW_SLOTS', 'SHARED_LOCK'):
        assert getattr(p, name) == getattr(p1, name)
    for stamp in (p.OPEN-timedelta(seconds=1), p.FREEZE):
        with pytest.raises(RuntimeError, match='boundary'):
            admit(ctx, at=stamp)
    for field in RESOURCES:
        with pytest.raises(RuntimeError, match='floor'):
            admit(ctx, resources={**RESOURCES, field: 0})
        assert p.yield_reason(ctx['root'], ctx['plan'], {**RESOURCES, field: 0}) == 'resource_floor'
    for field in ('paid', 'gpu', 'ollama'):
        with pytest.raises(ValueError, match='CPU-only'):
            admit(ctx, {**ctx['plan'], field: True})
    with pytest.raises(ValueError, match='threads'):
        admit(ctx, {**ctx['plan'], 'numerical_threads': 3})
    with pytest.raises(ValueError, match='runtime'):
        admit(ctx, {**ctx['plan'], 'accounting_runtime': 'week6-v1'})
    ctx['proof'].unlink()
    with pytest.raises(FileNotFoundError):
        admit(ctx)
    compatible = setup(tmp_path/'compatible-readers', monkeypatch, family='RW', key='RW1')
    for version in ('week6-v1', 'week6-v2'):
        attempt(compatible, version, accounting_runtime=version)
    p.require_new_family_transition(compatible['plan'], compatible['root'])
    attempt(compatible, 'unknown-reader', accounting_runtime='unreviewed-legacy')
    with pytest.raises(RuntimeError, match='terminal reconciliation'):
        p.require_new_family_transition(compatible['plan'], compatible['root'])
    def functions(path):
        return {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(path.read_text()).body
            if isinstance(node, ast.FunctionDef)}
    old, new = functions(Path(r1.__file__)), functions(Path(runtime.__file__))
    assert old['run'] == new['run'] and old['failure_charge'] == new['failure_charge']


def native_driver():
    """Only substitute fixture roots/clock; all native gates and handlers stay real."""
    import runpy
    mode = sys.argv[1]
    if mode == 'child':
        campaign, operation, root = sys.argv[2:]
        p1.ROOT = Path(campaign)
        sys.argv = ['week6_child_v1', operation, root]
        runpy.run_module('runners.drive.cards.week6_child_v1', run_name='__main__')
        return
    assert mode == 'supervisor'
    version, root_name, temp_name = sys.argv[2:]
    root, temp = Path(root_name), Path(temp_name)
    policy, runner = (p1, r1) if version == 'v1' else (p, runtime)
    campaign = temp/'campaign'
    for module in (limits, l1):
        module.PREDECESSOR = temp/'predecessor'
        module.DRAIN_REVIEW = temp/'DRAIN_REVIEW.json'
    p1.ROOT = p.ROOT = campaign
    policy.OLD_SLOTS, policy.NEW_SLOTS = temp/'slots-old', temp/'slots-new'
    policy.OLD_SLOTS.mkdir(exist_ok=True)
    policy.NEW_SLOTS.mkdir(exist_ok=True)
    paths, admission, available = policy.lease_paths, policy.admission, policy.available
    policy.lease_paths = lambda: paths(policy.OLD_SLOTS, policy.NEW_SLOTS)
    policy.available = lambda plan, root=campaign, exclude=None: available(plan, root, exclude)
    policy.admission = lambda plan: admission(plan, at=policy.OPEN+timedelta(minutes=1),
        budget_root=campaign, lock_path=temp/'shared.lock')
    measured = runner.measured_child
    def measured_in_fixture(root, operation, command):
        assert command[4:6] == ['-m', 'runners.drive.cards.week6_child_v1']
        return measured(root, operation, command[:4]+[str(Path(__file__).resolve()), 'child', str(campaign), operation, str(root)])
    runner.measured_child = measured_in_fixture
    stopped = threading.Event()
    errors = []
    def monitor():
        try:
            while not stopped.is_set():
                if (root/'OWNER.json').exists():
                    put(root/'MONITOR_READY.json', dict(owner_sha256=filehash(root/'OWNER.json')))
                    return
                time.sleep(.01)
        except Exception as exc:
            errors.append(exc)
    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()
    try:
        runner.run(root)
    finally:
        stopped.set()
        thread.join(timeout=2)
    assert not errors and not thread.is_alive()


if __name__ == '__main__':
    native_driver()
