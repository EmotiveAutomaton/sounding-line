"""Actual tiny-transformer paired LA score handler and resource-yield proof."""
from pathlib import Path
from . import week5_la_pipeline_v2 as producer
from .week5_at_fixture import fixture_loader
from .timing_census import read,filehash
from .timing_p6 import gzip_equal,write_equal


def masked_loader(manifest):
    import torch
    from transformers import RobertaConfig,RobertaForMaskedLM
    class Tokenizer:
        mask_token_id=3
        def __call__(self,text,**kwargs):return dict(input_ids=[ord(c)%30+4 for c in text])
        def build_inputs_with_special_tokens(self,ids):return [0]+ids+[2]
    torch.set_num_threads(2);torch.manual_seed(5)
    model=RobertaForMaskedLM(RobertaConfig(vocab_size=40,hidden_size=16,num_hidden_layers=1,num_attention_heads=2,
        intermediate_size=24,max_position_embeddings=514,pad_token_id=1,bos_token_id=0,eos_token_id=2)).eval()
    return model,Tokenizer(),torch


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('No human inputs in fixture')
    root=Path(output);selection=root/'constructed-selection';selection.mkdir(parents=True,exist_ok=True)
    write_equal(selection/'output/RESULT.json',dict(card='AT2',selected_model='constructed',selection_admissible=True))
    gzip_equal(root/'ROWS.json.gz',[dict(id=str(i),causal_prefix='a ',target='b',previous='old') for i in range(2)])
    for name in ('causal','masked'):write_equal(root/(name+'.json'),dict(model='constructed',revision='fixture'))
    args=dict(rows=str(root/'ROWS.json.gz'),causal_manifest=str(root/'causal.json'),masked_manifest=str(root/'masked.json'),selection_root=str(selection))
    saved=(producer.authenticate,producer.filehash,producer.load_model,producer.load_masked,producer.progress)
    producer.authenticate=lambda p:selection
    producer.filehash=lambda p:'constructed-selection' if Path(p).name=='COMPLETE.json' else filehash(p)
    producer.load_model=fixture_loader;producer.load_masked=masked_loader
    marker=root/'scores/YIELD_REQUEST.json'
    def progress(path,value):
        saved[-1](path,value)
        if value['acts']==1:write_equal(marker,dict(reason='constructed resource interrupt'))
    try:
        if not verifying:
            producer.progress=progress
            value=producer.score(root/'scores',args,dict(operation='score'))
            if value.get('status')!='yielded' or value['completed']!=1:raise ValueError('Paired act checkpoint did not yield')
            marker.unlink();producer.progress=saved[-1]
        value=producer.score(root/'scores',args,dict(operation='score'),verifying)
    finally:
        producer.authenticate,producer.filehash,producer.load_model,producer.load_masked,producer.progress=saved
    receipt=dict(fixture_only=True,actual_tiny_causal_and_masked_models=True,paired_act_yield=True,resume_complete=True,no_fake_completion=True)
    if verifying:
        if read(root/'FIXTURE.json')!=receipt or not value['verified']:raise ValueError('Full paired-score replay failed')
        return dict(verified=True,full_pair_score_handler_replay=True)
    write_equal(root/'FIXTURE.json',receipt);return dict(status='complete',fixture_only=True)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)

if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
