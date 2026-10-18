"""V5.d: saved-pair lean/context decomposition, never a cross-population ceiling.

DESIGN CHECK: LESSONS3-5 and mid-run errata read October18. Matching, decisions,
class labels and pair order remain those of completed V5. Canonical event labels
must exactly equal prepared and saved labels before analysis. Selected-option
identity is audited but never used here. Source/cap/checkpoint failures are
invalid instruments; every inferential control is fixed before corpus outcomes.
"""
from collections import Counter
from pathlib import Path
import gzip
import json
import math
import time
import numpy as np
from . import menus_v5 as original
from . import menus_v5_decomposition_stats as stats
from .menus_io import read,write,sha256,input_hashes,assert_equal,canonical

CONFIG=dict(seed=20261018,bootstrap_draws=2000,permutations=200,maximum_undefined_fraction=.05)


def completed_binding(completion,path):
    receipt=read(completion);root=Path(completion).resolve().parent
    if receipt.get('status')!='COMPLETE':raise ValueError('V5.d dependency incomplete')
    relative=Path(path).resolve().relative_to(root).as_posix()
    if receipt['outputs'].get(relative)!=sha256(path):raise ValueError('V5.d dependency changed')


def load(inputs):
    for name in ('v5_plan','v5_decisions','v5_pairs','v5_summary'):
        completed_binding(inputs['v5_complete'],inputs[name])
    if not read(inputs['v5_complete']).get('fresh_process_verified'):raise ValueError('V5 fresh replay absent')
    completed_binding(inputs['selection_complete'],inputs['selection_audit'])
    plan=read(inputs['v5_plan'])
    if plan['module']!='runners.drive.cards.menus_v5':raise ValueError('wrong V5 source module')
    if plan['inputs']['sessions']!=inputs['sessions'] or plan['pins'].get(inputs['sessions'])!=sha256(inputs['sessions']):
        raise ValueError('V5 source roster differs')
    sessions=read(inputs['sessions']);source={r['key']:r for s in sessions for r in s['rows']}
    metadata=read(inputs['v5_decisions']);audit=read(inputs['selection_audit']);audited={r['key']:r for r in audit}
    if len(source)!=sum(len(s['rows']) for s in sessions) or len(audited)!=len(audit):raise ValueError('duplicate V5 source/audit keys')
    if {r['key'] for r in metadata}!=set(source) or set(audited)!=set(source):raise ValueError('V5/audit/source coverage differs')
    canonical_files={};counts=Counter();times=[]
    for row in metadata:
        prepared=source[row['key']];verified=audited[row['key']]
        path=verified['canonical_path']
        if path not in canonical_files:
            if sha256(path)!=verified['canonical_sha256']:raise ValueError('canonical event source changed')
            saved=read(path);events=saved['events'];mapping={int(e['ordinal']):e for e in events}
            if len(mapping)!=len(events):raise ValueError('duplicate canonical event ordinal')
            canonical_files[path]=(verified['canonical_sha256'],mapping)
        digest,mapping=canonical_files[path]
        if digest!=verified['canonical_sha256']:raise ValueError('conflicting canonical source pin')
        event=mapping[prepared['ordinal']]
        labels=(prepared['handling'],verified['prepared_handling'],verified['canonical_handling'],event['decision'],original.ACTIONS[row['outcome']])
        if len(set(labels))!=1 or not event['usable'] or not verified['canonical_usable']:
            raise ValueError('canonical handling differs from frozen V5 labels')
        if labels[0] in ('accept','edit') and not event['verified_insertion']:
            raise ValueError('V5 accepted handling lacks verified canonical insertion')
        if (prepared['session'],prepared['writer'],prepared['ordinal'])!=(verified['session'],verified['writer'],verified['ordinal']):
            raise ValueError('V5 audit identity mismatch')
        if (row['writer'],row['session'],row['prompt'])!=(prepared['writer'],prepared['session'],prepared['prompt']):
            raise ValueError('V5 metadata identity mismatch')
        if prepared['open_at']!=verified['open_at'] or not math.isfinite(prepared['open_at']):raise ValueError('V5 clock source join differs')
        counts['handling_'+labels[0]]+=1;counts['index_'+verified['index_status']]+=1
        times.append(prepared['open_at']/1000.)
    with np.load(inputs['v5_pairs'],allow_pickle=False) as saved:pairs={k:saved[k] for k in saved.files}
    if set(pairs)!=set(('left','right','similarity')):raise ValueError('V5 pair schema differs')
    a,b=pairs['left'],pairs['right']
    if a.shape!=b.shape or a.shape!=pairs['similarity'].shape or np.any(a<0) or np.any(a>=b) or np.any(b>=len(metadata)):
        raise ValueError('V5 pair indices invalid')
    if not np.isfinite(pairs['similarity']).all():raise ValueError('V5 pair similarity invalid')
    writers,wi,si,_,truth=original.encode_metadata(metadata)
    if len(writers)<2:raise ValueError('V5.d requires two writers')
    return dict(metadata=metadata,pairs=pairs,writers=writers,writer=wi,session=si,truth=truth,times=np.asarray(times),
        audit=dict(counts=dict(counts),canonical_files=len(canonical_files),all_handling_labels_equal=True,
            selected_identity_used=False,timestamp_provenance='Frozen prepared SESSIONS joined by canonical event ordinal; no new raw clock replay.'))


