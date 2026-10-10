"""Frozen CPU encoder rival, not fitting on later targets.

DESIGN CHECK: LESSONS 2-5. NULL: mismatched option order or nonfinite embeddings
refuses; no labels enter this representation. ALTERNATIVE: pinned frozen native
encoding supplies an independent feature rival with explicit bounded context.
"""
import numpy as np
from .common import read,freeze,digest
from runners.stage13.detectors import cached_model,model_pins

def run(card,out,raw,tick):
    import torch
    from transformers import AutoTokenizer,AutoModel
    torch.set_num_threads(1);path=cached_model(card['backbone']);identity=model_pins(path)
    if identity!=card['model_files']:raise ValueError('encoder changed')
    tok=AutoTokenizer.from_pretrained(path,local_files_only=True,trust_remote_code=False);model=AutoModel.from_pretrained(path,local_files_only=True,trust_remote_code=False).eval();rows=read(raw/'jobs'/card['requires'][0]/'READER.json');cache={};features={};truncated=0
    rng=np.random.default_rng(141010);projection=rng.normal(size=(model.config.hidden_size,16))/4
    def encode(text):
        nonlocal truncated
        key=digest(text)
        if key not in cache:
            ids=tok.encode(text,add_special_tokens=True);truncated+=len(ids)>128
            batch=tok(text,return_tensors='pt',max_length=128,truncation=True)
            with torch.inference_mode():
                hidden=model(**batch).last_hidden_state;mask=batch['attention_mask'][...,None];v=(hidden*mask).sum(1)/mask.sum(1)
                v=v[0].numpy();v=v/max(np.linalg.norm(v),1e-12)
            if not np.isfinite(v).all():raise ValueError('nonfinite frozen embedding')
            cache[key]=v
        return cache[key]
    for i,r in enumerate(rows):
        e=r['evidence'];doc=encode(e['document'][-512:]);options=[encode(a) for a in e['alternatives']]
        a=np.array([[float(v@doc),*(v@projection)] for v in options]);a-=a.mean(0);features[r['key']]=a.tolist()
        if i%128==0:tick(dict(opportunities=i+1,total=len(rows)))
    freeze(out/'FEATURES.json',features);freeze(out/'MODEL.json',dict(files=identity,backbone=card['backbone'],pooling='masked token mean, unit L2 norm',projection='fixed seed 141010 Gaussian 16 dimensions',device='cpu'))
    freeze(out/'SUMMARY.json',dict(opportunities=len(rows),unique_texts=len(cache),truncated_texts=truncated,view='last 512 document characters; complete candidate passed to encoder with explicit 128 native-token cap; lexical rival retains full candidate',labels_accessed=False))
    freeze(out/'ADMISSION.json',dict(admitted=True,representation_only=True))
