"""Native T2 ancestry, real encoder and complete model/uncertainty controls."""
from pathlib import Path
import argparse,copy,json,shutil,subprocess,sys
from . import week5_bk_t2_source as source,week5_bk_t2_features as features,week5_bk_t2_analysis as analysis
from .week5_bk_s2_fixture import fixture_data
from . import week5_bk_s2_source as s2
from .week4_revision_utf16_h1 import apply_delta,text_of
from .timing_p6 import write_equal,gzip_equal,gzread
from .timing_census import read,filehash


def timeline(events):
    doc=source.units(events[0]['currentDoc']);tags=['prompt']*len(doc);pending=False
    for ordinal,event in enumerate(events):
        if event['eventName']=='suggestion-select':pending=True
        if not source.delta_ops(event.get('textDelta')):continue
        olddoc,oldtags=doc,tags;doc,tags,_=apply_delta(doc,tags,event['textDelta'],insertion_owner='typed' if event['eventSource']=='user' else 'api_unknown')
        if pending and event['eventSource']!='user':tags=oldtags[:-1]+['accepted']*(len(doc)-len(olddoc))+oldtags[-1:];pending=False
    spans=[];start=0
    for i in range(1,len(tags)+1):
        if i==len(tags) or tags[i]!=tags[start]:spans.append(dict(origin=tags[start],text=text_of(doc[start:i]),start_utf16=start,end_utf16=i));start=i
    return dict(final_document=text_of(doc),final_spans=spans)


def source_fixture(order=None,merge=False,split=False,full_append=False):
    original=fixture_data(order);first,_,_=s2.project(original['events'],original['p6'],original['intervals'],original['revision'])
    for i,row in enumerate(first):row['class']='flow' if i%2==0 else 'hesitant'
    events=copy.deepcopy(original['events'][:-1]);current=timeline(events)['final_document'];clock=events[-1]['eventTimestamp']+1000
    def change(ops,user=True):
        nonlocal current,clock
        clock+=1000;events.append(dict(eventName='text-change',eventSource='user' if user else 'api',eventTimestamp=clock,textDelta={'ops':ops}))
        doc,_,_=apply_delta(source.units(current),[None]*len(source.units(current)),{'ops':ops});current=text_of(doc)
    if merge:
        at=current.index('.');change([{'retain':len(source.units(current[:at]))},{'delete':2}])
    if split:
        at=current.index('kind');change([{'retain':len(source.units(current[:at]))},{'insert':'. '}])
    clock+=1000;events.append(dict(eventName='suggestion-select',eventSource='user',eventTimestamp=clock))
    if full_append:change([{'delete':len(source.units(current))},{'insert':current[:-1]+'\nAn offered idea.\n'}],False)
    else:change([{'retain':len(source.units(current))-1},{'insert':'\nAn offered idea.'}],False)
    clock+=1000;events.append(dict(eventName='system-finish',eventSource='api',eventTimestamp=clock))
    return dict(events=events,first_units=first,reference=source.revision.extract(events),timeline=timeline(events))


def world(kind):
    rows=[]
    for w in range(20):
        for i in range(8):
            y=i%2;base=[float(y) if kind=='baseline_only' else 0.,0.,0.]
            full=base+([float(y)] if kind=='signal' else [0.])
            rows.append(dict(writer=f'constructed-{w:02}',session=f'constructed-{w:02}',index=i,genre='creative' if w%2 else 'argumentative',labels={k:y for k in ('a','b','c')},baseline=base,features=full))
    return rows


def complete(root,names):
    write_equal(root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,constructed=True,outputs={'output/'+name:filehash(root/'output'/name) for name in names}))


def model_config(quantum=2200):return dict(card='BK-T2',target='a',cell='primary',draws=2000,permutations=200,max_new_draws=quantum)
def source_config(quantum):return dict(card='BK-T2-source',mode='constructed',expected_sessions=2,max_new_draws=quantum)


