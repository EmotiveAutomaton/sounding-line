"""Separate Week 3 campaign; preserve the earlier campaign's pinned guard.

DESIGN CHECK: LESSONS 3-5. No outcome can raise a cap. Missing explicit node
approval, duplicate submission, expired authority or unresolved earlier-node
billing refuses. Unknown calls retain their ceiling. Actual settled billing
releases only the unused reservation, never silently grants another campaign.
"""
from datetime import datetime
import time
from .budget import ceiling
from runners.stage14.common import REPO, read, filehash, atomic

CAMPAIGN = 'G3-S15-WEEK3'
APPROVAL = REPO/'.agent-state/drive-20261025/APPROVAL.json'
PACKET = REPO/'docs/design/stage-15/week3/PACKET.md'
CAPS = dict(PROC=200, VAL=250, K=250, AUTH=100, GOAL=50, P=50)
CUTOFF = datetime.fromisoformat('2026-10-31T00:00:00+00:00').timestamp()
ORDER = ('PROC','VAL','AUTH','GOAL','K','P')


def guard(runs, node, ident, cents, approval, now_epoch=None):
    if approval.get('campaign') != CAMPAIGN or approval.get('first_paid_cents') != 1000:
        raise ValueError('Specific Week3 approval required')
    if node not in approval.get('nodes', []): raise ValueError('Node not approved')
    if not approval.get('statement_verbatim') or len(approval.get('packet_sha256','')) != 64:
        raise ValueError('Missing bound statement and packet')
    if (time.time() if now_epoch is None else now_epoch) >= CUTOFF: raise ValueError('Paid cutoff')
    if node not in CAPS or type(cents) is not int or cents < 1: raise ValueError('Invalid node or reservation')
    ours = [r for r in runs if r.get('campaign_id') == CAMPAIGN]
    if any(r.get('invocation') == ident for r in ours): raise ValueError('Duplicate invocation; retrieval only')
    if any(type(r.get('booked_cents')) is not int or r['booked_cents'] < 0 for r in ours): raise ValueError('Invalid accounting')
    if any(r['node'] != node and r.get('status') != 'RECONCILED' for r in ours):
        raise ValueError('Reconcile previous node before reserving the next')
    if sum(r['booked_cents'] for r in ours) + cents > 1000: raise ValueError('Hard $10 campaign cap')
    if sum(r['booked_cents'] for r in ours if r['node'] == node) + cents > CAPS[node]: raise ValueError('Node cap')


def reserve(ident, node, cents, plan_sha256, provider='anthropic'):
    from runners import gear3
    if provider != 'anthropic': raise ValueError('Only commissioned Anthropic batches')
    approval = read(APPROVAL)
    if approval['packet_sha256'] != filehash(PACKET): raise ValueError('Approved packet changed')
    gear3._lock_ledger()
    try:
        ledger = gear3.load_ledger()
        guard(ledger['runs'], node, ident, cents, approval)
        row = dict(campaign_id=CAMPAIGN, invocation=ident, node=node, provider=provider,
            reserved_cents=cents, booked_cents=cents, est_actual_dollars=cents/100,
            status='RESERVED', ts=time.time(), plan_sha256=plan_sha256,
            approval_sha256=filehash(APPROVAL))
        ledger['runs'].append(row)
        atomic(gear3.LEDGER, ledger)
        return row
    finally:
        gear3._unlock_ledger()


def reconcile_row(row, cents, proof_sha256):
    if type(cents) is not int or cents < 0 or len(proof_sha256) != 64:
        raise ValueError('Complete billing proof required')
    if cents > row['reserved_cents']: raise ValueError('Usage exceeds reservation')
    if row.get('proof_sha256') not in (None, proof_sha256): raise ValueError('Proof changed')
    return dict(row, status='RECONCILED', booked_cents=cents,
                est_actual_dollars=cents/100, proof_sha256=proof_sha256)


def reconcile(ident, cents, proof_sha256):
    from runners import gear3
    gear3._lock_ledger()
    try:
        ledger = gear3.load_ledger()
        found = [i for i,r in enumerate(ledger['runs']) if r.get('campaign_id') == CAMPAIGN and r['invocation'] == ident]
        if len(found) != 1: raise ValueError('Exact reservation absent')
        i = found[0]
        ledger['runs'][i] = reconcile_row(ledger['runs'][i], cents, proof_sha256)
        atomic(gear3.LEDGER, ledger)
    finally:
        gear3._unlock_ledger()
