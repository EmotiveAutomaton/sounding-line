"""Complete native S4.k constructed source and numerical known-answer proof."""
from pathlib import Path
import argparse,csv,io,json,shutil,subprocess,sys,time,zipfile
import numpy as np
from . import week5_bk_klicke_intake as intake
from . import week5_bk_klicke_intake_v2 as intake_v2
from . import week5_bk_s4k_navigation as nav
from . import week5_bk_s4k_source as source
from . import week5_bk_s4k_analysis as analysis
from .batch_runtime import freeze,read,filehash,REPO


def encoded(text):
    return text.replace('\\','\\\\').replace('\n','\\n').replace('\t','\\t').replace('\r','\\r')


class Writer:
    def __init__(self): self.doc=[];self.events=[]
    def add(self,stamp,key,cursor,activity='Nonproduction',change='NoChange'):
        event=dict(DownTime=stamp*1000,UpTime=stamp*1000+10,ActionTime=10,DownEvent=key,UpEvent=key,
                   CursorPosition=cursor,PauseTime=0,WordCount=0,Activity=activity,TextChange=encoded(change),ordinal=len(self.events))
        self.doc,_=nav.operation(self.doc,event);self.events.append(event)
    def record(self,key='constructed'):
        return dict(session=key,events=self.events,final_text=(nav.text_of(self.doc)+'\n').replace('\n','\r\r\n'))


def writing_fixture(writer=0):
    w=Writer();text='First sentence. Second sentence. Third sentence. Fourth sentence. Fifth sentence. Sixth sentence. Seventh sentence. Eighth sentence.'
    w.add(0,'Paste',len(nav.units(text)),'Paste',text)
    for i in range(40):
        t=10+i*70;click=i%2==0;j=i//2
        w.add(t-1,'End',len(w.doc))
        if click: w.add(t,'Leftclick',20)
        else:
            w.add(t,'ArrowUp',21);w.add(t+.2,'ArrowLeft',20)
        successful=j<(12+writer%4 if click else 4-writer%4)
        if successful: w.add(t+1,'x',21,'Input','x')
    w.add(2900,'End',len(w.doc))
    return w.record('fixture-'+str(writer))


def csv_bytes(record):
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=['Participant',*intake.COLUMNS]);writer.writeheader()
    for e in record['events']:
        row={k:e.get(k,0) for k in intake.COLUMNS};row.update(Participant='constructed-private-token',DownEventID=e['ordinal'],UpEventID=e['ordinal']);writer.writerow(row)
    return stream.getvalue().encode()


def fixture_archive(root):
    root.mkdir(parents=True,exist_ok=True);archive=root/'source.zip'
    with zipfile.ZipFile(archive,'w') as z:
        for i in range(24):
            record=writing_fixture(i);z.writestr(f'csv/constructed-{i:03d}.csv',csv_bytes(record));z.writestr(f'txt/constructed-{i:03d}.txt',record['final_text'])
    (root/'salt.bin').write_bytes(bytes(range(32)))
    return dict(archive=str(archive),archive_sha256=filehash(archive),identity_salt=str(root/'salt.bin'))


def numeric_rows(kind='positive'):
    sessions=[]
    for i in range(24):
        rows=[]
        for device in ('click','arrow'):
            successes=10 if kind=='null' else 12+i%4 if device=='click' else 4-i%4
            if kind=='negative':successes=20-successes
            for j in range(20): rows.append(dict(kind=device,bin='2',edit_near=j<successes))
        sessions.append(dict(writer=str(i),session=str(i),landings=rows))
    return sessions