def verify_all(output,manifest,dictionary):
    proof=source.verify(output/'source/output',dict(constructed_source=str(output/'SOURCE_FIXTURE.json')),source_config(2))
    n=read(output/'source/output/SUMMARY.json')['sentences'];fi=dict(source_completion=str(output/'source/COMPLETE.json'),encoder_manifest=manifest,dictionary_completion=dictionary)
    forward=features.verify(output/'features/output',fi,dict(card='BK-T2-features',phase='score',start=0,stop=n))
    collection=features.verify(output/'collection/output',dict(source_completion=fi['source_completion'],feature_completions=[str(output/'features/COMPLETE.json')]),dict(card='BK-T2-features',phase='collect'))
    models={name:analysis.verify(output/name/'analysis',dict(feature_completion=str(output/name/'prepared/COMPLETE.json')),model_config()) for name in ('signal','null','baseline_only')}
    return dict(source=proof,encoder=forward,collection=collection,models=models)


def run(output,manifest,dictionary):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    write_equal(output/'SOURCE_FIXTURE.json',dict(constructed=True,sessions=[source_fixture(full_append=True),source_fixture(merge=True)]))
    inputs=dict(constructed_source=str(output/'SOURCE_FIXTURE.json'));pilot=source.execute(output/'pilot/output',inputs,source_config(1));assert pilot['status']=='yielded'
    shutil.copytree(output/'pilot/output',output/'source/output');assert source.execute(output/'source/output',inputs,source_config(2))['status']=='complete'
    complete(output/'source',['PRIVATE_SENTENCES.json.gz','SUMMARY.json'])
    n=read(output/'source/output/SUMMARY.json')['sentences'];fi=dict(source_completion=str(output/'source/COMPLETE.json'),encoder_manifest=manifest,dictionary_completion=dictionary)
    assert features.execute(output/'features/output',fi,dict(card='BK-T2-features',phase='score',start=0,stop=n))['status']=='complete';complete(output/'features',['PRIVATE_FEATURES.json.gz','SUMMARY.json'])
    features.execute(output/'collection/output',dict(source_completion=fi['source_completion'],feature_completions=[str(output/'features/COMPLETE.json')]),dict(card='BK-T2-features',phase='collect'))
    for name in ('signal','null','baseline_only'):
        gzip_equal(output/name/'prepared/output/PRIVATE_FEATURES.json.gz',world(name));complete(output/name/'prepared',['PRIVATE_FEATURES.json.gz'])
        inputs=dict(feature_completion=str(output/name/'prepared/COMPLETE.json'))
        assert analysis.execute(output/name/'pilot',inputs,model_config(110))['status']=='yielded'
        state=read(output/name/'pilot/PRIVATE_STATE.json');assert len(state['bootstrap'])==100 and len(state['permutation'])==10
        shutil.copytree(output/name/'pilot',output/name/'analysis')
        assert analysis.execute(output/name/'analysis',inputs,model_config())['status']=='complete'
        result=read(output/name/'analysis/SCIENCE.json');expected=.5 if name=='signal' else 0.
        assert abs(result['gain']-expected)<1e-12 and result['control_complete'] and result['useful']==(name=='signal')
    child=subprocess.run([sys.executable,'-X','utf8','-B','-m','runners.drive.cards.week5_bk_t2_fixture','--output',str(output),'--encoder-manifest',manifest,'--dictionary-completion',dictionary,'--verify'],capture_output=True,text=True)
    if child.returncode:raise RuntimeError(child.stderr[-3000:])
    receipt=dict(passed=True,constructed=True,human_execution=False,real_encoder=True,exact_source_and_numerical_pilots=True,all2000bootstrap200refitted_permutations=True,fresh_process=json.loads(child.stdout),
        source_pins={n:filehash(Path(__file__).with_name(n)) for n in ('week5_bk_t2_source.py','week5_bk_t2_features.py','week5_bk_t2_analysis.py','week5_bk_t2_fixture.py')})
    write_equal(output/'COMPLETE.json',receipt);return dict(passed=True,full_fresh_replay=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);p.add_argument('--encoder-manifest',required=True);p.add_argument('--dictionary-completion',required=True);p.add_argument('--verify',action='store_true');args=p.parse_args()
    print(json.dumps(verify_all(args.output,args.encoder_manifest,args.dictionary_completion) if args.verify else run(args.output,args.encoder_manifest,args.dictionary_completion),sort_keys=True))


if __name__=='__main__':main()
