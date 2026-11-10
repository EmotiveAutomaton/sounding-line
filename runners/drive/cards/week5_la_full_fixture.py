"""Complete 2,000-draw LA1/LA2 handlers on small constructed matched banks."""
from pathlib import Path
import numpy as np
from . import week5_la as la
from .timing_p6 import gzip_equal,write_equal
from .timing_census import read


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Full fixture takes no human input')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);rng=np.random.default_rng(4);acts=[];pairs=[]
    for m in range(20):
        for group in range(2):
            x=rng.normal(size=(6,2));p=np.exp(.8*x[:,0]+.3*x[:,1]);p/=p.sum();case=rng.choice(6,p=p)
            for j in range(6):acts.append(dict(id=f'{m}-{group}-{j}',meeting=str(m),speaker=str(group),act_type='inform',
                word_count=10,start=group*10+j,end=group*10+j+.5,laughed_after=j==case,resolution=float(x[j,0]),surprise=float(x[j,1])))
        for j in range(8):
            same=j%2;ra,rb=rng.uniform(.01,.1,2)
            pairs.append(dict(meeting=str(m),same=same,rate_a=float(ra),rate_b=float(rb),joined=float(.2*same+.1*ra+.2*rb+rng.normal(scale=.02))))
    for card,rows in [('LA1',acts),('LA2',pairs)]:
        path=root/(card+'.json.gz');gzip_equal(path,rows)
        (la.verify if verifying else la.execute)(root/card,dict(rows=str(path)),dict(card=card,draws=2000))
    a,b=[read(root/c/'RESULT.json') for c in ('LA1','LA2')]
    if a['primary']['draws']!=2000 or a['secondary_surprise']['draws']!=2000 or b['primary']['draws']!=2000:
        raise ValueError('Full laughter primary/companion uncertainty missing')
    value=dict(fixture_only=True,scientific_admission=False,cards=['LA1','LA2'],draws=2000,secondary_surprise_2000=True)
    if verifying:
        if read(root/'FIXTURE.json')!=value:raise ValueError('Laughter full fixture receipt differs')
        return dict(verified=True,full_2000_draw_primary_and_companion_refit=True)
    write_equal(root/'FIXTURE.json',value);return dict(status='complete',fixture_only=True)
def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)


if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
