"""Independent local-model precision/batching repair, outside closed Stage 8.

DESIGN CHECK (2026-09-06)
lessons read: LESSONS sections 3,4,5; CONTROLS sections 5,6.
NULL: identical continuation identities have invariant exact probabilities under permutation
and batch partition. ALTERNATIVE: finite precision can change the numerical readout.
gates: all options produce finite summed log probabilities with matching model/adapter identity;
missing/nonfinite scores refuse completion. bands: descriptive measured numerical envelope;
historical X05 rules (1e-6 and 0.01) are reported together, never amended by this probe.
Inputs are fixed artificial logs, independent of Stage 8 outcomes. No scientific card rerun,
training, download, network endpoint, or paid call. Latest curator repair authorization applies.
"""
from __future__ import annotations
import argparse
import gc
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    out=a.out.resolve()
    if any(out.is_relative_to(ROOT/f'results/phase_2_4_stage_{s}') for s in (7,8)):raise ValueError('closed stage output')
    from runners.readout_repair import readout,digest
    from runners.stage8 import model_server as server
    from runners.s4_lib import GpuSession
    import torch
    registry=json.loads((ROOT/'results/phase_2_4_stage_8/ADAPTERS.json').read_text())
    names=('fm_qwen','fm_smollm')
    # Independent artificial prefixes and complete option sets; no real stage unit is read.
    prefix='Document workshop. Audience: readers. Goal: explain.\n'+''.join(f'{i:02d} write sec1 s1.{i%3+1} done\n' for i in range(16))
    options={f'option-{i:02d}':f'16 {("write","revise","check","consult","cite")[i%5]} sec{i%4+1} s{i%4+1}.{i%3+1} done'+(' carefully' if i%2 else '')+'\n' for i in range(25)}
    # Repeated texts would duplicate probability mass; these options must be distinct.
    assert len(set(options.values()))==len(options)
    rows=[];start=time.time();adapter_files={}
    with GpuSession('ops-readout-precision-20260906') as gpu:
        for name in names:
            rec=registry[name];path=Path(rec['path']).resolve()
            assert path.is_relative_to(ROOT/'results/phase_2_4_stage_8/adapters')
            assert server._dir_hash(path)==rec['sha']
            adapter_files[name]={p.relative_to(path).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(path.rglob('*')) if p.is_file()}
            server.STATE['allowed']={rec['base']};server.STATE['adapters']={name:rec};server.STATE['adapter_hashes']={name:rec['sha']}
            server._ensure('adapter:'+name)
            assert server.STATE['revision']==rec['revision'],'base revision drift'
            identity={'model':rec['base'],'revision':server.STATE['revision'],'adapter_sha256':digest(json.dumps(adapter_files[name],sort_keys=True)),'scorer_sha256':hashlib.sha256(Path(server.__file__).read_bytes()).hexdigest(),'information_sha256':digest(prefix)}
            refs={}
            for dtype in (torch.float16,torch.float32):
                device='cuda' if dtype==torch.float16 else 'cpu'
                if device=='cpu':server.STATE['model'].to(device='cpu');torch.cuda.empty_cache()
                server.STATE['model'].to(device=device,dtype=dtype).eval()
                for batch in ((1,4,12) if device=='cuda' else (1,)):
                    for reverse in ((False,True) if device=='cuda' else (False,)):
                        keys=sorted(options,reverse=reverse)
                        raw=server.sequence_logprobs(prefix,[options[k] for k in keys],batch=batch)
                        assert len(raw['logprobs'])==len(keys) and all(math.isfinite(v) for v in raw['logprobs'])
                        components=[{'option_id':k,'valid':True,'logprob':v,'identity':identity,'prefix_sha256':digest(prefix),'continuation_sha256':digest(options[k]),'semantics':'sum_log_probability'} for k,v in zip(keys,raw['logprobs'])]
                        result=readout(prefix,options,lambda *_:components,identity)
                        assert result['valid'],result['reason']
                        key=str(dtype)
                        if batch==1 and not reverse:refs[key]=result['probs']
                        tv=sum(abs(result['probs'][k]-refs[key][k]) for k in options)/2
                        rows.append({'reader':name,'dtype':key,'device':device,'requested_batch':batch,'actual_batch':raw['batch'],'reverse':reverse,'identity':identity,'tv_from_same_precision_serial':tv,'original_x05_rule_holds':tv<=1e-6,'amended_x05_rule_holds':tv<=0.01,'logprobs_by_option':dict(zip(keys,raw['logprobs'])),'token_counts_by_option':dict(zip(keys,raw['n_tokens'])),'probabilities':result['probs']})
                print(f'{name} {dtype}: precision fixtures complete',flush=True)
            for r in rows:
                if r['reader']==name:r['tv_from_float32_serial']=sum(abs(r['probabilities'][k]-refs['torch.float32'][k]) for k in options)/2
            server.STATE['model']=server.STATE['tok']=None;server.STATE['base']=server.STATE['adapter']=None
            gc.collect();torch.cuda.empty_cache()
    sources={}
    for mod in list(sys.modules.values()):
        f=getattr(mod,'__file__',None)
        if f:
            p=Path(f).resolve()
            if p.is_relative_to(ROOT) and '.venv' not in p.parts and p.is_file():sources[p.relative_to(ROOT).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    result={'version':'model-precision-repair-20260906.1','complete':True,'scope':'independent apparatus measurement; no Stage 8 rescore or admission','inputs':{'prefix':prefix,'options':options,'sha256':digest(json.dumps([prefix,options],sort_keys=True))},'rows':rows,'adapter_files':adapter_files,'loaded_repository_sources':sources,'packages':{n:importlib.metadata.version(n) for n in ('torch','transformers','peft','numpy')},'cuda':torch.version.cuda,'device':torch.cuda.get_device_name(0),'tf32_matmul':torch.backends.cuda.matmul.allow_tf32,'elapsed_s':time.time()-start,'gpu_lock_seconds':gpu.held_s,'limits':'Observed envelope on fixed inputs and resident weights. Float32 CPU is a numerical reference, not a pure precision comparison with float16 CUDA. GPU lock duration is reservation, not measured utilization. No historical threshold is made predeclared or old scientific effect independently confirmed.'}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    return 0

if __name__=='__main__':raise SystemExit(main())
