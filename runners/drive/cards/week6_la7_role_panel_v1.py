"""Rates of laughter by ordered role with marginal role and timing adjustment.

Turn position is the first or second half of a target speaking interval. A laugh
in the post-utterance window belongs to the terminal half. Ongoing laughter is
an annotated vocal laugh by someone other than the potential laugher, already
in progress just before the onset. The numerator includes the two-second
post-utterance window; the denominator is exclusively the target's floor time.
"""
from bisect import bisect_left, bisect_right
from collections import Counter

import numpy as np

from .week6_la78_models_v1 import role_direction, role_model
from .week6_la78_support_v1 import group_by, meeting_support
from .week6_la78_targets_v1 import SpeakerFloor


def design(utterances, laughs, metadata):
    support, events=meeting_support(utterances,laughs,metadata)
    if not support["scenario_roles"]:
        return None
    roles={s:r["role"] for s,r in metadata["speakers"].items()}
    speakers=group_by(utterances,"speaker")
    floors={s:SpeakerFloor(speakers[s]) for s in roles}
    starts={s:[a for a,_ in f.merged] for s,f in floors.items()}
    vocal=[e for e in laughs if e["label"]=="vocal"]
    others={s:SpeakerFloor([e for e in vocal if e["speaker"]!=s]) for s in roles}
    other_intervals = {
        actor: [(row["start"], row["end"]) for row in vocal
                if row["speaker"] != actor and row["start"] < row["end"]]
        for actor in roles
    }
    other_starts = {actor: sorted(a for a, _ in intervals) for actor, intervals in other_intervals.items()}
    other_ends = {actor: sorted(b for _, b in intervals) for actor, intervals in other_intervals.items()}
    exposure=Counter()
    for target,floor in floors.items():
        for a,b in floor.merged:
            mid=(a+b)/2
            for actor in roles:
                if actor==target:
                    continue
                for late,(low,high) in enumerate(((a,mid),(mid,b))):
                    ongoing=others[actor].seconds(low,high)
                    pair=roles[actor],roles[target],late
                    exposure[(*pair,1)]+=ongoing/60
                    exposure[(*pair,0)]+=(high-low-ongoing)/60
    counts={name:Counter() for name in ("single","latest","fractional")}
    for actor,onset,candidates,last in events:
        ongoing = int(bisect_left(other_starts[actor], onset) > bisect_right(other_ends[actor], onset))
        rules=(("single",candidates if len(candidates)==1 else ()),("latest",last),("fractional",candidates))
        for rule,targets in rules:
            for target in targets:
                idx=bisect_right(starts[target],onset)-1
                a,b=floors[target].merged[idx]
                late=int(onset>=(a+b)/2)
                counts[rule][roles[actor],roles[target],late,ongoing]+=1/len(targets)
    return exposure, counts, sum(len(last) > 1 for _, _, _, last in events)


def table(meetings):
    exposure=Counter()
    counts={k:Counter() for k in ("single","latest","fractional")}
    for data in meetings:
        if data is None:
            continue
        exp,obs=data
        exposure.update(exp)
        for rule in counts:
            counts[rule].update(obs[rule])
    cells=sorted(set(exposure).union(*(set(v) for v in counts.values())))
    observed_pairs=sorted({(a,b) for a,b,_,_ in cells})
    positive=[cell for cell in cells if exposure[cell]>0]
    output={pair:{"target_floor_minutes":sum(exposure[c] for c in cells if c[:2]==pair)} for pair in observed_pairs}
    actor_roles=sorted({c[0] for c in positive});target_roles=sorted({c[1] for c in positive})
    if not positive:
        return []
    x=np.array([[1,*[a==v for v in actor_roles[1:]],*[b==v for v in target_roles[1:]],late,already]
                for a,b,late,already in positive],dtype=float)
    # Constant timing controls add nothing; other rank failures remain visible.
    keep=[0]+[i for i in range(1,x.shape[1]) if np.ptp(x[:,i])>0]
    times=np.array([exposure[c] for c in positive])
    for rule,values in counts.items():
        unsupported=sum(values[c] for c in cells if exposure[c]<=0)
        pred=None if unsupported else role_model(times,[values[c] for c in positive],x[:,keep])
        for pair,row in output.items():
            count=sum(values[c] for c in cells if c[:2]==pair)
            t=row["target_floor_minutes"]
            expected=None if pred is None else sum(float(v) for c,v in zip(positive,pred) if c[:2]==pair)
            row[rule]=dict(count=count,rate=count/t if t else None,expected=expected,
                           excess_rate=(count-expected)/t if expected is not None and t else None,
                           events_without_timing_exposure=unsupported)
    for pair,row in output.items():
        row["laugher_role"],row["target_role"]=pair
        row["BG_direction_check"]=role_direction(*(row[rule]["excess_rate"] for rule in counts))
    return list(output.values())
