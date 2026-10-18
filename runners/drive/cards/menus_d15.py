"""D15 crossed observed-response model and coarse/fine distance reliability.

DESIGN CHECK: LESSONS 3-5 read 2026-10-18. Under a stable prompt-conditional
writer plant, fine profiles can reproduce across session halves beyond coarse
rates. Shuffling outcomes within prompt/setting removes persistent writer
structure while retaining common effects. Pair distances share writers: only
writer-node bootstrap is used, excluding pairs of copies of the same writer.
Constant distance vectors, aliased variance components or >5% undefined draws
are invalid. Shared states_v2 gives every valid signed contrast an exact band.
"""
from __future__ import annotations
from collections import Counter,defaultdict
from pathlib import Path
import hashlib
import math
import time
import numpy as np

from . import menus_d12 as scores
from . import menus_crossed_stats as crossed
from . import states_v2 as states
from .menus_p8 import SETTINGS
from .menus_io import read,write,sha256,input_hashes,assert_equal,canonical
from .timing_census import session_paths

CONFIG=dict(seed=20261018,bootstrap=2000,minimum_writers=4,maximum_undefined_fraction=.05)
ACTIONS=('accept','edit','dismiss','ignore')
GROUPS=('writer','prompt','setting','writer_prompt')


def authenticate(inputs):
    scores.authenticate(inputs)
    complete=read(inputs['foundation_complete']);plan=read(inputs['foundation_plan'])
    if complete.get('status')!='COMPLETE' or complete.get('plan_sha256')!=sha256(inputs['foundation_plan']):
        raise ValueError('P2 foundation plan changed or incomplete')
    name=Path(inputs['sessions']).resolve().relative_to(Path(inputs['repo_root']).resolve()).as_posix()
    if plan['pins'].get(name)!=sha256(inputs['sessions']):raise ValueError('P2 prepared roster changed')


def rows_from_inputs(inputs):
    authenticate(inputs);sessions,producer=scores.load(inputs);writers,by_key=scores.prepare(sessions,producer)
    metadata={s['session']:s for group in writers.values() for s in group}
    halves={s['session']:i%2 for group in writers.values() for i,s in enumerate(group)}
    rows=[];support=[];seen=set();counts=Counter()
    for indexed,path in session_paths(inputs):
        timeline=read(path);session=metadata[indexed['session']];seen.add(session['session'])
        if (timeline['session'],timeline['writer'],timeline['prompt'])!=(session['session'],session['writer'],session['prompt']):
            raise ValueError('P2/source identity mismatch')
        decision_map={r['key']:r for r in timeline['decisions']}
        if len(decision_map)!=len(timeline['decisions']) or set(decision_map)!={r['key'] for r in session['rows']}:
            raise ValueError('P2 decision coverage differs')
        for source in sorted(session['rows'],key=lambda r:(r['ordinal'],r['key'])):
            decision=decision_map[source['key']];offered=by_key[source['key']]
            tuples=[tuple(r['decoding_numeric'][k] for k in SETTINGS) for r in offered]
            if len(set(tuples))!=1:raise ValueError('decoding setting differs inside menu')
            setting=tuples[0]
            if any(v is not None and (isinstance(v,bool) or not math.isfinite(v)) for v in setting):
                raise ValueError('nonfinite decoding tuple')
            if decision['handling']!=source['handling'] or decision['ordinal']!=source['ordinal'] or source['handling'] not in ACTIONS:
                raise ValueError('P2 handling identity mismatch')
            missing=sum(v is None for v in setting);counts['decisions']+=1;counts['missing_setting_decisions']+=bool(missing)
            observed=decision['latency_kind']=='observed_selection_or_close'
            latency=decision['latency_seconds']
            if not math.isfinite(latency) or latency<0:raise ValueError('invalid menu latency')
            interactions=decision['interactions'];counts['latency_'+decision['latency_kind']]+=1
            rows.append(dict(key=source['key'],writer=session['writer'],session=session['session'],
                prompt=session['prompt'],half=halves[session['session']],handling=source['handling'],
                setting=canonical(setting),setting_values=list(setting),missing_settings=missing,
                latency_log1p=math.log1p(latency) if observed else None,
                hover_log1p=math.log1p(sum('hover' in r['event'] for r in interactions)),
                typed_log1p=math.log1p(decision['typed_since_previous_decision'])))
        support.append(dict(session=session['session'],writer=session['writer'],prompt=session['prompt'],
                            half=halves[session['session']],decisions=len(session['rows'])))
    if seen!=set(metadata):raise ValueError('P2/session roster coverage differs')
    return sorted(rows,key=lambda r:r['key']),dict(counts=dict(counts),sessions=sorted(support,key=lambda r:r['session']),
        prompts=sorted({r['prompt'] for r in rows}),settings=sorted({r['setting'] for r in rows}),
        scope='Over writers conditional on the exact observed prompt roster; missing decoding values are explicit tuple levels.',
        pause_features='D17 slow-mixture pause feature unavailable after its failed card; not replaced by API-wait-contaminated intervals.')


