"""Full original-sized constructed raw/P2/P6/support chain for native admission."""
from pathlib import Path
import json
import math
import time
import numpy as np

from runners.drive.cards import timing_d33_supported as card
from runners.drive.cards import timing_d33_supported_source as source
from runners.drive.cards import timing_d33_pair_intake as intake
from runners.drive.cards.timing_d33 import make_rows
from runners.drive.cards.timing_d33_match import primary_roster
from runners.drive.cards.timing_text import replay_words
from runners.drive.cards.timing_census import read,write,filehash
from runners.drive.cards.timing_p6 import gzwrite
from runners.stage9.coauthor import units


def fixture(root,beta=.8):
    """No population shortcut:78602 original evaluation words and41writers."""
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True);rng=np.random.default_rng(9041)
    vocabulary=['a','bee','cedar','delta','ember','fox','garden','hill','iris','jet','king','lake']
    probability={w:float(p) for w,p in zip(vocabulary,rng.uniform(.001,.004,len(vocabulary)))}
    frequency={w:float(p) for w,p in zip(vocabulary,rng.uniform(-7,-2,len(vocabulary)))}
    records=[];raw_events={};typed={}
    for wi in range(41):
        distribution=rng.dirichlet(np.full(len(vocabulary),2.))
        for si in range(5):
            sid=f'w{wi:02}_s{si}';base=si*10000000+wi*10000
            n=1917+int(wi<5) if si==4 else 500
            if si==4:
                # Bulk insert blocks retain logged-delta timing semantics.
                labels=rng.choice(vocabulary,size=40,replace=True)
                chunks=[[str(w)]*(n//40+int(j<n%40)) for j,w in enumerate(labels)]
            else:chunks=[[str(w) for w in rng.choice(vocabulary,size=n,p=distribution)]]
            events=[dict(eventName='system-initialize',eventTimestamp=base,currentDoc='Prompt \n'),
                dict(eventName='retain',eventTimestamp=base+100,eventSource='api',textDelta={'ops':[{'retain':8}]})]
            document='Prompt \n'
            for j,chunk in enumerate(chunks):
                text=' '.join(chunk)+' '
                events.append(dict(eventName='insert',eventTimestamp=base+200+j*200,eventSource='user',
                    textDelta={'ops':[{'retain':len(units(document))-1},{'insert':text}]}))
                document=document[:-1]+text+'\n'
            words=replay_words(events)['words']
            for w in words:w.update(population_probability=probability[w['token']],population_surprisal=-math.log(probability[w['token']]),population_log_frequency=frequency[w['token']])
            records.append(dict(session=sid,writer=f'w{wi:02}',prompt=f'p{si%2}',timestamp=base,end_at=events[-1]['eventTimestamp'],
                training_sequences=[[w for chunk in chunks for w in chunk]],words=words))
            raw_events[sid]=events;typed[sid]=document
    old_rows,tuning,excluded=make_rows(records,'first_character_delta');assert len(old_rows)==78602
    roster,by_writer=primary_roster(old_rows,records,tuning);lookup={r['session']:r for r in records}
    targets=[dict(writer=w,session=sid,split=split) for w,p in sorted(roster['writers'].items())
        for split in ('calibration','evaluation') for sid in p[split+'_sessions']]
    pair_units={t['session']:intake.unit(t,'pair',by_writer,lookup) for t in targets}
    selected=source.population_roster(dict(rows=old_rows),roster,pair_units,lookup,'pair')
    tuned=source.calibrate(selected,pair_units,lookup)
    cov={sid:dict(words=source.screen_covariates(raw_events[sid],lookup[sid]['words'])) for sid in sorted({key[0] for key in selected['retained_keys']})}
    rows=source.scientific_rows(dict(rows=old_rows),selected,pair_units,lookup,tuned,cov)
    by_session={}
    for row in rows:by_session.setdefault(row['session'],[]).append(row)
    for sid,session_rows in by_session.items():
        events=raw_events[sid];clock=events[1]['eventTimestamp'];by_ordinal={}
        for row in session_rows:
            ordinal=lookup[sid]['words'][row['index']]['ordinal'];by_ordinal.setdefault(ordinal,[]).append(row)
        for ordinal,values in sorted(by_ordinal.items()):
            r=values[len(values)//2]
            y=beta*r['own_surprise']+.25*r['donor_surprise']+.03*r['population_surprisal']+.01*r['length']-.02*r['log_frequency']+.04*r['on_screen']+.05*r['session_surprisal']+int(r['writer'][1:])*.005+float(rng.normal(scale=.015))
            clock+=1000*math.exp(y);events[ordinal]['eventTimestamp']=clock
        lookup[sid]['end_at']=events[-1]['eventTimestamp']
        words=replay_words(events)['words']
        for w in words:w.update(population_probability=probability[w['token']],population_surprisal=-math.log(probability[w['token']]),population_log_frequency=frequency[w['token']])
        lookup[sid]['words']=words
    metas=[];raw_roster=[];p2_index=[];p6_index=[];pins={}
    for record in records:
        sid=record['session'];events=raw_events[sid];raw=root/'raw'/(sid+'.jsonl');raw.parent.mkdir(exist_ok=True)
        raw.write_text(''.join(json.dumps(e)+'\n' for e in events),encoding='utf8');sha=filehash(raw)
        pins[raw.relative_to(root).as_posix()]=sha;raw_roster.append(dict(session=sid,path=raw.relative_to(root).as_posix(),source_sha256=sha))
        meta={k:record[k] for k in ('session','writer','prompt','timestamp','end_at')};metas.append(dict(meta,rows=[]))
        p2=root/'foundation'/f'{sid}.json';write(p2,dict(meta,source_sha256=sha,final_document=typed[sid]))
        p2_index.append(dict(session=sid,writer=record['writer'],file=p2.name,sha256=filehash(p2)))
        p6=root/'p6'/f'{sid}.json.gz';gzwrite(p6,record);p6_index.append(dict(session=sid,writer=record['writer'],file=p6.name,sha256=filehash(p6)))
    write(root/'SESSIONS.json',metas);write(root/'ROSTER.json',raw_roster);write(root/'SOURCE_PINS.json',pins)
    write(root/'foundation/SESSION_INDEX.json',p2_index);write(root/'p6/P6_INDEX.json',p6_index)
    write(root/'foundation/PLAN.json',dict(pins={p.relative_to(root).as_posix():filehash(p) for p in (root/'SESSIONS.json',root/'ROSTER.json',root/'SOURCE_PINS.json')}))
    def complete(folder,names,**extra):
        write(folder/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,outputs={n:filehash(folder/n) for n in names},**extra))
    complete(root/'foundation',['SESSION_INDEX.json'],plan_sha256=filehash(root/'foundation/PLAN.json'))
    raw_inputs=dict(repo_root=str(root),foundation_complete=str(root/'foundation/COMPLETE.json'),foundation_plan=str(root/'foundation/PLAN.json'),
        session_index=str(root/'foundation/SESSION_INDEX.json'),prepared_sessions=str(root/'SESSIONS.json'),raw_roster=str(root/'ROSTER.json'),
        source_pins=str(root/'SOURCE_PINS.json'),p6_index=str(root/'p6/P6_INDEX.json'),p6_completion=str(root/'p6/COMPLETE.json'))
    write(root/'p6/P6_BINDINGS.json',dict(config={},repo_root=str(root),index_sha256=filehash(raw_inputs['p6_index']),
        inputs={k:filehash(raw_inputs[k]) for k in ('foundation_complete','prepared_sessions','raw_roster','session_index')}))
    complete(root/'p6',['P6_INDEX.json','P6_BINDINGS.json']);write(root/'tc/PRIMARY.json',dict(timing_mode='first_character_delta'));complete(root/'tc',['PRIMARY.json'])
    original_inputs=dict(p6_index=raw_inputs['p6_index'],p6_completion=raw_inputs['p6_completion'],tc_primary=str(root/'tc/PRIMARY.json'),tc_completion=str(root/'tc/COMPLETE.json'))
    rows,tuning,excluded=make_rows(records,'first_character_delta');assert len(rows)==78602
    saved=dict(rows=rows,tuning=tuning,exclusions=excluded)
    write(root/'d33/PLAN.json',dict(module='runners.drive.cards.timing_d33',config=dict(extension=False,bootstrap_draws=2000,seed=20261017),inputs=original_inputs))
    gzwrite(root/'d33/output/D33_INTERMEDIATES.json.gz',saved);write(root/'d33/output/D33_PRIMARY.json',dict(observations=len(rows)))
    complete(root/'d33',['PLAN.json','output/D33_INTERMEDIATES.json.gz','output/D33_PRIMARY.json'])
    intake_inputs=dict(original_inputs,d33_completion=str(root/'d33/COMPLETE.json'))
    write(root/'support/PLAN.json',dict(module='runners.drive.cards.timing_d33_pair_intake',config=intake.CONFIG,inputs=intake_inputs))
    roster,by_writer=primary_roster(rows,records,tuning);write(root/'support/output/PRIMARY_ROSTER.json',roster)
    paths=['PLAN.json','output/PRIMARY_ROSTER.json']
    for t in targets:
        for variant in ('pair','pair2'):
            name=f'output/sessions/{variant}/{t["session"]}.json';write(root/'support'/name,intake.unit(t,variant,by_writer,lookup));paths.append(name)
    complete(root/'support',paths)
    decision=root/'DECISION.json';write(decision,dict(authority='Curator reply: Build the supported match variant.'))
    inputs=dict(raw_inputs,**{k:v for k,v in intake_inputs.items() if k not in raw_inputs},support_completion=str(root/'support/COMPLETE.json'),supported_decision=str(decision))
    write(root/'INPUTS.json',inputs)
    return inputs


def test_full_size_raw_source_to_handler(tmp_path):
    start=time.perf_counter();inputs=fixture(tmp_path/'source');out=tmp_path/'output'
    result=card.execute(out,inputs,card.configuration('pair'))
    assert result['state']=='positive' and result['primary']['effect']>0
    assert result['coverage']['original_words']==78602 and result['coverage']['retained_words']==78602
    assert card.verify(out,inputs,card.configuration('pair'))['verified']
    write(tmp_path/'SMOKE.json',dict(seconds=time.perf_counter()-start,source_rows=78602,
        bytes=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())))
