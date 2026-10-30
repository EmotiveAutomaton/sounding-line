"""D5 exact session inner products, before any human identification scores.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 reread 2026-10-29.
NULL and ALTERNATIVE use the same unselected vocabulary and all source rows.
Sparse inner products must equal a direct explicit-coordinate oracle. Missing
rows remain masked and cannot become zero-valued observations in a reader.
Identical valid profiles tie fractionally; unique orthogonal profiles match;
reversed truth fails. No scientific admission follows numerical equivalence.
"""
from io import BytesIO
from pathlib import Path
import gzip
import math
import time

import numpy as np
from scipy.sparse import csr_matrix
from threadpoolctl import threadpool_limits

from runners.stage14.common import read, filehash, freeze, atomic
from .timing_p6 import gzread, gzip_equal
from . import week3_d5_gallery_support as support
from . import week3_d5_character_features as chars
from . import week3_d5_features as words

CONFIG = dict(card='D5-reader-cache', schema=1, mode='full', sessions=1399, writers=61)
CONSTRUCTED = dict(CONFIG, mode='constructed', sessions=16, writers=4)
CHANNELS = ('final',)+tuple('human'+str(n) for n in words.LENGTHS)


def representation(unit, channel):
    return unit['final'] if channel == 'final' else unit['human_prefixes'][channel[5:]]


def sparse_rows(values):
    """One exact column per (order, Unicode n-gram); equal order weights."""
    entries=[]; available=[]; vocabulary=set()
    for v in values:
        valid = v.get('supported', True)
        if type(valid) is not bool: raise ValueError('Explicit support required')
        row={}
        if valid:
            if set(v['counts']) != {'2','3','4'} or set(v['opportunities']) != {'2','3','4'}:
                raise ValueError('Character orders differ')
            for n in chars.ORDERS:
                d=v['counts'][str(n)]; total=v['opportunities'][str(n)]
                if type(total) is not int or total<0: raise ValueError('Invalid opportunity count')
                if any(not isinstance(k,str) or len(k)!=n or type(c) is not int or c<=0 for k,c in d.items()):
                    raise ValueError('Invalid exact n-gram counts')
                if sum(d.values()) != total: raise ValueError('Counts do not conserve opportunities')
                if total == 0: valid=False
                else:
                    for k,c in d.items(): row[(n,k)]=c/total/math.sqrt(3.)
        if not valid: row={}
        available.append(valid);entries.append(row);vocabulary.update(row)
    names=sorted(vocabulary); lookup={k:i for i,k in enumerate(names)}
    ix=[]; data=[]; pointer=[0]
    for row in entries:
        for key,value in sorted(row.items()):ix.append(lookup[key]);data.append(value)
        pointer.append(len(ix))
    matrix=csr_matrix((np.asarray(data,dtype=np.float64),np.asarray(ix,dtype=np.int32),np.asarray(pointer,dtype=np.int32)), shape=(len(values),len(names)))
    return matrix,np.asarray(available,dtype=bool)


def kernel(values):
    x,valid=sparse_rows(values)
    k=(x@x.T).toarray()
    if not np.isfinite(k).all() or not np.allclose(k,k.T,atol=1e-14,rtol=1e-14):
        raise ValueError('Invalid inner product matrix')
    return k,valid,dict(coordinates=x.shape[1],nonzero_entries=x.nnz)


def cosine_scores(k, valid, probes, galleries, truth):
    """Exact linear-profile reader; used on constructed tests only in this card."""
    k=np.asarray(k,float);valid=np.asarray(valid,bool)
    a,b=np.asarray(probes,float),np.asarray(galleries,float);truth=np.asarray(truth)
    if k.shape!=(len(valid),len(valid)) or a.ndim!=2 or b.ndim!=2 or a.shape[1]!=len(valid) or b.shape[1]!=len(valid):
        raise ValueError('Profile shape differs')
    if not np.isfinite(k).all() or not np.allclose(k,k.T,atol=1e-12,rtol=1e-12):raise ValueError('Invalid kernel')
    if not np.isfinite(a).all() or not np.isfinite(b).all() or (a<0).any() or (b<0).any():raise ValueError('Invalid profile weights')
    if len(b)<2 or truth.shape!=(len(a),) or not np.issubdtype(truth.dtype,np.integer) or (truth<0).any() or (truth>=len(b)).any():raise ValueError('Fixed truth/gallery required')
    if np.any(a[:,~valid]) or np.any(b[:,~valid]) or (a.sum(1)<=0).any() or (b.sum(1)<=0).any():raise ValueError('Missing evidence cannot be a zero profile')
    ak=a@k;bk=b@k;an=np.sum(ak*a,axis=1);bn=np.sum(bk*b,axis=1)
    if (an<=0).any() or (bn<=0).any():raise ValueError('Zero-norm profile')
    sim=(ak@b.T)/np.sqrt(an[:,None]*bn[None,:])
    ties=np.isclose(sim,sim.max(1)[:,None],atol=1e-12,rtol=1e-12)
    return ties[np.arange(len(a)),truth]/ties.sum(1)


