"""Native complete 2,000-draw T4 handler fixture using only constructed menus."""
from pathlib import Path
import time
import numpy as np
from threadpoolctl import threadpool_limits
from . import week5_bk_t4 as t4
from .timing_census import read
from .timing_p6 import write_equal, progress


def fixture_bundle():
    writers=['0','1','2'];w=np.repeat(np.arange(3),12);y=np.tile(np.arange(6),6)
    data=dict(x=np.zeros((36,5,5)).tolist(),z=np.zeros((36,2)).tolist(),w=w.tolist(),y=y.tolist(),mask=np.ones((36,5),bool).tolist())
    return dict(packed=dict(writers=writers,train=data,test=data),covariates=[dict(writer=s,identification=dict(margin=i),mean_hesitancy=float(i*i)) for i,s in enumerate(writers)])


def checks():
    bundle=fixture_bundle();packed=bundle['packed'];out=t4.resample(packed,[1,1,0])
    if set(out['train']['w'])!={0,1,2} or len(out['train']['w'])!=36:raise ValueError('Duplicate writer handling failed')
    changed=fixture_bundle();changed['packed']['train']=dict(changed['packed']['train'],y=[5]*36)
    a,pa,ra=t4.calibration_data(packed,1);b,pb,rb=t4.calibration_data(changed['packed'],1)
    if any(not np.array_equal(a[h][k],b[h][k]) for h in a for k in a[h]):raise ValueError('Human choices reach calibration')
    if not np.array_equal(pa,pb):raise ValueError('Calibration choice invariance failed')
    return dict(duplicate_writers_separate=True,matched_calibration_choice_blind=True)


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Fixture has no human inputs')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);bundle=fixture_bundle();packed=bundle['packed'];began=time.process_time()
    with threadpool_limits(limits=2):
        point=t4.pair({h:t4.packing.arrays(packed,h) for h in ('train','test')},bundle['covariates'],range(3));point['binding']='constructed'
        if abs(point['gain'])>1e-10:raise ValueError('Zero-feature exact primary null failed')
        blocks=[]
        for kind,total in t4.KINDS.items():
            for start in range(0,total,100):
                records=[]
                for index in range(start,min(start+100,total)):
                    value=t4.draw(bundle,kind,index,point)
                    if kind in ('reference','bootstrap') and abs(value['gain'])>1e-10:raise ValueError('Exact conditional null changed')
                    # Flat features make temperature likelihood-unidentified;
                    # the numerical certificate does not force q exactly zero.
                    # Check the predictive invariant, not an arbitrary optimum.
                    data=t4.packing.arrays(packed,'test');theta=np.asarray(value['individual']['theta'])
                    fixed=theta.copy();fixed[-3:]=0
                    if not np.array_equal(t4.model.logits(theta,data,True),t4.model.logits(fixed,data,True)):
                        raise ValueError('Zero-feature probabilities depend on temperature')
                    records.append(dict(index=index,status='complete',value=value,binding='constructed',kind=kind))
                block=dict(binding='constructed',kind=kind,start=start,count=len(records),records=records)
                p=root/f'{kind}-{start:04d}.json'
                if verifying:
                    if read(p)!=block:raise ValueError('Fresh complete draw refit differs')
                else:write_equal(p,block)
                blocks.append(block);progress(root/'PROGRESS.json',dict(phase='verify' if verifying else 'execute',kind=kind,draws=start+len(records),total=total))
        result=t4.reduce_values(point,blocks,2000)
    if result['primary']['draws']!=2000 or len(result['per_writer_intervals'])!=3 or result['reference']['draws']!=200:
        raise ValueError('Primary/companion count incomplete')
    if result['calibration']['gate']:raise ValueError('Uninformative features falsely cleared recovery gate')
    receipt=dict(fixture_only=True,checks=checks(),actual_kernel_refits=True,bootstrap_draws=2000,parameter_refits=2000,
                 reference_pairs=200,matched_worlds=40,primary_exact_zero=True,uninformative_calibration_refused=True)
    if verifying:
        if read(root/'FIXTURE.json')!=receipt or read(root/'RESULT.json')!=result:raise ValueError('Complete reduction differs')
        return dict(verified=True,full_primary_and_companion_refit=True)
    write_equal(root/'RESULT.json',result);write_equal(root/'FIXTURE.json',receipt)
    write_equal(root/'COST.json',dict(process_cpu_seconds=time.process_time()-began))
    return dict(status='complete',fixture_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)


if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
