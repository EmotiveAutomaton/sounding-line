"""Prospective watcher transition. All historical sources and scientific contracts remain pinned."""
from datetime import datetime, timezone
from pathlib import Path
from .week6_transition_services_v4 import (REPO, EPOCH, REQUIRED_SOURCES as HISTORICAL_SOURCES,
    need, check_files, directories, has, read, regular, filehash, calendar_compatibility,
    legacy_inventory, native_records, classify_process)

REQUIRED_SOURCES = HISTORICAL_SOURCES + tuple(REPO / 'runners/drive/cards' / name for name in (
    'week6_process_services_v2.py', 'week6_transition_services_v5.py', 'week6_lattice_policy_v2.py',
    'week6_lattice_launch_v2.py', 'week6_lattice_launch_runtime_v2.py'))

def check_process_census(compatible, root, *, services, images, companions):
    from . import week6_process_services_v2 as service
    from . import week6_companion_proof_v3 as companion
    proofs=[companion.reader_compatibility(row) for row in companions]
    allowed = list(compatible)+[native for group in proofs for native in group]
    for row in services:
        value=service.watcher_compatibility(row)
        if value is not None:allowed.append(value)
    for directory in directories(root):
        if not has(directory/'PLAN.json'):continue
        plan=read(directory/'PLAN.json')
        if plan.get('campaign')!='S15-WEEK6' or plan.get('accounting_runtime')!=EPOCH:continue
        metadata=('OWNER.json','EXECUTE_NATIVE.json','VERIFY_NATIVE.json','EXECUTE_CHILD.json','VERIFY_CHILD.json')
        if any(has(directory/name) for name in metadata):
            need(has(directory/'OWNER.json'),'Extension native proof lacks owner binding')
        if has(directory/'OWNER.json'):
            need(read(directory/'OWNER.json').get('plan_sha256')==filehash(directory/'PLAN.json'),
                 'Extension owner/plan binding differs')
        for name in metadata:
            if has(directory/name):allowed.extend(native_records(read(directory/name)))
    # There is deliberately no command-only pre-OWNER exemption. This runtime
    # publishes OWNER before claim; another unowned reader causes a safe refusal.
    service.check_census(allowed, classify_process, images)
    for row in services:service.watcher_compatibility(row)
    need(proofs==[companion.reader_compatibility(row) for row in companions],
         "Companion ownership changed during census")

def require_transition(review_path, review_sha256, root, *, at=None):
    path = regular(Path(review_path).resolve())
    need(filehash(path) == review_sha256, 'Migration review changed')
    review = read(path); root = Path(root).resolve()
    need(review.get('schema') == 'WEEK6_R18_WATCHER_TRANSITION_V4' and review.get('epoch') == EPOCH,
         'Wrong authenticated migration')
    need(review.get('owner_reviewed') is True and review.get('full_write_through') is True,
         'Owner review and full legacy filing required')
    need(Path(review['campaign_root']).resolve() == root, 'Different migration campaign')
    at = at or datetime.now(timezone.utc); stamp = datetime.fromisoformat(review['at'])
    need(at.tzinfo is not None and stamp.tzinfo is not None and stamp <= at, 'Invalid migration clock')
    need(review.get('legacy_launchers_retired_from_owner_workflow') is True,
         'Legacy launchers and budget writers have not been retired')
    need(review.get('source_pins'), 'Migration source closure missing')
    need(isinstance(review.get('pending_preparation'), dict), 'Explicit pending preparation inventory required')
    for pending in review['pending_preparation'].values():
        need(pending.get('evidence_pins'), 'Pending preparation cost evidence missing')
        check_files(pending['evidence_pins'])
    need(all(review['source_pins'].get(str(p.resolve())) == filehash(p) for p in REQUIRED_SOURCES),
         'Migration omitted or changed required reader/runtime/authority pins')
    check_files(review['source_pins'])
    need(len(review['compatible_services']) == 1, 'Exactly one reviewed durable watcher required')
    previous = read(regular(review['predecessor_review']))
    need(filehash(regular(review['predecessor_review'])) == review['predecessor_sha256'], 'Earlier review changed')
    for field in ('compatible_calendars', 'compatible_companions', 'python_forwarder_images','campaign_root',
                  'baseline_budget_pins','legacy_inventory','filing_receipts','pending_preparation'):
        need(review[field] == previous[field], 'Migration scope differs: ' + field)
    need(all(review['source_pins'].get(p) == h for p,h in previous['source_pins'].items()),
         'Historical source proofs changed')
    actual = legacy_inventory(root)
    need(review['legacy_inventory'] == actual, 'Legacy reader inventory changed or incomplete')
    for name, item in actual.items():
        if not (item['claimed'] or item['owned']):
            continue
        receipt = review['filing_receipts'][name]; receipt_path = regular(receipt['path'])
        need(filehash(receipt_path) == receipt['sha256'], 'Legacy filing receipt changed')
        filed = read(receipt_path)
        need(filed.get('full_write_through') is True and filed.get('accounting_reconciled') is True,
             'Legacy failed/native costs are not fully reconciled')
        need(Path(filed['attempt_root']).resolve() == root/name and filed['terminal_pins'] == item['pins'],
             'Legacy filing does not bind exact terminal/native evidence')
    for name, pin in review['baseline_budget_pins'].items():
        candidate = regular(root/'_budgets'/name)
        need(filehash(candidate) == pin, 'Original immutable budget ancestry changed')
    calendars = [calendar_compatibility(row) for row in review['compatible_calendars']]
    check_process_census(calendars, root, services=review['compatible_services'],
                         images=review['python_forwarder_images'], companions=review['compatible_companions'])
    return review
