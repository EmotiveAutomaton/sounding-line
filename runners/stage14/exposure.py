"""SL7/SL10 identity-only historical audit, without outcome-driven selection.

DESIGN CHECK: LESSONS 2-5. NULL: an unmatched archived identifier is UNKNOWN,
never fresh. ALTERNATIVE: source-session/ordinal joins witness actual model use.
All writers remain exposed. Partial archive coverage cannot prove never scored.
"""
from collections import Counter,defaultdict
from pathlib import Path
import re
from .common import REPO,read,freeze,digest,filehash
from runners.stage11.core import digest as legacy_digest

def run(card,out,raw,tick):
    roster=read(raw/'jobs'/card['requires'][0]/'ROSTER.json');sessions={legacy_digest({'coauthor-session':Path(r['path']).stem}):r for r in roster}
    native=REPO/'results/phase_2_4_stage_11_1/raw/NATIVE_OPPORTUNITIES.json';old=read(native);aliases={};pins={str(native.relative_to(REPO)):filehash(native)}
    for rows in old.values():
        for r in rows:
            if r['session'] in sessions:
                s=sessions[r['session']];aliases[r['key']]=digest([s['session'],r['ordinal']])
    for p in sorted((REPO/'results/phase_2_4_stage_13/raw/sources').glob('coauthor-v3-*.json')):
        pins[str(p.relative_to(REPO))]=filehash(p)
        for r in read(p):
            if r['session'] in sessions:aliases[r['key']]=digest([sessions[r['session']]['session'],r['ordinal']])
    witness=defaultdict(set);scanned=0;unreadable=[]
    def keys(value):
        if isinstance(value,dict):
            for k,v in value.items():
                if k in ('key','case_id','unit','source_id','id') and isinstance(v,str) and v in aliases:yield v
                if k in aliases:yield k
                if isinstance(v,(dict,list)):yield from keys(v)
        elif isinstance(value,list):
            for v in value:yield from keys(v)
    for stage in ('9','10','11','11_1','11_2','12','13'):
        root=REPO/f'results/phase_2_4_stage_{stage}/raw'
        if not root.exists():continue
        for p in root.rglob('*.json'):
            # Read only persisted model/scorer outputs, not source truth/rosters.
            if p.name not in ('PREDICTIONS.json','ROWS.json','RAW.json','RESPONSE.json','RECEIPT.json'):continue
            if p.stat().st_size>64*1024**2:unreadable.append(dict(path=str(p.relative_to(REPO)),reason='bounded audit size'));continue
            try:value=read(p)
            except (ValueError,OSError):unreadable.append(dict(path=str(p.relative_to(REPO)),reason='unreadable'));continue
            found=set(keys(value))
            for part in p.parts:
                for k in re.findall(r'[0-9a-f]{64}',part):
                    if k in aliases:found.add(k)
            scanned+=1
            if found:
                rel=str(p.relative_to(REPO)).replace('\\','/');pins[rel]=filehash(p)
                for k in found:witness[aliases[k]].add(rel)
            if scanned%1000==0:tick(dict(output_records_inspected=scanned,witnessed_events=len(witness)))
    ledger=[]
    for s in roster:
        for r in read(raw/'jobs'/card['requires'][0]/'reader'/f"{s['session']}.json"):
            ledger.append(dict(key=r['key'],writer=s['writer'],session=s['session'],ordinal=r['ordinal'],writer_exposure='historically exposed',event_exposure='MODEL_OR_SCORER_OUTPUT_WITNESSED' if r['key'] in witness else 'UNKNOWN_NOT_PROVEN_UNEXPOSED',witnesses=sorted(witness[r['key']]),pretraining='historical public corpus predates current reader packages; not fresh'))
    freeze(out/'EVENT_LEDGER.json',ledger);freeze(out/'SOURCE_PINS.json',pins);freeze(out/'EXCLUSIONS.json',unreadable)
    freeze(out/'SUMMARY.json',dict(events=len(ledger),writers=len({r['writer'] for r in ledger}),events_by_status=dict(Counter(r['event_exposure'] for r in ledger)),source_aliases=len(aliases),inspected_output_files=scanned,unreadable_files=len(unreadable),fresh_events_certified=0,
        scope='positive identity witnesses only; output naming and older unmapped schemas limit negative claims; absence of a match is unknown, never never-scored'))
