"""Integer-cent, campaign/node/first-tranche guard with retained uncertainty.

DESIGN CHECK: LESSONS 3-5. NULL and ALTERNATIVE spend identically until a frozen
futility look. Missing approval, cap, account evidence or duplicate invocation
refuses. Known ended usage may reconcile; unknown usage never releases funds.
"""
import time
from datetime import datetime
from decimal import Decimal, ROUND_CEILING
from runners.stage14.common import REPO, read, filehash, atomic

CAMPAIGN='G3-S15-DRIVE-1'
APPROVAL=REPO/'.agent-state/drive-20261016/APPROVAL.json'
CAPS={'A0':100,'A':2000,'B':2000,'D':800,'F':2500,'Reserve':500}
CUTOFF=datetime.fromisoformat('2026-10-20T00:00:00+00:00').timestamp()


def guard(runs,node,ident,cents,approval,now_epoch=None):
    if approval.get('campaign')!=CAMPAIGN or approval.get('first_paid_cents')!=1000:
        raise ValueError('specific first-tranche approval required')
    if (time.time() if now_epoch is None else now_epoch)>=CUTOFF:raise ValueError('paid dispatch cutoff')
    if node not in CAPS or node=='Reserve' or type(cents)!=int or cents<1:raise ValueError('invalid node/reservation')
    ours=[r for r in runs if r.get('campaign_id')==CAMPAIGN]
    if any(r.get('invocation')==ident for r in ours):raise ValueError('duplicate invocation; retrieval only')
    if any(type(r.get('booked_cents'))!=int or r['booked_cents']<0 for r in ours):raise ValueError('invalid prior accounting')
    total=sum(r['booked_cents'] for r in ours)+cents
    if total>6000 or sum(r['booked_cents'] for r in ours if r['node']==node)+cents>CAPS[node]:raise ValueError('hard campaign/node cap')
    # This implementation admits only the first tranche. A future reviewed route
    # must bind a concrete final-approval record before it can increase this limit.
    if total>1000:raise ValueError('detailed final approval required past $10')


def modal_headroom(account,runs):
    keys=('usage_limit_cents','metered_at_check_cents','storage_allowance_cents','spend_limit_cents','billed_at_check_cents')
    if any(type(account.get(k))!=int or account[k]<0 for k in keys):raise ValueError('account evidence incomplete')
    if not isinstance(account.get('observed_at'),(int,float)):raise ValueError('missing account observation')
    pending=0
    for r in runs:
        provider=r.get('provider')
        is_modal=provider=='modal' or str(r.get('invocation','')).startswith('modal-') or (provider is None and r.get('gpu'))
        if not is_modal:continue
        # Even an old unresolved reservation can still become a new account charge.
        uncertain=r.get('status') not in ('RECONCILED','COMPLETE','COMPLETED')
        if uncertain or r.get('ts',0)>=account['observed_at']:
            booked=r.get('booked_cents')
            if type(booked)!=int or booked<0:raise ValueError('unmapped account-wide reservation')
            pending+=booked
    return min(account['usage_limit_cents']-account['metered_at_check_cents'],
        account['spend_limit_cents']-account['billed_at_check_cents'])-account['storage_allowance_cents']-pending


def reserve(ident,node,cents,plan_sha256,provider):
    from runners import gear3
    if provider!='anthropic':raise ValueError('Modal dispatch not implemented until account evidence and pilot are bound')
    approval=read(APPROVAL);gear3._lock_ledger()
    try:
        led=gear3.load_ledger();guard(led['runs'],node,ident,cents,approval)
        row=dict(campaign_id=CAMPAIGN,invocation=ident,node=node,provider=provider,
            reserved_cents=cents,booked_cents=cents,est_actual_dollars=cents/100,status='RESERVED',ts=time.time(),
            plan_sha256=plan_sha256,approval_sha256=filehash(APPROVAL))
        led['runs'].append(row);atomic(gear3.LEDGER,led);return row
    finally:gear3._unlock_ledger()


def reconcile(ident,cents,proof_sha256):
    from runners import gear3
    if type(cents)!=int or cents<0 or len(proof_sha256)!=64:raise ValueError('invalid complete billing evidence')
    gear3._lock_ledger()
    try:
        led=gear3.load_ledger();rows=[r for r in led['runs'] if r.get('campaign_id')==CAMPAIGN and r['invocation']==ident]
        if len(rows)!=1:raise ValueError('reservation identity missing')
        row=rows[0]
        if cents>row['reserved_cents']:raise ValueError('usage exceeded reserved ceiling')
        if row.get('proof_sha256') not in (None,proof_sha256):raise ValueError('reconciliation proof changed')
        row.update(status='RECONCILED',booked_cents=cents,est_actual_dollars=cents/100,proof_sha256=proof_sha256)
        atomic(gear3.LEDGER,led)
    finally:gear3._unlock_ledger()


def ceiling(rows,counts):
    total=Decimal(0)
    for row in rows:
        n=counts[row['custom_id']]
        if type(n)!=int or not 0<n<100000:raise ValueError('invalid counted input')
        total+=(Decimal('.05')*n*Decimal('1.3')+Decimal('.25')*row['params']['max_tokens'])/10000
    return int(total.to_integral_value(rounding=ROUND_CEILING))+2
