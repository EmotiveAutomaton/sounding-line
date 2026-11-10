"""Native constructed CH analysis validation, distinct from corpus admission.

DESIGN CHECK: LESSONS 3-5. Signed worlds, exact-null, independent full-design
least squares and fresh-process serialized handler replay test the actual ruler.
"""
from pathlib import Path
import argparse,json,math,subprocess,sys
import numpy as np
from . import week5_ch_models as m
from . import week5_ch_histories as h
from .week5_ch_source import write_json,digest


def run(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);rng=np.random.default_rng(20261107)
    rows=[]
    for p in range(40):
        rating=800+400*(p%6);r=(rating-1600)/400
        for i in range(40):
            k=int(rng.integers(1,6));clock=float(rng.uniform(1,200));low=clock<=10
            nuisance=.15*k+.002*i;logtime=2+nuisance+.05*k*r-.8*low+rng.normal(0,.15)
            row=dict(player=str(p),game=f'constructed-{p}-{i//4}',month='2017-04',time_control='blitz',rating=rating,
                     initial=300,increment=2,ply=i+5,clock_before=clock,think_time=math.exp(logtime),
                     legal_moves=int(rng.integers(15,40)),material=int(rng.integers(10,70)),fen='constructed not a legal board',uci='e2e4',position='constructed')
            engine=dict(k50=k,k100=min(5,k+1),best_gap=float(rng.uniform(0,300)),breadth=max(k-2,0),stakes=float(rng.uniform(0,200)),
                        mate_sentinel_used=False,centipawn_loss=200-5*(logtime-2-nuisance)*r+rng.normal(0,1))
            write_json(output/'scores'/f'{p:03}-{i:03}.json',dict(position=row,engine=engine,node_limit=0,constructed=True));rows.append(dict(row,**engine))
    source=dict(scores=dict(path=str(output/'scores')))
    for card in ('CH2','CH3','CH5'):
        config=dict(card=card,draws=32,floor=20,include_secondaries=False,constructed_fixture=True)
        m.execute(output/card,source,config)
        result=json.loads((output/card/'SCIENCE.json').read_text())
        if card in ('CH2','CH3'):
            assert result['status']=='complete' and result['coefficient']>0
        else:
            assert result['point']['status']=='valid' and result['point']['iv_improvement']>1
        write_json(output/(card+'-config.json'),config)
    proof=h.target_recovery();assert proof['pass_gate']
    # Independent dummy-matrix calculation validates fixed-effect elimination.
    selected,_=m.eligible(rows,'blitz');y=np.log([r['think_time'] for r in selected]);x=np.column_stack([[r['k50'] for r in selected],m.controls(selected)])
    groups=np.array([r['player'] for r in selected]);dummies=np.column_stack([groups==v for v in sorted(set(groups))])
    beta=np.linalg.lstsq(np.column_stack([x,dummies]),y,rcond=None)[0][0]
    reported=json.loads((output/'CH2'/'SCIENCE.json').read_text())['coefficient'];assert abs(beta-reported)<1e-9
    child=subprocess.run([sys.executable,'-X','utf8','-B','-m','runners.drive.cards.week5_ch_analysis_fixture','--output',str(output),'--verify'],capture_output=True,text=True)
    if child.returncode:raise RuntimeError(child.stderr[-2000:])
    result=dict(constructed=True,checks=['CH2 positive known world','CH3 positive interaction world','CH5 strong-IV negative loss interaction',
                                         'independent dummy-matrix fixed effects','200 planted targets within5%','fresh process entire handlers replay'],
                target_recovery=proof,replay=json.loads(child.stdout),source_pins={name:digest(Path(__file__).with_name(name)) for name in ('week5_ch_models.py','week5_ch_histories.py','week5_ch_reserve_secondaries.py','week5_ch_collection.py','week5_ch_progress.py','week5_ch_grid.py')},scientific_admission=False)
    write_json(output/'COMPLETE.json',result);return dict(passed=True,checks=len(result['checks']))


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--verify',action='store_true');a=p.parse_args();output=Path(a.output)
    if a.verify:
        result={card:m.verify(output/card,dict(scores=dict(path=str(output/'scores'))),json.loads((output/(card+'-config.json')).read_text())) for card in ('CH2','CH3','CH5')}
    else:result=run(output)
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
