"""Read the Week 8 standing queue, keep its clock and render the curator return."""
import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runners.drive.cards import week8_gear as gear
from runners.stage14.common import atomic, freeze, read, filehash, now
from runners.stage9.process_identity import native_identity, is_same_live_process

STATE=ROOT/'.agent-state/drive-20261127/week8'
DESIGN=ROOT/'docs/design/stage-15/week8'
RETURN=ROOT/'docs/exchange/WEEK8_RETURN.md'
PUBLIC=ROOT/'results/phase_2_4_stage_15/WEEK8'
ROWS={
    'SLD5':('Spark','Purpose after loss','Three-wave marital-status, age and dated-loss binding and rehearsal'),
    'LKG1':('Spark','Liking across conversations','Reciprocal liking-item binding and repeat-speaker rehearsal'),
    'SLD6':('Spark','Trait by kind of daily stressor','Wave-two stressor and trait binding and three-way contrast rehearsal'),
    'SLD8':('Spark','Wave-one daily diary','Read-only combined diary/survey source, codebook and person-key binding'),
    'LGH6':('local','Voicing before another person joins a laugh','Within-laugh frame window and constructed audio checks'),
    'ACC1':('local','Acceleration in game outcomes','Player split and three validated standard-model fits'),
    'ADP1':('local','How good and bad surprises fade','Player split and qualified two-rate model'),
    'RML1':('local','Room level before laughter','Laugh-excluded half-minute sound and speech-rate operator'),
    'SLD9':('Spark','Traits and wellbeing scales','Wave-two composite dictionary and complete-roster rehearsal'),
    'TMP2':('Spark','Trait reader on written histories','Staged reader with source and constructed exclusion/range rehearsal'),
    'LAG2':('local','Next-prompt diary replay','Qualified independent replay of the 649 first-pass cells'),
    'LKG2':('Spark','Liking, standing and traits','Liking-gap, standing and trait codebook bindings'),
    'MNG1':('local','Meaning and happiness by activity','Activity and company file bindings and paired-rating rehearsal'),
    'SLD7':('Spark','Purpose after marriage','Three-wave common comparison adapter and married-gain roster'),
    'LGH7':('local','Meeting role and joining laughter','Documented meeting ranks and a within-meeting permutation fixture'),
    'ATL2':('local','Split-half stability of diary cells','Whole-person split qualification on the frozen atlas cells'),
    'ADM2':('local','Unused-source census','Source manifests, rights and codebook review'),
    'TWO3':('local','Lagged feelings within couples','Pair/occasion alignment and same-partner lag fixture'),
    'BMP1':('local','Body maps by feeling','ADM2 body-map admission and documented spatial regions'),
    'DRV1':('local','Falling standing, anxiety and sadness','Momentary item and same-day triple binding for each diary'),
    'TMP3':('Spark','Trait reader on conversation turns','Engine TP72 conversation adapter and source-mount rehearsal')
}
assert set(ROWS)==gear.CARDS


def snapshot():
    # A disposition records local filing. R48 also requires a pushed report.
    pushed=subprocess.run(['git','ls-tree','-r','--name-only','origin/main','--','docs/exchange/r48'],
                          cwd=ROOT,capture_output=True,text=True,check=True).stdout.splitlines()
    published={Path(p).stem for p in pushed if p.endswith('.md')}
    state=read(STATE/'dispositions.json') if (STATE/'dispositions.json').is_file() else {}
    attempts={}
    for ref in gear.ROOT.glob('*/RESERVATION.json'):
        d=ref.parent
        data=read(ref)
        terminal=next((s for s in ('COMPLETE','FAILED','PAUSED') if (d/(s+'.json')).exists()),None)
        attempts.setdefault(data['card'],[]).append((d.name,terminal,is_same_live_process(data['native']),data['sealed']))
    reviewed={}
    for p in (STATE/'reviews').glob('*.json'):
        v=read(p)
        reviewed.setdefault(v['card'],[]).append(p.stem)
    rows={}
    for card,(host,name,requirement) in ROWS.items():
        record=state.get(card,{})
        evidence=record.get('evidence',requirement)
        status=record.get('status','blocked')
        jobs=attempts.get(card,[])
        if any(not t and live for _,t,live,_ in jobs):
            status='running'
            evidence=', '.join(n for n,t,live,_ in jobs if not t and live)
        elif any(not t for _,t,_,_ in jobs):
            status='blocked'
            evidence='Owner inspection of interrupted reservation'
        elif status!='landed':
            idle=[n for n in reviewed.get(card,[]) if n not in {j[0] for j in jobs}
                  and not any((STATE/q/(n+'.hold.json')).exists() for q in ('local-queue','spark-queue'))]
            if idle:
                status='ready'
                evidence=', '.join(sorted(idle))
            elif jobs and all(t for _,t,_,_ in jobs) and 'evidence' not in record:
                evidence='Owner filing of '+', '.join(n for n,_,_,_ in jobs)
            if not idle and status=='ready':
                status='blocked'
                evidence='Reviewed admission or reporting dependency requires verification.'
        if status=='landed' and card not in published:
            status='awaiting report'
            evidence='Local receipt filed. The R48 report is due for publication.'
        rows[card]=dict(host=host,name=name,status=status,evidence=evidence,owner=record.get('owner','Sounding Line'),
                        result=record.get('result'),limit=record.get('limit'))
    charge,by_row,sealed=gear.balance()
    return dict(at=now(),rows=rows,free=gear.shared_slot_limit()-len(gear.resources.lease_paths()),
                reserved_or_charged=charge,by_row=by_row,sealed=sealed,
                ready=[c for c,v in rows.items() if v['status']=='ready'],attempts=attempts)


