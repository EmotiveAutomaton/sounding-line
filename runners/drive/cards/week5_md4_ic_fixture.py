"""Native complete MD4 slope-instrument proof with exact condition resampling."""
from pathlib import Path
import argparse,json,subprocess,sys,time,os
import numpy as np
import pandas as pd
from . import week5_md4_ic as ic, week5_md4_analysis as primary
from .week5_go import write,sha


def main(root,phase):
    root=Path(root).resolve();started=time.process_time()
    if phase=='verify':
        bundle=json.loads((root/'INPUTS.json').read_text('utf8'));v=ic.verify(root/'run',bundle['inputs'],bundle['config'])
        write(root/'FRESH_VERIFICATION.json',dict(v,cpu_seconds=time.process_time()-started));return
    root.mkdir(parents=True,exist_ok=False);source=root/'source';source.mkdir();data=[]
    for c,condition in enumerate(primary.CONDITIONS):
        for person in range(24):
            slope=[-.008,-.004,-.006][c]+(person-11.5)*.00001
            for order,minute in enumerate([0.,1.,2.,3.,4.,5.,6.]):
                data.append(dict(person=f'constructed-{c}-{person}',cohort=f'constructed-cohort-{c}',condition=condition,
                    rating_order=order,minute=minute,mood=.7+slope*minute))
    frame=pd.DataFrame(data);path=source/'PRIVATE_RATINGS.parquet';frame.to_parquet(path,index=False)
    write(source/'SOURCE.json',dict(complete=True,constructed=True,ratings_sha256=sha(path)))
    write(source/'VERIFIED.json',dict(verified=True,all_values_checked=True))
    parent=root/'primary';primary.execute(parent/'output',{'ratings':str(path)},{'constructed_fixture':True,'draws':2000})
    primary.verify(parent/'output',{'ratings':str(path)},{'constructed_fixture':True,'draws':2000})
    write(parent/'PLAN.json',dict(inputs={'ratings':str(path)},config={'draws':2000,'constructed_fixture':True}))
    write(parent/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,
        outputs={'output/'+p.name:sha(p) for p in (parent/'output').iterdir() if p.is_file()}))
    inputs=dict(ratings=str(path),primary_root=str(parent));config=dict(constructed_fixture=True,worlds=100,draws=2000,max_new_draws=2000)
    assert ic.execute(root/'run',inputs,config)['status']=='yielded';assert not (root/'run/RESULT.json').exists()
    config['max_new_draws']=600000;result=ic.execute(root/'run',inputs,config)
    assert result['sensitivity_pass'] and result['effects'][0]['zero_exclusion_rate']==1 and result['effects'][2]['zero_exclusion_rate']==1
    projected,_=primary.slopes(frame);point,bank,counts=ic.operators(projected,2000);y=np.array([r['slope'] for r in projected])
    rng=np.random.default_rng(primary.SEED);maximum=0.
    for c,condition in enumerate(primary.CONDITIONS):
        values=np.array([r['slope'] for r in projected if r['condition']==condition])
        for draw in range(2000):
            expected=values[rng.integers(0,len(values),len(values))].mean()
            maximum=max(maximum,abs(float(bank[draw,c]@y)-expected))
    assert maximum<1e-12
    try:ic.operators(projected[:10],2000)
    except ValueError:pass
    else:raise AssertionError('unsupported condition accepted')
    seal=root/'run/worlds/-1-000.seal.json';raw=seal.read_bytes();bad=json.loads(raw);bad['sha256']='changed';write(seal,bad)
    try:ic.execute(root/'run',inputs,config)
    except ValueError:pass
    else:raise AssertionError('changed world accepted')
    seal.write_bytes(raw)
    write(root/'INPUTS.json',dict(inputs=inputs,config=config))
    env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',NUMEXPR_NUM_THREADS='2')
    child=subprocess.run([sys.executable,'-X','utf8','-B','-m',__spec__.name,str(root),'verify'],capture_output=True,env=env)
    (root/'verify.stderr.log').write_bytes(child.stderr)
    if child.returncode:raise ValueError('MD4 sensitivity native replay failed')
    write(root/'FIXTURE.json',dict(verified=True,constructed_only=True,full_signed_and_null_handler=True,
        all_6000_condition_draws_equivalent=True,maximum_absolute_difference=maximum,
        worlds_per_effect=100,effects=[-1,0,1],draws=2000,source_floor_failure_reachable=True,
        pause_resume_and_world_tamper_refusal=True,fresh_process_verified=True,
        cpu_seconds=time.process_time()-started+json.loads((root/'FRESH_VERIFICATION.json').read_text('utf8'))['cpu_seconds'],module_sha256=sha(ic.__file__)))
    print(json.dumps(dict(verified=True,receipt=str(root/'FIXTURE.json'))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path);parser.add_argument('phase',choices=['fixture','verify'])
    args=parser.parse_args();main(args.root,args.phase)
