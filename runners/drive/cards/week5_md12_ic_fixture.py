"""Native three-world, 2000-draw MD instrument proof on the prior constructed bank."""
from pathlib import Path
import argparse,json,os,subprocess,sys,time
from . import week5_md12_ic as ic
from .week5_go import write,sha


def main(root,phase,card=None):
    root=Path(root).resolve();started=time.process_time()
    if phase=='verify':
        bundle=json.loads((root/'INPUTS.json').read_text('utf8'));value=ic.verify(root/'run',bundle['inputs'],bundle['config'])
        write(root/'FRESH_VERIFICATION.json',dict(value,cpu_seconds=time.process_time()-started));return
    root.mkdir(parents=True,exist_ok=False)
    private=root.parent;task=private/'md12-native/constructed-source/task.npz'
    prior=private/'md12-bounded-native-v3';proof=json.loads((prior/'FIXTURE.json').read_text('utf8'))
    assert proof['passed'] and proof['constructed_only']
    source_receipt=json.loads((task.parent/'SOURCE.json').read_text('utf8'))
    assert source_receipt['constructed_only'] and source_receipt['task_sha256']==sha(task)
    result=json.loads((prior/'RESULT.json').read_text('utf8'));assert result['complete_computation']
    original_result=json.loads((private/'md12-native/run/RESULT.json').read_text('utf8'))
    original_proof=json.loads((private/'md12-native/FIXTURE.json').read_text('utf8'))
    assert result==original_result and original_proof['whole_MD12_execute_verify'] and original_proof['primary_draws']==2000
    parent=root/'parent';write(parent/'output/RESULT.json',result);write(parent/'output/EXISTING_CONSTRUCTED_PROOF.json',proof)
    write(parent/'PLAN.json',dict(inputs={'task':str(task)},config={'draws':2000}))
    write(parent/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,
        outputs={'output/'+p.name:sha(p) for p in (parent/'output').iterdir()}))
    inputs=dict(task=str(task),primary_root=str(parent));config=dict(card=card,draws=2000,constructed_fixture=True,max_new_draws=100,max_wall_seconds=900)
    assert ic.execute(root/'run',inputs,config)['status']=='yielded';assert not (root/'run/RESULT.json').exists()
    seal=root/'run/worlds/-1.seal.json';raw=seal.read_bytes();bad=json.loads(raw);bad['sha256']='changed';write(seal,bad)
    try:ic.execute(root/'run',inputs,config)
    except ValueError:pass
    else:raise AssertionError('changed instrument draw checkpoint accepted')
    seal.write_bytes(raw);config['max_new_draws']=6000
    value=ic.execute(root/'run',inputs,config)
    assert value['status']=='complete' and len(value['worlds'])==3
    # The actual full pipeline must recover each signed direction. Its 1% MSE
    # recovery threshold is recorded, not forced to pass by changing the dose.
    assert value['worlds'][0]['coefficient']<0<value['worlds'][2]['coefficient']
    assert all(r['draws']==2000 and sum(r['bootstrap_gamma_counts'].values())==2000 for r in value['worlds'])
    write(root/'INPUTS.json',dict(inputs=inputs,config=config))
    env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',NUMEXPR_NUM_THREADS='2')
    child=subprocess.run([sys.executable,'-X','utf8','-B','-m',__spec__.name,str(root),'verify'],capture_output=True,env=env)
    (root/'verify.stderr.log').write_bytes(child.stderr)
    if child.returncode:raise ValueError('MD instrument fresh native replay failed')
    write(root/'FIXTURE.json',dict(verified=True,constructed_only=True,card=card,whole_handler=True,
        fixed_worlds=[-1,0,1],draws_per_world=2000,all_gamma_reselection=True,signed_coefficient_recovery=True,
        oracle_dose_never_retuned=True,pause_resume_and_tamper_refusal=True,fresh_process_verified=True,
        cpu_seconds=time.process_time()-started+json.loads((root/'FRESH_VERIFICATION.json').read_text('utf8'))['cpu_seconds'],module_sha256=sha(ic.__file__)))
    print(json.dumps(dict(verified=True,card=card,receipt=str(root/'FIXTURE.json'))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path);parser.add_argument('phase',choices=['fixture','verify']);parser.add_argument('--card',choices=['MD1.ic','MD2.ic'])
    args=parser.parse_args();main(args.root,args.phase,args.card)
