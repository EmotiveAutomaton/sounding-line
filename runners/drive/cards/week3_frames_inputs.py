"""FR1 maximal dismissal runs, complete typed windows and leakage-free profiles.

DESIGN CHECK: NP1's maximal run convention is retained: ignore/accept/edit break
a run; one maximal run of at least three dismissals is one event. A complete
window has exactly50 typed words. Calibration sessions and both paired arms are
excluded before building profiles. Thin support is unsupported, never null.
"""
from collections import Counter,defaultdict
import bisect
import hashlib
import math

import numpy as np

from . import week3_frames_io as io
from . import week3_outcome_blocks_inputs as wc2

CONFIG=dict(card='FR1-inputs',mode='full',expected_sessions=1399,session_limit=1399,seed=20261026)
PILOT=dict(CONFIG,mode='pilot',session_limit=140)


def typed_window(tokens,words,ordinal):
    start=bisect.bisect_right([w['ordinal'] for w in words],ordinal)
    selected=words[start:start+50]
    if len(selected)!=50:return None
    low,high=selected[0]['index'],selected[-1]['index']
    kept=[r for r in tokens if low<=r['index']<=high and r['ordinal']>ordinal]
    return dict(text=' '.join(r['token'] for r in kept),tokens=[r['token'] for r in kept],
                token_indices=[r['index'] for r in kept],word_indices=[r['index'] for r in selected],
                position=start/max(1,len(words)),first_ordinal=selected[0]['ordinal'],words=50,
                pause_seconds=selected[0].get('pause_seconds'))


def dismissal_runs(rows):
    runs=[];current=[]
    for row in rows:
        if row['handling']=='dismiss':current.append(row)
        else:
            if current:runs.append(current)
            current=[]
    if current:runs.append(current)
    return runs


def prepare_session(meta,events,timeline,canonical,p6):
    # The original, independent accepted-atom replay also certifies final text.
    spans=wc2.spans(events,timeline,canonical)
    menu=io.menus(events,timeline,canonical);words=wc2.word_stream(p6['words']);tokens=sorted(p6['words'],key=lambda r:r['index'])
    clock=[float(e['eventTimestamp']) for e in events]
    duration=clock[-1]-clock[0]
    if duration<0 or not all(map(math.isfinite,clock)) or clock!=sorted(clock):raise ValueError('invalid FR1 clock')
    rows=[]
    for run in dismissal_runs(menu):
        n=len(run)
        if n==2:continue
        anchor=run[-1]['resolution'];window=typed_window(tokens,words,anchor)
        rows.append(dict(id=f'{meta["session"]}:dismiss:{run[-1]["origin"]}',kind='frustration' if n>=3 else 'single',
                         run_length=n,ordinal=anchor,seconds=(clock[anchor]-clock[0])/1000,
                         time_fraction=(clock[anchor]-clock[0])/duration if duration else 0,
                         position=bisect.bisect_right([w['ordinal'] for w in words],anchor)/max(1,len(words)),window=window,
                         offers=[text for m in run for text in m['offers']],censored=any(m['censored'] for m in run)))
    for span in spans:
        if span['canonical'] and span['failure_ordinal'] is not None and span['text'].strip():
            ordinal=span['failure_ordinal']
            rows.append(dict(id=f'{meta["session"]}:deleted:{span["origin"]}',kind='deleted',ordinal=ordinal,
                             seconds=(clock[ordinal]-clock[0])/1000,time_fraction=(clock[ordinal]-clock[0])/duration if duration else 0,
                             position=bisect.bisect_right([w['ordinal'] for w in words],ordinal)/max(1,len(words)),window=typed_window(tokens,words,ordinal),
                             offers=[span['text']],censored=False))
    identity={k:meta[k] for k in ('session','writer','prompt','timestamp')}
    return dict(**identity,tokens=[{k:r[k] for k in ('index','token','is_word','ordinal')} for r in tokens],
                events=[dict(identity,**r) for r in rows],typed_words=len(words))


