"""S0: retained-response diagnosis and explicitly secondary training-cap analysis.

DESIGN CHECK: LESSONS 2-5. NULL: changing the sensitivity training cap cannot
overwrite a published table or silently use evaluator outcomes in fitting.
ALTERNATIVE: deterministic three-per-writer sampling yields a distinct fitted
rival and separately labelled sensitivity scores. Equal vectors have zero
contrast; all old raw responses reparse before analysis. No model calls.
"""
from collections import Counter,defaultdict
from runners.stage11 import core
from runners.stage11.prepare import balanced
from runners.stage11.report import attempt,reparse,average
from runners.stage11.run import execute
from .common import PRIVATE,OLD,contract,read,freeze,digest


def capped_training(rows):
    return balanced(rows,96,3)


def run(root=PRIVATE):
    contract(root)
    before=len(list((OLD/'calls').rglob('REQUEST.json')))
    assert execute(OLD)['status']=='COMPLETE'
    assert execute(OLD,pilot=True)['status']=='COMPLETE'
    assert before==len(list((OLD/'calls').rglob('REQUEST.json')))==204
    cohort=read(OLD/'COHORT.json');original=read(OLD/'BASELINES.json')
    capped=capped_training(cohort['train']);sensitivity=core.fit(capped)
    freeze(root/'S0/CAPPED_TRAIN.json',capped)
    freeze(root/'S0/CAPPED_BASELINES.json',sensitivity)
    cells=[];diagnostics=[]
    for tranche in ('initial','extension'):
        own=[r for r in cohort['evaluation'] if r['tranche']==tranche]
        for view in core.VIEWS:
            for version,model in [('published_96',original),('cap_3_per_writer',sensitivity)]:
                for arm in ('prior','features'):
                    rows=[dict(writer=r['writer'],**core.scores(core.predict(r['views'][view],view,model,arm),r['truth'])) for r in own]
                    cells.append(dict(tranche=tranche,view=view,arm=arm,training=version,
                        **{k:average(rows,k) for k in ('brier','accuracy','log_loss')}))
            for arm in core.ARMS:
                classes=Counter();errors=Counter();bins=defaultdict(list);unobserved=Counter();wrong=0
                for r in own:
                    saved=reparse(attempt(OLD,'evaluation',r,view,arm),r['views'][view],arm)
                    classes[r['truth']]+=1
                    if saved['forecast'] is None:errors[saved['error']]+=1;continue
                    f=saved['forecast'];p=f['probabilities'];chosen=max(range(4),key=lambda j:p[j]);correct=core.ACTIONS[chosen]==r['truth']
                    wrong+=not correct;bins[min(int(max(p)*4),3)].append(dict(writer=r['writer'],confidence=max(p),correct=float(correct)))
                    for e in f.get('events',[]):
                        op=e['operation'].casefold().strip()
                        if op in ('review','reviewed','endorse','endorsed','understand','understood','expert'):
                            unobserved[op]+=1
                diagnostics.append(dict(tranche=tranche,view=view,arm=arm,classes=dict(classes),invalid=dict(errors),
                    valid_wrong_decisions=wrong,unobserved_event_attributes=dict(unobserved),
                    reliability_bins=[dict(bin=i,episodes=len(v),writers=len({r['writer'] for r in v}),
                        mean_confidence=average(v,'confidence'),observed_accuracy=average(v,'correct')) for i,v in sorted(bins.items())],
                    caution='Descriptive confidence bins, not calibration training; unobserved operation vocabulary flags are not semantic grading of every narrative. Six-case manual audit remains separately retained.'))
    result=dict(status='COMPLETE',branch='S0',partition='historical_stage11',new_model_calls=0,
        original_attempts_reparsed=204,training_deviation='Stage 11 applied a per-writer cap of 96 in training instead of the requested three. Published primary scores remain unchanged; this is a separately reported sensitivity.',
        training=dict(published=len(cohort['train']),sensitivity=len(capped),writers=len({r['writer'] for r in capped}),counts=dict(Counter(r['writer'] for r in capped))),
        original_comparison_digest=digest(read(OLD/'COMPARISONS.json')),cells=cells,diagnostics=diagnostics,
        pursuit='Carry capped and uncapped training controls explicitly; construct a low-dimensional alignment rival for the common production targets.',
        warrant='Secondary descriptive sensitivity on historically exposed episodes; no alteration of L390 and no fresh confirmation.',
        next_action='S0 alignment rival and S1 direct reference bank on the frozen expanded discovery roster')
    freeze(root/'S0/COMPLETE.json',result)
    return dict(status=result['status'],branch='S0',attempts_reparsed=204,new_model_calls=0,sensitivity_training_episodes=len(capped))


if __name__=='__main__':print(run())