def time_curves(data):
    pair=data['pairs'];mask=pair['similarity']>=.8;a=pair['left'][mask];b=pair['right'][mask]
    elapsed=np.abs(data['times'][a]-data['times'][b]);same=data['writer'][a]==data['writer'][b]
    same_session=data['session'][a]==data['session'][b];lean,valid,_=stats.lean_expectation(a,b,data['truth'],data['writer'])
    equal=(data['truth'][a]==data['truth'][b]).astype(float);gaps=np.full(len(a),np.nan)
    for writer in range(len(data['writers'])):
        times=np.sort(data['times'][data['writer']==writer]);sel=same&(data['writer'][a]==writer)
        lo=np.minimum(data['times'][a[sel]],data['times'][b[sel]]);hi=np.maximum(data['times'][a[sel]],data['times'][b[sel]])
        gaps[sel]=np.maximum(0,np.searchsorted(times,hi,side='left')-np.searchsorted(times,lo,side='right'))
    result={}
    for variable,values,edges in (('elapsed_seconds',elapsed,[0,60,600,3600,86400,604800,float('inf')]),
        ('intervening_same_writer_decisions',gaps,[0,1,5,20,100,float('inf')])):
        bins=[]
        for lower,upper in zip(edges[:-1],edges[1:]):
            by_group={}
            for name,group in (('within_writer_cross_session',same&~same_session),('cross_writer',~same),('same_session',same_session)):
                selected=group&valid&np.isfinite(values)&(values>=lower)&(values<upper)
                n=int(selected.sum())
                by_group[name]=dict(pairs=n,agreement=float(equal[selected].mean()) if n else None,
                    lean=float(lean[selected].mean()) if n else None,residual=float((equal[selected]-lean[selected]).mean()) if n else None)
            bins.append(dict(lower_inclusive=lower,upper_exclusive=upper if math.isfinite(upper) else None,groups=by_group))
        result[variable]=bins
    return result|dict(scope='Primary cutoff0.8, descriptive pair-weighted curves. Clock gaps are absolute elapsed time. Intervening decisions count strictly between the endpoints in the same writer clock sequence; tied timestamps excluded; cross-writer counts undefined. No causal session-boundary claim.')


