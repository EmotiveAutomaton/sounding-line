"""Native tiny-transformer proof of complete GO1 numerical inheritance.

DESIGN CHECK: real sealed dependency validation, actual causal inference,
whole score replay and complete uncertainty; all texts and vectors constructed.
"""
from pathlib import Path
import argparse
import hashlib
import json
import time
import numpy as np
from . import week5_go1_pipeline_v2 as go
from . import week5_at_scoring_v4 as scoring
from .week5_at_fixture import fixture_loader
from .week5_at_scoring import digest


def load(manifest):
    if manifest!={'model':'constructed','revision':'fixed','files':{}}:raise ValueError('Constructed model only')
    model,tokenizer,torch=fixture_loader(manifest)
    class Tokenizer:
        eos_token_id=0;bos_token_id=0
        def __call__(self,text,**kwargs):return tokenizer(text,**kwargs)
        def encode(self,text,**kwargs):return tokenizer(text)['input_ids']
    model.double()
    assert all(p.dtype==torch.float64 for p in model.parameters())
    return model,Tokenizer(),torch


def vectors(texts,manifest,cache=None,on_vector=None):
    cache={} if cache is None else dict(cache)
    for text in dict.fromkeys(texts):
        if text in cache:continue
        seed=int.from_bytes(hashlib.sha256(text.encode()).digest()[:8],'big')
        vector=np.random.default_rng(seed).normal(size=384).astype(np.float32)
        vector/=np.linalg.norm(vector);cache[text]=vector
        if on_vector is not None:on_vector(text,vector)
    return np.asarray([cache[text] for text in texts])


def expected_refusal(fn,label):
    try:fn()
    except ValueError:return
    raise AssertionError(label+' accepted')


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Constructed fixture only')
    root=Path(output);root.mkdir(parents=True,exist_ok=True)
    rows=[dict(repository='eips',type='Standards Track',category='Core',author=f'constructed-{i}',document=str(i),
               motivation=f'goal {i}',rest=f'topic {i}') for i in range(24)]
    rows[-1]['rest']='long '*20
    documents=root/'documents.json';go.core.write(documents,dict(documents=rows))
    model=dict(model='constructed',revision='fixed',files={});manifest=root/'model.json';go.core.write(manifest,model)
    encoder=root/'encoder.json';go.core.write(encoder,dict(constructed_only=True))
    selection=root/'selection';result=dict(card='AT2',selection_admissible=True,selected_model='constructed')
    go.core.write(selection/'output/RESULT.json',result)
    selected=dict(model=model['model'],revision=model['revision'],manifest_sha256=digest(model),numerical_spec=scoring.NUMERICAL_SPEC)
    go.core.write(selection/'output/READER_BINDING.json',selected)
    go.core.write(selection/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,
        outputs={p.relative_to(selection).as_posix():go.core.sha(p) for p in (selection/'output').glob('*.json')}))
    args=dict(documents=str(documents),model_manifest=str(manifest),encoder_manifest=str(encoder),at2_selection=str(selection))
    cfg=dict(phase='GO1-score',reader='language_model',distractors=1,context_length=64)
    old_loader,old_vectors=scoring.load_model,go.readers.embeddings
    scoring.load_model=load;go.readers.embeddings=vectors
    try:
        out=root/'language_model'
        if not verifying:
            paused=go.execute(out,args,{**cfg,'max_new_queries':1})
            assert paused.get('status')=='yielded'
            assert len(list((out/'queries').glob('[0-9]*.json')))==2 # row and seal
        completed=go.execute(out,args,cfg)
        assert completed['selected_reader_binding']==go.reader_binding(args)
        assert go.verify(out,args,cfg)['verified']
        for name in ('tfidf','encoder'):
            value=go.execute(root/name,args,{**cfg,'reader':name})
            assert value['rows']==24 and go.verify(root/name,args,{**cfg,'reader':name})['verified']
        collection={**args,'readers':{name:str(root/name) for name in ('tfidf','encoder','language_model')}}
        collection_cfg=dict(phase='GO1-collect',distractors=1,draws=2000)
        complete=go.execute(root/'collected',collection,collection_cfg)
        assert complete['selected_reader_binding']==go.reader_binding(args)
        assert go.verify(root/'collected',collection,collection_cfg)['verified']
        bank={name:np.load(root/name/'scores.npy') for name in collection['readers']}
        supported=np.logical_and.reduce([np.isfinite(v).all(axis=1) for v in bank.values()])
        assert supported.sum()==23
        receipt=out/'SCORED.json';saved=receipt.read_bytes();changed=json.loads(saved);changed.pop('selected_reader_binding')
        go.core.write(receipt,changed)
        try:expected_refusal(lambda:go.execute(root/'rejected-old-bank',collection,collection_cfg),'old numerical bank')
        finally:receipt.write_bytes(saved)
        path=out/'queries/000000.json';saved=path.read_bytes();seal=path.with_suffix('.seal.json');seal_saved=seal.read_bytes()
        changed=json.loads(saved);changed['binding']='old-FP32';go.core.write(path,changed);go.core.write(seal,dict(sha256=go.core.sha(path)))
        try:expected_refusal(lambda:go.execute(out,args,cfg),'old row checkpoint')
        finally:path.write_bytes(saved);seal.write_bytes(seal_saved)
        changed=dict(model,revision='changed');go.core.write(manifest,changed)
        try:expected_refusal(lambda:go.reader_binding(args),'changed selected revision')
        finally:go.core.write(manifest,model)
        got=np.load(out/'scores.npy');replayed=np.load(out/'independent-replay/scores.npy')
        assert np.array_equal(got,replayed,equal_nan=True)
    finally:scoring.load_model=old_loader;go.readers.embeddings=old_vectors
    proof=dict(constructed_only=True,actual_tiny_transformer_float64=True,encoder_vectors_constructed=True,
        real_sealed_selection_authenticator=True,selected_revision_numerical_spec_and_manifest_bound=True,
        summed_token_likelihood_enforced=True,complete_24_row_score_replay=True,common_context_supported=23,
        complete_2000_draw_author_collection=True,one_row_pause_resume=True,legacy_score_bank_and_row_binding_refused=True,
        changed_revision_refused=True,scientific_admission=False)
    if verifying:
        assert json.loads((root/'FIXTURE.json').read_text('utf8'))==proof
        return dict(verified=True,complete_native_handler_replay=True)
    go.core.write(root/'FIXTURE.json',proof)
    return dict(status='complete',fixture_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)


if __name__=='__main__':
    from threadpoolctl import threadpool_limits
    parser=argparse.ArgumentParser();parser.add_argument('output');parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    began=time.process_time()
    with threadpool_limits(limits=2):value=(verify if args.verify else execute)(Path(args.output),{}, {})
    go.core.write(Path(args.output)/('NATIVE_VERIFY_CPU.json' if args.verify else 'NATIVE_EXECUTE_CPU.json'),dict(cpu_seconds=time.process_time()-began))
    print(json.dumps(value))
