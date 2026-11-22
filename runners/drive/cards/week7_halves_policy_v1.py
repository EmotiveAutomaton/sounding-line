"""November 21 diary CPU budgets on the existing Week 6 ledger.

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
    memory_reserve, post_claim, read,
    runtime_contract, sealed_fixture_contract, shared_reservation, yield_reason,
)

# The three November 21 studies share the existing diary family room.
from .week6_lattice_policy_v2 import FAMILY_ADDITIONS as ORIGINAL_ADDITIONS, bounds
from .week6_bo_accounting_v1 import FAMILY_CEILINGS,charges,compatible_active_readers
FAMILY_ADDITIONS=dict(ORIGINAL_ADDITIONS,WLG=0)
VERSION='phase0-halves-20261122'
CARDS={'PSD3': ('0057', '0056')}
MODULE='runners.drive.cards.week7_halves_v1'
MANIFEST='cc63f8f6ffb5a47845b98b0d754b6412c18b0e6c79ea5badd8466d5589075f6d'
AUTHORITY_PINS={str(REPO/'docs/design/stage-15/week7/PACKET.md'):'38dd14ee77c4b087aa67caaf853ea9945f5864f3419f2f39b9e6479a01c24efb',str(REPO/'docs/design/stage-15/week7/PSD3_HALVES.md'):'ae2896a9b3ffa0e87aef3ceca8a24832042dfe610f3ba95894f3b7bec605e086'}

def card_identity(key):
    card, member=key.split('-')
    if member not in CARDS.get(card,()): raise ValueError('Unbound CK row/source')
    return 'ES','ES-'+key,20000


def authority(pins):
    for p, sha in AUTHORITY_PINS.items():
        if pins.get(p)!=sha or filehash(p)!=sha: raise ValueError('Changed November 21 authority')


def review_budget_scope(row):
    family,key,cap=card_identity(row['key'].removeprefix('ES-'))
    if (row['family'],row['key'],row['ceiling_cpu_seconds'])!=(family,key,cap) or 'extension' in row:
        raise ValueError('Wrong November 21 budget')
    authority(row['evidence_pins'])


def review_plan_scope(plan):
    card=plan['lattice_card']
    cfg=plan['config']
    family,key,cap=card_identity(card+'-'+cfg['member'])
    if (plan.get('lattice_policy_version')!=VERSION or plan['module']!=MODULE
        or plan['budget_key']!=key or plan['family']!=family or cfg['card']!=card
        or cfg['member'] not in CARDS[card] or not 1<=cfg['max_new_draws']<=2000
        or not 0<cfg['max_wall_seconds']<=21600 or plan['inputs']['manifest_sha256']!=MANIFEST):
        raise ValueError('November 21 plan scope differs')
    pointer=read(REPO/'.agent-state/data_collection_root.json')
    if (not pointer.get('repair_hold') or pointer['manifest_sha256']!=MANIFEST
        or plan['inputs']['data_root']!=pointer['root'] or pointer['logical_root']!='DRT1-20261121'):
        raise ValueError('November 21 source did not bind the temporary root')
    authority(plan['pins'])
    return family,cap


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


def require_new_family_transition(plan, root=ROOT):
    """Old policy readers reject unknown families, even unclaimed plans.

    Call BEFORE writing a new-family PLAN and again under the admission mutex.
    Never treat a missing receipt, inaccessible identity, or unexplained dead
    legacy attempt as permission to proceed. All old code remains immutable.
    """
    runtime_contract(plan)
    from .week6_transition_services_v5 import require_transition
    path = str(Path(plan['migration_review']).resolve())
    digest = plan['migration_review_sha256']
    if plan['pins'].get(path) != digest:
        raise ValueError('Exact R18 migration review must be pinned')
    review = require_transition(path, digest, root)
    # Legacy readers prevent posting new-family fixture receipts early. Once
    # migrated, every already-incurred pending charge must enter the ledger
    # before any extension-runtime study can start.
    latest = limits.budgets(root)
    for key, pending in review['pending_preparation'].items():
        row = latest[key]
        if row['family'] != pending['family'] or row['preparation_cpu_seconds'] < finite(pending['minimum_cpu_seconds']):
            raise ValueError('Pending preparation charges not fully posted')
        if any(row['evidence_pins'].get(p) != h for p,h in pending['evidence_pins'].items()):
            raise ValueError('Pending preparation evidence omitted')
    return review


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
