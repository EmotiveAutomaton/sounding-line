"""Native Week 6 inclusive charges, with two ring-fenced BO writer allowances."""
from datetime import datetime, timezone
from pathlib import Path
import stat
from . import week6_limits_extension_v2 as limits
from .week6_policy_services_v5 import (FAMILY_CEILINGS as PRIOR_CEILINGS, CEILING, ROOT,
    finite, instant, present, read, retry_read)
FAMILY_CEILINGS=dict(PRIOR_CEILINGS,WLG=20000)

def charges(root=ROOT, exclude=None, card_key=None):
    """Count actual attempt CPU; unknown terminated attempts retain their full cap.

    Monitor progress is refreshed every two seconds. The additional two-second
    sampling envelope per active two-thread worker covers concurrent last ticks.
    """
    families={k:0.0 for k in FAMILY_CEILINGS};pending=[]
    for key,row in limits.budgets(root).items():
        if row['family'] not in families: raise ValueError('Unknown preparation family')
        if card_key is None or key==card_key: families[row['family']]+=row['preparation_cpu_seconds']
    # Explicit listing propagates directory access failure instead of silently
    # turning a failed glob into an empty campaign.
    directories=retry_read(lambda:list(Path(root).iterdir()),root)
    for directory in directories:
        if not stat.S_ISDIR(retry_read(directory.stat,directory).st_mode):continue
        path=directory/'PLAN.json'
        if not present(path):continue
        if exclude and path.parent.resolve()==Path(exclude).resolve(): continue
        plan=read(path)
        if plan.get('campaign')!='S15-WEEK6': continue
        if card_key is not None and plan['budget_key']!=card_key: continue
        family=plan['family']
        if family not in families: raise ValueError('Unknown campaign family')
        terminals=[path.parent/n for n in ('COMPLETE.json','FAILED.json','PAUSED.json') if present(path.parent/n)]
        if len(terminals)>1: raise ValueError('Ambiguous terminal accounting')
        claimed=present(path.parent/'ATTEMPT.claim')
        if terminals: charge=finite(read(terminals[0])['cpu_seconds'])
        elif not claimed: charge=0.0
        elif present(path.parent/'BUDGET_PROGRESS.json'):
            progress=read(path.parent/'BUDGET_PROGRESS.json')
            pending.append((family,finite(progress['cpu_seconds']),instant(progress['at']),finite(plan['max_cpu_seconds'])))
            charge=0.0 # Replaced by the complete pending contribution below.
        else: charge=finite(plan['max_cpu_seconds'])
        # Supervisor/launcher/replay coordination is charged conservatively.
        families[family]+=charge+(30 if claimed else 0)
    at=datetime.now(timezone.utc)
    for family,measured,stamp,cap in pending:
        age=(at-stamp).total_seconds()
        if age<0:raise ValueError('Accounting progress clock is in the future')
        # Reconcile elapsed retry/listing time at the end of the complete
        # snapshot; retain the two-second, two-thread sampling envelope.
        families[family]+=measured+2*(age+2) if age<15 else max(cap,measured)
    return families


def check_campaign_room(used):
    if max(0,20000-used['WLG'])>CEILING-sum(used.values()):
        raise RuntimeError('Campaign cannot cover both independent writing allowances')


def compatible_active_readers(root):
    """An older live numerical worker cannot account for the new family."""
    root=Path(root)
    for p in root.iterdir():
        if not p.is_dir() or not present(p/'ATTEMPT.claim') or any(present(p/t) for t in ('FAILED.json','COMPLETE.json','PAUSED.json')):
            continue
        plan=read(p/'PLAN.json')
        if plan.get('campaign')=='S15-WEEK6' and plan.get('accounting_addendum')!='BO':
            raise RuntimeError('Live pre-BO research owner must drain before introducing new family')
