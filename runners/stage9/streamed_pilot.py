"""Real-base discarded loss/gradient and long-microbatch memory measurement.

DESIGN CHECK: C05/I03. CPU fixtures precede this finite BF16 calculation check.
Use one actual discarded replay snippet for full-vs-blocked gradients, then one
long discarded mixed microbatch for measured memory/time. No optimizer updates,
scientific training inputs or performance selection. Failure retains measurements.
"""
import argparse
from pathlib import Path
import time

from runners.stage9.common import REPO,ROOT,closure,digest,file_hash,freeze,read
from runners.stage9.streamed_loss import causal_loss
from runners.stage9.train import BASES,LORA,batch_tensors


def run(family):
    import torch
    from transformers import AutoModelForCausalLM,AutoTokenizer
    from peft import LoraConfig,get_peft_model
    from runners.s5_lib import GpuSession
    from runners.stage9.process_identity import native_identity
    # The deliberately bounded long-dose attempt must have stopped first. This
    # is verified by both its chain disposition and exact native worker identity.
    if not (ROOT/'private/dose-chain-2/FAILED.json').exists() and not (ROOT/'private/dose-chain-2/COMPLETE.json').exists():
        raise ValueError('preceding discarded GPU chain has not closed')
    disposition=read(ROOT/'private/pilot-dose-v2/qwen/ATTEMPT_DISPOSITION.json')
    if disposition['later_native_absence_verified'] is not True or any(
            native_identity(int(pid)) is not None for pid in disposition['native_processes_absent']):
        raise ValueError('preceding pilot process ownership has not cleared')
    output=ROOT/'private/pilot-streamed-loss'/family
    if (output/'COMPLETE.json').exists():return read(output/'COMPLETE.json')
    base=BASES[family];torch.set_num_threads(6);torch.manual_seed(998001)
    source=ROOT/('private/pilot/qwen-corpus.json' if family=='qwen' else 'private/pilot/smollm-corpus.json')
    corpus=read(source)
    if corpus['split']!='pilot':raise ValueError('only discarded pilot input permitted')
    short_ids=corpus['examples'][0]['input_ids'][:48]
    short={'ids':short_ids,'labels':[-100]*12+short_ids[12:]}
    if family=='qwen':
        long_source=ROOT/'private/pilot-dose-v2/qwen/mixed.json'
    else:
        long_source=source
    long_corpus=read(long_source)
    if long_corpus['split']!='pilot':raise ValueError('only discarded long input permitted')
    longest=sorted(long_corpus['examples'],key=lambda r:(-len(r['input_ids']),r['key']))[:4]
    long_rows=[{'ids':r['input_ids'],'labels':r.get('labels',r['input_ids'])} for r in longest]
    identity={'base':base,'seed':998001,'lora':LORA,'precision':'bfloat16',
        'source_sha256':file_hash(source),'long_source_sha256':file_hash(long_source),
        'long_keys':[r['key'] for r in longest],'chunk_tokens':64,
        'checks':{'absolute_loss_tolerance':.001,'relative_gradient_l2_tolerance':.02,'minimum_gradient_cosine':.999},
        'scope':'finite real-base calculation and one worst-length microbatch; not scientific competence or full training throughput',
        'sources':closure([REPO/'runners/stage9'/p for p in ('streamed_pilot.py','streamed_loss.py','train.py','common.py')])}
    freeze(output/'IDENTITY.json',identity);started=time.time()
    with GpuSession('s9_streamed_loss_'+family):
        tok=AutoTokenizer.from_pretrained(base['model'],revision=base['revision'],local_files_only=True)
        if tok.pad_token is None:tok.pad_token=tok.eos_token
        core=AutoModelForCausalLM.from_pretrained(base['model'],revision=base['revision'],local_files_only=True,
                                               trust_remote_code=False,dtype=torch.bfloat16).to('cuda')
        model=get_peft_model(core,LoraConfig(**LORA))
        model.gradient_checkpointing_enable();model.enable_input_require_grads();model.config.use_cache=False
        model.train();batch=batch_tensors(torch,[short],tok.pad_token_id,'cuda')
        cpu_rng=torch.get_rng_state();gpu_rng=torch.cuda.get_rng_state_all()
        full_loss=model(**batch).loss;full_loss.backward();torch.cuda.synchronize()
        reference_loss=float(full_loss.detach());del full_loss
        reference={n:p.grad.detach().float().cpu().clone() for n,p in model.named_parameters() if p.requires_grad}
        model.zero_grad(set_to_none=True);torch.cuda.empty_cache()
        torch.set_rng_state(cpu_rng);torch.cuda.set_rng_state_all(gpu_rng)
        blocked=causal_loss(model,batch,64);blocked.backward();torch.cuda.synchronize()
        observed_loss=float(blocked.detach());del blocked
        reference_norm=observed_norm=dot=error=maximum=0.
        for name,parameter in model.named_parameters():
            if not parameter.requires_grad:continue
            want=reference[name];got=parameter.grad.detach().float().cpu()
            if not torch.isfinite(got).all():raise ValueError('nonfinite blocked gradient')
            delta=got-want
            reference_norm+=float((want*want).sum());observed_norm+=float((got*got).sum())
            dot+=float((got*want).sum());error+=float((delta*delta).sum());maximum=max(maximum,float(delta.abs().max()))
        cosine=dot/(reference_norm*observed_norm)**.5 if reference_norm and observed_norm else 0.
        relative=(error/reference_norm)**.5 if reference_norm else None
        comparison={'reference_loss':reference_loss,'blocked_loss':observed_loss,
            'absolute_loss_difference':abs(reference_loss-observed_loss),'relative_gradient_l2':relative,
            'gradient_cosine':cosine,'maximum_absolute_gradient_difference':maximum}
        checks={'loss':comparison['absolute_loss_difference']<=.001,
                'gradient':relative is not None and relative<=.02,'gradient_direction':cosine>=.999}
        freeze(output/'GRADIENT_COMPARISON.json',{'comparison':comparison,'checks':checks})
        model.zero_grad(set_to_none=True);del reference,batch;torch.cuda.empty_cache()
        if not all(checks.values()):raise ValueError('actual-base calculation differs beyond fixed tolerances')
        batch=batch_tensors(torch,long_rows,tok.pad_token_id,'cuda')
        torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();long_started=time.time()
        loss=causal_loss(model,batch,64);loss.backward();torch.cuda.synchronize()
        long_measurement={'batch_examples':len(long_rows),'padded_tokens':int(batch['input_ids'].numel()),
            'maximum_length':int(batch['input_ids'].shape[1]),
            'supervised_tokens':int((batch['labels'][:,1:]!=-100).sum()),
            'forward_backward_seconds':time.time()-long_started,
            'peak_cuda_allocated_bytes':torch.cuda.max_memory_allocated(),
            'peak_cuda_reserved_bytes':torch.cuda.max_memory_reserved(),'loss_finite':bool(torch.isfinite(loss))}
        if not long_measurement['loss_finite']:raise ValueError('long loss is nonfinite')
        freeze(output/'LONG_MICROBATCH.json',long_measurement)
    result={'family':family,'identity_sha256':digest(identity),'comparison':comparison,'checks':checks,
        'long_microbatch':long_measurement,'wall_seconds':time.time()-started,'completed_at':time.time(),
        'scientific_admission':False,'training_optimizer_updates':0}
    freeze(output/'COMPLETE.json',result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--family',required=True,choices=BASES)
    run(p.parse_args().family)
