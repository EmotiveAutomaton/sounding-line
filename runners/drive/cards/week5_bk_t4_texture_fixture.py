"""Full 200-draw texture refit and genre fallback native handler fixture."""
from pathlib import Path
from threadpoolctl import threadpool_limits
from . import week5_bk_t4_texture as card
from .week5_bk_t4_fixture import fixture_bundle
from .timing_census import read
from .timing_p6 import gzip_equal,write_equal,progress


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Fixture takes no human input')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);bundle=fixture_bundle()
    for h in ('train','test'):bundle['packed'][h]=dict(bundle['packed'][h],genres=['creative']*36)
    checks=card.weights.known_answers();source=root/'constructed-source'
    genre=card.genre_bundle(bundle,'creative');gzip_equal(source/'output/BUNDLE.json.gz',genre)
    old=card.authenticate;card.authenticate=lambda p:source
    try:(card.verify if verifying else card.execute)(root/'genre-fallback',dict(source_root=str(source)),dict(operation='genre_fallback'))
    finally:card.authenticate=old
    with threadpool_limits(limits=2):
        point=card.pair({h:card.core.packing.arrays(bundle['packed'],h) for h in ('train','test')},bundle['covariates'],range(3));point['binding']='constructed'
        if abs(point['gain'])>1e-10:raise ValueError('Exact zero-feature contrast failed')
        blocks=[]
        for kind,total in [('calibration',40),('bootstrap',200)]:
            for start in range(0,total,20):
                records=[]
                for index in range(start,min(start+20,total)):
                    value=card.draw(bundle,kind,index)
                    if kind=='bootstrap' and abs(value['gain'])>1e-10:raise ValueError('Refit null changed')
                    records.append(dict(index=index,status='complete',value=value,binding='constructed'))
                block=dict(binding='constructed',kind=kind,records=records);p=root/f'{kind}-{start:04d}.json'
                if verifying:
                    if read(p)!=block:raise ValueError('Fresh identified-weight refit differs')
                else:write_equal(p,block)
                blocks.append(block);progress(root/'PROGRESS.json',dict(kind=kind,draws=start+len(records),total=total,phase='verify' if verifying else 'execute'))
        result=card.reduce_values(point,blocks,200)
    if result['calibration']['gate']:raise ValueError('Uninformative features falsely passed calibration')
    receipt=dict(fixture_only=True,checks=checks,actual_kernel_refits=True,bootstrap_draws=200,matched_worlds=40,
                 primary_exact_zero=True,uninformative_calibration_refused=True,actual_pooled_fallback_handler=True)
    for name,value in [('RESULT.json',result),('FIXTURE.json',receipt)]:
        if verifying:
            if read(root/name)!=value:raise ValueError('Complete texture fixture differs')
        else:write_equal(root/name,value)
    return dict(verified=True,complete_200_draw_texture_refit=True) if verifying else dict(status='complete',fixture_only=True)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)

if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
