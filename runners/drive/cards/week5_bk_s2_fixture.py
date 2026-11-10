"""Native complete S2 linkage and known-answer inference fixture."""
from pathlib import Path
import argparse,json,subprocess,sys
import numpy as np
from threadpoolctl import threadpool_limits
from . import week5_bk_s2_source as source,week5_bk_s2_analysis as analysis
from .timing_text import replay_words
from .week4_revision_source_h1 import extract
from .week4_revision_utf16_h1 import text_of,apply_delta
from .timing_p6 import write_equal,gzip_equal,gzread
from .timing_census import filehash,read

def fixture_data(replacement_order=None):
    events=[dict(eventName='system-initialize',eventSource='api',eventTimestamp=1000000000.,currentDoc='\n')]
    doc='\n';clock=1000000.
    def change(ops,user=True,gap=.2):
        nonlocal doc,clock
        clock+=gap
        events.append(dict(eventName='text-change',eventSource='user' if user else 'api',eventTimestamp=clock*1000,textDelta={'ops':ops}))
        values,_,_=apply_delta(source.units(doc),[None]*len(source.units(doc)),{'ops':ops});doc=text_of(values)
    for char in 'Alpha bright birds sing. Beta calm cats sleep. Gamma kind dogs run. Delta quick foxes jump.':
        change([{'retain':len(source.units(doc))-1},{'insert':char}])
    # Sentence1 becomes mixed, then receives a later user edit. The primary
    # follows its original typed provenance; the frozen-census companion does not.
    if replacement_order:
        replacement=[{'insert':'Alpha bright birds sing.'},{'delete':24}]
        if replacement_order=='delete-first':replacement.reverse()
        change(replacement,False,5)
    else:change([{'retain':6},{'insert':'AI '}],False,5)
    change([{'retain':10},{'insert':'very '}],True,3)
    # Delete sentence2 in full. Its original denominator must remain.
    at=doc.index('Beta');end=doc.index('Gamma');change([{'retain':at},{'delete':end-at}],True,4)
    clock+=180;events.append(dict(eventName='system-finish',eventSource='api',eventTimestamp=clock*1000))
    p6=replay_words(events)
    for w in p6['words']:w['population_log_frequency']=-2.
    intervals=[]
    for ordinal,event in enumerate(events):
        if ordinal==0:continue
        ops=source.delta_ops(event.get('textDelta'));insert=''.join(op.get('insert','') for op in ops)
        if event['eventSource']=='user' and len(insert)==1:
            previous=events[ordinal-1]['eventTimestamp']/1000;seconds=event['eventTimestamp']/1000
            intervals.append(dict(ordinal=ordinal,onset=True,fast=.8 if ordinal%3 else .2,interval_seconds=seconds-previous))
    return dict(constructed=True,events=events,p6=p6,intervals=intervals,revision=extract(events))

def model_world(sign=1):
    sessions=[]
    for w in range(30):
        rows=[]
        for i in range(40):
            flow=i%2;k=i//2;outcome=int(k%10<(8 if flow else 2))
            if sign==-1:outcome=1-outcome
            elif sign==0:outcome=int(k%2==0)
            controls={k:0. for k in analysis.CONTROL_NAMES if k!='creative'}
            controls.update(sentence_length=8,mean_word_length=4,population_log_frequency=-2,own_prior_log_frequency=-2,
                            sentence_boundary=1,remaining_minutes=5,session_order=w)
            rows.append(dict(timing_state='eligible',**{'class':'flow' if flow else 'hesitant'},remaining_seconds=300,
                             controls=controls,intervening_nonuser_edit=False,
                             later_revisions=[dict(ordinal=i+100,lag_seconds=150,paragraph_nonlocal=True,current_target_fully_typed=True)] if outcome else []))
        sessions.append(dict(writer=f'constructed-{w}',session=f'constructed-{w}',genre='creative' if w%2 else 'argumentative',sentences=rows))
    return sessions

def complete_projection(root,sessions):
    output=root/'output';gzip_equal(output/'PRIVATE_SENTENCES.json.gz',sessions);write_equal(output/'SUMMARY.json',dict(constructed=True))
    receipt=dict(status='COMPLETE',fresh_process_verified=True,constructed=True,
                 outputs={'output/'+name:filehash(output/name) for name in ('PRIVATE_SENTENCES.json.gz','SUMMARY.json')})
    write_equal(root/'COMPLETE.json',receipt)

