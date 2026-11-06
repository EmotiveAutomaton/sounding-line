"""Existing AUTH balanced prompt-matched pairs; no scores or API access.

DESIGN CHECK: LESSONS 2-5; CONTROLS 4-7; AUTH_PAIRS.md. NULL/ALTERNATIVE
both require exact truth, coverage, prompt matching and no duplicate pairs.
Absent support refuses. Native examples are not human authorship evidence.
"""
from collections import Counter,defaultdict
from itertools import combinations
from pathlib import Path
from runners.stage14.common import read,filehash,digest
from .timing_p6 import gzread,write_equal

GENRES=('argumentative','creative')


def configuration(mode):
    if mode not in ('constructed','full'):raise ValueError('fixed mode')
    return dict(mode=mode,seed=20261102,blocks_per_genre=24 if mode=='constructed' else 1000,
                writers=4 if mode=='constructed' else 24,calibration_pairs=8 if mode=='constructed' else 100)


def payload_key(a,b):return digest(sorted((a['typed']['text'],b['typed']['text'])))


def draw(sessions,config):
    mapping={r['session']:r for r in sessions}
    if len(mapping)!=len(sessions) or len({r['writer'] for r in sessions})!=config['writers']:raise ValueError('identity coverage')
    if any(not r['source_exact'] or not r['typed']['text'].strip() or not 0<r['typed']['payload_words']<=400 for r in sessions):raise ValueError('ineligible source')
    if len({r['typed']['text'] for r in sessions})!=len(sessions):raise ValueError('duplicate source text')
    if set(r['genre'] for r in sessions)!=set(GENRES):raise ValueError('genre coverage')
    rows=[];used=set();skipped=Counter();n=config['blocks_per_genre']
    for genre in GENRES:
        groups=defaultdict(list);prompts=defaultdict(list)
        for r in sorted(sessions,key=lambda r:r['session']):
            if r['genre']==genre:groups[r['writer']].append(r);prompts[r['prompt']].append(r)
        candidates=[(a,b) for group in groups.values() for a,b in combinations(group,2) if a['prompt']!=b['prompt']]
        candidates.sort(key=lambda ab:digest([config['seed'],genre,ab[0]['session'],ab[1]['session']]))
        blocks=0
        for a,b in candidates:
            if payload_key(a,b) in used:continue
            donors=sorted((r for r in prompts[b['prompt']] if r['writer']!=a['writer']),key=lambda r:digest([config['seed'],a['session'],b['session'],r['session']]))
            d=next((r for r in donors if payload_key(a,r) not in used),None)
            if d is None:skipped[genre]+=1;continue
            block=digest([genre,blocks,a['session'],b['session'],d['session']])
            for right,truth in ((b,True),(d,False)):
                key=payload_key(a,right);used.add(key)
                rows.append(dict(pair_id=key,block=block,genre=genre,left=a['session'],right=right['session'],same_writer=truth,
                                 prompts=[a['prompt'],right['prompt']],texts=[a['typed']['text'],right['typed']['text']]))
            blocks+=1
            if blocks==n:break
        if blocks!=n:raise ValueError('insufficient matched pair support')
    summary=validate(rows,sessions,config)
    arguments=[r['pair_id'] for r in rows if r['genre']=='argumentative'];c=config['calibration_pairs']
    selection=dict(calibration=arguments[:c],fresh=arguments[c:2*c],primary_policy='Exclude exactly the calibration sets actually used; unused fresh reserve remains eligible.')
    if len(selection['fresh'])!=c:raise ValueError('fresh calibration support')
    return rows,selection,dict(summary,unsupported_candidates=dict(skipped))


