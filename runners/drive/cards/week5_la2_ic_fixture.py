"""Complete constructed signed/null LA2 instrument and fresh-process proof."""
from pathlib import Path
import argparse
import gzip
import json
import os
import subprocess
import sys
import time
import numpy as np
from . import week5_la2_ic as ic, week5_la as primary
from .week5_go import write,sha


def rows():
    rng=np.random.default_rng(810);out=[]
    for m in range(24):
        for j in range(6):
            same=j%2;a,b=rng.uniform(0,.1,2)
            out.append(dict(meeting=f'constructed-{m}',same=same,rate_a=float(a),rate_b=float(b),
                joined=float(.4+.04*same+.1*a-.2*b+.001*rng.normal())))
    return out


def complete(root):
    write(root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,
        outputs={'output/'+p.name:sha(p) for p in (root/'output').iterdir() if p.is_file()}))


def main(root,phase):
    root=Path(root).resolve();start=time.process_time()
    if phase=='verify':
        bundle=json.loads((root/'INPUTS.json').read_text('utf8'))
        out=ic.verify(root/'run',bundle['inputs'],bundle['config'])
        write(root/'FRESH_VERIFICATION.json',dict(out,cpu_seconds=time.process_time()-start));return
    root.mkdir(parents=True,exist_ok=False);data=rows();source=root/'source';parent=root/'primary'
    (source/'output').mkdir(parents=True);(parent/'output').mkdir(parents=True)
    with gzip.open(source/'output/ROWS.json.gz','wt',encoding='utf8') as stream:json.dump(data,stream)
    write(source/'output/SUMMARY.json',dict(card='LA2',corpus='AMI',background='native_language',constructed=True))
    complete(source)
    parent_result=primary.la2(data,2000)
    write(parent/'output/RESULT.json',parent_result)
    write(parent/'PLAN.json',dict(inputs={'rows':str(source/'output/ROWS.json.gz')},config={'card':'LA2','draws':2000}));complete(parent)
    inputs=dict(source_root=str(source),primary_root=str(parent));config=dict(constructed_fixture=True,worlds=100,draws=2000,max_new_draws=100)
    assert ic.execute(root/'run',inputs,config)['status']=='yielded'
    assert not (root/'run/RESULT.json').exists()
    # A changed sealed operator is refused without recreating the source run.
    seal=root/'run/operators/0000.seal.json';saved=seal.read_bytes();bad=json.loads(saved);bad['sha256']='wrong';write(seal,bad)
    try:ic.execute(root/'run',inputs,config)
    except ValueError:pass
    else:raise AssertionError('tampered operator accepted')
    seal.write_bytes(saved)
    config['max_new_draws']=2000
    result=ic.execute(root/'run',inputs,config)
    assert result['sensitivity_pass'] and result['effects'][0]['zero_exclusion_rate']==1 and result['effects'][2]['zero_exclusion_rate']==1
    write(root/'INPUTS.json',dict(inputs=inputs,config=config))
    # Independent expanded-row least squares for every one of the 2000 draws.
    x,y,code,n=ic.design(data);rng=np.random.default_rng(ic.SEED)
    bank=np.concatenate([np.load(p) for p in sorted((root/'run/operators').glob('*.npy'))])
    maximum=0.
    for index in range(2000):
        ids=np.concatenate([np.flatnonzero(code==m) for m in rng.choice(n,n,replace=True)])
        for response in [y,x[:,0]*ic.BAR,-x[:,0]*ic.BAR,np.zeros(len(y))]:
            exact=np.linalg.lstsq(x[ids],response[ids],rcond=1e-10)[0][0]
            maximum=max(maximum,abs(float(bank[index]@response)-exact))
    assert maximum<1e-11
    # One informative meeting: some exact original bootstrap draws omit it.
    broken=x.copy();broken[code!=0,0]=0
    failure=ic.calibration(broken,y,code,n,config,root/'rank-failure',{'constructed':True})
    assert failure['status']=='invalid sensitivity' and failure['failed_draws']
    env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',NUMEXPR_NUM_THREADS='2')
    child=subprocess.run([sys.executable,'-X','utf8','-B','-m',__spec__.name,str(root),'verify'],capture_output=True,env=env)
    (root/'verify.stdout.log').write_bytes(child.stdout);(root/'verify.stderr.log').write_bytes(child.stderr)
    if child.returncode:raise ValueError('native replay failed; private stderr retained')
    write(root/'FIXTURE.json',dict(verified=True,constructed_only=True,whole_handler_signed_and_null=True,
        worlds_per_effect=100,effects=[-1,0,1],draws=2000,all_2000_expanded_row_equivalence=True,
        maximum_absolute_difference=maximum,failed_draws_retained=len(failure['failed_draws']),
        checkpoint_pause_resume_and_tamper_refusal=True,fresh_process_verified=True,
        measured_cpu_seconds=time.process_time()-start+json.loads((root/'FRESH_VERIFICATION.json').read_text('utf8'))['cpu_seconds'],
        module_sha256=sha(ic.__file__)))
    print(json.dumps(dict(verified=True,receipt=str(root/'FIXTURE.json'))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path);parser.add_argument('phase',choices=['fixture','verify'])
    args=parser.parse_args();main(args.root,args.phase)
