"""Installed HF readers, raw next-token scores and scoped activation capture.

DESIGN CHECK: LESSONS 3–5. NULL: zero patch preserves every logit and exceptions
remove hooks; ALTERNATIVE: selective patches outperform equal-norm controls.
Capability bands >=70% action and >=80% factual state admit; others are instrument
limitations. Candidate-normalized probabilities are never calibrated confidence.
"""
from __future__ import annotations
import os
os.environ.setdefault('HF_HUB_OFFLINE','1')
os.environ.setdefault('TRANSFORMERS_OFFLINE','1')
os.environ.setdefault('OMP_NUM_THREADS','4')
from contextlib import contextmanager
from pathlib import Path
import time
from .common import digest, filehash

MODELS=['HuggingFaceTB/SmolLM2-360M-Instruct','Qwen/Qwen2.5-0.5B-Instruct',
        'Qwen/Qwen2.5-1.5B-Instruct','HuggingFaceTB/SmolLM2-1.7B-Instruct',
        'Qwen/Qwen2.5-3B-Instruct']

class Reader:
    def __init__(self,name,stop_at=None,precision='float32'):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from soundingline.probe.interventions import get_blocks
        torch.set_num_threads(4)
        torch.manual_seed(112)
        self.stop_at=stop_at
        self.name=name
        self.tok=AutoTokenizer.from_pretrained(name,local_files_only=True)
        placement = dict(device_map='auto',max_memory={0:'4500MiB','cpu':'6GiB'}) if '-3B-' in name else {}
        self.model=AutoModelForCausalLM.from_pretrained(name,local_files_only=True,
            dtype=getattr(torch,precision),attn_implementation='eager',**placement).eval()
        if not placement:self.model.to('cuda')
        self.model.requires_grad_(False)
        self.blocks=get_blocks(self.model)
        self.layers=sorted(set([len(self.blocks)//3,2*len(self.blocks)//3]))
        self.options={c:self.tok.encode(c,add_special_tokens=False) for c in 'ABCD'}
        if any(len(ids)!=1 for ids in self.options.values()):
            raise ValueError('letter continuation is not one token')
        self.ids=[self.options[c][0] for c in 'ABCD']
        self.bound=dict(checkpoint=name,revision=self.model.config._commit_hash,
            layers=self.layers,dtype=precision,token_mask='final prompt token only',
            torch=torch.__version__,transformers=__import__('transformers').__version__)
        if placement:self.bound['device_map']={k:str(v) for k,v in self.model.hf_device_map.items()}
        self.deadline_handles=[]
        if stop_at is not None:
            def guard(_m,_i): self.check_time()
            self.deadline_handles=[b.register_forward_pre_hook(guard) for b in self.blocks]

    def check_time(self):
        if self.stop_at is not None and time.monotonic()>=self.stop_at:
            raise TimeoutError('reserved GPU block exhausted')

    def encode(self,text):
        import torch
        self.check_time()
        rendered=self.tok.apply_chat_template([dict(role='user',content=text)],tokenize=False,add_generation_prompt=True)
        ids=self.tok(rendered,return_tensors='pt',add_special_tokens=False).input_ids.to('cuda')
        if ids.shape[1]>4096: raise ValueError('context outside frozen envelope')
        return ids,rendered

    @contextmanager
    def patch(self,layer,delta=None,transform=None):
        """Only final prompt position. Transform preserves autograd for alignment."""
        def hook(_module,_inputs,output):
            hs=output[0] if isinstance(output,tuple) else output
            replacement=hs[:,-1,:]
            if transform is not None: replacement=transform(replacement)
            elif delta is not None: replacement=replacement+delta.to(hs)
            changed=hs.clone(); changed[:,-1,:]=replacement
            return (changed,)+output[1:] if isinstance(output,tuple) else changed
        handle=self.blocks[layer].register_forward_hook(hook)
        try: yield
        finally: handle.remove()

    def forward(self,text,capture=False,grad=False):
        import torch
        ids,rendered=self.encode(text); saved={}; handles=[]
        if capture:
            for layer in self.layers:
                def hook(_m,_i,output,layer=layer):
                    hs=output[0] if isinstance(output,tuple) else output
                    saved[layer]=hs[:,-1,:].detach().float().cpu()
                handles.append(self.blocks[layer].register_forward_hook(hook))
        try:
            with torch.set_grad_enabled(grad):
                output=self.model(input_ids=ids,use_cache=False,logits_to_keep=1)
                logits=output.logits[0,-1].float()
            return logits,saved,dict(prompt=rendered,input_ids=ids[0].tolist(),
                input_sha256=digest(ids[0].tolist()),tokens=ids.shape[1],**self.bound)
        finally:
            for h in handles:h.remove()

    def score(self,text,n=4,capture=False):
        import torch
        start=time.perf_counter(); logits,states,identity=self.forward(text,capture)
        values=logits[self.ids[:n]]
        probs=torch.softmax(values,dim=0).detach().cpu().tolist()
        raw=torch.log_softmax(logits,dim=0)[self.ids[:n]].detach().cpu().tolist()
        return dict(probabilities=probs,letter_logprobs=raw,seconds=time.perf_counter()-start,
                    identity=identity),states

    def close(self):
        import torch
        for h in self.deadline_handles:h.remove()
        del self.model
        torch.cuda.empty_cache()