def load(inputs,config):
    if config not in (CONFIG,CONSTRUCTED):raise ValueError('Frozen reader-cache configuration required')
    if config==CONSTRUCTED:
        if set(inputs)!={'fixture'}:raise ValueError('Constructed fixture required')
        p=Path(inputs['fixture']);v=read(p)
        if v.get('constructed') is not True:raise ValueError('Constructed source required')
        return v['rows'],v['characters'],v['process'],{str(p.resolve()):filehash(p)}
    if set(inputs)!={'support_complete'}:raise ValueError('Completed whole support source required')
    terminal=Path(inputs['support_complete']).resolve();root=terminal.parent;c=read(terminal);pins={str(terminal):filehash(terminal)}
    def artifact(base,complete,name):
        p=(base/name).resolve();p.relative_to(base)
        h=filehash(p)
        if complete.get('status')!='COMPLETE' or not complete.get('fresh_process_verified') or complete['outputs'].get(name)!=h:raise ValueError('Completed source bytes differ')
        pins[str(p)]=h
        return gzread(p) if p.suffix=='.gz' else read(p)
    plan=artifact(root,c,'PLAN.json')
    if plan['module']!=support.__name__ or plan['config']!=support.CONFIG:raise ValueError('Wrong support producer')
    detail=artifact(root,c,'output/GALLERIES.json.gz')
    binding=artifact(root,c,'output/BINDING.json')
    for path,h in binding['inputs'].items():
        if filehash(path)!=h:raise ValueError('Original support binding changed')
        pins[path]=h
    channels={}
    for key,module in [('word_complete',words),('character_complete',chars)]:
        terminal=Path(plan['inputs'][key]).resolve();base=terminal.parent;complete=read(terminal);pins[str(terminal)]=filehash(terminal)
        producer=artifact(base,complete,'PLAN.json')
        if producer['module']!=module.__name__ or producer['config']!=module.CONFIG:raise ValueError('Wrong feature producer')
        values={}
        for unit in artifact(base,complete,'output/FEATURE_INDEX.json'):
            relative='output/'+unit['file'];value=artifact(base,complete,relative)
            if pins[str((base/relative).resolve())]!=unit['sha256'] or any(value[k]!=unit[k] for k in ('session','writer')):raise ValueError('Feature index differs')
            if value['session'] in values:raise ValueError('Duplicate feature identity')
            values[value['session']]=value
        channels[key]=values
    wc,cc=channels['word_complete'],channels['character_complete'];rows=detail['rows']
    if set(wc)!=set(cc) or {r['session'] for r in rows}!=set(wc):raise ValueError('Full source population differs')
    for r in rows:
        if support.join(wc[r['session']],cc[r['session']])!=r:raise ValueError('Support/feature join differs')
    return rows,[cc[r['session']] for r in rows],[wc[r['session']]['process'] for r in rows],pins


def compute(output,inputs,config,verification=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);started=time.process_time()
    rows,characters,process,pins=load(inputs,config)
    if len(rows)!=config['sessions'] or len({r['session'] for r in rows})!=len(rows) or len({r['writer'] for r in rows})!=config['writers']:raise ValueError('Full census required')
    if len(characters)!=len(rows) or len(process)!=len(rows) or any(any(r[k]!=u[k] for k in ('session','writer','prompt','timestamp','model_share')) for r,u in zip(rows,characters)):raise ValueError('Character/session identity differs')
    order=sorted(range(len(rows)),key=lambda i:rows[i]['session']);rows=[rows[i] for i in order];characters=[characters[i] for i in order];process=[process[i] for i in order]
    def retain(name,value):
        p=output/name
        if verification:
            if (gzread(p) if p.suffix=='.gz' else read(p))!=value:raise ValueError('Fresh complete cache replay differs')
        elif p.suffix=='.gz':gzip_equal(p,value)
        else:freeze(p,value)
    retain('BINDING.json',dict(inputs=pins,config=config))
    retain('ROWS.json.gz',dict(rows=rows,process=process))
    summary={}
    with threadpool_limits(limits=2):
        for i,channel in enumerate(CHANNELS):
            if (output/'YIELD_REQUEST.json').exists() or (output.parent/'STOP').exists():
                if verification:raise InterruptedError('Reader-cache yield at channel boundary')
                return dict(status='yielded',source_only=True)
            k,valid,stats=kernel([representation(u,channel) for u in characters])
            buff=BytesIO();np.save(buff,k,allow_pickle=False);data=gzip.compress(buff.getvalue(),compresslevel=3,mtime=0);p=output/(channel+'.npy.gz')
            if p.exists():
                if gzip.decompress(p.read_bytes())!=buff.getvalue():raise ValueError('Exact kernel replay differs')
            elif verification:raise ValueError('Missing kernel output')
            else:p.write_bytes(data)
            retain(channel+'-support.json',valid.tolist())
            summary[channel]=dict(**stats,supported_sessions=int(valid.sum()),unsupported_sessions=int((~valid).sum()),matrix_shape=list(k.shape),dtype=str(k.dtype))
            atomic(output/'PROGRESS.json',dict(phase='verify' if verification else 'execute',done=i+1,total=len(CHANNELS)))
            if not verification and i==0 and not (output/'FIRST_TENTH.json').exists():
                freeze(output/'FIRST_TENTH.json',dict(projected_cpu_seconds=max(.001,4*(time.process_time()-started)*len(CHANNELS)),scope='Conservative first-channel extrapolation for both cache passes times two; no scientific workload admission'))
    retain('SUMMARY.json',dict(sessions=len(rows),writers=config['writers'],channels=summary,all_sessions_retained=True,
        representation='Exact frequency per n-gram opportunity; equal weights for orders 2,3,4; no learned vocabulary or feature pruning',
        source_only=True,effect_computed=False,scientific_admission=False,
        scope='Exact inner-product cache and original process vectors; missing rows stay explicitly masked; no population or length chosen'))
    return dict(verified=True,full_fresh_cache_replay=True,source_only=True) if verification else dict(status='complete',source_only=True)


def execute(output,inputs,config):return compute(output,inputs,config)
def verify(output,inputs,config):return compute(output,inputs,config,True)
