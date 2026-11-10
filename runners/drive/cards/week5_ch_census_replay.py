"""Successor CH census verification: copied execution prefixes are not evidence.

DESIGN CHECK: LESSONS 2-5. Original source code stays frozen. Verification
starts at source ordinal zero in a new database, excludes resume_frame, and
compares every row in every source table. A rehashed false prefix must fail.
"""
from pathlib import Path
import sqlite3
from . import week5_ch_source as base

TABLES=('frame','openings','opening_positions','histories','checkpoints','settings')

def execute(output,inputs,config):
    if config.get('phase')!='census':raise ValueError('Census successor only')
    return base.execute(output,inputs,config)

def compare(left_path,right_path):
    left=sqlite3.connect(left_path);right=sqlite3.connect(right_path);counts={}
    try:
        for table in TABLES:
            if left.execute('PRAGMA table_info('+table+')').fetchall()!=right.execute('PRAGMA table_info('+table+')').fetchall():raise ValueError('Census schema differs')
            n=len(left.execute('PRAGMA table_info('+table+')').fetchall());order=','.join(str(i+1) for i in range(n))
            a=left.execute(f'SELECT * FROM {table} ORDER BY {order}');b=right.execute(f'SELECT * FROM {table} ORDER BY {order}');counts[table]=0
            while True:
                x=a.fetchmany(1000);y=b.fetchmany(1000)
                if x!=y:raise ValueError('Independent source census differs: '+table)
                if not x:break
                counts[table]+=len(x)
    finally:left.close();right.close()
    return counts

def verify(output,inputs,config):
    if config.get('phase')!='census':raise ValueError('Census successor only')
    output=Path(output);scratch=output/'independent_census';scratch.mkdir(exist_ok=True)
    database=scratch/'PRIVATE_FRAME.sqlite'
    if database.exists():raise ValueError('Independent census verification needs a new attempt; no trusted prefix reuse')
    # Deliberately never read or propagate inputs.resume_frame. The fresh
    # database and ordinal zero are mandatory even if execute reused a prefix.
    clean={k:v for k,v in inputs.items() if k!='resume_frame'}
    spec=clean['source'];salt=Path(clean['salt']['path']).read_bytes()
    result=base.census(spec['path'],spec['sha256'],config['month'],salt,database,
                       config.get('max_games'),telemetry=output,expected_games=config.get('expected_games'))
    if '_yield' in result:
        checkpoint=dict(path=str(database),sha256=base.digest(database),**result.pop('_yield'),
                        full_source_verification=False,restart_verification_at_ordinal_zero=True)
        base.write_json(output/'VERIFY_CHECKPOINT.json',checkpoint)
        return dict(status='yielded',reason='independent verifier owner request',checkpoint=checkpoint)
    if result!=base.json.loads((output/'SOURCE.json').read_text('utf8')):raise ValueError('Independent complete source counts differ')
    counts=compare(output/'PRIVATE_FRAME.sqlite',database)
    proof=dict(verified=True,complete_recalculation=True,source_start_ordinal=0,resume_frame_excluded=True,
               every_database_row_compared=counts,source_module_sha256=base.digest(Path(base.__file__)))
    base.write_json(output/'INDEPENDENT_CENSUS_VERIFIED.json',proof)
    return proof
