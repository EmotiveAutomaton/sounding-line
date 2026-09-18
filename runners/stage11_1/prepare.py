"""Outcome-blind expanded roster; source projection before model dispatch.

DESIGN CHECK: LESSONS 2-5, CONTROLS 6. NULL: private outcomes cannot order samples;
exposure or split crossing cannot become fresh confirmation. ALTERNATIVE: session
breadth precedes depth and all retained targets match native handling and endpoint.
Malformed/ambiguous projections are explicit exclusions, never silent negatives.
"""
from collections import Counter,defaultdict
import hashlib
from runners.stage9.coauthor import raw_inputs
from runners.stage11.replay import replay
from .common import PRIVATE,contract,allocation,read,freeze,digest
from .targets import project,public
from .models import request_for,VIEWS,MAX_RETAINED_BYTES


def balanced(rows,limit,cap,seed):
    grouped=defaultdict(lambda:defaultdict(list))
    for r in sorted(rows,key=lambda r:digest([seed,r['key']])):grouped[r['writer']][r['session']].append(r)
    by={}
    for w,sessions in grouped.items():
        order=sorted(sessions,key=lambda s:digest([seed,s]))
        by[w]=[sessions[s][i] for i in range(max(map(len,sessions.values()))) for s in order if len(sessions[s])>i]
    writers=sorted(by,key=lambda w:digest([seed,w]))
    return [by[w][i] for i in range(cap) for w in writers if len(by[w])>i][:limit]


def prepare(root=PRIVATE):
    contract(root);allocation(root)
    if (root/'PREPARED.json').exists():
        result=read(root/'PREPARED.json')
        if digest(read(root/'COHORT.json'))!=result['cohort_digest']:raise ValueError('changed roster')
        return result
    native=read(root/'NATIVE_OPPORTUNITIES.json');paths,_,_=raw_inputs()
    lookup={digest({'coauthor-session':p.stem}):p for p in paths}
    source={};audit=[];exclusions=[];eligible=defaultdict(list)
    for session in sorted({r['session'] for rows in native.values() for r in rows}):
        p=lookup[session];lines=p.read_text(encoding='utf-8').splitlines();r=replay(lines)
        if not r['reconstructed']:raise ValueError('previously eligible session no longer reconstructs')
        source[session]=(lines,{e['ordinal']:e for e in r['events']})
        audit.append(dict(session=session,path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    for lane,rows in native.items():
        for r in rows:
            lines,events=source[r['session']];e=events[r['ordinal']]
            if not e['usable'] or e['decision']!=r['truth'] or e['document']!=r['views']['artifact']['document']:raise ValueError('native identity mismatch')
            try:
                target=project(e,lines);views={v:public(e,v) for v in VIEWS}
                for v in VIEWS:
                    request_for(views[v],'account')
                    request_for(views[v],'review',{'reserved':'x'*(MAX_RETAINED_BYTES-30)})
            except (ValueError,UnicodeError) as exc:
                exclusions.append(dict(key=r['key'],partition=lane,reason=str(exc)));continue
            eligible[lane].append(dict(key=r['key'],writer=r['unit'],prompt=r['stimulus'],session=r['session'],
                domain=r['domain'],ordinal=r['ordinal'],cutoff_ordinal=e['cutoff_ordinal'],target=target,views=views,
                exposure='historically exposed',partition=lane))
    discovery=balanced(eligible['evaluation'],128,8,'stage11.1-discovery')
    keys={r['key'] for r in discovery}
    breadth=balanced([r for r in eligible['evaluation'] if r['key'] not in keys],128,128,'stage11.1-breadth')
    cohort=dict(train=balanced(eligible['train'],96,3,'stage11.1-train'),development=balanced(eligible['development'],9,9,'stage11.1-dev'),
        discovery=discovery,breadth=breadth)
    selected={r['key'] for rows in cohort.values() for r in rows}
    exclusions += [dict(key=r['key'],partition=lane,reason='frozen sample cap') for lane,rows in eligible.items() for r in rows if r['key'] not in selected]
    for lane,rows in cohort.items():
        for i,r in enumerate(rows):r['tranche']='initial' if lane=='discovery' and i<32 else 'extension' if lane=='discovery' else lane
    for a,b in [('train','development'),('train','discovery'),('train','breadth'),('development','discovery'),('development','breadth')]:
        for f in ('writer','session','prompt'):
            if {r[f] for r in cohort[a]}&{r[f] for r in cohort[b]}:raise ValueError('inherited partition crossing')
    freeze(root/'COHORT.json',cohort)
    freeze(root/'SOURCE.json',dict(audit=audit,exclusions=exclusions,native_metadata=read(root/'NATIVE_METADATA.json'),
        confirmations='none; admitted CoAuthor records are historically exposed'))
    result=dict(status='PREPARED',cohort_digest=digest(cohort),
        counts={k:dict(episodes=len(v),writers=len({r['writer'] for r in v}),sessions=len({r['session'] for r in v}),
            prompts=len({r['prompt'] for r in v}),domains=dict(Counter(r['domain'] for r in v))) for k,v in cohort.items()},
        exclusions=dict(Counter(e['reason'] for e in exclusions)),source_sessions=len(audit),
        target_contract_sha256=hashlib.sha256(__import__('pathlib').Path('runners/stage11_1/TARGET_CONTRACT.md').read_bytes()).hexdigest(),
        scope='descriptive exposed human records; development one writer, no learned calibration',
        next_action='source-based target audit, literal interface pilot, S1 initial then extension')
    freeze(root/'PREPARED.json',result);return result


if __name__=='__main__':print(prepare())