def encode(rows):
    labels=[[r['writer'] for r in rows],[r['prompt'] for r in rows],[r['setting'] for r in rows],
            [canonical([r['writer'],r['prompt']]) for r in rows]]
    encoded=[crossed.encode(g) for g in labels]
    y=np.eye(4)[[ACTIONS.index(r['handling']) for r in rows]]
    return y,[g for g,_ in encoded],[n for _,n in encoded]


def serial_fit(result):
    return {k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in result.items()}


def fitted_profiles(rows,prompts):
    if not rows:return dict(valid=False,reason='empty session half',profiles={})
    y,groups,names=encode(rows)
    try:
        fit=crossed.fit(y,groups,GROUPS);blup=crossed.blup(y,groups,fit)
    except ValueError as exc:
        return dict(valid=False,reason=str(exc),profiles={},design_groups=[len(n) for n in names])
    writer_index={w:i for i,w in enumerate(names[0])};wp_index={wp:i for i,wp in enumerate(names[3])}
    profiles={}
    for w,j in writer_index.items():
        fine=[]
        for prompt in prompts:
            effect=blup['effects'][0][j].copy();wp=canonical([w,prompt])
            if wp in wp_index:effect+=blup['effects'][3][wp_index[wp]]
            fine.extend(effect.tolist())
        mask=groups[0]==j
        profiles[w]=dict(fine=fine,coarse=y[mask].mean(axis=0).tolist(),decisions=int(mask.sum()),
                        observed_prompts=sorted({rows[i]['prompt'] for i in np.flatnonzero(mask)}))
    return dict(valid=True,profiles=profiles,fit=serial_fit(fit),intercepts=blup['intercepts'],
                interpretation='Fine coordinates are BLUP writer plus writer-by-prompt effects, after common prompt and decoding effects; no calibrated probability claim.')


def distance_statistic(profiles,indices=None):
    names=sorted(profiles)
    matrices=[]
    for kind in ('fine','coarse'):
        for half in (0,1):
            vectors=np.asarray([profiles[name][half][kind] for name in names])
            matrices.append(np.sqrt(np.mean((vectors[:,None,:]-vectors[None,:,:])**2,axis=2)))
    return distances_from_matrices(matrices,indices)


def distances_from_matrices(matrices,indices=None):
    index=np.arange(len(matrices[0])) if indices is None else np.asarray(indices,int)
    if len(set(index))<3:return None,None,None
    a,b=np.triu_indices(len(index),1);mask=index[a]!=index[b];a=index[a[mask]];b=index[b[mask]]
    fine=scores.correlation(matrices[0][a,b],matrices[1][a,b])
    coarse=scores.correlation(matrices[2][a,b],matrices[3][a,b])
    return fine-coarse if fine is not None and coarse is not None else None,fine,coarse


def summarize_profiles(halves,config):
    if any(not h['valid'] for h in halves):
        invalid=scores.interval(None,[],config)
        return dict(primary=invalid,reason=[h.get('reason') for h in halves],writers=0)
    writers=sorted(set(halves[0]['profiles'])&set(halves[1]['profiles']))
    if len(writers)<config['minimum_writers']:
        return dict(primary=scores.interval(None,[],config),reason=['insufficient paired-half writers'],writers=len(writers))
    profiles={w:[h['profiles'][w] for h in halves] for w in writers}
    matrices=[]
    for kind in ('fine','coarse'):
        for half in (0,1):
            vectors=np.asarray([profiles[w][half][kind] for w in writers])
            matrices.append(np.sqrt(np.mean((vectors[:,None,:]-vectors[None,:,:])**2,axis=2)))
    point,fine,coarse=distances_from_matrices(matrices);rng=np.random.default_rng(config['seed'])
    draws=[];fine_draws=[];coarse_draws=[]
    for _ in range(config['bootstrap']):
        a,b,c=distances_from_matrices(matrices,rng.integers(len(writers),size=len(writers)))
        draws.append(a);fine_draws.append(b);coarse_draws.append(c)
    return dict(primary=scores.interval(point,draws,config),fine_reliability=scores.interval(fine,fine_draws,config),
                coarse_reliability=scores.interval(coarse,coarse_draws,config),writers=len(writers),
                paired_writers=writers,unsupported_writers=sorted((set(halves[0]['profiles'])|set(halves[1]['profiles']))-set(writers)),
                uncertainty='Writer-node bootstrap conditional on the separately fitted half-models; all pairs of copies of one original writer excluded. Not full variance-component refit uncertainty.')