def check_source(path):
    sessions=gzread(path/'PRIVATE_SENTENCES.json.gz');rows=sessions[0]['sentences'];assert len(rows)==4
    assert [bool(r['later_revisions']) for r in rows]==[True,True,False,False]
    assert rows[0]['intervening_nonuser_edit']
    assert not rows[0]['later_revisions'][0]['current_target_fully_typed']
    assert rows[1]['later_revisions'][0]['current_target_fully_typed']
    assert rows[0]['start_seconds']<1 and all(r['timing_state']=='eligible' for r in rows)

def run(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);write_equal(output/'CONSTRUCTED_SOURCE.json',fixture_data())
    inputs=dict(constructed_source=str(output/'CONSTRUCTED_SOURCE.json'));config=dict(card='BK-S2-inputs',seed=source.SEED,mode='constructed')
    source.execute(output/'source-output',inputs,config);check_source(output/'source-output')
    for order in ('delete-first','insert-first'):
        f=fixture_data(order);rows,_,_=source.project(f['events'],f['p6'],f['intervals'],f['revision'])
        assert len(rows)==4 and rows[0]['intervening_nonuser_edit'] and len(rows[0]['later_revisions'])==1
    for verification in (False,True):
        folder=output/('source-verify-yield' if verification else 'source-execute-yield')
        write_equal(folder/'YIELD_REQUEST.json',{'reason':'constructed owner request'})
        assert source.run(folder,inputs,config,verification)['status']=='yielded'
    for label,sign in [('positive',1),('negative',-1),('null',0)]:
        complete_projection(output/label/'prepared',model_world(sign))
        cfg=dict(card='BK-S2',cell='primary',draws=2000,permutations=200,mode='constructed')
        analysis.execute(output/label/'analysis',dict(source_completion=str(output/label/'prepared'/'COMPLETE.json')),cfg)
        result=read(output/label/'analysis'/'SCIENCE.json');expected=.6*sign
        assert abs(result['primary']['effect']-expected)<1e-10
        assert result['direction']=={1:'positive',-1:'negative',0:'inconclusive'}[sign]
    for verification in (False,True):
        folder=output/('analysis-verify-yield' if verification else 'analysis-execute-yield')
        write_equal(folder/'YIELD_REQUEST.json',{'reason':'constructed owner request'})
        assert analysis.run(folder,dict(source_completion=str(output/'positive'/'prepared'/'COMPLETE.json')),cfg,verification)['status']=='yielded'
    # Dense independent GLS with the fitted random-intercept covariance checks
    # the sufficient-statistic within coefficient on nonconstant controls.
    data=model_world(1);rng=np.random.default_rng(43)
    for s in data:
        for r in s['sentences']:r['controls']['mean_word_length']=float(rng.uniform(2,8))
    rows,_=analysis.select(data);bundle=analysis.arrays(rows);fit=analysis.random_intercept_fit(bundle)
    x=fit.pop('_design');g=bundle['g'];v=np.eye(len(g))+fit['writer_variance_ratio']*(g[:,None]==g[None,:])
    beta=np.linalg.solve(x.T@np.linalg.solve(v,x),x.T@np.linalg.solve(v,bundle['y']))[0]/bundle['scale'][0]
    assert abs(beta-fit['effect'])<1e-9
    child=subprocess.run([sys.executable,'-X','utf8','-B','-m','runners.drive.cards.week5_bk_s2_fixture','--output',str(output),'--verify'],capture_output=True,text=True)
    if child.returncode:raise RuntimeError(child.stderr[-2000:])
    receipt=dict(passed=True,constructed=True,scientific_admission=False,source_pins={n:filehash(Path(__file__).with_name(n)) for n in ('week5_bk_s2_source.py','week5_bk_s2_analysis.py','week5_bk_s2_fixture.py')},
                 checks=['typed-to-mixed-to-user revision','both whole replacement delta orders','whole later deletion retained','no-user-revision negative','native source handler replay','source and analysis execute/verify owner yield','exact signed 0.6 and null controls','dense random-intercept GLS oracle','all2000bootstrap and200permutation fresh-process replay'],replay=json.loads(child.stdout))
    write_equal(output/'COMPLETE.json',receipt);return dict(passed=True,checks=len(receipt['checks']))

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--verify',action='store_true');args=p.parse_args();output=Path(args.output)
    if args.verify:
        proof=source.verify(output/'source-output',dict(constructed_source=str(output/'CONSTRUCTED_SOURCE.json')),dict(card='BK-S2-inputs',seed=source.SEED,mode='constructed'))
        results={label:analysis.verify(output/label/'analysis',dict(source_completion=str(output/label/'prepared'/'COMPLETE.json')),
                        dict(card='BK-S2',cell='primary',draws=2000,permutations=200,mode='constructed')) for label in ('positive','negative','null')}
        result=dict(source=proof,models=results)
    else:
        with threadpool_limits(limits=1):result=run(output)
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
