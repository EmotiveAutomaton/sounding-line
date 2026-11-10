"""Read-only predecessor qualification and WAL-safe execution-state recovery.

No recovered prefix is independently verified here. The successor must replay
the whole immutable source through week5_ch_census_replay before completion.
"""
from pathlib import Path
import argparse,json,shutil,sqlite3
from .batch_runtime import filehash,freeze,read
from .week5_policy_v2 import ROOT
from runners.stage9.process_identity import is_same_live_process

def snapshot(database,destination):
    """Copy stable raw database/WAL bytes first; never open the predecessor."""
    database=Path(database).resolve();destination=Path(destination).resolve()
    if destination.exists():raise ValueError('Recovery requires a fresh destination')
    destination.mkdir(parents=True);copydir=destination/'retained-copy';copydir.mkdir()
    members=[p for p in (database,Path(str(database)+'-wal'),Path(str(database)+'-shm')) if p.exists()]
    if not members or members[0]!=database:raise ValueError('Missing predecessor database')
    before={p.name:filehash(p) for p in members}
    for path in members:
        shutil.copyfile(path,copydir/path.name)
        if filehash(copydir/path.name)!=before[path.name]:raise ValueError('Predecessor changed during copy')
    con=sqlite3.connect(copydir/database.name);target=destination/'PRIVATE_FRAME.sqlite';out=sqlite3.connect(target)
    try:
        if con.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('Invalid retained SQLite checkpoint')
        con.backup(out);out.commit()
        if out.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('Invalid backed-up checkpoint')
        checkpoints=out.execute('SELECT month,ordinal,source,counts,complete FROM checkpoints').fetchall()
        salt=out.execute("SELECT value FROM settings WHERE key='salt_sha256'").fetchone()
        counts={table:out.execute('SELECT COUNT(*) FROM '+table).fetchone()[0] for table in ('frame','openings','opening_positions','histories')}
        largest_history=out.execute('SELECT MAX(ordinal) FROM histories').fetchone()[0]
    finally:out.close();con.close()
    if {p.name:filehash(p) for p in members}!=before:raise ValueError('Predecessor changed while snapshotting')
    if len(checkpoints)!=1 or salt is None:raise ValueError('Checkpoint month/salt scope missing or ambiguous')
    month,ordinal,source,census,complete=checkpoints[0];census=json.loads(census)
    if ordinal<0 or census.get('source_games')!=ordinal+1 or (largest_history is not None and largest_history>ordinal):raise ValueError('Checkpoint ordinal/count inconsistency')
    return dict(database=str(target),sha256=filehash(target),retained_member_pins=before,month=month,ordinal=ordinal,
                source_sha256=source,salt_sha256=salt[0],complete=bool(complete),census=census,table_rows=counts,
                prefix_independently_verified=False,full_source_replay_required=True)

def prepare(predecessor,destination):
    predecessor=Path(predecessor).resolve();predecessor.relative_to(ROOT)
    plan=read(predecessor/'PLAN.json');failure=read(predecessor/'FAILED.json')
    if plan.get('campaign')!='S15-WEEK5' or plan.get('family')!='CH' or plan.get('module')!='runners.drive.cards.week5_ch_source' or plan.get('config',{}).get('phase')!='census':raise ValueError('Not an original Week 5 chess census')
    if failure.get('status')!='FAILED' or 'PermissionError' not in failure.get('error',''):raise ValueError('Not the qualified sharing-denial predecessor')
    if any((predecessor/name).exists() for name in ('COMPLETE.json','PAUSED.json')):raise ValueError('Ambiguous predecessor terminal')
    identities={}
    for name in ('OWNER.json','EXECUTE_CHILD.json','EXECUTE_NATIVE.json','VERIFY_CHILD.json','VERIFY_NATIVE.json'):
        path=predecessor/name
        if path.exists():
            identities[name]=read(path)['native']
            if is_same_live_process(identities[name]):raise ValueError('Predecessor identity still live')
    if 'OWNER.json' not in identities or 'EXECUTE_CHILD.json' not in identities:raise ValueError('Predecessor ownership incomplete')
    normalized={str(Path(p).resolve()):digest for p,digest in plan['pins'].items()}
    for key in ('source','salt'):
        spec=plan['inputs'][key]
        if normalized.get(str(Path(spec['path']).resolve()))!=spec['sha256']:raise ValueError('Predecessor source/salt pin missing')
    if filehash(plan['inputs']['salt']['path'])!=plan['inputs']['salt']['sha256']:raise ValueError('Campaign salt changed')
    result=snapshot(predecessor/'output/PRIVATE_FRAME.sqlite',destination)
    if result['month']!=plan['config']['month'] or result['source_sha256']!=plan['inputs']['source']['sha256'] or result['salt_sha256']!=plan['inputs']['salt']['sha256']:raise ValueError('Recovered checkpoint does not match original source contract')
    for identity in identities.values():
        if is_same_live_process(identity):raise ValueError('Predecessor identity unexpectedly active')
    result.update(predecessor=str(predecessor),predecessor_plan_sha256=filehash(predecessor/'PLAN.json'),
                  predecessor_failure_sha256=filehash(predecessor/'FAILED.json'),prior_cpu_seconds=failure['cpu_seconds'],
                  stopped_identities_verified=True,source_file_rehash_required_at_new_admission=True,
                  required_module='runners.drive.cards.week5_ch_census_replay',required_runtime='runners.drive.cards.week5_runtime_v4')
    freeze(Path(destination)/'CHECKPOINT_RECOVERY.json',result)
    template=dict(module=result['required_module'],runtime=result['required_runtime'],family='CH',campaign='S15-WEEK5',
                  inputs=dict(plan['inputs'],resume_frame=dict(path=result['database'],sha256=result['sha256'])),
                  config=plan['config'],recovery_receipt=str(Path(destination)/'CHECKPOINT_RECOVERY.json'),
                  recovery_receipt_sha256=filehash(Path(destination)/'CHECKPOINT_RECOVERY.json'),
                  cost_review_required=True,full_source_verification_required=True,launch_authorized_by_this_template=False)
    freeze(Path(destination)/'RECOVERY_TEMPLATE.json',template)
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--predecessor',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=prepare(args.predecessor,args.output)
    print(json.dumps({k:result[k] for k in ('month','ordinal','prior_cpu_seconds','full_source_replay_required')}))

if __name__=='__main__':main()
