"""Small constructed banks through complete 2,000-draw AT primary handlers."""
from pathlib import Path
import numpy as np
from .week5_at_fixture import rows
from .week5_at_scoring import MODELS
from . import week5_at_analysis as analysis,week5_at_history as history
from .timing_census import read
from .timing_p6 import gzip_equal,write_equal,progress


class ConstructedBank:
    writers=list(range(20))
    def draw(self,writer,rng,*args):
        # Fixed recipient records; only the donor feature changes per draw.
        own_rng=np.random.default_rng(1000+writer);x=own_rng.normal(size=(24,8));noise=own_rng.normal(scale=.1,size=24)
        donor=rng.normal(size=24);values=[]
        for j in range(len(x)):
            values.append(dict(writer=str(writer),own_surprise=x[j,0],donor_surprise=donor[j],
                population_surprisal=x[j,1],length=x[j,2],log_frequency=x[j,3],sentence_start=x[j,4],
                after_punctuation=x[j,5],on_screen=x[j,6],session_surprisal=x[j,7],
                log_pause=.4*x[j,0]+noise[j]+writer*.02))
        return values,dict(redraws=0)


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Full fixture takes no human input')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);data=rows()
    for i,row in enumerate(data):
        base=next(iter(row['scores'].values()))
        row['scores']={m:dict(base) for m in MODELS}
        row.update(after_punctuation=int(i%7==0),on_screen=int(i%3==0),session_surprisal=float(np.sin(i)))
    gzip_equal(root/'ROWS.json.gz',data)
    results={}
    for card in ('AT2','AT3','AT4'):
        cfg=dict(card=card,draws=2000,models=list(MODELS)) if card=='AT2' else dict(card=card,draws=2000,model=MODELS[0])
        fn=analysis.verify if verifying else analysis.execute
        fn(root/card,dict(rows=str(root/'ROWS.json.gz')),cfg);results[card]=read(root/card/'RESULT.json')
        progress(root/'PROGRESS.json',dict(phase='verify' if verifying else 'execute',card=card))
    original=history.load;history.load=lambda inputs,config=None:ConstructedBank()
    try:
        blocks=[]
        for start in range(0,2000,100):
            cfg=dict(draws=2000,draw_start=start,draw_count=100)
            history.run_block(root/f'AT1-block-{start:04d}',dict(fixture=str(root/'ROWS.json.gz')),cfg,verifying)
            blocks.append(read(root/f'AT1-block-{start:04d}'/'BLOCK.json'))
            progress(root/'PROGRESS.json',dict(phase='verify' if verifying else 'execute',card='AT1',draws=start+100,total=2000))
        value=history.reduce_values(blocks)
    finally:history.load=original
    if value['primary']['state']!='supports' or value['complete_draws']!=2000:raise ValueError('Full donor block fixture failed')
    if any(results[c]['primary']['draws']!=2000 for c in ('AT2','AT3','AT4')):raise ValueError('Primary draw coverage failed')
    if results['AT3']['secondary_surprisal']['draws']!=2000 or len(results['AT2']['secondary'])!=10:
        raise ValueError('Companion uncertainty coverage failed')
    receipt=dict(fixture_only=True,scientific_admission=False,full_primary_cards=['AT1','AT2','AT3','AT4'],draws_per_primary=2000,
                 at2_companion_readers=10,at3_companion_surprisal=True,at1_point=value['point'],at1_complete_draws=value['complete_draws'])
    if verifying:
        if read(root/'FIXTURE.json')!=receipt or read(root/'AT1-RESULT.json')!=value:raise ValueError('Full AT fixture reduction differs')
        return dict(verified=True,complete_2000_draw_primary_and_companion_refit=True)
    write_equal(root/'AT1-RESULT.json',value);write_equal(root/'FIXTURE.json',receipt)
    return dict(status='complete',fixture_only=True,full_2000_draw_handlers=True)
def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)


if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
