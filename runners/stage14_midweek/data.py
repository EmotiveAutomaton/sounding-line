"""Past-only roster and effort extraction; no model or scoring calls.

DESIGN CHECK: LESSONS 2-5; CONTROLS. NULL: unknown exposure stays unknown;
late labels/effort and target labels never enter readers. ALTERNATIVE: fully
resolved historical labels and UTF-16 insertions survive known-answer replay.
Malformed chronology fails, unsupported writers are retained as exclusions.
"""
from collections import defaultdict, Counter
from pathlib import Path
import json, math
from runners.stage14.common import REPO, read, freeze, digest, filehash
from runners.stage9.coauthor import delta_ops, units, text_of
from runners.stage9.common import digest as legacy_digest

ROOT=REPO/'results/gear3/G3-S14-MAKER-1'
RAW=ROOT/'raw'
SEED='20261013'
ACTIONS=('accept','edit','dismiss','ignore')

def key(*parts):
    import hashlib
    return hashlib.sha256('|'.join(map(str,parts)).encode()).hexdigest()

def effort(events, start, end, decision):
    """end is next canonical menu; reopens are one target, not duplicate units."""
    stop=next((i for i in range(start+1,end) if events[i]['eventName']=='suggestion-open'),end)
    resolutions=[i for i in range(start+1,stop) if events[i]['eventName'] in ('suggestion-select','suggestion-close')]
    resolution=resolutions[-1] if resolutions and decision!='ignore' else start
    inserted=[]
    for i in range(resolution+1,stop):
        if events[i].get('eventSource')=='user':
            n=sum(len(units(o['insert'])) for o in delta_ops(events[i].get('textDelta')) if 'insert' in o)
            if n:inserted.append((i,n))
    timestamp=lambda i:float(events[i]['eventTimestamp'])
    decided=timestamp(resolution)-timestamp(start)
    if decision=='ignore':decided=timestamp(inserted[0][0])-timestamp(start) if inserted else None
    if decided is not None and decided<0:raise ValueError('negative elapsed decision time')
    return {'chars_typed_after':min(2000,sum(n for _,n in inserted)),
            'decide_seconds':None if decided is None else round(decided/1000,1),
            'resolution_ordinal':resolution,'effort_end_ordinal':stop}

def brief(events):
    # Initial document is the released task's supplied prompt/context. No final text.
    value=events[0].get('currentDoc')
    if not isinstance(value,str):raise ValueError('initial prompt/context absent')
    return value

def history_select(rows, count=16):
    chosen=[];sessions=Counter()
    for r in sorted(rows,key=lambda r:(r['session_time'],r['open_at'],r['key']),reverse=True):
        if sessions[r['session']]>=4:continue
        chosen.append(r);sessions[r['session']]+=1
        if len(chosen)==count:break
    return chosen

def render_history(rows, annotated=False):
    lines=[]
    for i,r in enumerate(rows):
        # Prompt code is an anonymous within-bundle category, not a writer ID.
        line={'prompt':r['prompt'],'draft_end':r['document'][-200:],
              'menu':r['menu'],'decision':r['handling']}
        if r['handling'] in ('accept','edit'):line['inserted']=r['inserted'][:200]
        if annotated:line['effort']={k:r['effort'][k] for k in ('chars_typed_after','decide_seconds')}
        lines.append(line)
    return lines

