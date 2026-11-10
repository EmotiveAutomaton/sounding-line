"""Exact original 16-text encoding batches with immutable cooperative checkpoints."""
from pathlib import Path
import time
import numpy as np
from runners.stage14.common import read, digest, filehash
from .timing_p6 import gzread
from . import week5_bk_wb1_source as source
from . import week3_pieces_effects_h1 as effects


class YieldRequested(Exception):
    pass


class Encoder:
    def __init__(self, root, model_path, mode, binding, verifying, began):
        self.root=Path(root);self.model_path=model_path;self.mode=mode
        self.binding=binding;self.verifying=verifying;self.began=began
        self.encoder=None;self.current=None;self.call=0

    def begin_session(self,index,identity):
        self.current=(index,digest(identity));self.call=0

    def vectors(self,texts,context=False):
        if self.current is None or not texts:raise ValueError('Bound original nonempty encoding call required')
        index,identity=self.current;call=self.call;self.call+=1
        complete=[];scopes=[]
        for start in range(0,len(texts),16):
            if (self.root/'YIELD_REQUEST.json').exists() or time.monotonic()-self.began>=1200:
                raise YieldRequested('sealed original 16-text encoding boundary')
            block=texts[start:start+16]
            binding=dict(source=self.binding,session=index,identity=identity,call=call,start=start,
                         texts_sha256=digest(block),context=context,mode=self.mode,
                         original_encoder_sha256=filehash(effects.__file__))
            path=self.root/'vectors'/f'session-{index:04d}-call-{call}-batch-{start:06d}.json.gz'
            seal=path.with_suffix('.seal.json');proof=path.with_suffix('.verified.json')
            cached=None
            if path.exists() and seal.exists():
                cached=gzread(path)
                if read(seal)!=dict(binding=binding,sha256=filehash(path)) or cached['binding']!=binding:
                    raise ValueError('Original encoding batch binding or bytes changed')
            if self.verifying and cached is None:raise ValueError('Missing execute batch for independent verification')
            evidence=dict(binding=binding,sha256=filehash(path),verifier_sha256=filehash(__file__)) if cached else None
            already_verified=self.verifying and proof.exists() and read(proof)==evidence
            if cached is None or (self.verifying and not already_verified):
                if self.encoder is None:self.encoder=effects.FrozenEncoder(self.model_path,self.mode)
                vectors,scope=self.encoder.vectors(block,context=context)
                value=dict(binding=binding,dtype=vectors.dtype.str,vectors=vectors.tolist(),scopes=scope)
                source.checked(path,value,self.verifying,True)
                source.checked(seal,dict(binding=binding,sha256=filehash(path)),self.verifying)
                cached=value
                if self.verifying:
                    source.checked(proof,dict(binding=binding,sha256=filehash(path),verifier_sha256=filehash(__file__)))
            arr=np.asarray(cached['vectors'],dtype=cached['dtype'])
            if arr.ndim!=2 or len(arr)!=len(block) or not np.isfinite(arr).all() or len(cached['scopes'])!=len(block):
                raise ValueError('Invalid checkpointed original encoder output')
            complete.append(arr);scopes.extend(cached['scopes'])
        return np.concatenate(complete,axis=0),scopes
