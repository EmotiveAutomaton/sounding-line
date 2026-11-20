"""Round 29 prospective CPU budgets on the existing Week 6 ledger.

DESIGN CHECK: LESSONS 3?5. The source, model, native ownership and measured
charges survive a bounded continuation under either scientific outcome.
"""
from datetime import datetime, timezone
from pathlib import Path
import os
from .batch_runtime import REPO, filehash, resource_snapshot
from . import week6_limits_extension_v2 as limits
from .week6_policy_services_v5 import (
    AccountingReadError, CEILING, DRAIN, FAMILY_CEILINGS, FREEZE, NEW_SLOTS,
    OLD_SLOTS, OPEN, ROOT, SHARED_LOCK, charges, finite, lease_paths,
    memory_reserve, post_claim, read, require_new_family_transition,
    runtime_contract, sealed_fixture_contract, shared_reservation, yield_reason,
)

# Each supplemental allowance belongs only to newly reviewed Round 29 plans.
# Other readers continue to read the original immutable family/card budgets.
VERSION = 'week6-lattice-v1'
FAMILY_ADDITIONS = {'ES': 400000, 'LA': 60000, 'KP': 70000}
DIARY = frozenset({'LD1', 'LD2', 'LD3', 'LD4', 'LB1', 'LB2', 'LB3', 'LB4', 'LB5', 'LB6'})
LAUGHTER = frozenset({'LA6', 'LA7', 'LA8'})
KP_MODULE = 'runners.drive.cards.week6_kp_riders_capsule_clock_units_v1'
AUTHORITY_PINS = {
    str((REPO / 'docs/design/stage-15/week6/PACKET_EXTENSION_2026-11-19.md').resolve()): 'f1c26b047db1384d152c718594d64482169daa8424f98c5572625b92f780bbbb',
    str((REPO / 'docs/design/stage-15/week6/LATTICE_IMPLEMENTATION_20261119.md').resolve()): 'fd6c226c5ec4c105e52f6a31996a6568141b347d75e1d8b88e117666d60a5932',
    str((REPO / 'docs/design/stage-15/week6/LATTICE_CALIBRATION_20261119.md').resolve()): '15f96bc6cccfdcd06cb254f09123d5051c91b44fa71997cbac257c142974c568',
}


def card_identity(card):
    if card in DIARY:
        return 'ES', 'ES-' + card, 10000 if card == 'LD4' else 20000
    if card in LAUGHTER:
        return 'LA', card, None
    if card == 'KP1':
        return 'KP', 'KP1', 90000
    raise ValueError('Uncommissioned Round 29 budget identity')


def review_budget_scope(row):
    key = row['key']
    if key == 'KP1' or key in LAUGHTER:
        card = key
    else:
        card = key.partition('-')[2]
    family, expected_key, cap = card_identity(card)
    if key != expected_key or row['family'] != family:
        raise ValueError('Round 29 family and accounting identity disagree')
    if family == 'ES' and (row['ceiling_cpu_seconds'] != cap or 'extension' in row):
        raise ValueError('Diary allowance includes preparation and complete replay')
    for path, digest in AUTHORITY_PINS.items():
        if row['evidence_pins'].get(path) != digest or filehash(path) != digest:
            raise ValueError('Round 29 allowance authority differs')


def review_plan_scope(plan):
    if plan.get('lattice_policy_version') != VERSION:
        raise ValueError('Missing prospective Round 29 plan binding')
    card = plan['lattice_card']
    family, key, cap = card_identity(card)
    if key != plan['budget_key'] or family != plan['family']:
        raise ValueError('Round 29 scope does not match charged budget')
    if card == 'KP1' and (plan['module'] != KP_MODULE or plan['config'].get('card') != 'KP1'
            or plan['inputs'].get('data_access') != 'original-D33-only'):
        raise ValueError('Supplemental KP allowance belongs only to the original-source KP1 study')
    for path, digest in AUTHORITY_PINS.items():
        if plan['pins'].get(path) != digest or filehash(path) != digest:
            raise ValueError('Unpinned or changed Round 29 authority')
    return family, cap


def bounds(family, card_cap, budget):
    if family == 'KP':
        if budget['ceiling_cpu_seconds'] != 20000 or budget['key'] != 'KP1':
            raise ValueError('Original KP1 budget identity differs')
        return card_cap
    effective = budget['effective_ceiling_cpu_seconds']
    if family == 'ES':
        if budget['ceiling_cpu_seconds'] != card_cap or budget['allowance_mode'] != 'original':
            raise ValueError('Diary card or replay allowance differs')
        return card_cap
    return effective


def room_from_charges(family, card_ceiling, prior, spent, all_charges):
    room = min(FAMILY_CEILINGS[family] + FAMILY_ADDITIONS[family] - all_charges[family],
               CEILING - sum(all_charges.values()))
    if card_ceiling is not None:
        room = min(room, card_ceiling - prior - spent)
    return max(0.0, room)


