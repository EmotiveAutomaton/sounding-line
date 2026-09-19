"""Offline packet materialization; requires terminal queue, never dispatches calls.

DESIGN CHECK: LESSONS 3-5. NULL/ALTERNATIVE: incomplete cells remain unavailable;
raw semantic reconstruction and source checks precede comparisons. Illustrations
follow frozen role rules, with absent effects labeled, not invented.
"""
import argparse
import json
import math
from pathlib import Path
from .common import RAW,ROOT,check_pins,digest,freeze,read

RULES=dict(version=1,selection='First distinct unit by stable identifier satisfying each predicate; fallback first unused reference case with absent role explicitly labeled',
    roles=['useful reconstruction','wrong plausible reconstruction','selective prompt intervention','nonselective prompt intervention','context correction','unresolved case'],
    timing='frozen before complete neural scientific cells; development used only if corresponding test cell unavailable',
    useful='persistent expected Brier lower than raw history on same unit/encounter',
    wrong='modal action wrong with maximum elicited probability at least .5',
    selective='maker-observation belief argmax changes correctly while reader-only belief matches correct raw belief',
    nonselective='reader-only belief changes despite unchanged target',
    correction='corrected-context expected Brier lower than wrong-context on same unit/encounter',
    unresolved='largest Shannon entropy among remaining valid forecasts; uncertainty is not calibration',
    scope='prompt interventions are distinct from unperformed activation interventions; fallback never asserts the missing effect')


def prepare(root=RAW):return freeze(Path(root)/'PACKET_RULES.json',RULES)


