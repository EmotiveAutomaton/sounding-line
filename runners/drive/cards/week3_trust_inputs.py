"""TR5 canonical failure anchors and prospective kept-history controls.

DESIGN CHECK: LESSONS 3-5 read 2026-10-25. Accepted Unicode atoms are replayed
and their survival is queried at the failure/control anchor, never session end.
Future deletion must not change prior run bins. Five complete canonical menus
are required on each side of an anchor; thin matched support is unsupported.
The source census and frozen run median precede any outcome comparison.
"""
from bisect import bisect_right
from collections import Counter, defaultdict
import math

import numpy as np

from runners.stage9.coauthor import units,text_of,delta_ops
from . import week3_frames_io as io
from . import week3_outcome_blocks_inputs as wc2

CONFIG=dict(card='TR5-inputs',mode='full',expected_sessions=1399,session_limit=1399,seed=20261026)
PILOT=dict(CONFIG,mode='pilot',session_limit=140)


def history(events,timeline,canonical):
    """Independent replay retains sparse survival counts at every removal."""
    certified={s['origin']:s for s in wc2.spans(events,timeline,canonical)}
    doc=units(events[0]['currentDoc']);owners=[None]*len(doc)
    current=pending=None;serial=0;records={}
    for ordinal,event in enumerate(events):
        name=event['eventName']
        if name=='suggestion-open':current=ordinal
        if name=='suggestion-select':pending=current
        ops=delta_ops(event.get('textDelta'))
        if not ops:continue
        user=event.get('eventSource')=='user';origin=pending if not user and pending is not None else None
        out=[];labels=[];position=0;inserted=[];removed=set();first_positions={}
        for op in ops:
            if 'insert' in op:
                for char in op['insert']:
                    tag=(origin,serial) if origin is not None else None;serial+=1
                    out.extend(units(char));labels.extend([tag]*len(units(char)))
                    if tag is not None:inserted.append(tag)
            else:
                n=op.get('retain',op.get('delete'))
                if type(n) is not int or n<0 or position+n>len(doc):raise ValueError('invalid survival UTF16 boundary')
                if 'retain' in op:out.extend(doc[position:position+n]);labels.extend(owners[position:position+n])
                else:
                    gone=set(owners[position:position+n])-{None};removed|=gone
                    for tag in gone:first_positions.setdefault(tag[0],len(out))
                position+=n
        out.extend(doc[position:]);labels.extend(owners[position:]);prior=owners;doc=out;owners=labels
        if origin is not None:
            proof=certified[origin]
            if len(inserted)!=proof['original_codepoints']:raise ValueError('original accepted atom count differs')
            # Canonical accepted text is appended before the terminal newline;
            # the raw API delta can implement that append by replacing content.
            newlabels=[tag for tag,char in zip(inserted,proof['text']) for _ in units(char)]
            owners=prior[:-1]+newlabels+prior[-1:]
            records[origin]=dict(**proof,retention=[[ordinal,len(inserted)]],removed=set(),failure_position=None,failure_removed=None)
            pending=None
        if user:
            changed={tag[0] for tag in removed}
            for key in changed:
                r=records[key];r['removed'].update(tag for tag in removed if tag[0]==key)
                retained=r['original_codepoints']-len(r['removed'])
                r['retention'].append([ordinal,retained])
                if ordinal==r['failure_ordinal']:
                    r['failure_position']=first_positions[key];r['failure_removed']=len(r['removed'])
    if text_of(doc)!=timeline['final_document']:raise ValueError('survival final text differs')
    for key,r in records.items():
        if r['retention'][-1][1]!=r['retained_codepoints']:raise ValueError('survival counts differ from independent replay')
        r.pop('removed')
    return records


def retained(span,ordinal):
    at=bisect_right([x[0] for x in span['retention']],ordinal)-1
    return 0 if at<0 else span['retention'][at][1]


def kept(span,ordinal):
    return span is not None and span['canonical'] and 5*retained(span,ordinal)>=4*span['original_codepoints']


def run_length(menu,spans,origin,anchor):
    at=next(i for i,m in enumerate(menu) if m['origin']==origin);count=0
    for m in reversed(menu[:at]):
        if m['handling'] not in ('accept','edit') or not kept(spans.get(m['origin']),anchor):break
        count+=1
        if count==5:break
    return count


def strict_retyped(events,span):
    failure=span['failure_ordinal']
    if failure is None:return False
    clocks=[float(e['eventTimestamp']) for e in events]
    if clocks[failure]-clocks[span['inserted_ordinal']]>30000:return False
    cursor=span['failure_position'];typed=0
    for e in events[failure+1:]:
        if float(e['eventTimestamp'])-clocks[failure]>60000:break
        ops=delta_ops(e.get('textDelta'));old=0;before=cursor;after=cursor
        # Cursor follows the post-failure replacement location through edits.
        for op in ops:
            if 'insert' in op:
                n=len(units(op['insert']))
                if old==before and e.get('eventSource')=='user':typed+=len(op['insert'])
                if old<=before:after+=n
            elif 'retain' in op:
                old+=op['retain']
            else:
                n=op['delete']
                if old<before:after-=min(n,before-old)
                old+=n
        cursor=after
        if 2*typed>=span['failure_removed']:return True
    return False


