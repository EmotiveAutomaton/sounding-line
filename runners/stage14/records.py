"""H01 source replay and full writer/time census before new fitting.

DESIGN CHECK: LESSONS 2-5; CONTROLS 1,6. NULL: malformed deltas, accidental
endpoint equality, missing chronology or target leakage refuse admission.
ALTERNATIVE: exact Unicode replay recovers witnessed selection/edit/dismiss/ignore;
identical endpoints cannot reveal invisible selection. Exclusions remain explicit.
No private motive, endorsement, or untouched-human-confirmation claim.
"""
from collections import Counter, defaultdict
from pathlib import Path
import json
from .common import REPO, freeze, digest, filehash
from runners.stage9.coauthor import raw_inputs, units
from runners.stage11.replay import replay
from runners.stage11_1.targets import project, public

def fixtures():
    cases=[]
    for i in range(16):
        before=f'Workshop {i}: 🌞\n'; offer=f' choice {i}'
        menu=[dict(index=0,original=offer,trimmed=offer)]
        base=[dict(eventName='system-initialize',currentDoc=before),
              dict(eventName='suggestion-open',currentSuggestions=menu)]
        for action in ('accept','edit','dismiss','ignore'):
            rows=list(base)
            end=before
            if action in ('accept','edit'):
                rows += [dict(eventName='suggestion-select',currentSuggestionIndex=0),
                    dict(eventName='text-insert',eventSource='api',textDelta={'ops':[{'retain':len(units(before))-1},{'insert':offer}]})]
                end=before[:-1]+offer+'\n'
                if action=='edit':
                    rows += [dict(eventName='text-insert',eventSource='user',textDelta={'ops':[{'retain':len(units(before))},{'delete':1},{'insert':'X'}]})]
                    end=before[:-1]+' X'+offer[2:]+'\n'
            else:
                if action=='dismiss': rows += [dict(eventName='suggestion-close')]
                rows += [dict(eventName='text-insert',eventSource='user',textDelta={'ops':[{'retain':len(units(before))}]})]
            r=replay(rows); e=r['events'][0]
            assert r['reconstructed'] and e['usable'] and e['decision']==action
            assert e['end_document']==end
            target=project(e,rows)
            assert target['handling']==action
            assert target['attributes']==dict(reviewed='unknown',endorsed='unknown',understood='unknown')
            cases.append(dict(key=f'fixture-{i}-{action}',lines=rows,event=e,target=target))
    bad=list(cases[0]['lines'])+[dict(eventName='text-delete',eventSource='user',textDelta={'ops':[{'delete':1000000}]})]
    assert not replay(bad)['reconstructed']
    return cases

def run(card,out,raw,tick):
    controls=fixtures(); freeze(out/'FIXTURES.json',controls)
    paths, metadata, identity=raw_inputs()
    roster=[]; errors=[]; counts=Counter(); writers=defaultdict(list); source_pins={}
    # No fitted prediction is produced here. Source truth and reader views are stored
    # separately; chronology is established from recorded timestamps, never file order.
    for i,p in enumerate(paths):
        if p.stem not in metadata: continue
        lines=p.read_text(encoding='utf-8').splitlines(); events=[json.loads(x) for x in lines]
        m=metadata[p.stem]; sid=digest(['session',p.stem]); r=replay(events)
        source_pins[str(p.relative_to(REPO)).replace('\\','/')]=filehash(p)
        stamp=next((x.get('timestamp') for x in events if x.get('timestamp') is not None),None)
        # Dataset revisions use eventTimestamp; retain exact field and value.
        stamp_field='timestamp'
        if stamp is None:
            stamp=next((x.get('eventTimestamp') for x in events if x.get('eventTimestamp') is not None),None)
            stamp_field='eventTimestamp'
        session=dict(session=sid,writer=m['writer'],prompt=m['prompt'],domain=m['domain'],timestamp=stamp,timestamp_field=stamp_field,
            reconstructed=r['reconstructed'],opportunities=len(r['events']),path=str(p.relative_to(REPO)).replace('\\','/'),source_sha256=source_pins[str(p.relative_to(REPO)).replace('\\','/')])
        roster.append(session); writers[m['writer']].append(session)
        reader=[]; truth=[]
        for e in r['events']:
            counts['attempted_opportunities']+=1
            key=digest([sid,e['ordinal']])
            if not e['usable']:
                errors.append(dict(key=key,reason=e.get('exclusion') or 'session reconstruction failed'));continue
            try: target=project(e,events)
            except (ValueError,UnicodeError,AssertionError) as exc:
                errors.append(dict(key=key,reason=str(exc)));continue
            counts[target['handling']]+=1
            reader.append(dict(key=key,session=sid,writer=m['writer'],prompt=m['prompt'],domain=m['domain'],ordinal=e['ordinal'],
                V0={'menu_was_available':True},V1=public(e,'artifact'),V3=public(e,'alternatives'),
                prospective={'document':e['document'],'alternatives':[x['original'] for x in e['options']]},
                exposure='previously available project corpus; event-level reconciliation pending'))
            truth.append(dict(key=key,target=target,selected_index=e['selected_index'],cutoff_ordinal=e['cutoff_ordinal'],
                source_ordinal=e['ordinal'],source_sha256=session['source_sha256']))
        freeze(out/'reader'/f'{sid}.json',reader); freeze(out/'evaluator'/f'{sid}.json',truth)
        tick(dict(sessions=i+1,total_sessions=len(paths),opportunities=counts['attempted_opportunities']))
    missing=sum(x['timestamp'] is None for x in roster)
    # Admission is for exact replay only. Chronological studies independently refuse
    # missing/ambiguous time and must freeze their train/calibration/test manifest.
    summary=dict(status='complete',source_sessions=len(roster),writers=len(writers),prompts=len({x['prompt'] for x in roster}),
        counts=dict(counts),excluded_opportunities=len(errors),missing_timestamps=missing,known_controls=len(controls),
        exact_fixture_gate=True,scope='source-consistency and witnessed-event extraction; not independent truth validation',
        exposure='historically exposed human corpus; no fresh-writer confirmation',rights=identity['permission'],
        brier='one half sum of squared class-probability errors; invalid=1; unsmoothed zero support has infinite logarithmic loss')
    freeze(out/'ROSTER.json',roster); freeze(out/'EXCLUSIONS.json',errors)
    freeze(out/'SOURCE.json',dict(identity=identity,source_pins=source_pins))
    freeze(out/'SUMMARY.json',summary)
    freeze(out/'ADMISSION.json',dict(admitted=True,exact_replay=True,chronology_complete=missing==0,
        inference_admitted=False,confirmation_admitted=False))
    return summary