def match_control(event,singles):
    choices=[r for r in singles if r['writer']==event['writer'] and r['prompt']==event['prompt'] and r['window'] is not None and not r['censored']]
    if not choices:return None
    return min(choices,key=lambda r:(r['session']!=event['session'],abs(r['time_fraction']-event['time_fraction'])+abs(r['position']-event['position']),r['session'],r['ordinal']))


def assemble(sessions):
    events=[r for s in sessions for r in s['events']];singles=[r for r in events if r['kind']=='single'];pairs=[]
    for event in events:
        if event['kind'] in {'frustration','deleted'} and event['window'] is not None and not event['censored']:
            control=match_control(event,singles)
            if control is not None:pairs.append(dict(event=event,control=control))
    excluded=defaultdict(set)
    for pair in pairs:
        for row in pair.values():excluded[row['session']].update(row['window']['token_indices'])
    grouped=defaultdict(list)
    for s in sessions:grouped[s['writer']].append(s)
    profiles={}
    for writer,rows in sorted(grouped.items()):
        other=[s for s in rows if s['session'] not in excluded and len(s['tokens'])>=50]
        seed=int.from_bytes(hashlib.sha256((writer+':20261026').encode()).digest()[:8],'big')
        order=np.random.default_rng(seed).permutation(sorted(s['session'] for s in other)).tolist()
        held=set(order[:math.ceil(len(order)/4)])
        train=[t['token'] for s in rows if s['session'] not in held for t in s['tokens'] if t['index'] not in excluded[s['session']]]
        calibration=[t['token'] for s in rows if s['session'] in held for t in s['tokens']]
        profiles[writer]=dict(tokens=train,heldout_tokens=calibration,heldout_sessions=sorted(held),
                              support=len(train)>=50 and len(calibration)>=50,
                              excluded_window_token_count=sum(len(excluded[s['session']]) for s in rows))
    eligible=[p for p in pairs if profiles[p['event']['writer']]['support']]
    # One complete neutral window per different writer, separately matched to
    # each arm's prompt position. No event-context value is reused for control.
    for p in eligible:
        p['context']={}
        for arm in ('event','control'):
            target=p[arm];donors=defaultdict(list)
            for s in sessions:
                if s['writer']==target['writer'] or s['prompt']!=target['prompt']:continue
                words=[r for r in s['tokens'] if r['is_word']]
                n=len(words)
                if n<50:continue
                start=min(n-50,round(target['position']*n));ids=[r['index'] for r in words[start:start+50]]
                selected=[r['token'] for r in s['tokens'] if ids[0]<=r['index']<=ids[-1]]
                donors[s['writer']].append(dict(session=s['session'],writer=s['writer'],position=start/max(1,n),tokens=selected))
            p['context'][arm]=[min(rr,key=lambda r:(abs(r['position']-target['position']),r['session'])) for _,rr in sorted(donors.items())]
    eligible=[p for p in eligible if p['context']['event'] and p['context']['control']]
    primary=[p for p in eligible if p['event']['kind']=='frustration'];writers={p['event']['writer'] for p in primary}
    support=len(primary)>=100 and len(writers)>=25
    return dict(sessions=sessions,pairs=eligible,profiles=profiles,summary=dict(card='FR1-inputs',sessions=len(sessions),
                event_counts=dict(Counter(r['kind'] for r in events)),complete_matched_before_profile=len(pairs),
                complete_matched_frustration=len(primary),supported_writers=len(writers),support=support,
                support_state='ready' if support else 'unsupported',support_rule='100 complete matched frustration windows from25writers, with independent held-out calibration text and prompt context',
                secondary_deleted_pairs=sum(p['event']['kind']=='deleted' for p in eligible),
                profile_missing_writers=sorted(w for w,p in profiles.items() if not p['support'])))


def execute(output,inputs,config):return io.run(output,inputs,config,prepare_session,assemble)
def verify(output,inputs,config):return io.run(output,inputs,config,prepare_session,assemble,True)