def available(plan, root=ROOT, exclude=None):
    family, cap = review_plan_scope(plan)
    budget = limits.plan_budget(plan, root)
    spent = sum(charges(root, exclude, card_key=plan['budget_key']).values())
    return room_from_charges(family, bounds(family, cap, budget),
                             budget['prior_campaign_cpu_seconds'], spent,
                             charges(root, exclude))


def admission(plan, at=None, resources=None, lock_path=SHARED_LOCK,
              budget_root=ROOT, occupied=None, logical=None):
    runtime_contract(plan)
    scope_family, scope_cap = review_plan_scope(plan)
    require_new_family_transition(plan, budget_root)
    sealed_fixture_contract(plan)
    if plan.get('operating_gear') != 2: raise ValueError('Explicit CPU-only Gear 2 required')
    at=at or datetime.now(timezone.utc)
    if at.tzinfo is None or not OPEN<=at<FREEZE: raise RuntimeError('Week 6 no-new-start boundary')
    limits.require_predecessor_drain(plan,at,lease_paths())
    if plan.get('campaign')!='S15-WEEK6' or plan.get('family') not in FAMILY_CEILINGS:
        raise ValueError('Explicit Week 6 campaign and family required')
    if plan.get('paid') or plan.get('gpu') or plan.get('ollama'):
        raise ValueError('Week 6 is CPU-only without paid or Ollama calls')
    if plan.get('numerical_threads') not in (1,2): raise ValueError('At most two numerical threads')
    if (os.cpu_count() if logical is None else logical)<24: raise RuntimeError('Eight-slot allocation requires the declared host capacity')
    for key in ('case_and_check','smaller_route'):
        if not plan.get('premortem',{}).get(key): raise ValueError('Two-line pre-mortem required')
    for key in ('max_cpu_seconds','max_wall_seconds','projected_peak_ram_GiB'):
        finite(plan[key],True)
    if plan.get('forecast_cpu_seconds',0)>7200 and plan.get('pilot_fraction')!=0.05:
        raise ValueError('Checkpointed first-five-percent in-slot pilot required')
    from .week6_local_review_v1 import review_design
    review_design(plan)
    snapshot=resource_snapshot() if resources is None else dict(resources)
    if any(snapshot[k]<v for k,v in [('ram_available_GiB',6),('commit_headroom_GiB',8),('disk_free_GiB',20)]):
        raise RuntimeError('CPU resource floor')
    paths=lease_paths() if occupied is None else occupied
    shared=shared_reservation(lock_path,at)
    if len(paths)>=8-int(shared['active']): raise RuntimeError('Counted CPU slots occupied')
    needed=finite(plan['projected_peak_ram_GiB'],True)+memory_reserve(paths)+6.0 # reserve one reviewed companion handoff peak
    if needed>min(snapshot['ram_available_GiB'],snapshot['commit_headroom_GiB'])-8: raise RuntimeError('Projected concurrent peak leaves less than eight GiB')
    room=available(plan,budget_root,exclude=plan.get('attempt_root'))
    if room<=30: raise RuntimeError('Family or campaign CPU allowance exhausted')
    budget=limits.plan_budget(plan,budget_root)
    current=sum(charges(budget_root,exclude=plan.get('attempt_root'),card_key=plan['budget_key']).values())
    return dict(at=at.isoformat(),campaign='S15-WEEK6',resources=snapshot,slots=8-int(shared['active']),
                allowance_mode=budget['allowance_mode'],budget_receipt=budget['bound_receipt'],
                budget_receipt_sha256=budget['bound_receipt_sha256'],budget_revision=budget['bound_revision'],
                original_ceiling_cpu_seconds=budget['ceiling_cpu_seconds'],
                effective_ceiling_cpu_seconds=bounds(scope_family, scope_cap, budget),
                lattice_policy_version=VERSION,lattice_card=plan['lattice_card'],
                family_ceiling_cpu_seconds=FAMILY_CEILINGS[scope_family]+FAMILY_ADDITIONS[scope_family],
                campaign_ceiling_cpu_seconds=CEILING,
                prior_campaign_cpu_seconds=budget['prior_campaign_cpu_seconds'],
                current_campaign_card_cpu_seconds=current,
                cumulative_card_cpu_seconds=budget['prior_campaign_cpu_seconds']+current,
                cumulative_preparation_cpu_seconds=budget['preparation_cpu_seconds'],
                idle_slots_before_claim=8-int(shared['active'])-len(paths),
                shared_reservation=shared,projected_peak_ram_GiB=plan['projected_peak_ram_GiB'],
                remaining_cpu_seconds=room-30,drain_utc=DRAIN.isoformat(),no_new_start_utc=FREEZE.isoformat())