def render(s):
    ready=s['ready']
    free=max(0,s['free'])
    if free and not ready:
        line=f'The ready list is empty with {free} free shared CPU slots. '
        if datetime.now(timezone.utc)>=gear.FREEZE:
            line+='The Week 8 start window is closed.'
        else:
            line+='The remaining studies are in preparation or await the source or fixture named below.'
    elif ready:
        line=f'{len(ready)} studies are ready with {free} free shared CPU slots. Next ready: '+', '.join(ready)+'.'
    else:
        line='All shared CPU slots are occupied and the ready list is empty.'
    header='| Row | Study | Host | Status | Current evidence or next input | Owner |\n|---|---|---|---|---|---|\n'
    table=header+''.join(f"| {c} | {v['name']} | {v['host']} | {v['status']} | {v['evidence']} | {v['owner']} |\n" for c,v in s['rows'].items())
    dr=DESIGN/'README.md'
    dr.write_text('# Stage 15 · Week 8\n\n'+line+'\n\n'+table+
       '\n[Packet](PACKET.md) · [Originals and hashes](INTAKE.json) · [Round 37 handoff](../week6/THEORY_HANDOFF_R37.md) · [Live return](../../../exchange/WEEK8_RETURN.md).\n',
       encoding='utf8',newline='\n')
    contrary=read(STATE/'contrary.json') if (STATE/'contrary.json').exists() else []
    census=read(STATE/'census.json') if (STATE/'census.json').exists() else []
    landed=[(c,v) for c,v in s['rows'].items() if v.get('result')]
    lines=[line,'','# Week 8 return','','## Against, and clear','',*(
        contrary or ['No filed public comparison yet meets this condition.']),'','## Study roster','',table.rstrip(),'',
        '## Filed results','',*([f"- {c}. {v['result']} {v.get('limit') or ''}" for c,v in landed] or ['No row has landed yet.']),'',
        '## Sealed invocations','',f"{s['sealed']} of 30 are used or reserved. Week 8 CPU charges and outstanding reservations total {s['reserved_or_charged']:,.1f} seconds.",'']
    for c,jobs in s['attempts'].items():
        for name,term,live,sealed in sorted(jobs):
            if sealed:
                d=gear.ROOT/name
                if not (d/'SUBMITTED.json').exists() and (d/'COST.json').exists() and read(d/'COST.json').get('never_submitted'):
                    continue
                ret=read(d/'EXIT.json') if (d/'EXIT.json').exists() else {}
                lines.append(f"- {c}, {name}. "+(f"Exit {ret['code']}." if 'code'in ret else 'Reserved or in progress.'))
    lines+=['','## Unused sources','',*(census or ['ADM2 source and terms review is pending.']),'',
            'The campaign opened November 27 at 06:50 Pacific. New starts freeze November 29 at 08:00, the drain is at 10:00 and the final addendum is due at 11:00. The standing queue has a 15-minute local reader and a 25-minute owner check. The result ledger is separate from Week 7.','']
    RETURN.write_text('\n'.join(lines),encoding='utf8',newline='\n')


def clock():
    owner=STATE/'QUEUE_READER_OWNER.json'
    if owner.exists() and is_same_live_process(read(owner)['native']):
        raise RuntimeError('Week 8 reader already live')
    atomic(owner,dict(native=native_identity(),at=now(),source_sha256=filehash(Path(__file__)),interval_seconds=900))
    clockroot=gear.ROOT.parent/'drive-calendar-20261127-week8'
    clockroot.mkdir(exist_ok=True)
    while True:
        at=datetime.now(timezone.utc)
        s=snapshot()
        atomic(STATE/'QUEUE_READ.json',s)
        with (STATE/'queue_reads.jsonl').open('a',encoding='utf8') as stream:
            import json
            stream.write(json.dumps(dict(at=s['at'],free=s['free'],ready=s['ready'],sealed=s['sealed']))+'\n')
        for name,t in [('FINAL_START_FREEZE',gear.FREEZE),('DRAIN_DUE',gear.DRAIN),('FINAL_ADDENDUM_DUE',gear.FINAL)]:
            if at>=t and not (clockroot/(name+'.json')).exists():
                freeze(clockroot/(name+'.json'),dict(at=now(),due=t.isoformat(),calendar_only=True))
        if at>=gear.FINAL:
            return
        future=[(t-at).total_seconds() for t in (gear.FREEZE,gear.DRAIN,gear.FINAL) if t>at]
        time.sleep(min(900,*future))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['read','render','clock'])
    action=parser.parse_args().action
    STATE.mkdir(parents=True,exist_ok=True)
    if action=='clock':
        clock()
    elif action=='render':
        from tools.week8_return import render as render_public_return
        render_public_return()
    else:
        s=snapshot()
        print(s['at'], 'free',s['free'],'ready',s['ready'],'sealed',s['sealed'])