def load_source():
    base=REPO/'results/phase_2_4_stage_14/raw/jobs/H01-replay-census-v1'
    roster=read(base/'ROSTER.json');exposure_path=REPO/'results/phase_2_4_stage_14/raw/jobs/H01-event-exposure-v1/EVENT_LEDGER.json'
    exposure={r['key']:r for r in read(exposure_path)};sessions=[];pins={};source_exclusions=[]
    for p in (base/'ROSTER.json',exposure_path):pins[str(p.relative_to(REPO))]=filehash(p)
    for s in roster:
        source=REPO/s['path']
        if filehash(source)!=s['source_sha256']:raise ValueError('raw source changed')
        pins[s['path']]=s['source_sha256']
        oldkey=legacy_digest({'coauthor-session':source.stem})
        prepared=REPO/'results/phase_2_4_stage_9/private/prepared/coauthor-v2/sessions'/f'{oldkey}.json'
        saved=read(prepared);pins[str(prepared.relative_to(REPO))]=filehash(prepared)
        if not saved['usable'] or not s['reconstructed']:continue
        events=[json.loads(x) for x in source.read_text(encoding='utf8').splitlines()]
        times=[float(e['eventTimestamp']) for e in events]
        if any(not math.isfinite(t) for t in times) or times!=sorted(times):
            source_exclusions.append(dict(session=s['session'],reason='nonmonotone timestamp; excluded before outcome selection'))
            sessions.append(dict(**s,end_at=max(times),brief=brief(events),rows=[],raw_events=events))
            continue
        rows=[]
        for j,e in enumerate(saved['events']):
            if not e['usable']:continue
            start=e['ordinal'];end=saved['events'][j+1]['ordinal'] if j+1<len(saved['events']) else len(events)
            ident=digest([s['session'],start])
            if ident not in exposure:raise ValueError('missing historical exposure join')
            selected=e['selected_index'];options=e['options']
            cursor=events[start].get('currentCursor')
            if type(cursor) is not int or not 0<=cursor<=len(units(e['document'])):raise ValueError('invalid UTF-16 cursor')
            before_cursor=text_of(units(e['document'])[:cursor])
            rows.append(dict(key=ident,writer=s['writer'],session=s['session'],prompt=s['prompt'],
                session_time=s['timestamp'],open_at=times[start],resolved_at=times[end] if end<len(events) else times[-1],
                ordinal=start,decision_index=j,document=before_cursor,menu=[o['original'] for o in options],
                inserted=options[selected]['original'] if selected is not None and 0<=selected<len(options) else '',
                handling=e['decision'],end_ordinal=end,
                exposure=exposure[ident]['event_exposure']))
        sessions.append(dict(**s,end_at=times[-1],brief=brief(events),rows=rows,raw_events=events))
    return sessions,pins,source_exclusions

