"""Launch reviewed Round 29 prospective allowance plans with authenticated monitoring and native ownership.

DESIGN CHECK: LESSONS 3-5. Changed reviewed design, source, fixture or owner
fails under both scientific directions. Existing attempts never restart here.
"""
from pathlib import Path
import argparse,json
from runners.stage14.common import read,freeze,filehash
from .week6_launch_services_v5 import launch_monitored
from runners.theory_days.launch import closure
from runners.drive.cards.batch_runtime import check_files
from runners.drive.cards import week6_br_pair_policy_v1 as policy

MODULES=['runners.drive.cards.week6_br_pair_launch_runtime_v1','runners.drive.cards.week6_br_pair_launch_v1','runners.drive.cards.week6_br_pair_policy_v1','runners.drive.cards.week6_child_v1']

def qualified_binding(record, pins):
    from .week6_lattice_policy_fixture_v1 import qualified_native
    binding = record.get('lattice_qualification')
    if not isinstance(binding, dict) or set(binding) != {'path', 'sha256'}:
        raise ValueError('Exact native Round 29 policy qualification required')
    path = Path(binding['path']).resolve()
    if pins.get(str(path)) != binding['sha256'] or filehash(path) != binding['sha256']:
        raise ValueError('Lattice policy fixture must be pinned')
    qualified_native(path)
    return str(path)


def review(plan):
    policy.runtime_contract(plan)
    check_files(plan['pins'])
    policy.review_plan_scope(plan)
    qualification = qualified_binding(plan, plan['pins'])
    if qualification not in plan.get('validation_receipts', []):
        raise ValueError('Lattice policy qualification absent from validation receipts')
    if not plan.get('owner_reviewed') or not plan.get('validation_receipts'):raise ValueError('Owner review and native fixtures required')
    for path in plan['validation_receipts']:
        if plan['pins'].get(path)!=filehash(path):raise ValueError('Unpinned native fixture')
    from .week6_local_review_v1 import review_design
    review_design(plan)
    for p in closure([plan['module'],*MODULES]):
        if plan['pins'].get(str(p))!=filehash(p):raise ValueError('Missing source closure pin: '+str(p))

def freeze_plan(root, plan):
    """The only supported new-family plan writer; preserve legacy live readers."""
    from runners.drive.cards import batch_runtime_v8 as kernel
    root=Path(root).resolve();root.relative_to(policy.ROOT)
    review(plan)
    with kernel.admission_lock(policy.OLD_SLOTS):
        policy.admission(plan)
        if root.exists():raise ValueError('New attempt root required')
        freeze(root/'PLAN.json',plan)
    return root


def freeze_budget(row, review_path, review_sha256):
    """New family preparation receipts also break legacy readers: guard first.

    This is an owner-only explicit write, never called on import or launch.
    No ledger revision or review is manufactured by the transition itself.
    """
    from datetime import datetime, timezone
    from runners.drive.cards import batch_runtime_v8 as kernel
    from runners.drive.cards import week6_limits_extension_v2 as limits
    from runners.drive.cards.week6_transition_services_v5 import require_transition
    policy.review_budget_scope(row)
    qualified_binding(row, row['evidence_pins'])
    with kernel.admission_lock(policy.OLD_SLOTS):
        at = datetime.now(timezone.utc)
        if not policy.OPEN <= at < policy.FREEZE:
            raise RuntimeError('Original no-new-start boundary')
        require_transition(review_path, review_sha256, policy.ROOT, at=at)
        if row['family'] not in policy.FAMILY_CEILINGS:
            raise ValueError('Unknown family')
        policy.compatible_active_readers(policy.ROOT)
        limits.validate_prospective_revision(policy.ROOT, row)
        destination = policy.ROOT/'_budgets'/f"{row['key']}-r{row['revision']:04d}.json"
        if destination.exists():
            raise ValueError('Existing immutable budget revision')
        freeze(destination, row)
    return destination

def launch(root):
    root=Path(root).resolve();root.relative_to(policy.ROOT)
    if (root/'ATTEMPT.claim').exists():raise ValueError('Existing attempt; inspect instead of relaunch')
    plan=read(root/'PLAN.json');review(plan);policy.admission(plan)
    return launch_monitored(root,'runners.drive.cards.week6_br_pair_launch_runtime_v1',plan['card'],['COMPLETE','FAILED','PAUSED','MONITOR_FAILED'],[plan['module'],*MODULES])

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path)
    print(json.dumps(launch(parser.parse_args().root)))
