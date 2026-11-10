"""Exact canonical full-document accepted-append ancestry regression fixture."""
from pathlib import Path
import argparse,copy,json,shutil,subprocess,sys
from . import week5_bk_s2_source as original,week5_bk_s2_source_h1 as repaired,week5_bk_s2_source_checkpointed_h1 as source
from .week5_bk_s2_fixture import fixture_data
from .timing_text import replay_words
from .week4_revision_utf16_h1 import apply_delta,text_of
from .timing_p6 import write_equal,gzread,gzip_equal,gzwrite
from .timing_census import read,filehash


def append_fixture(order='delete-first'):
    data=fixture_data();end=next(i for i,e in enumerate(data['events']) if e.get('eventSource')=='api' and e.get('textDelta'))
    events=copy.deepcopy(data['events'][:end]);doc='\n'
    for event in events[1:]:
        values,_,_=apply_delta(original.units(doc),[None]*len(original.units(doc)),event.get('textDelta'));doc=text_of(values)
    clock=events[-1]['eventTimestamp']+1000;events.append(dict(eventName='suggestion-select',eventSource='user',eventTimestamp=clock))
    after=doc[:-1]+'\nAn offered idea. A final model line.\n';ops=[{'delete':len(original.units(doc))},{'insert':after}]
    if order=='insert-first':ops.reverse()
    clock+=1000;events.append(dict(eventName='text-change',eventSource='api',eventTimestamp=clock,textDelta={'ops':ops}))
    clock+=1000;at=len(original.units(after[:after.index('offered')+2]));events.append(dict(eventName='text-change',eventSource='user',eventTimestamp=clock,textDelta={'ops':[{'retain':at},{'insert':'new'}]}))
    clock+=1000;events.append(dict(eventName='system-finish',eventSource='api',eventTimestamp=clock))
    p6=replay_words(events)
    for word in p6['words']:word['population_log_frequency']=-2.
    return dict(events=events,p6=p6,intervals=[r for r in data['intervals'] if r['ordinal']<end],revision=original.revision.extract(events))


def checks():
    for order in ('delete-first','insert-first'):
        data=append_fixture(order);old,_,_=original.project(**dict(events=data['events'],p6=data['p6'],intervals=data['intervals'],prior_revision=data['revision']))
        new,_,_=repaired.project(data['events'],data['p6'],data['intervals'],data['revision'])
        assert len(old)==len(new)==4 and all(r['later_revisions'] for r in old) and not any(r['later_revisions'] for r in new)
        assert [(r['text'],r['completed_ordinal'],r['hesitancy'],r['timing_state']) for r in old]==[(r['text'],r['completed_ordinal'],r['hesitancy'],r['timing_state']) for r in new]
    for order in (None,'delete-first','insert-first'):
        data=fixture_data(order);old=original.project(data['events'],data['p6'],data['intervals'],data['revision']);new=repaired.project(data['events'],data['p6'],data['intervals'],data['revision'])
        assert old==new
    return dict(both_canonical_replacement_orders=True,legacy_false_link_to_all_four_initial_units_reproduced=True,new_append_no_false_prior_ancestry=True,ordinary_nonacceptance_api_edits_unchanged=True,timing_and_denominator_unchanged=True)


def config(quantum):return dict(card='BK-S2-inputs',mode='constructed',seed=20261102,expected_sessions=3,max_new_draws=quantum)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path);parser.add_argument('--verify',action='store_true');args=parser.parse_args();output=args.output
    inputs=dict(constructed_source=str(output/'FIXTURE.json'))
    if args.verify:
        result=source.verify(output/'resumed',inputs,config(3));check=checks()
        try:source.verify(output/'false-prefix',inputs,config(3))
        except ValueError as error:assert 'independent complete-session' in str(error)
        else:raise AssertionError('False cached prefix passed')
        print(json.dumps(dict(replay=result,known_answers=check,false_prefix_refused=True)));return
    output.mkdir(parents=True,exist_ok=True);check=checks();write_equal(output/'FIXTURE.json',dict(constructed=True,sessions=[fixture_data(),append_fixture(),append_fixture('insert-first')]))
    assert source.execute(output/'pilot',inputs,config(1))['status']=='yielded';shutil.copytree(output/'pilot',output/'resumed')
    done=source.execute(output/'resumed',inputs,config(3));assert done['new_sessions']==2 and done['reused_sessions']==1
    shutil.copytree(output/'resumed',output/'false-prefix');path=output/'false-prefix/raw-sessions/00000.json.gz';value=gzread(path);value['session']['sentences'][0]['text']='false constructed prefix';path.unlink();gzwrite(path,value)
    child=subprocess.run([sys.executable,'-X','utf8','-B','-m','runners.drive.cards.week5_bk_s2_append_fixture','--output',str(output),'--verify'],capture_output=True,text=True)
    if child.returncode:raise RuntimeError(child.stderr[-3000:])
    proof=dict(passed=True,constructed=True,known_answers=check,exact_source_quantum=True,new_resume_sessions=2,reused_sessions=1,fresh_process=json.loads(child.stdout),source_pins={n:filehash(Path(__file__).with_name(n)) for n in ('week5_bk_s2_source.py','week5_bk_s2_source_h1.py','week5_bk_s2_source_checkpointed_h1.py','week5_bk_s2_append_fixture.py')})
    write_equal(output/'COMPLETE.json',proof);print(json.dumps(dict(passed=True,full_fresh_replay=True)))


if __name__=='__main__':main()
