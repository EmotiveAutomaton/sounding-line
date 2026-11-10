"""Pinned small MiniLM, original batch equality and interrupted verification.

DESIGN CHECK: LESSONS3--5. All texts are constructed. A missing or changed
batch refuses; checkpointing preserves exact original arrays and token scopes.
"""
from pathlib import Path
import math
import shutil
import time
import numpy as np
from threadpoolctl import threadpool_limits
from runners.stage14.common import read,filehash,digest
from .timing_p6 import write_equal
from . import week5_bk_wb1_source as source
from . import week5_bk_wb1_vectors as checkpoint
from . import week3_pieces_effects_h1 as effects


def comparison(actual,expected):
    if not np.array_equal(actual[0],expected[0]) or actual[1]!=expected[1]:
        raise ValueError('Original frozen encoder arrays or token scopes changed')


def run(output,inputs,config,verifying=False):
    if set(inputs)!={'content_model','content_complete'} or config:
        raise ValueError('Exact original small encoder identity required')
    source.model(inputs,'corpus');root=Path(output);root.mkdir(parents=True,exist_ok=True)
    if (root/'YIELD_REQUEST.json').exists():return dict(status='yielded',reason='before small constructed encoder')
    texts=[('alpha beta '*160 if i%13==0 else 'alpha '*(i%19+1))+f'word {i} caf\u00e9 \U0001f642.' for i in range(49)]
    prompt=['A constructed prompt '+('gamma '*300)]
    binding=digest(dict(texts=texts,prompt=prompt,model=filehash(inputs['content_model'])))
    raw=effects.FrozenEncoder(inputs['content_model'],'corpus')
    expected_prompt=raw.vectors(prompt);expected=raw.vectors(texts,context=True)
    target=root/'complete'
    if verifying:
        target=root/'fresh_verification'/str(time.time_ns())
        shutil.copytree(root/'complete',target,ignore=shutil.ignore_patterns('*.verified.json'))
    current=checkpoint.Encoder(target,inputs['content_model'],'corpus',binding,verifying,time.monotonic())
    current.begin_session(0,dict(binding=binding))
    comparison(current.vectors(prompt),expected_prompt)
    comparison(current.vectors(texts,context=True),expected)
    if not verifying:
        proof=checkpoint.Encoder(root/'complete',inputs['content_model'],'corpus',binding,True,time.monotonic())
        proof.begin_session(0,dict(binding=binding))
        comparison(proof.vectors(prompt),expected_prompt);comparison(proof.vectors(texts,context=True),expected)
    interrupted=root/'interrupted'
    class Traced:
        calls=0
        def vectors(self,items,context=False):
            self.calls+=1;value=raw.vectors(items,context=context)
            if self.calls==1:write_equal(interrupted/'YIELD_REQUEST.json',dict(reason='constructed batch interrupt'))
            return value
    if not verifying:
        tracing=Traced();part=checkpoint.Encoder(interrupted,inputs['content_model'],'corpus',binding,False,time.monotonic())
        part.encoder=tracing;part.begin_session(1,dict(binding=binding))
        try:part.vectors(texts,context=True)
        except checkpoint.YieldRequested:pass
        else:raise ValueError('Batch-boundary yield absent')
        first=interrupted/'vectors/session-0001-call-0-batch-000000.json.gz';before=filehash(first)
        (interrupted/'YIELD_REQUEST.json').unlink()
        resumed=checkpoint.Encoder(interrupted,inputs['content_model'],'corpus',binding,False,time.monotonic())
        resumed.begin_session(1,dict(binding=binding));comparison(resumed.vectors(texts,context=True),expected)
        if filehash(first)!=before:raise ValueError('Completed array changed at resume')
        tracing=Traced();check=checkpoint.Encoder(interrupted,inputs['content_model'],'corpus',binding,True,time.monotonic())
        check.encoder=tracing;check.begin_session(1,dict(binding=binding))
        try:check.vectors(texts,context=True)
        except checkpoint.YieldRequested:pass
        else:raise ValueError('Independent verification did not yield after sealing a batch')
        proof=first.with_suffix('.verified.json');before=filehash(proof)
        (interrupted/'YIELD_REQUEST.json').unlink()
        resumed=checkpoint.Encoder(interrupted,inputs['content_model'],'corpus',binding,True,time.monotonic())
        resumed.begin_session(1,dict(binding=binding));comparison(resumed.vectors(texts,context=True),expected)
        if filehash(proof)!=before:raise ValueError('Independent verification proof replaced')
    else:
        fresh=root/'interrupted_fresh_verification'/str(time.time_ns())
        shutil.copytree(interrupted,fresh,ignore=shutil.ignore_patterns('*.verified.json'))
        check=checkpoint.Encoder(fresh,inputs['content_model'],'corpus',binding,True,time.monotonic())
        check.begin_session(1,dict(binding=binding));comparison(check.vectors(texts,context=True),expected)
    changed=checkpoint.Encoder(interrupted,inputs['content_model'],'corpus',binding,False,time.monotonic())
    changed.begin_session(1,dict(binding='changed'))
    try:changed.vectors(texts,context=True)
    except ValueError:pass
    else:raise ValueError('Changed original session identity accepted')
    first=interrupted/'vectors/session-0001-call-0-batch-000000.json.gz';saved=first.read_bytes()
    try:
        first.write_bytes(saved+b'tamper')
        changed=checkpoint.Encoder(interrupted,inputs['content_model'],'corpus',binding,False,time.monotonic())
        changed.begin_session(1,dict(binding=binding))
        try:changed.vectors(texts,context=True)
        except ValueError:pass
        else:raise ValueError('Altered vector bytes accepted')
    finally:first.write_bytes(saved)
    receipt=dict(fixture_only=True,constructed_texts=50,actual_pinned_minilm=True,exact_arrays_and_scopes=True,
                 original_batch_size=16,partial_final_batch=True,first_and_last_254_token_views=True,
                 interrupted_execute_and_verify_resumed=True,independent_fresh_verification_without_prior_proofs=True,
                 changed_identity_and_bytes_refused=True,model_sha256=filehash(inputs['content_model']))
    source.checked(root/'FIXTURE.json',receipt,verifying)
    return dict(verified=True,complete_original_encoder_replay=True) if verifying else dict(status='complete',fixture_only=True)


def execute(output,inputs,config):
    with threadpool_limits(limits=2):return source.timed(run,output,inputs,config,False)
def verify(output,inputs,config):
    with threadpool_limits(limits=2):return source.timed(run,output,inputs,config,True)
