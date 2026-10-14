"""One integer-cent campaign ledger behind runners/gear3.py.

DESIGN CHECK: LESSONS 3-5. NULL/ALTERNATIVE share the same caps. Duplicate,
unknown, missing approval, expired or oversized attempts refuse before dispatch.
Only measured ended ownership can release a reservation; uncertainty retains it.
"""
from contextlib import contextmanager
from decimal import Decimal,ROUND_CEILING
import time
from .data import ROOT
from runners.stage14.common import read,filehash,digest

CAMPAIGN='G3-S14-MAKER-1'
RATE=Decimal('.000542')+2*Decimal('.0000131')+32*Decimal('.00000222')
CAPS={'P':350,'M-27':1400,'M-API':2850,'Reserve':400}

def account_headroom(account,runs):
    """Gross and net limits are independent; never assume credits or instant billing."""
    fields=('usage_limit_cents','metered_at_check_cents','storage_allowance_cents','spend_limit_cents','billed_at_check_cents')
    if any(type(account.get(k))!=int or account[k]<0 for k in fields):raise ValueError('gross/net account bounds required')
    unreported=sum(r['booked_cents'] for r in runs if r.get('campaign_id')==CAMPAIGN and r['invocation'].startswith('modal-') and r['ts']>=account['observed_at'])
    gross=account['usage_limit_cents']-account['metered_at_check_cents']-account['storage_allowance_cents']-unreported
    net=account['spend_limit_cents']-account['billed_at_check_cents']-account['storage_allowance_cents']-unreported
    return min(gross,net)

def cost(seconds,overhead=30):
    if not 0<=seconds<=86400 or type(overhead)!=int or overhead<0:raise ValueError('invalid bounded allocation')
    return int((RATE*Decimal(str(seconds))*100).to_integral_value(rounding=ROUND_CEILING))+overhead

def guard(runs,node,ident,cents):
    if node not in CAPS or type(cents)!=int or cents<1:raise ValueError('invalid reservation')
    ours=[r for r in runs if r.get('campaign_id')==CAMPAIGN]
    if any(r['invocation']==ident for r in ours):raise ValueError('prior attempt; retrieval only')
    if any(type(r.get('booked_cents'))!=int or r['booked_cents']<0 for r in ours):raise ValueError('bad accounting')
    if sum(r['booked_cents'] for r in ours)+cents>5000 or sum(r['booked_cents'] for r in ours if r['node']==node)+cents>CAPS[node]:raise ValueError('campaign or node ceiling')
    if node=='Reserve':raise ValueError('reserve needs a separately reviewed recovery plan')

def reserve(ident,node,cents,plan_sha256,seconds):
    from runners import gear3
    approval=read(ROOT/'APPROVAL.json')
    if approval['hard_gross_ceiling_cents']!=5000 or approval['campaign']!=CAMPAIGN:raise ValueError('specific approval required')
    gear3._lock_ledger()
    try:
        ledger=gear3.load_ledger();guard(ledger['runs'],node,ident,cents)
        row=dict(campaign_id=CAMPAIGN,invocation=ident,node=node,reserved_cents=cents,booked_cents=cents,
                 est_actual_dollars=cents/100,status='RESERVED',ts=time.time(),expires=time.time()+seconds,
                 plan_sha256=plan_sha256,approval_sha256=filehash(ROOT/'APPROVAL.json'))
        ledger['runs'].append(row);gear3.save_ledger(ledger);return row
    finally:gear3._unlock_ledger()

def reconcile(ident,*,status,measured_seconds,owner_ended,proof_sha256):
    from runners import gear3
    if not owner_ended or not proof_sha256:raise ValueError('ended owner proof required')
    gear3._lock_ledger()
    try:
        ledger=gear3.load_ledger();row=next(r for r in ledger['runs'] if r.get('campaign_id')==CAMPAIGN and r['invocation']==ident)
        measured=cost(measured_seconds)
        if measured>row['reserved_cents']:raise ValueError('measured allocation exceeded reservation')
        row.update(status=status,booked_cents=measured,est_actual_dollars=measured/100,owner_ended=True,
                   measured_allocation_seconds=measured_seconds,proof_sha256=proof_sha256,accounting='conservative measured allocation plus overhead; invoice pending')
        gear3.save_ledger(ledger)
    finally:gear3._unlock_ledger()

def reconcile_tokens(ident,cents,proof_sha256):
    from runners import gear3
    if not ident.startswith('api-') or type(cents)!=int or cents<0 or not proof_sha256:raise ValueError('invalid ended token accounting')
    gear3._lock_ledger()
    try:
        ledger=gear3.load_ledger();row=next(r for r in ledger['runs'] if r.get('campaign_id')==CAMPAIGN and r['invocation']==ident)
        if cents>row['reserved_cents']:raise ValueError('token usage exceeded reservation')
        if row.get('proof_sha256') and row['proof_sha256']!=proof_sha256:raise ValueError('accounting proof changed')
        row.update(status='RECONCILED',booked_cents=cents,est_actual_dollars=cents/100,proof_sha256=proof_sha256,
                   accounting='ended provider batch; complete token accounting; rounded up to integer cents')
        gear3.save_ledger(ledger)
    finally:gear3._unlock_ledger()
