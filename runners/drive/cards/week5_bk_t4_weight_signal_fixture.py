"""Known differing/common direction recovery in fully constructed choice worlds."""
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from . import week5_bk_t4_texture as card
from .timing_census import read
from .timing_p6 import write_equal


def fixture():
    rng=np.random.default_rng(908);writers=8;packed=dict(writers=[str(i) for i in range(writers)])
    for half,count in [('train',100),('test',300)]:
        ids=np.repeat(np.arange(writers),count);n=len(ids)
        packed[half]=dict(x=rng.normal(size=(n,5,5)).tolist(),z=rng.normal(size=(n,2)).tolist(),
                          w=ids.tolist(),y=[0]*n,mask=np.ones((n,5),bool).tolist())
    bundle=dict(packed=packed,covariates=[dict(writer=str(i),identification=dict(margin=float(i)),mean_hesitancy=float(i*i)) for i in range(writers)])
    records=[]
    with threadpool_limits(limits=2):
        for index in (0,1):records.append(card.draw(bundle,'calibration',index))
    if records[0]['gain']>.005 or records[1]['gain']<=.02:
        raise ValueError('Known common/differing direction recovery failed')
    return dict(fixture_only=True,records=records,common_direction_not_materially_positive=True,different_directions_recovered=True,
                conditional_expected_scores=True,full_matched_human_geometry_bank_still_required=True)


def execute(output,inputs,config):
    if inputs or config:raise ValueError('Fixture takes no human inputs')
    write_equal(Path(output)/'FIXTURE.json',fixture());return dict(status='complete',fixture_only=True)
def verify(output,inputs,config):
    if inputs or config:raise ValueError('Fixture takes no human inputs')
    if read(Path(output)/'FIXTURE.json')!=fixture():raise ValueError('Fresh planted direction replay differs')
    return dict(verified=True,complete_planted_direction_refit=True)

if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
