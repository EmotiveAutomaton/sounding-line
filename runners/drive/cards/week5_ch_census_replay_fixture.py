"""Native honest/malicious prefix and cooperative verification-yield checks."""
from pathlib import Path
import argparse,json,sqlite3,subprocess,sys
from . import week5_ch_source as base,week5_ch_census_replay as successor
from .week5_ch_fixture import PGN

def prepare(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    salt=output/'salt.bin';salt.write_bytes(b'fixture-salt-not-human-data-12345')
    for i in range(2000):
        pgn=PGN.replace('fixture-white',f'constructed-history-{i}')
        meta,_=base.decode_headers(pgn,salt.read_bytes())
        if any(base.selected_history(p) for p in meta['players']):break
    else:raise AssertionError('Constructed history hash support absent')
    source=output/'source.pgn';source.write_text(pgn*24,encoding='utf8')
    inputs=dict(source=dict(path=str(source),sha256=base.digest(source)),salt=dict(path=str(salt),sha256=base.digest(salt)))
    config=dict(phase='census',month='2017-04')
    prefix=output/'prefix';prefix.mkdir();base.write_json(prefix/'YIELD_REQUEST.json',dict(reason='constructed prefix'))
    paused=base.execute(prefix,inputs,config);assert paused['status']=='yielded'
    resumed=dict(inputs,resume_frame={k:paused['checkpoint'][k] for k in ('path','sha256')})
    successor.execute(output/'honest',resumed,config)
    # Deliberately falsify and rehash the *copied* prefix, proving hash checks
    # alone do not substitute for independent source replay.
    con=sqlite3.connect(prefix/'PRIVATE_FRAME.sqlite')
    count=con.execute('SELECT COUNT(*) FROM frame').fetchone()[0];assert count>0
    con.execute('UPDATE frame SET rating_sum=rating_sum+1');con.commit();con.close()
    changed=dict(inputs,resume_frame=dict(path=str(prefix/'PRIVATE_FRAME.sqlite'),sha256=base.digest(prefix/'PRIVATE_FRAME.sqlite')))
    successor.execute(output/'false-prefix',changed,config)
    successor.execute(output/'verify-yield',inputs,config);base.write_json(output/'verify-yield'/'YIELD_REQUEST.json',dict(reason='native verify yield'))
    base.write_json(output/'INPUTS.json',dict(honest=resumed,changed=changed,original=inputs));base.write_json(output/'CONFIG.json',config)

def verify_all(output):
    output=Path(output);inputs=json.loads((output/'INPUTS.json').read_text());config=json.loads((output/'CONFIG.json').read_text())
    honest=successor.verify(output/'honest',inputs['honest'],config)
    try:successor.verify(output/'false-prefix',inputs['changed'],config)
    except ValueError as error:refused='Independent source census differs' in str(error)
    else:refused=False
    assert refused
    paused=successor.verify(output/'verify-yield',inputs['original'],config);assert paused['status']=='yielded'
    assert not (output/'verify-yield'/'INDEPENDENT_CENSUS_VERIFIED.json').exists()
    return dict(honest_complete_replay=honest,rehash_false_prefix_refused=refused,cooperative_verifier_yield=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--verify',action='store_true');args=p.parse_args();output=Path(args.output)
    if args.verify:result=verify_all(output)
    else:
        prepare(output)
        child=subprocess.run([sys.executable,'-X','utf8','-B','-m','runners.drive.cards.week5_ch_census_replay_fixture','--verify','--output',str(output)],capture_output=True,text=True)
        if child.returncode:raise RuntimeError(child.stderr[-2000:])
        result=dict(passed=True,constructed=True,scientific_admission=False,checks=json.loads(child.stdout),
                    source_pins={name:base.digest(Path(__file__).with_name(name)) for name in ('week5_ch_source.py','week5_ch_census_replay.py','week5_ch_census_replay_fixture.py')})
        base.write_json(output/'COMPLETE.json',result)
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
