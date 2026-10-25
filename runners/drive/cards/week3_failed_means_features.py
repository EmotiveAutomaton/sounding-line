"""WC2 frozen MiniLM features with a separate first-tenth cost pilot.

DESIGN CHECK: LESSONS3-5/CONTROLS1-7, 2026-10-25. No outcome gate here.
Exact same prefix254 token view and CPUfloat32 mean pooling as completed
content_features_v2; no downloaded weights or GPU. Every required target,
unchosen offer, own window and matched context is encoded once; labels cannot
choose text exposure. Repeated text is exact, source/model corruption refuses,
and fresh verification re-encodes all admitted text. Pilot never licenses main.
"""
import hashlib
import math
import time
from pathlib import Path

import numpy as np

from . import week3_failed_means as stats
from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal,progress
from .timing_pmap_source import completed
from .timing_closure_measure import model_identity

CONFIG=dict(card='WC2-features',schema=1,mode='full',threads=2)
PILOT=dict(CONFIG,mode='pilot')
CONSTRUCTED=dict(CONFIG,mode='constructed')


def text_id(text):return hashlib.sha256(text.encode('utf8')).hexdigest()


class Encoder:
    def __init__(self,inputs,threads):
        import torch
        from transformers import AutoModel,AutoTokenizer
        self.torch=torch;torch.set_num_threads(threads)
        manifest=model_identity(inputs);self.manifest=manifest
        self.tokenizer=AutoTokenizer.from_pretrained(manifest['path'],local_files_only=True,trust_remote_code=False,use_fast=True)
        self.model=AutoModel.from_pretrained(manifest['path'],local_files_only=True,trust_remote_code=False).to('cpu',dtype=torch.float32).eval()
        if any(p.device.type!='cpu' or p.dtype!=torch.float32 for p in self.model.parameters()):raise ValueError('CPUfloat32 required')

    def vector(self,text):
        tok=self.tokenizer;t=self.torch
        raw=tok(text,add_special_tokens=False,return_offsets_mapping=True,truncation=False)
        used=raw['input_ids'][:254]
        if tok.cls_token_id is None or tok.sep_token_id is None:raise ValueError('BERT boundary tokens absent')
        ids=[tok.cls_token_id]+used+[tok.sep_token_id]
        with t.inference_mode():
            v=self.model(input_ids=t.tensor([ids]),attention_mask=t.ones((1,len(ids)),dtype=t.int64)).last_hidden_state.mean(1)[0].numpy().astype(np.float32)
        norm=float(np.linalg.norm(v))
        if norm<=0 or not math.isfinite(norm):raise ValueError('invalid embedding norm')
        v=v/norm
        if v.shape!=(384,) or not np.isfinite(v).all():raise ValueError('invalid MiniLM vector')
        return v.tolist(),dict(text_sha256=text_id(text),full_tokens=len(raw['input_ids']),used_tokens=len(used),
            truncated=len(raw['input_ids'])>254,visible_codepoint_end=raw['offset_mapping'][len(used)-1][1] if used else 0,
            native_ids=ids,pooling='all visible positions including CLS/SEP; arithmetic mean then L2norm')


class ConstructedEncoder:
    """Plumbing fixture only; cannot be dispatched with full/pilot configuration."""
    def vector(self,text):
        v=np.frombuffer(hashlib.sha256(text.encode()).digest(),dtype=np.uint8).astype(float)+1
        return (v/np.linalg.norm(v)).tolist(),dict(text_sha256=text_id(text),constructed_only=True)


