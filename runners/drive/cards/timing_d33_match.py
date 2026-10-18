"""Input-only exact-support matching for D33.pair/pair2; no scientific fit.

DESIGN CHECK: LESSONS3-5 read October18. Same saved primary rows, own cache,
calibration sessions and nuisance values remain fixed. Donor selection uses
only strictly earlier completed sessions, prompt identity and typed-token
counts. Exact unsupported history sizes return an explicit refusal; no target
row deletion, own-history shortening, future borrowing or outcome optimization.
Boundary-preserving donor prefix trimming alone matches the exact token budget.
"""
from __future__ import annotations

from collections import Counter,defaultdict
import math


def token_count(session):
    return sum(len(s) for s in session['training_sequences'])


def earlier(sessions,target,exclude_prompt=False):
    return sorted((s for s in sessions if s['end_at']<target['timestamp'] and
                   (not exclude_prompt or s['prompt']!=target['prompt'])),
                  key=lambda s:(s['timestamp'],s['session']))


def truncate_sequences(sequences,budget):
    if type(budget) is not int or budget<0 or budget>sum(map(len,sequences)):
        raise ValueError('invalid history token budget')
    out=[]
    for seq in sequences:
        take=min(budget,len(seq))
        if take:out.append(list(seq[:take]))
        budget-=take
    if budget:raise ValueError('history token budget not realized')
    return out


def allocated_budgets(capacities,budget):
    """Proportional largest-remainder allocation, preserving nonempty sessions
    when the target budget can support one token per nonempty donor session.
    Session order is frozen chronology; equal fractional parts break by order.
    """
    if type(budget) is not int or budget<0 or budget>sum(capacities) or any(type(c) is not int or c<0 for c in capacities):
        raise ValueError('invalid donor capacity')
    counts=[int(c>0) if budget>=sum(c>0 for c in capacities) else 0 for c in capacities]
    left=budget-sum(counts); remaining=[c-n for c,n in zip(capacities,counts)]
    if left and sum(remaining):
        quotas=[left*c/sum(remaining) for c in remaining]; base=[math.floor(q) for q in quotas]
        counts=[n+b for n,b in zip(counts,base)]
        for j in sorted(range(len(capacities)),key=lambda j:(-(quotas[j]-base[j]),j))[:left-sum(base)]:counts[j]+=1
    if sum(counts)!=budget or any(n>c for n,c in zip(counts,capacities)):
        raise ValueError('donor token allocation mismatch')
    return counts


def select_sessions(available,own):
    """Greedy prompt/length matching with an exact capacity feasibility guard.

    At every step remaining sessions must still be able to meet the complete
    target token budget. This guards against a close small match accidentally
    consuming capacity required later. It is not an outcome-fitted optimizer.
    """
    n,budget=len(own),sum(map(token_count,own))
    available=sorted(available,key=lambda s:(s['timestamp'],s['session']))
    if len(available)<n or sum(sorted(map(token_count,available),reverse=True)[:n])<budget:return None
    chosen=[];matches=0;distance=0
    for target in own:
        remaining=n-len(chosen)-1;used=sum(map(token_count,chosen));possible=[]
        for candidate in available:
            rest=[s for s in available if s['session']!=candidate['session']]
            if used+token_count(candidate)+sum(sorted(map(token_count,rest),reverse=True)[:remaining])<budget:continue
            possible.append(candidate)
        if not possible:raise ValueError('feasible capacity lost during greedy matching')
        selected=min(possible,key=lambda s:(s['prompt']!=target['prompt'],abs(token_count(s)-token_count(target)),s['timestamp'],s['session']))
        matches+=selected['prompt']==target['prompt'];distance+=abs(token_count(selected)-token_count(target))
        chosen.append(selected);available=[s for s in available if s['session']!=selected['session']]
    selected=sorted(chosen,key=lambda s:(s['timestamp'],s['session']))
    return dict(sessions=selected,prompt_matches=matches,length_distance=distance,
        capacity=sum(map(token_count,selected)),target_tokens=budget)


