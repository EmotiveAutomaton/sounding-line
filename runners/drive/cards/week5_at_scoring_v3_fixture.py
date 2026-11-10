"""Native v3 checkpoint and exact v2-score fixture, using a tiny real transformer."""
from pathlib import Path
from . import week5_at_scoring_v3 as scorer
from .week5_at_fixture import fixture_loader
from .timing_census import read
from .timing_p6 import write_equal


def run(output, inputs, config, verifying=False):
    if inputs or config: raise ValueError('Constructed fixture takes no human inputs')
    root=Path(output); rows=[dict(row_key=str(i),final_prefix='a '*i,target='b') for i in range(18)]
    old_loader=scorer.load_model;old_progress=scorer.progress
    scorer.load_model=fixture_loader
    marker=root/'scores/YIELD_REQUEST.json'
    def progress(path, value):
        old_progress(path,value)
        if value['words']==8: write_equal(marker, {'reason':'constructed resource interrupt'})
    try:
        if not verifying:
            scorer.progress=progress
            value=scorer.score_batch(root/'scores',rows,dict(model='constructed',revision='fixture'),context_length=64)
            if value.get('status')!='yielded' or value['completed']!=8:raise ValueError('Sealed block did not yield')
            marker.unlink();scorer.progress=old_progress
        value=scorer.score_batch(root/'scores',rows,dict(model='constructed',revision='fixture'),context_length=64,verifying=verifying)
    finally:
        scorer.load_model=old_loader;scorer.progress=old_progress
    receipt=dict(fixture_only=True,sealed_block_yield=True,resumed_complete_scores=True,numerical_reader='tiny real GPT2')
    if verifying:
        if read(root/'FIXTURE.json')!=receipt or not value['verified']:raise ValueError('Fresh scoring replay failed')
        return dict(verified=True, complete_scoring_replay=True)
    write_equal(root/'FIXTURE.json',receipt);return dict(status='complete',fixture_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)


if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