def load(inputs,config):
    if config not in (CONFIG,PILOT,CONSTRUCTED):raise ValueError('fixed feature contract required')
    if config==CONSTRUCTED:
        if set(inputs)!={'fixture'}:raise ValueError('constructed fixture required')
        return read(inputs['fixture']),ConstructedEncoder()
    if set(inputs)!={'source_completion','content_complete','model_manifest'}:raise ValueError('complete sources and frozen model required')
    parent=Path(inputs['source_completion']).parent
    for name in ('EVENTS.json.gz','BINDING.json'):completed(inputs['source_completion'],parent/'output'/name)
    binding=read(parent/'output/BINDING.json')
    if binding['config']['mode']!='full':raise ValueError('partial source census cannot feed WC2')
    return gzread(parent/'output/EVENTS.json.gz'),Encoder(inputs,config['threads'])


def run(output,inputs,config,verification=False):
    started=time.perf_counter();cpu=time.process_time()
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    data,encoder=load(inputs,config);selected,texts=stats.required(data['events'])
    all_count=len(texts);texts=texts[:max(1,math.ceil(all_count/10))] if config==PILOT else texts
    binding=dict(config=config,inputs={k:filehash(v) for k,v in sorted(inputs.items())})
    encoded={};scopes={};ids=[]
    for index,text in enumerate(texts):
        v,scope=encoder.vector(text);key=text_id(text)
        if key in scopes:raise ValueError('duplicate text hash')
        encoded[text]=v;scopes[key]=scope;ids.append(key)
        if index%16==0 or index+1==len(texts):
            progress(output/'PROGRESS.json',dict(phase='verify' if verification else 'encode',done=index+1,total=len(texts)))
            if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():raise InterruptedError('owner requested yield')
    if texts and encoder.vector(texts[0])[0]!=encoded[texts[0]]:raise ValueError('repeat embedding differs')
    if config!=CONSTRUCTED:model_identity(inputs)
    if binding['inputs']!={k:filehash(v) for k,v in sorted(inputs.items())}:raise ValueError('source changed during encoding')
    summary=dict(card='WC2-features',mode=config['mode'],required_unique_texts=all_count,encoded=len(texts),
        selected_events=len(selected),model='constructed plumbing' if config==CONSTRUCTED else 'frozen all-MiniLM-L6-v2 CPUfloat32',
        scientific_admission=False,analysis_ready=config==CONFIG,
        forecast_policy='pilot source/load+selected first-tenth costs must be charged before separate whole-run admission')
    if verification:
        if (read(output/'BINDING.json')!=binding or read(output/'SUMMARY.json')!=summary
                or gzread(output/'VECTORS.json.gz')!=encoded or gzread(output/'SCOPES.json.gz')!=scopes):raise ValueError('fresh complete encoding differs')
        if config!=PILOT and gzread(output/'EVENTS.json.gz')!=dict(data,events=selected):raise ValueError('feature event population changed')
    else:
        write_equal(output/'BINDING.json',binding);write_equal(output/'SUMMARY.json',summary)
        gzip_equal(output/'VECTORS.json.gz',encoded);gzip_equal(output/'SCOPES.json.gz',scopes)
        if config!=PILOT:gzip_equal(output/'EVENTS.json.gz',dict(data,events=selected))
    timing=dict(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu,encoded=len(texts),required=all_count)
    phase='VERIFY' if verification else 'EXECUTE'
    # Timing is a receipt of actual work, not a deterministic scientific output.
    if not (output/(phase+'_TIME.json')).exists():write_equal(output/(phase+'_TIME.json'),timing)
    if verification and config==PILOT:
        first=read(output/'EXECUTE_TIME.json');scale=all_count/max(1,len(texts))
        write_equal(output/'FORECAST.json',dict(projected_execute_plus_verify_cpu_seconds=(first['cpu_seconds']+timing['cpu_seconds'])*scale,
            pilot_cpu_charge=first['cpu_seconds']+timing['cpu_seconds'],shared_card_cpu_ceiling_seconds=7200,
            excludes='source preparation and statistic/replay charges; owner adds all prior costs',scientific_admission=False))
    return dict(verified=True,full_encoding_replay=True) if verification else dict(status='complete',analysis_ready=summary['analysis_ready'])


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