def matched_other(by_writer,target,exclude_prompt=False):
    own=earlier(by_writer[target['writer']],target,exclude_prompt)
    budget=sum(map(token_count,own));candidates=[];capacities={}
    for writer,sessions in sorted(by_writer.items()):
        if writer==target['writer']:continue
        pool=earlier(sessions,target,exclude_prompt)
        capacities[writer]=dict(sessions=len(pool),largest_matching_count_tokens=sum(sorted(map(token_count,pool),reverse=True)[:len(own)]))
        match=select_sessions(pool,own)
        if match is not None:candidates.append((writer,match))
    base=dict(target_session=target['session'],target_writer=target['writer'],before=target['timestamp'],
        exclude_target_prompt=exclude_prompt,own_sessions=[s['session'] for s in own],own_tokens=budget,
        required_session_count=len(own),candidate_capacities=capacities)
    if not candidates:
        return dict(base,supported=False,reason='no single other writer has exact prior-session-count/token capacity; target rows retained as unsupported'),None
    writer,best=min(candidates,key=lambda pair:(-pair[1]['prompt_matches'],pair[1]['capacity']-budget,pair[1]['length_distance'],pair[0]))
    selected=best['sessions'];allocations=allocated_budgets([token_count(s) for s in selected],budget)
    donor=[dict(s,training_sequences=truncate_sequences(s['training_sequences'],n)) for s,n in zip(selected,allocations)]
    proof=dict(base,supported=True,donor_writer=writer,donor_sessions=[s['session'] for s in donor],
        donor_tokens=sum(map(token_count,donor)),donor_tokens_before_trim=best['capacity'],
        prompt_matches=best['prompt_matches'],trim_allocations=allocations,
        empty_trimmed_sessions=sum(token_count(s)==0 for s in donor),
        matching='exact session count and token count; greedy prompt match then token-length distance; excess-only boundary-preserving prefix trim')
    if len(donor)!=len(own) or proof['donor_tokens']!=budget:raise ValueError('matched history support mismatch')
    return proof,donor


def primary_roster(saved_rows,records,saved_tuning):
    """Freeze the original evaluation/calibration identities before any variant.

    Caller authenticates all three retained source artifacts before this pure
    routine. Original nuisance/own-surprise values are copied by the consumer.
    """
    by_writer=defaultdict(list)
    for r in records:by_writer[r['writer']].append(r)
    lookup={s['session']:s for s in records}
    if len(lookup)!=len(records):raise ValueError('duplicate P6 session')
    writers=sorted({r['writer'] for r in saved_rows});keys=[(r['session'],r['index']) for r in saved_rows]
    if len(set(keys))!=len(keys):raise ValueError('duplicate original primary row')
    tuning={r['writer']:r for r in saved_tuning};out={}
    if len(tuning)!=len(saved_tuning):raise ValueError('duplicate original tuning writer')
    for w in writers:
        sessions=sorted(by_writer[w],key=lambda s:(s['timestamp'],s['session']));a,b=int(.6*len(sessions)),int(.8*len(sessions))
        if a<3 or b-a<1 or len(sessions)-b<1 or w not in tuning:raise ValueError('original chronological tuning support differs')
        ownrows=[r for r in saved_rows if r['writer']==w];tail={s['session'] for s in sessions[b:]}
        if any(r['session'] not in tail or lookup[r['session']]['writer']!=w or type(r['index']) is not int or not 0<=r['index']<len(lookup[r['session']]['words']) for r in ownrows):
            raise ValueError('original primary row identity differs')
        out[w]=dict(calibration_sessions=[s['session'] for s in sessions[a:b]],evaluation_sessions=[s['session'] for s in sessions[b:]],
            original_alpha=tuning[w]['alpha'],primary_rows=len(ownrows))
    return dict(writers=out,rows=len(saved_rows),keys=[list(k) for k in keys]),dict(by_writer)
