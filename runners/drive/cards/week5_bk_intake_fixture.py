"""Native known-answer source-intake proof; all records here are constructed."""
from pathlib import Path
import argparse,csv,io,json,shutil,subprocess,sys,zipfile
from . import week5_bk_klicke_intake as k


def csv_fixture():
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=['Participant',*k.COLUMNS]);writer.writeheader()
    for i,key in enumerate(('a','Leftclick','ArrowLeft','ArrowRight','ArrowUp','ArrowDown')):
        row={c:0 for c in k.COLUMNS};row.update(Participant='constructed-sensitive-token',DownEventID=i,UpEventID=i,DownTime=i*100,UpTime=i*100+10,ActionTime=10,DownEvent=key,UpEvent=key,CursorPosition=0,PauseTime=90,WordCount=0,TextChange='a' if i==0 else '',Activity='Input' if i==0 else 'Nonproduction');writer.writerow(row)
    return stream.getvalue().encode()


def build(root):
    root.mkdir(parents=True,exist_ok=True);archive=root/'fixture.zip'
    with zipfile.ZipFile(archive,'w') as z:
        for i in range(3):z.writestr(f'csv/constructed-person-{i}.csv',csv_fixture());z.writestr(f'text/constructed-person-{i}.txt','A constructed sentence.\n')
        z.writestr('idfx/constructed-person-0.idfx','<session>identity not retained</session>');z.writestr('scores.csv','ID,Score\nconstructed-person-0,6\n')
    (root/'salt.bin').write_bytes(bytes(range(32)))
    return dict(archive=str(archive),archive_sha256=k.digest(archive),identity_salt=str(root/'salt.bin'))


def checks():
    record=k.project(csv_fixture(),b'A constructed sentence.\n','private-hash');assert record['counts']==dict(events=6,left_click_events=1,arrow_key_events=4)
    assert 'constructed-sensitive-token' not in json.dumps(record)
    assert record['final_text']=='A constructed sentence.\n'
    invalid=csv_fixture().replace(b'CursorPosition',b'UnknownColumn')
    try:k.project(invalid,b'text','hash')
    except ValueError:pass
    else:raise AssertionError('Missing schema accepted')
    for name in ('../escape.csv','C:/escape.csv','a\\escape.csv'):
        buff=io.BytesIO()
        with zipfile.ZipFile(buff,'w') as z:
            info=zipfile.ZipInfo('placeholder');info.filename=name;z.writestr(info,b'bad')
        with zipfile.ZipFile(io.BytesIO(buff.getvalue())) as z:
            try:k.inventory(z)
            except ValueError:pass
            else:raise AssertionError('Unsafe path accepted')
    return dict(exact_event_counts=True,all_four_arrows=True,identity_column_dropped=True,exact_private_text=True,missing_schema_refused=True,unsafe_paths_refused=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);p.add_argument('--verify',action='store_true');a=p.parse_args();root=a.output
    config=dict(card='BK-S4.k-intake',mode='constructed',expected_sessions=3,max_new_draws=1)
    if a.verify:
        inputs=k.read(root/'INPUTS.json');result=k.verify(root/'resumed',inputs,config)
        false=root/'false-prefix';shutil.copytree(root/'resumed',false);path=false/'sessions/00000.json.gz';data=k.read(path);data['events'][0]['CursorPosition']=999;path.unlink();k.write(path,data)
        try:k.verify(false,inputs,config)
        except ValueError:pass
        else:raise AssertionError('False cached prefix accepted')
        print(json.dumps(dict(replay=result,false_prefix_refused=True,checks=checks())));return
    inputs=build(root);k.write(root/'INPUTS.json',inputs);check=checks()
    first=k.execute(root/'pilot',inputs,config);assert first['status']=='yielded' and first['completed_units']==1
    shutil.copytree(root/'pilot',root/'resumed');config['max_new_draws']=3
    done=k.execute(root/'resumed',inputs,config);assert done['new_sessions']==2 and done['reused_sessions']==1
    assert k.read(root/'resumed/SUMMARY.json')['counts']==dict(events=18,left_click_events=3,arrow_key_events=12)
    child=subprocess.run([sys.executable,'-X','utf8','-B','-m','runners.drive.cards.week5_bk_intake_fixture','--output',str(root),'--verify'],capture_output=True,text=True)
    if child.returncode:raise RuntimeError(child.stderr[-3000:])
    k.write(root/'COMPLETE.json',dict(passed=True,constructed=True,checks=check,quantum_resume=True,fresh_process=json.loads(child.stdout),source_pins={name:k.digest(Path(__file__).with_name(name)) for name in ('week5_bk_klicke_intake.py','week5_bk_intake_fixture.py')}));print(json.dumps(dict(passed=True,complete_source_replay=True)))


if __name__=='__main__':main()