def checks():
    # Exact Unicode/escape, delete, replacement, and overlapping-coordinate move.
    w=Writer();w.add(0,'Paste',7,'Paste','A😀\nB\\C');w.add(1,'Backspace',6,'Remove/Cut','C')
    w.add(2,'x',6,'Replace','\\ => x');w.add(3,'Paste',8,'Input','\\n')
    assert nav.replay(w.record(),False)['final_text']=='A😀\nBx\\n'
    moved=list(nav.units('abcdef'))
    event=dict(Activity='Move From [0, 2] To [1, 3]',TextChange='ab',CursorPosition=3)
    after,_=nav.operation(moved,event);assert nav.text_of(after)=='cabdef'
    event=dict(Activity='Move From [3, 5] To [1, 3]',TextChange='de',CursorPosition=3)
    after,_=nav.operation(moved,event);assert nav.text_of(after)=='adebcf'
    record=writing_fixture();result=nav.extract(record)
    assert len(result['landings'])==40 and result['census']['inside_arrow_run']==20
    assert sum(r['edit_near'] for r in result['landings'] if r['kind']=='click')==12
    assert sum(r['edit_near'] for r in result['landings'] if r['kind']=='arrow')==4
    false={**record,'final_text':'Incorrect.\n'}
    assert source.project(false)['status']=='reconstruction_failed'
    short={**record,'events':record['events'][:-1]}
    assert nav.extract(short)['census']['followup_window_censored']>=1
    p=Writer();p.add(0,'Paste',len(nav.units('One. Two. Three. Four.')),'Paste','One. Two. Three. Four.')
    p.add(5,'Leftclick',0);p.add(6,'Leftclick',5);p.add(7,'x',6,'Input','x');p.add(80,'End',len(p.doc))
    assert nav.extract(p.record())['census']['pass_through_click']==1
    results={}
    for kind in ('null','positive','negative'):
        summary,_=analysis.analyze(numeric_rows(kind));results[kind]=summary
    assert results['null']['estimate']==0 and results['null']['state']=='null'
    assert abs(results['positive']['estimate']-.55)<1e-14 and results['positive']['interval'][0]>0
    assert abs(results['negative']['estimate']+.55)<1e-14 and results['negative']['interval'][1]<0
    # Strong raw device/distance confounding; both within-bin differences zero.
    distance=[]
    for i in range(24):
        rows=[]
        for b in ('1','>5'):
            for device,n in [('click',100 if b=='1' else 10),('arrow',10 if b=='1' else 100)]:
                for j in range(n):rows.append(dict(kind=device,bin=b,edit_near=j<(n*9//10 if b=='1' else n//10)))
        distance.append(dict(writer=str(i),session=str(i),landings=rows))
    summary,_=analysis.analyze(distance);assert summary['estimate']==0 and summary['state']=='null'
    below,_=analysis.analyze(numeric_rows()[:1]);assert below['state']=='below floor, descriptive' and below['interval'] is None and below['pooled_descriptive']['estimate']==.4
    empty,_=analysis.analyze([]);assert empty['estimate'] is None
    identical=numeric_rows()
    for row in identical:row['landings']=identical[0]['landings']
    collapsed,_=analysis.analyze(identical)
    assert collapsed['control_status']=='degenerate cluster uncertainty' and not collapsed['inference_eligible']
    return dict(utf16_and_escaped_text_exact=True,edit_reconstruction_exact=True,independent_final_text_required=True,
                pass_through_and_arrow_runs=True,right_censoring=True,signed_and_exact_null=True,
                distance_confounding_removed=True,below_floor_pooled_fit=True,no_shared_bins_undefined=True,constant_nonzero_uncertainty_blocked=True)


def seal(root,module,inputs,config,verified):
    freeze(root/'PLAN.json',dict(module=module,inputs=inputs,config=config))
    freeze(root/'VERIFIED.json',verified)
    files=[root/'PLAN.json',root/'VERIFIED.json',*sorted((root/'output').rglob('*'))]
    freeze(root/'COMPLETE.json',dict(status='COMPLETE',constructed_fixture=True,fresh_process_verified=True,
        outputs={p.relative_to(root).as_posix():filehash(p) for p in files if p.is_file()}))


def fresh(root,phase):
    child=subprocess.run([sys.executable,'-X','utf8','-B','-m',__spec__.name,'--output',str(root),'--replay',phase],capture_output=True,text=True)
    if child.returncode: raise RuntimeError(child.stderr[-3000:])
    result=json.loads(child.stdout);cost=result.pop('_fixture_process_cpu_seconds')
    freeze(root/'fresh-costs'/(phase+'.json'),dict(cpu_seconds=cost))
    return result


def run(root):
    root.mkdir(parents=True,exist_ok=False);start=time.process_time();known=checks()
    inputs=fixture_archive(root/'raw');ic=dict(card='BK-S4.k-intake',mode='constructed',expected_sessions=24,max_new_draws=24)
    intake_v2.execute(root/'intake/output',inputs,ic)
    freeze(root/'intake/REPLAY.json',dict(inputs=inputs,config=ic))
    seal(root/'intake','runners.drive.cards.week5_bk_klicke_intake_v2',inputs,ic,fresh(root,'intake'))
    source_inputs=dict(intake_complete=str(root/'intake/COMPLETE.json'));sc=dict(card='BK-S4.k-source',mode='constructed',max_new_draws=1)
    first=source.execute(root/'pause',source_inputs,sc);assert first['status']=='yielded'
    shutil.copytree(root/'pause',root/'source/output');done=source.execute(root/'source/output',source_inputs,{**sc,'max_new_draws':24})
    assert done['new_sessions']==23
    freeze(root/'source/REPLAY.json',dict(inputs=source_inputs,config=sc))
    seal(root/'source','runners.drive.cards.week5_bk_s4k_source',source_inputs,sc,fresh(root,'source'))
    for window in (30,60):
        ai=dict(source_complete=str(root/'source/COMPLETE.json'));ac=dict(card='BK-S4.k',mode='constructed',window=window,draws=2000 if window==30 else 200,permutations=200)
        output=root/str(window);analysis.execute(output,ai,ac)
        freeze(output/'REPLAY.json',dict(inputs=ai,config=ac));verified=fresh(root,str(window));assert verified['full_numerical_replay']
        assert abs(read(output/'SUMMARY.json')['estimate']-.55)<1e-14
    false=root/'tampered';shutil.copytree(root/'source/output',false)
    path=false/'sessions/00000.json.gz';changed=intake.read(path)
    changed['windows']['30']['landings'][0]['edit_near']=not changed['windows']['30']['landings'][0]['edit_near']
    path.unlink();intake.write(path,changed)
    try:source.verify(false,source_inputs,sc)
    except ValueError:pass
    else:raise AssertionError('Tampered source prefix accepted')
    known['tampered_cached_outcome_refused']=True
    child_cpu=sum(read(p)['cpu_seconds'] for p in (root/'fresh-costs').glob('*.json'))
    freeze(root/'FIXTURE.json',dict(passed=True,constructed=True,checks=known,whole_source_and_numerical_replay=True,
        source_sessions=24,primary_draws=2000,texture_draws=200,permutations_each=200,cpu_seconds=time.process_time()-start+child_cpu,
        child_cpu_seconds=child_cpu,
        files={str(Path(m.__file__).relative_to(REPO)):filehash(m.__file__) for m in (nav,source,analysis)},fixture_sha256=filehash(__file__)))
    return dict(passed=True,proof=str(root/'FIXTURE.json'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--replay');a=p.parse_args();root=a.output.resolve()
    if a.replay:
        if a.replay=='intake':m=intake_v2;output=root/'intake/output';spec=read(root/'intake/REPLAY.json')
        elif a.replay=='source':m=source;output=root/'source/output';spec=read(root/'source/REPLAY.json')
        else:m=analysis;output=root/a.replay;spec=read(output/'REPLAY.json')
        result=m.verify(output,spec['inputs'],spec['config']);result['_fixture_process_cpu_seconds']=time.process_time()
        print(json.dumps(result))
    else:print(json.dumps(run(root)))
