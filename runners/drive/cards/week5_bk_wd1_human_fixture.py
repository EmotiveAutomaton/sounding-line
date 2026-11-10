"""Constructed native corrected-fit handler, exact reuse and full uncertainty."""
from pathlib import Path
import numpy as np
from . import week5_bk_wd1_human as producer
from . import week5_bk_wd1 as bank
from .week5_bk_wd1_fixture import profiles
from .timing_census import read,filehash
from .timing_p6 import gzip_equal,write_equal


def summary_bundle():
    rng=np.random.default_rng(91);a=np.linspace(-1,1,12)
    real=profiles(a,a+.01*np.sin(np.arange(12)))
    fake=[profiles(rng.normal(size=12),rng.normal(size=12)) for _ in range(1000)]
    bundle=dict(real=real,reused={str(i):dict(value=fake[i]) for i in range(940)},missing=list(range(940,1000)),bank=dict(writers=sorted(real['profiles'])))
    binding=producer.digest(bundle)
    blocks=[dict(binding=binding,records=[dict(index=i,status='complete',value=fake[i]) for i in range(start,start+20)]) for start in (940,960,980)]
    return bundle,blocks


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Fixture has no human input')
    root=Path(output);source=root/'constructed-source'
    world=bank.make_world('stable',0,bank.original.configuration('constructed'))
    world.update(missing=[1],proof=dict(solver_sha256=filehash(producer.solver.__file__)),config=dict(seed=world['seed'],pca_dimensions=16))
    gzip_equal(source/'output/BUNDLE.json.gz',world)
    old=producer.authenticate;producer.authenticate=lambda p:source
    try:
        (producer.verify if verifying else producer.execute)(root/'fit',dict(source_root=str(source)),dict(operation='block',start=0,count=1))
    finally:producer.authenticate=old
    block=read(root/'fit/BLOCK.json')
    if block['records'][0]['status']!='complete':raise ValueError('Original new-assignment fit failed')
    bundle,blocks=summary_bundle();value=producer.reduce_values(bundle,blocks)
    if value['state']!='positive' or value['bootstrap_draws']!=2000 or value['permutation_draws']!=1000:raise ValueError('Full corrected reduction failed')
    try:producer.reduce_values(bundle,blocks[:-1])
    except ValueError:pass
    else:raise ValueError('Missing assignments accepted')
    receipt=dict(fixture_only=True,actual_original_solver_handler=True,exact_reuse=940,new_reference_profiles=60,
                 summary_draws=2000,references=1000,partial_collection_refused=True,no_fake_completion=True)
    for name,record in [('RESULT.json',value),('FIXTURE.json',receipt)]:
        if verifying:
            if read(root/name)!=record:raise ValueError('Complete corrected native fixture differs')
        else:write_equal(root/name,record)
    return dict(verified=True,complete_new_fit_and_full_reduction_replay=True) if verifying else dict(status='complete',fixture_only=True)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)

if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
