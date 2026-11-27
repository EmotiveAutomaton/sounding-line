"""Add 0057 to the released next-prompt family tables after its full native replay."""
import argparse
from collections import defaultdict
import csv
from pathlib import Path
from statistics import median
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runners.drive.cards import week8_lag2 as replay
from runners.stage14.common import freeze,filehash,read

STAGE=ROOT/'results/phase_2_4_stage_15'
OLD=STAGE/'WEEK7'
HIST=ROOT/'.agent-state/drive-20261115/week7-phase1'
STATE=ROOT/'.agent-state/drive-20261127/week8'
CURRENT=STAGE/'raw/drive-week8-20261127'/replay.UNIT

def maybe_median(values):
    present=[v for v in values if v is not None]
    return median(present) if present else None

def summarize(cells):
    groups=defaultdict(list)
    for r in cells:
        groups[r['member'],r['family'],r['gap']].append(r)
    diaries=[]
    for (m,family,gap),rows in sorted(groups.items()):
        estimates=[r['estimate'] for r in rows]
        ratios=[r['ratio'] for r in rows]
        diaries.append(dict(member=m,family=family,gap=gap,cells=len(rows),
            identified=sum(v is not None for v in estimates),undecided=sum(r['reading']=='undecided' for r in rows),
            slope=maybe_median(estimates),ratio=maybe_median(ratios)))
    pooled=[]
    for family,gap in sorted({(r['family'],r['gap']) for r in diaries}):
        rows=[r for r in diaries if (r['family'],r['gap'])==(family,gap)]
        pooled.append(dict(family=family,gap=gap,contributing_diaries=sum(r['ratio'] is not None for r in rows),
            slope=maybe_median([r['slope'] for r in rows]),ratio=maybe_median([r['ratio'] for r in rows])))
    return diaries,pooled

def base():
    receipt=read(OLD/'LAG_NEXT_PROMPT_FAMILY_RETURN.json')
    file=OLD/'LAG_NEXT_PROMPT_FAMILY_RETURN_tables.json'
    old=read(file)
    if not receipt['full_write_through'] or receipt['tables']!=filehash(file):
        raise ValueError('Original family table differs from its filed receipt')
    if (old['restricted_member_excluded']!='0049' or any(r['member'] in ('0049','0057') for r in old['cells'])
            or summarize(old['cells'])!=(old['diaries'],old['pooled'])):
        raise ValueError('Original public roster or equal-diary family computation differs')
    return old

def assemble():
    old=base()
    done=read(CURRENT/'COMPLETE.json')
    if not done.get('verified') or done.get('unit')!=replay.UNIT:
        raise ValueError('The original replay has no verified terminal')
    checks=replay.check(replay.UNIT,CURRENT)
    if checks!=done['results'] or checks['cells']!=649:
        raise ValueError('The replay does not authenticate all 649 first-pass cells')
    source=HIST/'ATL_CLOCK_CORRECTION/items.csv'
    if filehash(source)!=old['mapping_sha256']:
        raise ValueError('Atlas mapping changed')
    with source.open(encoding='utf8',newline='') as stream:
        mapping={r['event']+'/'+r['feeling']:r for r in csv.DictReader(stream) if r['member']=='0057'}
    actual=read(CURRENT/'verify_INTERNAL.json')['cells']
    cells=list(old['cells'])
    for key,result in sorted(actual.items()):
        item=mapping[key]
        for gap in ('all','short'):
            cells.append(dict(member='0057',cell=key,family=item['feeling_family'],same_prompt=float(item['point']),
                gap=gap,reading=result['reading'],**result[gap]))
    diaries,pooled=summarize(cells)
    freeze(STATE/'LAG2_EXTENDED_FAMILY_TABLES.json',dict(cells=cells,diaries=diaries,pooled=pooled,
           source_mapping=filehash(source),terminal=filehash(CURRENT/'COMPLETE.json'),
           prior_table=filehash(OLD/'LAG_NEXT_PROMPT_FAMILY_RETURN_tables.json'),restricted_member_excluded='0049'))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--verify-prior',action='store_true')
    options=parser.parse_args()
    if options.verify_prior:
        v=base();print('Prior public cells, diary rows and pooled rows:',len(v['cells']),len(v['diaries']),len(v['pooled']))
    else:
        assemble()