def verify_extension(kind,split,root):
    from .extensions import long_unit,requests,summary_call
    from .repair import call
    from .consumer import measures,summarize,target_for
    out=Path(root)/'repair-v1'/f'extension-{kind}-{split}';receipt=read(out/'COMPLETE.json')
    public=read(Path(root)/'fixture'/f'{split}-public.json')
    if kind=='history':
        pairs=[long_unit(split,i) for i in range(len(public))];public=[u for u,t in pairs]
        truth=[dict(unit=u['unit'],queries=[t]) for u,t in pairs]
        if public!=read(out/'PUBLIC.json') or truth!=read(out/'EVALUATOR.json'):raise ValueError('long history changed')
    else:truth=read(Path(root)/'fixture'/f'{split}-evaluator.json')
    expected=[]
    for i,u in enumerate(public):
        summary=None
        if kind=='summary':
            p=out/'summaries'/f'{i:03d}'
            if not (p/'COMPLETE.json').exists():raise ValueError('incomplete summary')
            summary=summary_call(u['queries'][(i//4)%4]['observation'],p,root)
        for arm,question,q,text,view in requests(kind,u,public[(i+1)%len(public)],i,summary):
            path=out/'calls'/f'{i:03d}-{arm}-{question}'
            if text is not None:
                if not (path/'COMPLETE.json').exists():raise ValueError('incomplete extension forecast')
                result=call(text,4 if question=='action' else 2,path,root)
            else:result=dict(valid=False,probabilities=None,seconds=0,error='upstream summary invalid',cost={})
            expected.append(dict(unit=u['unit'],cluster=u['cluster'],encounter=q,arm=arm,question=question,
                observation=view['queries'][q]['observation'],**result))
    if expected!=read(out/'PREDICTIONS.json') or digest(expected)!=receipt['predictions_sha256']:raise ValueError('extension semantic replay differs')
    keyed={(u['unit'],t['encounter']):t for u in truth for t in u['queries']}
    scored=[dict(r,score=measures(r['probabilities'],*target_for(r,keyed[(r['unit'],r['encounter'])]))) for r in expected]
    comparison=summarize(scored,'raw_history')
    if comparison!=read(out/'COMPARISON.json') or digest(comparison)!=receipt['comparison_sha256']:raise ValueError('extension scoring replay differs')
    return comparison


def illustrations(blocks):
    candidates=[]
    for name,rows in blocks.items():
        keyed={(r['unit'],r['encounter'],r['arm'],r['question']):r for r in rows}
        for r in rows:
            if not r['score']['valid']:continue
            def sibling(arm):return keyed.get((r['unit'],r['encounter'],arm,r['question']))
            raw=sibling('raw_history');flags=[]
            if r['arm']=='persistent' and raw and r['score']['expected_brier']<raw['score']['expected_brier']:flags.append(RULES['roles'][0])
            if not r['score']['modal_accuracy'] and max(r['probabilities'])>=.5:flags.append(RULES['roles'][1])
            if r['question']=='belief':
                reader=sibling('reader_only')
                if r['arm']=='maker_observation' and raw and reader and all(x['score']['modal_accuracy'] for x in [r,raw,reader]) and r['target']!=raw['target']:flags.append(RULES['roles'][2])
                if r['arm']=='reader_only' and raw and r['target']==raw['target'] and max(range(2),key=r['probabilities'].__getitem__)!=max(range(2),key=raw['probabilities'].__getitem__):flags.append(RULES['roles'][3])
            wrong=sibling('wrong_context')
            if r['arm']=='corrected_context' and wrong and r['score']['expected_brier']<wrong['score']['expected_brier']:flags.append(RULES['roles'][4])
            entropy=-sum(p*math.log(p) for p in r['probabilities'] if p>0)
            candidates.append(dict(block=name,row=r,flags=flags,entropy=entropy))
    result=[];used=set()
    for role in RULES['roles']:
        available=[c for c in candidates if c['row']['unit'] not in used]
        if not available:raise ValueError('six distinct inspectable cases unavailable')
        eligible=[c for c in available if role in c['flags']]
        if role==RULES['roles'][-1]:eligible=sorted(available,key=lambda c:(-c['entropy'],c['row']['unit']))
        fallback=[c for c in available if c['row']['arm'] in ('raw_history','raw_facts')]
        chosen=(eligible[0] if role==RULES['roles'][-1] else min(eligible or fallback or available,key=lambda c:(c['row']['unit'],c['row']['encounter'],c['block'],c['row']['arm'])))
        used.add(chosen['row']['unit'])
        result.append(dict(role=role,realized=bool(eligible),selection_status='frozen predicate' if eligible else 'effect absent; reference fallback',
            **chosen,state_status='observations are constructed public facts; candidate traits inferred; target is evaluator truth',
            interpretation='inspectable case, not a separate performance estimate or calibrated confidence'))
    return result


def collect(root=RAW):
    from . import local_reader
    from .consumer import run as audit
    from .executable import run as exact
    from .revision import run as revision
    from .workflow import verify_admission
    root=Path(root);plan=read(root/'QUEUE-repair-v1.json');terminal=read(root/'queue/QUEUE-repair-v1/COMPLETE.json')
    if terminal['status']!='complete' or terminal['manifest_sha256']!=digest(plan):raise ValueError('queue not terminal')
    check_pins(plan['source_pins'])
    def forbidden(*args,**kwargs):raise AssertionError('packet cannot make inference or network calls')
    local_reader.api=forbidden;verify_admission(root)
    comparisons={};blocks={}
    for split in ['dev','test']:
        exact(root,split);revision(split,root)
        for branch in ['M0-executable','M0-revision']:comparisons[f'{branch}-{split}']=read(root/branch/split/'COMPARISON.json')
    dispositions={d['id']:d for d in terminal['dispositions']}
    for job in plan['jobs']:
        if dispositions[job['id']]['status']!='complete':continue
        if job['kind']=='core':
            audit(job['branch'],job['split'],root)
            folder=root/'repair-v1'/f'{job["branch"]}-ollama-{job["split"]}'
            comparisons[job['id']]=read(folder/'COMPARISON.json')
            # Prefer test by replacing the same branch's development case roster.
            blocks[job['branch']+'-selected']=read(folder/'SCORED.json')
        else:comparisons[job['id']]=verify_extension(job['kind'],job['split'],root)
    cases=illustrations(blocks)
    for case in cases:
        r=case['row'];split,index=r['unit'].rsplit('-',1);branch=case['block'].split('-')[0]
        directory=root/'repair-v1'/f'{branch}-ollama-{split}'/'calls'/f'{int(index):03d}-{r["encounter"]}-{r["arm"]}-{r["question"]}'
        case['request']=read(directory/'REQUEST.json')
        case['saved_model_output']=read(directory/'RAW.json')['message']['content']
        case['model_output_status']='recorded model explanation and elicited forecast; explanation is not verified internal reasoning'
    freeze(root/'packet/COMPARISONS.json',comparisons);freeze(root/'packet/CASES.json',cases)
    return freeze(root/'packet/INTEGRITY.json',dict(status='complete',comparisons=len(comparisons),cases=len(cases),
        comparison_sha256=digest(comparisons),cases_sha256=digest(cases),rules_sha256=digest(read(root/'PACKET_RULES.json')),
        dispositions=terminal['dispositions'],scope='offline semantic materialization; final finding write-through and report still required'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--root',type=Path,default=RAW);a=p.parse_args()
    print(prepare(a.root) if a.prepare else collect(a.root))
