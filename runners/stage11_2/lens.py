"""Pinned average-Jacobian fit and overlapping-coordinate intervention.

DESIGN CHECK: LESSONS 3–5 and upstream fitting/hf/recorder/lens read.
NULL: coordinate identity and zero dose preserve state; a nonorthogonal frame
must match its pseudoinverse oracle. ALTERNATIVE: selective target interchange
can change counterfactual behavior while controls preserve unrelated capability.
Fit failure is an instrument disposition. Capability failure blocks science.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import time
import traceback
from .common import RAW, REPO, atomic, digest, filehash, freeze, gpu_service, now, read, source_pins

def vendor():
    path=Path(__file__).parent/'vendor'
    if str(path) not in sys.path:sys.path.insert(0,str(path))
    from jlens.fitting import jacobian_for_prompt
    from jlens.hf import from_hf
    return jacobian_for_prompt,from_hf

def coordinate_swap(h,frame,alpha=1.0):
    """Published two-coordinate swap, not a sum of orthogonal projections."""
    import torch
    v=frame.to(device=h.device,dtype=torch.float32)
    if v.shape[1]!=2:raise ValueError('two concept vectors required')
    c=h.float() @ torch.linalg.pinv(v).T
    delta=(c.flip(-1)-c) @ v.T
    return (h.float()+alpha*delta).to(h.dtype),c,delta

def donor_patch(base,donor,frame,alpha=1.0):
    """Interchange coordinates within an overlapping frame, orthogonal remainder fixed."""
    import torch
    v=frame.to(device=base.device,dtype=torch.float32)
    inverse=torch.linalg.pinv(v)
    c=base.float()@inverse.T; d=donor.float()@inverse.T
    delta=(d-c)@v.T
    return (base.float()+alpha*delta).to(base.dtype),c,d,delta

def neutral_inputs(root):
    paths=sorted((REPO/'corpora/public/argrewrite/essays/Draft1').glob('*.txt'))
    rows=[dict(path=p.relative_to(REPO).as_posix(),sha256=filehash(p),text=p.read_text(encoding='utf-8',errors='strict')) for p in paths]
    if len(rows)<16:raise ValueError('fewer than sixteen neutral cached passages')
    # No duplicate clipping into nominally independent prompts to reach 100.
    rows=rows[:100]
    freeze(Path(root)/'NEUTRAL.json',rows)
    return rows

def fit(root=RAW,model_index=0,prompts=16):
    import torch
    from .hf import Reader,MODELS
    from soundingline.gpulock import acquire_gpu_lock,release_gpu_lock
    from runners.stage9.process_identity import native_identity
    root=Path(root); out=root/f'M1-fit-{model_index}-{prompts}'
    if (out/'COMPLETE.json').exists():return verify(out)
    freeze(out/'SOURCE.json',source_pins());freeze(out/'NATIVE.json',native_identity())
    neutral=neutral_inputs(root)
    selected=neutral[:prompts]
    admission=root/f'admission-{model_index}'/'COMPLETE.json'
    admitted=admission.exists() and read(admission)['admitted']
    n=min(prompts,len(selected)); reservation= min(10800,600*n+120)
    acquire_gpu_lock('Stage11.2 average Jacobian fit');reader=None
    try:
        with gpu_service(root,f'M1-fit-{model_index}-{prompts}',reservation):
            reader=Reader(MODELS[model_index],stop_at=time.monotonic()+reservation-30,precision='bfloat16')
            jacobian_for_prompt,from_hf=vendor()
            model=from_hf(reader.model,reader.tok,compile=False,force_bos=False)
            matrices=[];timings=[]
            for i,item in enumerate(selected):
                reader.check_time()
                meta=dict(prompt_sha256=digest(item['text']),source_sha256=item['sha256'],
                    model=reader.bound,layers=reader.layers,max_tokens=128,skip_first=16,
                    target_layer=len(reader.blocks)-1,vendor_revision=(Path(__file__).parent/'vendor/REVISION').read_text().strip())
                path=out/f'prompt-{i:03d}.pt'; receipt=out/f'prompt-{i:03d}.json'
                if receipt.exists():
                    saved=read(receipt)
                    if saved['input']!=meta or saved['tensor_sha256']!=filehash(path):raise ValueError('neutral cache changed')
                    values=torch.load(path,map_location='cpu',weights_only=True)
                    seconds=saved['seconds']
                else:
                    start=time.perf_counter()
                    # One bounded memory repair halves cotangent batch 4 -> 2.
                    try:
                        values,length,valid=jacobian_for_prompt(model,item['text'],reader.layers,dim_batch=4,max_seq_len=128)
                        batch=4
                    except torch.cuda.OutOfMemoryError:
                        if (out/'MEMORY_REPAIR.json').exists():raise
                        freeze(out/'MEMORY_REPAIR.json',dict(at=now(),prompt=i,from_batch=4,to_batch=2))
                        torch.cuda.empty_cache()
                        values,length,valid=jacobian_for_prompt(model,item['text'],reader.layers,dim_batch=2,max_seq_len=128)
                        batch=2
                    seconds=time.perf_counter()-start
                    if any(not torch.isfinite(v).all() for v in values.values()):raise ValueError('nonfinite Jacobian')
                    torch.save(values,path)
                    freeze(receipt,dict(input=meta,seconds=seconds,tensor_sha256=filehash(path),
                        sequence_length=length,valid_positions=valid,cotangent_batch=batch))
                matrices.append(values);timings.append(seconds)
                atomic(out/'STATUS.json',dict(at=now(),completed_prompts=len(matrices),requested=prompts,
                    available=len(selected),seconds=timings))
            lens={layer:sum(row[layer] for row in matrices)/n for layer in reader.layers}
            midpoint=n//2
            stability={}
            for layer in reader.layers:
                a=sum(row[layer] for row in matrices[:midpoint])/midpoint
                b=sum(row[layer] for row in matrices[midpoint:])/(n-midpoint)
                stability[str(layer)]=dict(cosine=float(torch.nn.functional.cosine_similarity(a.flatten(),b.flatten(),dim=0)),
                    relative_difference=float((a-b).norm()/((a.norm()+b.norm())/2)))
            torch.save(lens,out/'lens.pt')
            import numpy as np
            return freeze(out/'COMPLETE.json',dict(status='complete',model=reader.bound,requested=prompts,
                fitted=n,half_stability=stability,fit_seconds=sum(timings),
                p50_prompt_seconds=float(np.median(timings)),p90_prompt_seconds=float(np.quantile(timings,.9)),
                lens_sha256=filehash(out/'lens.pt'),admitted_for_science=admitted,
                scope='reduced neutral-text fit; transport only unless separate capability admission passes',
                source_limit='86 cached independent passages available; no duplication to claim 100'))
    except BaseException as exc:
        freeze(out/'FAILED.json',dict(at=now(),error=repr(exc),traceback=traceback.format_exc()));raise
    finally:
        if reader is not None:reader.close()
        release_gpu_lock()

def verify(out):
    receipt=read(out/'COMPLETE.json')
    if filehash(out/'lens.pt')!=receipt['lens_sha256']:raise ValueError('fitted lens changed')
    for p in out.glob('prompt-*.json'):
        row=read(p)
        if filehash(p.with_suffix('.pt'))!=row['tensor_sha256']:raise ValueError('prompt fit changed')
    return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=RAW);p.add_argument('--model-index',type=int,default=0);p.add_argument('--prompts',type=int,default=16)
    a=p.parse_args();r=fit(a.root,a.model_index,a.prompts);print({'status':r['status'],'fitted':r['fitted']})
