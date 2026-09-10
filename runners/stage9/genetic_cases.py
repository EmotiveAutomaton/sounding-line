"""Verified local manuscript changes, with all earlier pilot wording retained.

DESIGN CHECK: H04/X01/X02/X03/X05; LESSONS 2--5. NULL: ambiguous markup,
changed acquired bytes, repeated exposed replacements or absent alternatives refuse.
ALTERNATIVE: a withheld documented local addition is offered from a verified earlier
local reading. One famous work supplies qualitative correspondence only; no global
chronology, independent-work inference, fresh reserve or historical intent claim.
"""
from .common import REPO,ROOT,digest,file_hash,read
from .split_guard import Separation,normalized_evidence
from .tei import replacements


def offered(case,pool):
    true=case['local_after'];before=case['local_before']
    candidates=sorted({r['local_after'] for r in pool if normalized_evidence(r['local_after'])!=normalized_evidence(true)},
        key=lambda text:(abs(len(text.split())-len(true.split())),digest([before,text])))[:3]
    if len(candidates)!=3:raise ValueError('insufficient distinct manuscript replacements')
    options={'choice_'+str(i):text for i,text in enumerate(sorted([true,*candidates],key=lambda text:digest([before,text])))}
    evidence={'prefix':'A local manuscript reading before a documented revision:\n'+before+'\nA possible replacement is:\n','options':options}
    truth=next(k for k,v in options.items() if v==true)
    return {'key':case['key'],'unit':case['work'],'evidence':evidence,'truth':truth,'case':case,
        'candidate_design':'documented replacement and three alternatives matched first on target word count; order depends on visible text',
        'claim_ceiling':'qualitative local correspondence in one famous work, with memorization unresolved'}


def inputs(scope):
    if scope not in ('pilot','scientific'):raise ValueError('explicit genetic source scope required')
    prepared=ROOT/'private/prepared/sga';identity=read(prepared/'IDENTITY.json');old=read(prepared/'tasks.json');cases=read(prepared/'cases.json')
    receipt=read(ROOT/'intake/SGA_PREPARATION.json');cross_root=ROOT/'private/prepared/cross-source-v2';cross=Separation.verified(cross_root)
    if receipt['identity_sha256']!=digest(identity) or receipt['local_replacements']!=len(cases) or identity['source']!=file_hash(REPO/'runners/stage9/tei.py'):
        raise ValueError('genetic preparation identity/count/source changed')
    if identity['selected_keys']!=[r['key'] for r in old] or len(old)!=24 or {r['work'] for r in cases}!={'Frankenstein manuscripts'}:
        raise ValueError('original genetic exposure or work roster changed')
    if 'sga:Frankenstein' not in cross.groups or not cross.groups['sga:Frankenstein']['previously_exposed']:
        raise ValueError('one-work source exposure absent from overlap inventory')
    rebuilt=[];source_counts=[]
    for row in receipt['source_counts']:
        if 'sha256' not in row:
            source_counts.append(row);continue
        raw=ROOT/'private/intake/objects'/row['sha256']
        if file_hash(raw)!=row['sha256']:raise ValueError('acquired manuscript source changed')
        found,counts=replacements(raw.read_bytes(),row['sha256'])
        if any(row[k]!=v for k,v in counts.items()):raise ValueError('actual manuscript parsing counts differ')
        rebuilt.extend(case|{'source_path':row['path']} for case in found);source_counts.append(row)
    rebuilt.sort(key=lambda r:digest([90604,r['key']]))
    if rebuilt!=cases:raise ValueError('canonical local readings do not reconstruct from acquired TEI')
    excluded=[]
    if scope=='pilot':selected=old[:2]
    else:
        exposed={normalized_evidence(text) for r in old for text in [r['case']['local_before'],*r['evidence']['options'].values()]}
        pool=[]
        for case in cases:
            if case['key'] in identity['selected_keys'] or any(normalized_evidence(case[k]) in exposed for k in ('local_before','local_after')):
                excluded.append({'key':case['key'],'reason':'earlier pilot source or offered replacement wording'});continue
            pool.append(case)
        chosen=sorted(pool,key=lambda r:digest(['s9-genetic-scientific-order',r['key']]))[:24]
        if not chosen:raise ValueError('no unscored local source remains after pilot wording exclusion')
        selected=[offered(case,pool) for case in chosen]
        excluded.extend({'key':r['key'],'reason':'outside fixed bounded qualitative sample'} for r in pool if r not in chosen)
    validate(selected)
    return selected,{'preparation_sha256':file_hash(prepared/'IDENTITY.json'),'old_tasks_sha256':file_hash(prepared/'tasks.json'),
        'source_cases_sha256':file_hash(prepared/'cases.json'),'cross_source_complete_sha256':file_hash(cross_root/'COMPLETE.json'),
        'source_counts':source_counts,'source_dependency_component':sorted(cross.connected({'sga:Frankenstein'})),
        'selected_keys':[r['key'] for r in selected],'exclusions':excluded,'scope':scope,'independent_works':1,
        'data_scope':'already exposed manuscript corpus; pilot wording excluded from scientific targets and distractors; no fresh reserve',
        'reserve_payload_parsed':False,'famous_text_memorization':'unresolved, no training-corpus exclusion established',
        'temporal_scope':'local deletion precedes addition only; never global manuscript chronology'}


def validate(rows):
    if not rows or len({r['key'] for r in rows})!=len(rows):raise ValueError('complete distinct genetic tasks required')
    for row in rows:
        case=row['case'];evidence=row['evidence'];options=evidence['options']
        if set(evidence)!={'prefix','options'} or len(options)!=4 or len({normalized_evidence(v) for v in options.values()})!=4:
            raise ValueError('genetic reader evidence/support differs')
        expected='A local manuscript reading before a documented revision:\n'+case['local_before']+'\nA possible replacement is:\n'
        if evidence['prefix']!=expected or options.get(row['truth'])!=case['local_after'] or row['key']!=case['key'] or row['unit']!=case['work']:
            raise ValueError('genetic truth, source unit or earlier text differs')
        if not case['local_before'] or max(map(len,[case['local_before'],*options.values()]))>4096:
            raise ValueError('local genetic text outside declared reader envelope')