def construct(sessions):
    by=defaultdict(list)
    for s in sessions:by[s['writer']].append(s)
    windows={};exclusions=[]
    for w,ss in by.items():
        ss.sort(key=lambda s:(s['timestamp'],s['session']))
        n=math.floor(.6*len(ss));hist=ss[:n];targets=ss[n:]
        for s in hist:
            for r in s['rows']:
                r['effort']=effort(s['raw_events'],r['ordinal'],r['end_ordinal'],r['handling'])
        if len(ss)<3 or sum(len(s['rows']) for s in hist)<8:
            exclusions.append(dict(writer=w,reason='insufficient history'));continue
        windows[w]=(hist,targets)
    def eligible(relaxed):
        out={}
        for w,(hist,targets) in windows.items():
            prohibited={s['prompt'] for s in (hist[-3:] if relaxed else hist)}
            candidates=[]
            for s in targets:
                if s['prompt'] in prohibited or len(s['rows'])<5:continue
                for r in s['rows']:
                    previous=[e for e in s['rows'] if e['ordinal']<r['ordinal'] and e['resolved_at']<=r['open_at']]
                    if len(previous)>=4:candidates.append(dict(r,brief=s['brief'],h1=previous[-16:][::-1]))
            if not candidates:continue
            cutoff=min(r['open_at'] for r in candidates)
            history=[r for s in hist if s['end_at']<=cutoff for r in s['rows'] if r['resolved_at']<=cutoff]
            h2=history_select(history)
            if len(h2)<8 or len({r['prompt'] for r in h2})<2:continue
            out[w]=dict(history=history,h2=h2,cutoff=cutoff,
                        targets=sorted(candidates,key=lambda r:key(w,r['key'],SEED))[:8])
        return out
    strict=eligible(False);relaxed=len(strict)<40;eligible_rows=eligible(relaxed)
    donor_order=sorted(eligible_rows,key=lambda w:key(w,'donor',SEED))
    for i,w in enumerate(donor_order):
        donor=donor_order[(i+1)%len(donor_order)];row=eligible_rows[w]
        available=[r for r in eligible_rows[donor]['history'] if r['resolved_at']<=row['cutoff']]
        desired=len(json.dumps(render_history(row['h2']),ensure_ascii=False))
        possibilities=[history_select(available,n) for n in range(4,33)]
        possibilities=[p for p in possibilities if len({r['prompt'] for r in p})>=2]
        if not possibilities:
            row['excluded']='cyclic donor lacks fully resolved two-prompt past';continue
        h3=min(possibilities,key=lambda p:(abs(len(json.dumps(render_history(p),ensure_ascii=False))/desired-1),len(p)))
        row.update(donor=donor,h3=h3,donor_length_ratio=len(json.dumps(render_history(h3),ensure_ascii=False))/desired)
    usable={w:r for w,r in eligible_rows.items() if 'excluded' not in r}
    ordered=sorted(usable,key=lambda w:key(w,'pilot',SEED));pilot_writers=[w for w in ordered if len(usable[w]['targets'])>=4][:3]
    if len(pilot_writers)!=3 or any(len(usable[w]['targets'])<4 for w in pilot_writers):raise ValueError('pilot support absent')
    reader=[];evaluator=[];training={};roster=[]
    for w,row in usable.items():
        pilot=w in pilot_writers;selected=row['targets'][:4] if pilot else row['targets']
        training[w]={k:row[k] for k in ('history','h2','h3','cutoff','donor','donor_length_ratio')}
        for r in selected:
            common={'writing_prompt':r['brief'],'draft_end':r['document'][-1200:],'menu':r['menu']}
            for arm,hist in [('H0',[]),('H1',r['h1']),('H2',row['h2']),('H3',row['h3']),('H2e',row['h2'])]:
                header='' if arm=='H0' else 'Earlier decisions by this writer in this session' if arm=='H1' else 'Decisions by this writer in earlier sessions'
                public=dict(common=common,history_header=header,history=render_history(hist,arm=='H2e'))
                if arm=='H2e':public['effort_legend']='Recorded typing after the menu and elapsed decision time. These are observations; they do not by themselves identify preference strength.'
                reader.append(dict(id=key(r['key'],arm),target=r['key'],writer=w,arm=arm,pilot=pilot,public=public))
            evaluator.append(dict(key=r['key'],writer=w,prompt=r['prompt'],handling=r['handling'],pilot=pilot,
                                  ordinal=r['ordinal'],decision_index=r['decision_index'],previous_handling=r['h1'][0]['handling'],open_at=r['open_at'],document=r['document'],menu=r['menu']))
            roster.append(dict(key=r['key'],writer=w,prompt=r['prompt'],session=r['session'],pilot=pilot,exposure=r['exposure']))
    for w,r in eligible_rows.items():
        if 'excluded' in r:exclusions.append(dict(writer=w,reason=r['excluded']))
    return dict(reader=reader,evaluator=evaluator,training=training,roster=roster,exclusions=exclusions,
        summary=dict(strict_writers=len(strict),relaxed_prompt_rule=relaxed,supported_writers=len(eligible_rows),
                     writers=len(usable),pilot_writers=len(pilot_writers),pilot_targets=sum(r['pilot'] for r in roster),
                     main_targets=sum(not r['pilot'] for r in roster),h2_sizes=dict(Counter(len(r['h2']) for r in usable.values())),
                     unmatched_donors=sum(not .85<=r['donor_length_ratio']<=1.15 for r in usable.values()),
                     exposure=dict(Counter(r['exposure'] for r in roster))))

def prepare(destination=RAW/'data-v2'):
    if destination.exists():raise ValueError('immutable data build exists; inspect it instead of overwriting')
    sessions,pins,source_exclusions=load_source();data=construct(sessions)
    data['exclusions'].extend(source_exclusions)
    data['summary']['timestamp_excluded_sessions']=len(source_exclusions)
    for name in ('reader','evaluator','training','roster','exclusions'):freeze(destination/(name.upper()+'.json'),data[name])
    freeze(destination/'SOURCE_PINS.json',pins);freeze(destination/'SUMMARY.json',data['summary'])
    return data['summary']

if __name__=='__main__':print(json.dumps(prepare()))
