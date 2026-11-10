"""Exact empty-stratum recovery with complete native source replay."""
from pathlib import Path
import argparse,copy,json,shutil,subprocess,sys
from . import week5_bk_s2_source_h1 as old,week5_bk_s2_empty_support as new,week5_bk_s2_source_checkpointed_h2 as source
from .week5_bk_s2_fixture import fixture_data
from .week5_bk_s2_append_fixture import append_fixture,checks as append_checks
from .timing_p6 import write_equal,gzread,gzip_equal,gzwrite
from .timing_census import read,filehash


def session(data,writer):
    rows,_,pairs=old.project(data['events'],data['p6'],data['intervals'],data['revision']);words,_=old.produced_words(data['p6']['words'])
    return dict(session='constructed-'+writer,writer=writer,genre='creative',timestamp=0,session_order=0,sentences=rows,bigram_intervals=pairs,first_words=words)


def checks():
    data=fixture_data();supported=session(data,'supported');empty=session(data,'empty')
    for row in empty['sentences']:row['timing_state']='missing_onset_timing';row['hesitancy']=None
    expected=copy.deepcopy([supported]);old.classify_and_controls(expected)
    mixed=copy.deepcopy([supported,empty]);report=new.classify_and_controls(mixed)
    assert mixed[0]==expected[0] and len(mixed[1]['sentences'])==len(empty['sentences'])
    assert not any('class' in row for row in mixed[1]['sentences']) and sum(r['status']=='no_eligible_timing' for r in report)==1
    try:old.classify_and_controls(copy.deepcopy([supported,empty]))
    except ValueError as error:assert str(error)=='Finite stretch values required'
    else:raise AssertionError('Original empty-stratum fault not reproduced')
    all_empty=copy.deepcopy([empty]);assert new.classify_and_controls(all_empty)[0]['status']=='no_eligible_timing'
    tied=copy.deepcopy(supported)
    for row in tied['sentences']:
        if row['timing_state']=='eligible':row['hesitancy']=0.5
    a,b=copy.deepcopy([tied]),copy.deepcopy([tied]);old.classify_and_controls(a);new.classify_and_controls(b);assert a==b
    assert all(row.get('class')=='middle' for row in b[0]['sentences'] if row.get('class'))
    broken=copy.deepcopy(supported);next(r for r in broken['sentences'] if r['timing_state']=='eligible')['hesitancy']=float('nan')
    try:new.classify_and_controls([broken])
    except ValueError:pass
    else:raise AssertionError('Nonfinite eligible value accepted')
    assert new.project is old.project
    return dict(original_crash_reproduced=True,nonempty_outputs_exact=True,all_empty_retained=True,tied_thirds_exact=True,nonfinite_still_refused=True,mixed_cohort_retains_undefined_rows=True,original_project_identity=True,append_regressions=append_checks())


def config(quantum):return dict(card='BK-S2-inputs',mode='constructed',seed=20261102,expected_sessions=3,max_new_draws=quantum)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);p.add_argument('--verify',action='store_true');a=p.parse_args();root=a.output;inputs=dict(constructed_source=str(root/'FIXTURE.json'))
    if a.verify:
        result=source.verify(root/'resumed',inputs,config(3))
        false=root/'false-prefix';shutil.copytree(root/'resumed',false);path=false/'raw-sessions/00000.json.gz';value=gzread(path);value['session']['sentences'][0]['text']='false prefix';path.unlink();gzwrite(path,value)
        try:source.verify(false,inputs,config(3))
        except ValueError:pass
        else:raise AssertionError('False prefix passed source replay')
        print(json.dumps(dict(replay=result,false_prefix_refused=True,checks=checks())));return
    root.mkdir(parents=True,exist_ok=True);check=checks();data=[fixture_data(),append_fixture(),append_fixture('insert-first')]
    for item in data:item['intervals']=[]
    write_equal(root/'FIXTURE.json',dict(constructed=True,sessions=data))
    assert source.execute(root/'pilot',inputs,config(1))['status']=='yielded';shutil.copytree(root/'pilot',root/'resumed')
    result=source.execute(root/'resumed',inputs,config(3));assert result['new_sessions']==2 and result['reused_sessions']==1
    summary=read(root/'resumed/SUMMARY.json');assert summary['sessions']==3 and summary['writers']==1 and summary['zero_eligible_timing_writers']==1
    assert sum(len(s['sentences']) for s in gzread(root/'resumed/PRIVATE_SENTENCES.json.gz'))==12
    child=subprocess.run([sys.executable,'-X','utf8','-B','-m','runners.drive.cards.week5_bk_s2_empty_fixture','--output',str(root),'--verify'],capture_output=True,text=True)
    if child.returncode:raise RuntimeError(child.stderr[-3000:])
    write_equal(root/'COMPLETE.json',dict(passed=True,constructed=True,checks=check,source_quantum_resume=True,all12undefined_source_sentences_retained=True,fresh_process=json.loads(child.stdout),source_pins={n:filehash(Path(__file__).with_name(n)) for n in ('week5_bk_s2_source_h1.py','week5_bk_s2_source_checkpointed_h1.py','week5_bk_s2_empty_support.py','week5_bk_s2_source_checkpointed_h2.py','week5_bk_s2_empty_fixture.py')}));print(json.dumps(dict(passed=True,complete_source_replay=True)))


if __name__=='__main__':main()
