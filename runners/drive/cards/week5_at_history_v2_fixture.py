"""Native full 2,000-draw AT1 checkpoint replay and frozen-v1 equivalence."""
from pathlib import Path
from . import week5_at_history_v2 as card
from . import week5_at_history as old
from .week5_at_full_fixture import ConstructedBank
from .timing_census import read
from .timing_p6 import write_equal


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('AT1 checkpoint fixture takes no human input')
    root=Path(output);root.mkdir(parents=True,exist_ok=True)
    write_equal(root/'CONSTRUCTED.json',dict(fixture_only=True,bank='fixed recipient records; donors redrawn by original global RNG'))
    data=dict(fixture=str(root/'CONSTRUCTED.json'));original_load=old.load;original_estimate=old.estimate
    old.load=lambda inputs,config=None:ConstructedBank()
    invoke=card.verify if verifying else card.execute;blocks=[]
    try:
        # Prove that splitting, pausing and fresh replay preserve v1 bytes.
        cfg=dict(draws=2000,draw_start=0,draw_count=3)
        (old.verify if verifying else old.execute)(root/'v1-reference',data,cfg)
        paused=root/'v2-reference';paused.mkdir(parents=True,exist_ok=True)
        if not verifying:
            write_equal(paused/'YIELD_REQUEST.json',dict(reason='before-load fixture'))
            if card.execute(paused,data,cfg).get('status')!='yielded' or (paused/'point.json').exists():raise ValueError('Preload pause failed')
            (paused/'YIELD_REQUEST.json').unlink()
            calls=0
            def pause_after_one_draw(*args,**kwargs):
                nonlocal calls
                value=original_estimate(*args,**kwargs);calls+=1
                if calls==2:write_equal(paused/'YIELD_REQUEST.json',dict(reason='after-one-draw fixture'))
                return value
            old.estimate=pause_after_one_draw
            try:result=card.execute(paused,data,cfg)
            finally:old.estimate=original_estimate
            if result.get('status')!='yielded' or result.get('completed')!=1 or not (paused/'draw-0000.receipt.json').exists() or (paused/'draw-0001.json').exists():raise ValueError('Draw boundary was not sealed')
            (paused/'YIELD_REQUEST.json').unlink()
        invoke(paused,data,cfg)
        if read(paused/'BLOCK.json')!=read(root/'v1-reference/BLOCK.json'):raise ValueError('Frozen v1 estimand or donor RNG changed')
        for start in range(0,2000,100):
            dest=root/f'block-{start:04d}';cfg=dict(draws=2000,draw_start=start,draw_count=100)
            invoke(dest,data,cfg);blocks.append(read(dest/'BLOCK.json'))
        result=old.reduce_values(blocks)
        if result['complete_draws']!=2000 or result['primary']['state']!='supports':raise ValueError('Full signed donor fixture failed')
        # A corrupted seal must fail closed without a scientific refit.
        if not verifying:
            seal=paused/'draw-0000.receipt.json';original=seal.read_bytes();seal.write_text('{"sha256":"wrong"}\n',encoding='utf8')
            try:
                try:card.execute(paused,data,dict(draws=2000,draw_start=0,draw_count=3))
                except ValueError as error:
                    if 'seal differs' not in str(error):raise
                else:raise ValueError('Changed checkpoint seal accepted')
            finally:seal.write_bytes(original)
    finally:old.load=original_load;old.estimate=original_estimate
    receipt=dict(fixture_only=True,complete_actual_block_handlers=True,global_draws=2000,original_point_and_draw_rng=True,
                 frozen_v1_block_byte_equivalence=True,preload_resource_pause=True,one_draw_sealed_yield_resume=True,changed_seal_refused=True)
    for name,value in [('RESULT.json',result),('FIXTURE.json',receipt)]:
        if verifying:
            if read(root/name)!=value:raise ValueError('Full checkpoint fixture reduction differs')
        else:write_equal(root/name,value)
    return dict(verified=True,complete_2000_checkpoint_replay=True) if verifying else dict(status='complete',fixture_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)

if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
