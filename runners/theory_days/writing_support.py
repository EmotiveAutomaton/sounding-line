"""TD7 pre-fit case check on authenticated canonical menus and actual hovers.

DESIGN CHECK: LESSONS 2-5. Ignored menus never become choices; next-three windows
cannot cross sessions or share a menu. Unsupported cases are not negative effects.
"""
from collections import defaultdict,Counter
from pathlib import Path
import numpy as np
from runners.stage14.common import read,freeze,filehash
from runners.drive.cards.timing_p6 import gzread
from runners.drive.cards.timing_pmap_source import completed


def support(sessions,navigation,seed=20261106):
    nav={x['key']:x for x in navigation}
    menus=[m for s in sessions for m in s['menus']]
    if len(nav)!=len(navigation) or len({m['key'] for m in menus})!=len(menus) or set(nav)!={m['key'] for m in menus}:
        raise ValueError('Canonical menu/navigation coverage mismatch')
    times=defaultdict(list)
    for m in menus:
        r=nav[m['key']]
        if r['writer']!=m['writer'] or r['session']!=m['session'] or r['canonical_choice']!=m['choice']:
            raise ValueError('Canonical join mismatch')
        if m['resolved_at'] is not None:
            duration=m['resolved_at']-m['open_at']
            if not np.isfinite(duration) or duration<0:raise ValueError('Invalid menu duration')
            times[m['writer']].append(duration)
    cuts={w:np.quantile(t,[1/3,2/3]) for w,t in times.items()}
    candidates=[];counts=Counter();claimed=set()
    for session in sorted(sessions,key=lambda s:(s['timestamp'],s['session'])):
        ordered=sorted(session['menus'],key=lambda m:(m['open_at'],m['ordinal']))
        duration=session['end_at']-session['timestamp']
        if duration<=0:raise ValueError('Invalid session duration')
        for i,m in enumerate(ordered):
            if m['resolved_at'] is None or m['handling']=='ignore':continue
            tercile=int(np.searchsorted(cuts[m['writer']],m['resolved_at']-m['open_at'],side='right'))
            hovered=bool(nav[m['key']]['navigation']['hover_ordinals'])
            upper=tercile==2
            examined=upper or hovered
            counts['hover_and_upper' if hovered and upper else 'hover_only' if hovered else 'upper_only' if upper else 'neither']+=1
            if not examined:
                if m['handling']=='dismiss':counts['fast_dismissals']+=1
                continue
            if m['handling'] not in ('dismiss','accept','edit'):raise ValueError('Unknown handling')
            future=[x for x in ordered[i+1:] if x['choice'] is not None][:3]
            if len(future)!=3:counts['fewer_than_three_future_choices']+=1;continue
            if any(x['key'] in claimed for x in future):counts['overlap_with_earlier_event']+=1;continue
            claimed.update(x['key'] for x in future)
            decile=min(9,max(0,int(10*(m['open_at']-session['timestamp'])/duration)))
            candidates.append(dict(writer=m['writer'],session=m['session'],key=m['key'],
                arm='dismiss' if m['handling']=='dismiss' else 'accept',tercile=tercile,
                decile=decile,open_time_clause=upper,hover_clause=hovered,
                future=[x['key'] for x in future],open_at=m['open_at']))
    strata=defaultdict(lambda:defaultdict(list))
    for c in candidates:strata[(c['writer'],c['tercile'],c['decile'])][c['arm']].append(c)
    rng=np.random.default_rng(seed);matches=[];writer_counts=Counter()
    for key,arms in sorted(strata.items()):
        a=sorted(arms['dismiss'],key=lambda c:c['key']);b=sorted(arms['accept'],key=lambda c:c['key'])
        rng.shuffle(a);rng.shuffle(b)
        for left,right in zip(a,b):matches.append(dict(dismiss=left,accept=right));writer_counts[key[0]]+=1
    supported=sorted(w for w,n in writer_counts.items() if n>=10)
    summary=dict(opened_menus=len(menus),sessions=len(sessions),writers=len(times),
        qualifying_candidate_events=len(candidates),matched_pairs=len(matches),
        writers_with_ten_pairs=len(supported),required_writers=20,clauses=dict(sorted(counts.items())),
        support_pass=len(supported)>=20,scientific_effect_computed=False,
        status='source case supported; feature and model admission pending' if len(supported)>=20 else 'design cannot test',
        interpretation='Necessary source-case check before complete feature availability; no effect estimated')
    return summary,matches,supported


def calculate(inputs):
    menus=Path(inputs['menus_completion']);hover=Path(inputs['hover_completion'])
    mp=menus.parent/'output/MENUS.json.gz';hp=hover.parent/'output/PRIVATE_ROWS.json.gz'
    completed(menus,mp);completed(hover,hp)
    return support(gzread(mp),gzread(hp))


def execute(output,inputs,config):
    summary,matches,writers=calculate(inputs)
    freeze(Path(output)/'SUMMARY.json',summary)
    freeze(Path(output)/'PRIVATE_WINDOWS.json',dict(matches=matches,supported_writers=writers))
    return dict(status='complete',scientific_effect_computed=False)


def verify(output,inputs,config):
    summary,matches,writers=calculate(inputs)
    assert read(Path(output)/'SUMMARY.json')==summary
    assert read(Path(output)/'PRIVATE_WINDOWS.json')==dict(matches=matches,supported_writers=writers)
    return dict(verified=True,complete_support_replay=True,scientific_effect_computed=False)
