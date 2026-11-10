"""AT scoring v3: resource yields at sealed blocks, exact v2 scores retained.

The frozen source/scoring v1 remains immutable for source provenance. This
implementation uses the identical tested causal scoring primitive.
"""
from pathlib import Path
import math,time
import numpy as np
from .week5_at_scoring import CausalScorer,load_model,tokenize_target,SEED,digest
from .timing_census import read,filehash
from .timing_p6 import gzread,write_equal,progress


def score_batch(output,rows,manifest,*,context='final',context_length=1024,max_wall_seconds=1200,verifying=False):
    began=time.monotonic();cpu_start=time.process_time()
    if context not in ('final','at_typing') or context_length not in (64,256,1024) or not rows:
        raise ValueError('Unsupported AT scoring condition')
    if not 30<=max_wall_seconds<=1500:raise ValueError('Quantum must leave room for fresh verification')
    root=Path(output);root.mkdir(parents=True,exist_ok=True)
    binding=digest(dict(rows=rows,manifest=manifest,context=context,context_length=context_length))
    if (root/'YIELD_REQUEST.json').exists():
        return dict(status='yielded',reason='resource request before model loading',completed=0,total=len(rows))
    write_equal(root/'BINDING.json',dict(sha256=binding))
    model,tok,torch=load_model(manifest);cold_load=time.monotonic()-began
    scorer=CausalScorer(model,tok,torch,context_length)
    chosen=set(np.random.default_rng(SEED).choice(len(rows),max(1,math.ceil(.02*len(rows))),replace=False))
    index=[];errors=[];completed=0
    for offset in range(0,len(rows),8):
        path=root/f'block-{offset//8:05d}.json';seal=path.with_suffix('.receipt.json')
        if path.exists():
            if not seal.exists() or read(seal)['sha256']!=filehash(path):raise ValueError('Score checkpoint seal mismatch')
            saved=read(path)
            if saved['binding']!=binding or saved['offset']!=offset:raise ValueError('Score block binding changed')
        elif verifying:raise ValueError('Missing complete score block')
        else:
            values=[]
            for i,row in enumerate(rows[offset:offset+8],offset):
                prefix=row[context+'_prefix']
                if prefix is None:raise ValueError('Unsupported context entered score bank')
                values.append(dict(row_key=row['row_key'],score=scorer.score(prefix,row['target'])))
            saved=dict(binding=binding,offset=offset,values=values)
            write_equal(path,saved);write_equal(seal,dict(sha256=filehash(path)))
        wanted=rows[offset:offset+8]
        if len(saved['values'])!=len(wanted):raise ValueError('Score block row count differs')
        for slot,(row,value) in enumerate(zip(wanted,saved['values'])):
            i=offset+slot;prefix=row[context+'_prefix'];score=value['score']
            if value['row_key']!=row['row_key']:raise ValueError('Score row identity changed')
            ids,positions,dropped=tokenize_target(tok,prefix,row['target'],context_length)
            native=score['native_token_nll']
            if (score['native_token_ids']!=[ids[j] for j in positions] or score['prefix_tokens_dropped']!=dropped or
                len(native)!=len(positions) or any(not math.isfinite(v) or v<0 for v in native+[score['entropy_nats']]) or
                score['surprisal_nats']!=sum(native)):raise ValueError('Retained word score does not reconstruct')
            if verifying and i in chosen:errors.append(scorer.direct_check(prefix,row['target'],score))
            index.append(dict(row_key=row['row_key'],file=path.name,slot=slot,sha256=filehash(path)))
        completed+=len(wanted)
        progress(root/'PROGRESS.json',dict(phase='verify' if verifying else 'score',words=completed,total=len(rows),
                 cold_load_wall_seconds=cold_load,elapsed_wall_seconds=time.monotonic()-began,
                 elapsed_process_cpu_seconds=time.process_time()-cpu_start))
        if completed<len(rows) and ((root/'YIELD_REQUEST.json').exists() or
                                   (not verifying and time.monotonic()-began>=max_wall_seconds)):
            return dict(status='yielded',reason='resource request or bounded scoring checkpoint',completed=completed,total=len(rows))
    result=dict(status='complete',words=len(rows),context=context,context_length=context_length,
                model=manifest['model'],model_revision=manifest['revision'],scientific_admission=False,storage='sealed_blocks_v2')
    if verifying:
        if read(root/'INDEX.json')!=index or read(root/'SUMMARY.json')!=result:raise ValueError('Batch reduction replay differs')
        return dict(verified=True,fresh_forward_count=len(chosen),max_error=max(errors,default=0.))
    write_equal(root/'INDEX.json',index);write_equal(root/'SUMMARY.json',result)
    write_equal(root/'COST.json',dict(cold_load_wall_seconds=cold_load,elapsed_wall_seconds=time.monotonic()-began,
                                    elapsed_process_cpu_seconds=time.process_time()-cpu_start,
                                    forecast_note='Add independent verification and all prior quantum accounting before admission'))
    return result


def execute(output,inputs,config):return score_batch(output,gzread(inputs['rows']),read(inputs['model_manifest']),**config)
def verify(output,inputs,config):return score_batch(output,gzread(inputs['rows']),read(inputs['model_manifest']),verifying=True,**config)
