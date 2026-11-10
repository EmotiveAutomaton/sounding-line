"""Native paused S2 prefix, suffix continuation and fresh full verification."""
from pathlib import Path
import argparse,json,shutil,subprocess,sys
from . import week5_bk_s2_source_checkpointed as source
from .week5_bk_s2_fixture import fixture_data
from .timing_p6 import write_equal,gzread,gzip_equal
from .timing_census import read,filehash

def config(quantum):return dict(card='BK-S2-inputs',mode='constructed',seed=20261102,expected_sessions=3,max_new_draws=quantum)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);p.add_argument('--verify',action='store_true');args=p.parse_args();output=args.output
    inputs=dict(constructed_source=str(output/'FIXTURE.json'))
    if args.verify:
        proof=source.verify(output/'resumed',inputs,config(3));assert proof['recomputed_sessions']==3
        try:source.verify(output/'false-prefix',inputs,config(3))
        except ValueError as error:assert 'independent complete-session' in str(error)
        else:raise AssertionError('A resealed false prefix passed fresh replay')
        print(json.dumps(dict(full_replay=proof,false_prefix_refused=True)));return
    output.mkdir(parents=True,exist_ok=True);write_equal(output/'FIXTURE.json',dict(constructed=True,sessions=[fixture_data() for _ in range(3)]))
    paused=source.execute(output/'pilot',inputs,config(1));assert paused['status']=='yielded' and paused['checkpoint']['sessions']==1
    shutil.copytree(output/'pilot',output/'resumed')
    done=source.execute(output/'resumed',inputs,config(3));assert done['new_sessions']==2 and done['reused_sessions']==1
    shutil.copytree(output/'resumed',output/'false-prefix');path=output/'false-prefix/raw-sessions/00000.json.gz'
    value=gzread(path);value['session']['sentences'][0]['text']='false constructed prefix'
    # A new tampered copy is deliberate here; the original prefix stays intact.
    from .timing_p6 import gzwrite
    path.unlink();gzwrite(path,value)
    child=subprocess.run([sys.executable,'-X','utf8','-B','-m','runners.drive.cards.week5_bk_s2_checkpoint_fixture','--output',str(output),'--verify'],capture_output=True,text=True)
    if child.returncode:raise RuntimeError(child.stderr[-3000:])
    receipt=dict(passed=True,constructed=True,exact_pilot_boundary=True,resumed_only_uncomputed_sessions=True,fresh_process=json.loads(child.stdout),
                 source_pins={n:filehash(Path(__file__).with_name(n)) for n in ('week5_bk_s2_source.py','week5_bk_s2_source_checkpointed.py','week5_bk_s2_checkpoint_fixture.py')})
    write_equal(output/'COMPLETE.json',receipt);print(json.dumps(dict(passed=True,pilot_sessions=1,new_resume_sessions=2,verified_sessions=3)))

if __name__=='__main__':main()