def shuffled(rows,seed):
    rows=[r.copy() for r in rows];strata=defaultdict(list)
    for i,r in enumerate(rows):strata[(r['prompt'],r['setting'])].append(i)
    rng=np.random.default_rng(seed)
    for key,index in sorted(strata.items()):
        values=[rows[i]['handling'] for i in index]
        for i,y in zip(index,rng.permutation(values)):rows[i]['handling']=str(y)
    return rows


def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);started=time.perf_counter()
    binding=dict(inputs=input_hashes(inputs),config=config)
    if (output/'BINDING.json').exists():assert_equal(read(output/'BINDING.json'),binding)
    else:write(output/'BINDING.json',binding)
    if (output/'SUMMARY.json').exists():verify(output,inputs,config);return read(output/'SUMMARY.json')
    rows,support=rows_from_inputs(inputs)
    for name,value in (('ROWS.json',rows),('SUPPORT.json',support)):
        if (output/name).exists():assert_equal(read(output/name),value)
        else:write(output/name,value)
    arms={};fits={}
    for arm,data in (('primary',rows),('outcome_control',shuffled(rows,config['seed']+1))):
        halves=[]
        for half in (0,1):
            if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',completed_fits=len(fits))
            path=output/f'{arm}-{half}.json'
            if path.exists():
                if sha256(path)!=read(path.with_suffix('.seal.json'))['sha256']:raise ValueError('changed half-model')
                value=read(path);assert_equal(value['binding'],binding)
            else:
                value=dict(binding=binding,fit=fitted_profiles([r for r in data if r['half']==half],support['prompts']))
                write(path,value);write(path.with_suffix('.seal.json'),dict(sha256=sha256(path)))
            halves.append(value['fit']);fits[path.name]=sha256(path)
            if not (output/'FIRST_TENTH.json').exists():
                elapsed=time.perf_counter()-started
                write(output/'FIRST_TENTH.json',dict(completed_fits=1,total_fits=4,elapsed_seconds=elapsed,projected_seconds=4*elapsed))
        arms[arm]=summarize_profiles(halves,config)
    if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',completed_fits=4)
    report=dict(card='D15',descriptive=True,scientific_admission=False,primary=arms['primary']['primary'],
        state=arms['primary']['primary']['state'],arms=arms,fit_hashes=fits,config=config,input_hashes=binding['inputs'],
        row_hash=sha256(output/'ROWS.json'),support_hash=sha256(output/'SUPPORT.json'),support=support,
        model='Trial-level crossed response-scale Gaussian second-moment model of four one-hot handling indicators; writer, prompt, exact decoding tuple and writer-by-prompt components; nonnegative least-squares moments, unconstrained diagnostics retained.')
    write(output/'SUMMARY.json',report);return report


def verify(output,inputs,config):
    output=Path(output);report=read(output/'SUMMARY.json');binding=dict(inputs=input_hashes(inputs),config=config)
    assert_equal(report['input_hashes'],binding['inputs']);assert_equal(report['config'],config)
    rows,support=rows_from_inputs(inputs);assert_equal(rows,read(output/'ROWS.json'));assert_equal(support,report['support'])
    if sha256(output/'ROWS.json')!=report['row_hash'] or sha256(output/'SUPPORT.json')!=report['support_hash']:
        raise ValueError('changed source intermediates')
    for arm in ('primary','outcome_control'):
        halves=[]
        for half in (0,1):
            name=f'{arm}-{half}.json'
            if sha256(output/name)!=report['fit_hashes'][name]:raise ValueError('changed half-model')
            value=read(output/name);assert_equal(value['binding'],binding);halves.append(value['fit'])
        assert_equal(summarize_profiles(halves,config),report['arms'][arm])
    assert_equal(report['primary'],report['arms']['primary']['primary'])
    return dict(verified=True,primary_recomputed=report['primary'],state=report['state'],source_rows_replayed=True)