def anchor_window(menu,requests,anchor,seconds,clocks):
    # Choices resolving at the anchor belong to the before window. All choices
    # must have observed resolutions; right-censored menus cannot be outcomes.
    at=bisect_right([m['resolution'] for m in menu],anchor)
    before=menu[max(0,at-5):at];after=menu[at:at+5]
    if len(before)!=5 or len(after)!=5 or any(m['censored'] for m in before+after):return None
    rates=[]
    for low,high in ((clocks[before[0]['origin']],seconds),(seconds,clocks[after[-1]['resolution']])):
        duration=high-low
        rates.append(sum(low<t<=high for t in requests)/duration if duration>0 else None)
    return dict(before=[m['origin'] for m in before],after=[m['origin'] for m in after],
                acceptance_before=sum(m['handling'] in ('accept','edit') for m in before)/5,
                acceptance_after=sum(m['handling'] in ('accept','edit') for m in after)/5,
                request_rate_before=rates[0],request_rate_after=rates[1])


def prepare_session(meta,events,timeline,canonical,p6):
    spans=history(events,timeline,canonical);menu=io.menus(events,timeline,canonical)
    if [m['resolution'] for m in menu]!=sorted(m['resolution'] for m in menu):raise ValueError('menu resolution chronology differs')
    clocks=[(float(e['eventTimestamp'])-float(events[0]['eventTimestamp']))/1000 for e in events]
    requests=[clocks[i] for i,e in enumerate(events) if e['eventName']=='suggestion-get']
    for m in menu:
        value=events[m['origin']].get('currentTemperature')
        m['temperature']=None if value in (None,'') else float(value)
        if m['temperature'] is not None and not math.isfinite(m['temperature']):raise ValueError('nonfinite decoding temperature')
        m['seconds']=clocks[m['resolution']]
    accepted=[s for s in spans.values() if s['canonical'] and s['text'].strip()]
    failures=[]
    for s in accepted:
        if s['failure_ordinal'] is None:continue
        anchor=s['failure_ordinal'];window=anchor_window(menu,requests,anchor,clocks[anchor],clocks)
        at=bisect_right([m['resolution'] for m in menu],anchor)
        failures.append(dict(id=meta['session']+':'+str(s['origin']),origin=s['origin'],anchor=anchor,anchor_seconds=clocks[anchor],
            delay_seconds=clocks[anchor]-clocks[s['inserted_ordinal']],run_length=run_length(menu,spans,s['origin'],anchor),
            decile=min(9,10*at//max(1,len(menu))),window=window,strict_retyped=strict_retyped(events,s)))
    return dict(**{k:meta[k] for k in ('session','writer','prompt','timestamp')},menu=menu,
                clocks=clocks,requests=requests,spans=list(spans.values()),failures=failures,
                legacy_failure_candidates=sum(s['failure_ordinal'] is not None for s in spans.values()))


def matched_controls(failure,source,candidates):
    matches=[]
    for session in candidates:
        spans={r['origin']:r for r in session['spans']};menu=session['menu'];clocks=session['clocks']
        for span in spans.values():
            if not span['canonical'] or not span['text'].strip():continue
            if session['session']==source['session'] and span['origin']==failure['origin']:continue
            seconds=clocks[span['inserted_ordinal']]+failure['delay_seconds']
            if seconds>clocks[-1]:continue
            anchor=bisect_right(clocks,seconds)-1
            if not kept(span,anchor):continue
            at=bisect_right([m['resolution'] for m in menu],anchor)
            decile=min(9,10*at//max(1,len(menu)))
            run=run_length(menu,spans,span['origin'],anchor)
            if (decile,run)!=(failure['decile'],failure['run_length']):continue
            window=anchor_window(menu,session['requests'],anchor,seconds,clocks)
            if window is None:continue
            matches.append(dict(session=session['session'],origin=span['origin'],anchor=anchor,anchor_seconds=seconds,
                                run_length=run,decile=decile,window=window))
    return matches


def assemble(sessions):
    by_writer=defaultdict(list)
    for s in sessions:by_writer[s['writer']].append(s)
    pairs=[]
    for s in sessions:
        for f in s['failures']:
            if f['window'] is None:continue
            controls=matched_controls(f,s,by_writer[s['writer']])
            if controls:pairs.append(dict(writer=s['writer'],session=s['session'],failure=f,controls=controls))
    median=float(np.median([p['failure']['run_length'] for p in pairs])) if pairs else None
    for p in pairs:p['run_bin']='long' if p['failure']['run_length']>=median else 'short'
    writers={p['writer'] for p in pairs};bins=dict(Counter(p['run_bin'] for p in pairs))
    support=len(pairs)>=60 and len(writers)>=20 and set(bins)=={'long','short'}
    return dict(sessions=sessions,pairs=pairs,run_median=median,summary=dict(card='TR5-inputs',sessions=len(sessions),
                legacy_failure_candidates=sum(s['legacy_failure_candidates'] for s in sessions),
                canonical_failure_candidates=sum(len(s['failures']) for s in sessions),
                complete_failure_windows=sum(f['window'] is not None for s in sessions for f in s['failures']),
                matched_failures=len(pairs),supported_writers=len(writers),run_bins=bins,support=support,
                support_state='ready' if support else 'unsupported',
                support_rule='60 complete matched failures from20writers with both frozen run bins'))


def execute(output,inputs,config):return io.run(output,inputs,config,prepare_session,assemble)
def verify(output,inputs,config):return io.run(output,inputs,config,prepare_session,assemble,True)