def unit_store(output,binding,started,config,hashes):
    def unit(kind,index,build):
        if (output/'YIELD_REQUEST.json').exists():raise stats.CheckpointYield()
        path=output/'controls'/f'{kind}-{index:03d}.json.gz';seal=path.with_suffix('.seal.json')
        if path.exists():
            if sha256(path)!=read(seal)['sha256']:raise ValueError('changed V5.d control checkpoint')
            saved=json.loads(gzip.decompress(path.read_bytes()));assert_equal(saved['binding'],binding)
            if (saved['kind'],saved['index'])!=(kind,index):raise ValueError('V5.d control identity differs')
        else:
            saved=dict(binding=binding,kind=kind,index=index,value=build());path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as stream:stream.write(gzip.compress((canonical(saved)+'\n').encode(),mtime=0))
            write(seal,dict(sha256=sha256(path)))
        hashes[path.relative_to(output).as_posix()]=sha256(path)
        if len(hashes)>=math.ceil(.1*2*config['permutations']) and not (output/'FIRST_TENTH.json').exists():
            elapsed=time.perf_counter()-started
            write(output/'FIRST_TENTH.json',dict(completed_units=len(hashes),total_units=2*config['permutations'],
                elapsed_seconds=elapsed,projected_seconds=elapsed*2*config['permutations']/len(hashes)))
        return saved['value']
    return unit


def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);started=time.perf_counter()
    if config['permutations']!=200 or config['seed']!=20261018:raise ValueError('midrun controls require200 permutations at seed20261018')
    binding=dict(inputs=input_hashes(inputs),config=config)
    if (output/'BINDING.json').exists():assert_equal(read(output/'BINDING.json'),binding)
    else:write(output/'BINDING.json',binding)
    if (output/'SUMMARY.json').exists():verify(output,inputs,config);return read(output/'SUMMARY.json')
    data=load(inputs);hashes={}
    try:result,_=stats.analyze(data['truth'],data['writer'],data['session'],data['pairs'],config,
        unit_store(output,binding,started,config,hashes))
    except stats.CheckpointYield:return dict(status='yielded',saved_control_units=len(hashes))
    ci=result['primary']['ci95'];route='near_zero' if ci[1] is not None and ci[1]<.005 else 'context_consistency' if ci[0] is not None and ci[0]>0 else 'undetermined'
    report=dict(card='V5.d',descriptive=True,scientific_admission=False,**result,route=route,
        input_hashes=binding['inputs'],config=config,control_hashes=hashes,label_audit=data['audit'],timing=time_curves(data),
        writers=len(data['writers']),decisions=len(data['truth']),
        method='Exact saved V5 pair graph. Each writer class rate leaves out BOTH pair decisions from that writer, or its own endpoint for a cross-writer pair. H_context=0.5*(A_within-A_between)-0.5*(E_within-E_between).',
        uncertainty='2000 real-writer node resamples: within-real-writer edges weighted once, cross-real-writer edges by product. Fake-writer controls reuse the exact pair graph and paired real-writer weights; reported own-minus-mean-of200fake difference.',
        chance='Cohen kappa uses separate endpoint marginals. The separately named pooled-mix adjustment uses the pair sample pooled class mix squared, as requested in the errata. Degenerate chance1 is undefined.',
        pure_lean_check='Balanced full-rate algebra is separate from unequal matched-pair weights and pair-specific leave-out rates; distinct writer draws require the finite n/(n-1) correction.',
        caveat='Matcher-conditional proxy only. Never used as a denominator for gains on other populations. Original V5 labels and outputs remain frozen.',
        controls_scope='Outcome permutations and fake-session reassignment controls apply to the fixed primary cutoff0.8; full descriptive decomposition and uncertainty retained at every original cutoff.')
    write(output/'SUMMARY.json',report);return report


def verify(output,inputs,config):
    output=Path(output);report=read(output/'SUMMARY.json');binding=dict(inputs=input_hashes(inputs),config=config)
    assert_equal(report['input_hashes'],binding['inputs']);assert_equal(report['config'],config)
    assert_equal(read(output/'BINDING.json'),binding)
    for name,digest in report['control_hashes'].items():
        if sha256(output/name)!=digest:raise ValueError('changed V5.d saved control')
    data=load(inputs);result,_=stats.analyze(data['truth'],data['writer'],data['session'],data['pairs'],config)
    assert_equal(result,{k:report[k] for k in result});assert_equal(data['audit'],report['label_audit']);assert_equal(time_curves(data),report['timing'])
    return dict(verified=True,primary_recomputed=result['primary'],state=result['state'],canonical_handling_replayed=True,
        full200_outcome_controls_recomputed=True,paired200_fake_controls_recomputed=True)
