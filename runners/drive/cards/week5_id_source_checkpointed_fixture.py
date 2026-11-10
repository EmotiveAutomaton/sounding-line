"""Constructed cross-prefix pairs, native pauses, complete replay and old-rule equivalence."""
from pathlib import Path
import argparse,csv,io,json,math,os,shutil,sqlite3,subprocess,sys,tarfile,time
import pandas as pd
from . import week5_id_source_checkpointed as new
from . import week5_id_source as old
from .week5_go import write,sha


def construct(root):
    sides=[[],[]]
    for person in range(1003):
        for session in range(2 if person==1002 else 1):
            for order in range(1,14):
                kind='Species' if order<=3 else 'Random' if order>=7 else 'Other'
                for side in (0,1):
                    r=dict.fromkeys(old.HUMANS+old.PET,0);r['Man']=int(side==0);r['Dog']=(2 if kind=='Random' else 1)*int(side==1)
                    r.update(ResponseID=f'constructed-{person}-{session}-{order}',UserID='constructed\nquoted-csv-record' if person==0 else f'constructed-{person}',
                        ExtendedSessionID=f'constructed-{person}-{session}',ScenarioOrder=order,ScenarioType=kind,ScenarioTypeStrict=kind,
                        Intervention=side,Saved=int(side==0),NumberOfCharacters=r['Man']+r['Dog'])
                    sides[side].append(r)
    # Keep explicit duplicate, orphan and conflicting metadata rows in both
    # implementations; they cannot be silently healed by a checkpoint boundary.
    rows=sides[0]+sides[1]
    rows.append(dict(rows[5]))
    orphan=dict(rows[0],ResponseID='constructed-orphan');rows.append(orphan)
    conflict=dict(rows[10],UserID='constructed-conflict');rows.append(conflict)
    text=io.StringIO();writer=csv.DictWriter(text,fieldnames=old.BASE+old.HUMANS+old.PET);writer.writeheader();writer.writerows(rows)
    payload=text.getvalue().encode();archive=root/'constructed.tar.gz'
    with tarfile.open(archive,'w:gz') as container:
        member=tarfile.TarInfo('SharedResponses.csv');member.size=len(payload);container.addfile(member,io.BytesIO(payload))
    salt=root/'salt.bin';salt.write_bytes(b'q'*32)
    return dict(inputs={'source':str(archive),'salt':str(salt)},source_sha256=sha(archive),rows=len(rows),pilot=math.ceil(len(rows)/20))


def clone(source,target):
    shutil.copytree(source,target,ignore=shutil.ignore_patterns('YIELD_REQUEST.json','PROGRESS.json'))


def child(root,mode):
    bundle=json.loads((root/'INPUTS.json').read_text('utf8'))
    new.SOURCE_SHA=old.SOURCE_SHA=bundle['source_sha256'];new.SOURCE_ROWS=bundle['rows'];new.PILOT_ROWS=bundle['pilot']
    config=dict(phase='prepare',pilot_rows=new.PILOT_ROWS,max_wall_seconds=900)
    if mode=='pilot':value=new.execute(root/'pilot',bundle['inputs'],config)
    elif mode=='projection-pause':
        original=new.requested;new.requested=lambda output:(output/'parts/000000.seal.json').exists()
        try:value=new.execute(root/'projection-pause',bundle['inputs'],config)
        finally:new.requested=original
    elif mode=='complete':value=new.execute(root/'complete',bundle['inputs'],config)
    elif mode=='verify':value=new.verify(root/'complete',bundle['inputs'],config)
    elif mode=='old':value=old.execute(root/'old',bundle['inputs'],{})
    else:raise ValueError(mode)
    write(root/(mode+'-RETURN.json'),value)
    write(root/(mode+'-USAGE.json'),dict(cpu_seconds=time.process_time()))


def run(root):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=False);started=time.process_time();bundle=construct(root);write(root/'INPUTS.json',bundle)
    env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',NUMEXPR_NUM_THREADS='2')
    usage=[]
    def invoke(mode,index=0):
        p=subprocess.run([sys.executable,'-X','utf8','-B','-m',__spec__.name,str(root),'--child',mode],capture_output=True,env=env)
        (root/f'{mode}-{index}.stderr.log').write_bytes(p.stderr)
        if p.returncode:raise ValueError('constructed native source '+mode+' failed; private stderr retained')
        usage.append(json.loads((root/(mode+'-USAGE.json')).read_text('utf8'))['cpu_seconds'])
        return json.loads((root/(mode+'-RETURN.json')).read_text('utf8'))
    first=invoke('pilot');assert first['status']=='yielded' and first['source_rows']==bundle['pilot']
    assert not (root/'pilot/SOURCE.json').exists()
    db=sqlite3.connect(root/'pilot/pairs.sqlite');orphans=db.execute('SELECT count(*) FROM pairs WHERE n=1').fetchone()[0];db.close()
    assert orphans>0
    before={p.relative_to(root/'pilot').as_posix():sha(p) for p in (root/'pilot').rglob('*') if p.is_file()}
    clone(root/'pilot',root/'projection-pause');second=invoke('projection-pause')
    assert second['status']=='yielded' and second['source_rows']==bundle['rows'] and second['projected_people']==1000
    clone(root/'projection-pause',root/'complete');final=invoke('complete');assert not final['prefix_only']
    assert before=={p.relative_to(root/'pilot').as_posix():sha(p) for p in (root/'pilot').rglob('*') if p.is_file()}
    check=invoke('verify');assert check['status']=='yielded' and check['verified'] is False
    check=invoke('verify',1);assert check['verified'] and check['all_pair_state_fields_compared']
    original=invoke('old')
    assert final['counts']==original['counts']
    pd.testing.assert_frame_equal(pd.read_parquet(root/'complete/cases.parquet'),pd.read_parquet(root/'old/cases.parquet'))
    clone(root/'pilot',root/'tampered');db=sqlite3.connect(root/'tampered/pairs.sqlite');db.execute('UPDATE pairs SET saved=saved+1');db.commit();db.close()
    new.SOURCE_SHA=old.SOURCE_SHA=bundle['source_sha256'];new.SOURCE_ROWS=bundle['rows'];new.PILOT_ROWS=bundle['pilot']
    try:new.execute(root/'tampered',bundle['inputs'],dict(phase='prepare',pilot_rows=bundle['pilot']))
    except ValueError as error:assert 'snapshot changed' in str(error)
    else:raise AssertionError('altered stopped database accepted')
    write(root/'FIXTURE.json',dict(verified=True,constructed_only=True,source_rows=bundle['rows'],pilot_rows=bundle['pilot'],
        first_pause_retained_orphans=orphans,whole_person_projection_pause=1000,all_pair_state_fields_freshly_replayed=True,
        complete_cases_and_all_dispositions_equal_original=True,quoted_newline_csv_record_supported=True,
        duplicate_orphan_conflict_dispositions_preserved=True,immutable_predecessor=True,tampered_sqlite_snapshot_refused=True,
        no_human_prefix_run=True,module_sha256=sha(new.__file__),measured_native_cpu_seconds=sum(usage),parent_fixture_process_cpu_seconds=time.process_time()-started))
    print(json.dumps(dict(verified=True,receipt=str(root/'FIXTURE.json'))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path);parser.add_argument('--child',choices=['pilot','projection-pause','complete','verify','old'])
    args=parser.parse_args();child(args.root.resolve(),args.child) if args.child else run(args.root)
