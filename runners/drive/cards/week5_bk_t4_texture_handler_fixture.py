"""Constructed complete texture block, projection, gate, and reduction I/O proof."""
from pathlib import Path
from threadpoolctl import threadpool_limits
from . import week5_bk_t4_texture as card
from .week5_bk_t4_fixture import fixture_bundle
from .timing_census import read,filehash
from .timing_p6 import gzip_equal,write_equal


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Constructed fixture accepts no human input')
    root=Path(output);root.mkdir(parents=True,exist_ok=True)
    bundle=fixture_bundle()
    for half in ('train','test'):bundle['packed'][half]['genres']=['creative']*len(bundle['packed'][half]['w'])
    source=root/'constructed-source';gzip_equal(source/'output/BUNDLE.json.gz',bundle)
    binding=card.core.digest(dict(source=filehash(source/'output/BUNDLE.json.gz'),model='unit-directions-v1',seed=20261107))
    old=card.authenticate
    # This bypass authenticates only this fixture's local synthetic directories.
    # No COMPLETE marker is manufactured; production authentication is unchanged.
    def fixture_auth(path):
        p=Path(path)
        if not p.resolve().is_relative_to(root.resolve()):raise ValueError('Nonfixture authentication refused')
        return p
    card.authenticate=fixture_auth
    invoke=card.verify if verifying else card.execute
    try:
        with threadpool_limits(limits=2):
            genre=root/'genre';invoke(genre/'output',dict(source_root=str(source)),dict(operation='genre',genre='creative'))
            invoke(root/'genre-fallback/output',dict(source_root=str(genre)),dict(operation='genre_fallback'))
            point=card.pair({h:card.core.packing.arrays(bundle['packed'],h) for h in ('train','test')},bundle['covariates'],range(3))
            point['binding']=binding
            if abs(point['gain'])>1e-10:raise ValueError('Constructed zero-feature point contrast changed')
            point_root=root/'constructed-point';write_equal(point_root/'output/POINT.json',point)
            blocks=[];cal=[]
            for kind,total in [('calibration',40),('bootstrap',200)]:
                for start in range(0,total,20):
                    block=root/f'{kind}-{start:04d}';args=dict(source_root=str(source))
                    if kind=='bootstrap':args['point_root']=str(point_root)
                    invoke(block/'output',args,dict(operation='block',kind=kind,start=start,count=20))
                    value=read(block/'output/BLOCK.json')
                    if any(r['status']!='complete' for r in value['records']):raise ValueError('Constructed actual handler rejected a fit')
                    if kind=='bootstrap' and any(abs(r['value']['gain'])>1e-10 for r in value['records']):raise ValueError('Refit null changed')
                    blocks.append(str(block))
                    if kind=='calibration':cal.append(str(block))
            write_equal(root/'BLOCKS.json',blocks);write_equal(root/'CALIBRATION_BLOCKS.json',cal)
            reduce_inputs=dict(source_root=str(source),point_root=str(point_root),blocks=str(root/'BLOCKS.json'))
            invoke(root/'reduction/output',reduce_inputs,dict(operation='reduce',draws=200))
            result=read(root/'reduction/output/RESULT.json')
            if result['calibration']['gate']:raise ValueError('Flat features passed calibration')
            try:invoke(root/'forbidden-point/output',dict(source_root=str(source),calibration_blocks=str(root/'CALIBRATION_BLOCKS.json')),dict(operation='point'))
            except ValueError as error:
                if 'matched calibration failed' not in str(error):raise
            else:raise ValueError('Failed calibration allowed a point fit')
            write_equal(root/'INCOMPLETE_BLOCKS.json',blocks[:-1])
            try:invoke(root/'incomplete/output',dict(reduce_inputs,blocks=str(root/'INCOMPLETE_BLOCKS.json')),dict(operation='reduce',draws=200))
            except ValueError as error:
                if 'Incomplete texture' not in str(error):raise
            else:raise ValueError('Incomplete uncertainty accepted')
            # Resource pause occurs only after a complete, sealed fitted draw.
            pause=root/'pause/output';pause.mkdir(parents=True,exist_ok=True)
            args=dict(source_root=str(source));conf=dict(operation='block',kind='calibration',start=0,count=2)
            if not verifying:
                write_equal(pause/'YIELD_REQUEST.json',dict(reason='constructed boundary request'))
                if card.execute(pause,args,conf).get('status')!='yielded':raise ValueError('Checkpoint yield ignored')
                if not (pause/'draw-0000.receipt.json').exists() or (pause/'draw-0001.json').exists():raise ValueError('Yield boundary not sealed')
                (pause/'YIELD_REQUEST.json').unlink()
                card.execute(pause,args,conf)
            else:card.verify(pause,args,conf)
    finally:card.authenticate=old
    receipt=dict(fixture_only=True,actual_block_handlers=True,bootstrap_refits=200,matched_calibration_refits=40,
                 actual_projection_and_fallback=True,complete_reduction=True,failed_calibration_refused=True,
                 incomplete_uncertainty_refused=True,sealed_resource_yield_and_resume=True)
    if verifying:
        if read(root/'FIXTURE.json')!=receipt:raise ValueError('Handler fixture receipt differs')
        return dict(verified=True,complete_actual_texture_handler_replay=True)
    write_equal(root/'FIXTURE.json',receipt);return dict(status='complete',fixture_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)

if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