def validate(rows,sessions,config):
    by={r['session']:r for r in sessions};seen=set();blocks=defaultdict(list);counts=Counter();authors=defaultdict(set)
    if len(rows)!=4*config['blocks_per_genre']:raise ValueError('pair coverage')
    for r in rows:
        a,b=by[r['left']],by[r['right']]
        if a['session']==b['session'] or a['genre']!=b['genre'] or r['genre']!=a['genre'] or a['prompt']==b['prompt']:raise ValueError('invalid comparison')
        if type(r['same_writer']) is not bool or r['same_writer']!=(a['writer']==b['writer']):raise ValueError('wrong truth')
        if r['texts']!=[a['typed']['text'],b['typed']['text']] or r['prompts']!=[a['prompt'],b['prompt']]:raise ValueError('text/prompt changed')
        key=digest(sorted(r['texts']))
        if key!=r['pair_id'] or key in seen:raise ValueError('duplicate/misbound pair')
        seen.add(key);blocks[r['block']].append(r);counts[(r['genre'],r['same_writer'])]+=1
        if r['same_writer']:authors[r['genre']].add(a['writer'])
    for pair in blocks.values():
        if len(pair)!=2 or [r['same_writer'] for r in pair]!=[True,False] or pair[0]['left']!=pair[1]['left'] or pair[0]['prompts']!=pair[1]['prompts'] or pair[0]['genre']!=pair[1]['genre']:raise ValueError('unmatched truth block')
    expected={r['writer'] for r in sessions}
    if any(counts[(g,truth)]!=config['blocks_per_genre'] for g in GENRES for truth in (True,False)):raise ValueError('unbalanced pairs')
    if any(authors[g]!=expected for g in GENRES):raise ValueError('missing writer in genre')
    return dict(pairs=len(rows),blocks=len(blocks),writers=len(expected),by_genre={g:dict(same=counts[(g,True)],different=counts[(g,False)]) for g in GENRES},exact_prompt_matching=True,duplicate_pairs=0,scientific_admission=False,paid_admission=False)


def fixture():
    return [dict(session=f'{g}-{w}-{p}',writer=str(w),genre=g,prompt=str(p),source_exact=True,
                 typed=dict(text=f'Constructed {g} writer{w} prompt{p}.',payload_words=4)) for g in GENRES for w in range(4) for p in range(4)]


def load(inputs):
    if set(inputs)!={'source_root','source_landing'}:raise ValueError('fixed source')
    root=Path(inputs['source_root']);c=read(root/'COMPLETE.json');land=read(inputs['source_landing'])
    if not c['fresh_process_verified'] or not land['full_write_through'] or land['complete_sha256']!=filehash(root/'COMPLETE.json'):raise ValueError('unlanded source')
    for name in ('PLAN.json','output/INDEX.json','output/SUMMARY.json'):
        if filehash(root/name)!=c['outputs'][name]:raise ValueError('source changed')
    index=read(root/'output/INDEX.json');result=[]
    if len(index)!=990:raise ValueError('original cohort only')
    for r in index:
        p=(root/'output'/r['file']).resolve();p.relative_to((root/'output').resolve())
        if filehash(p)!=r['sha256'] or c['outputs']['output/'+r['file']]!=r['sha256']:raise ValueError('session changed')
        value=gzread(p)
        if value['session']!=r['session']:raise ValueError('session binding')
        result.append(value)
    return result


def run(output,inputs,config,verification=False):
    if config!=configuration(config['mode']):raise ValueError('changed allocation')
    if config['mode']=='constructed' and inputs:raise ValueError('no fixture external inputs')
    sessions=fixture() if config['mode']=='constructed' else load(inputs)
    rows,selection,summary=draw(list(reversed(sessions)) if verification else sessions,config)
    values={'PRIVATE_PAIRS.json':rows,'SELECTION.json':selection,'SUMMARY.json':summary,
            'PROVIDER_TEXTS.json':[dict(pair_id=r['pair_id'],texts=r['texts']) for r in rows]}
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    for name,value in values.items():
        if verification:
            if read(out/name)!=value:raise ValueError('fresh allocation replay differs')
        else:write_equal(out/name,value)
    return dict(verified=True,independent_identity_prompt_checks=True,scientific_admission=False) if verification else dict(status='complete',scientific_admission=False)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
