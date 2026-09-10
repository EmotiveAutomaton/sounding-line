"""Development-only B-roll forward-selection baselines under matched script access.

DESIGN CHECK: H03/I02/X04/X05. Train population POS/goal preferences on development
people and five nonheld scripts. Predict other development people's selections on
two unseen scripts. Personal adaptation sees at most three genuinely earlier trials;
wrong-person adaptation sees the same script set and goal. Score Bernoulli Brier,
not a categorical next-action score. No reserve/discovery outcome file is opened.
NULL: identical histories produce zero adaptation gain. ALTERNATIVE: stable known
POS preferences improve held-out selection while a wrong person's profile hurts.
"""
from collections import Counter,defaultdict
import math
import time

from runners.stage9.common import REPO,ROOT,closure,digest,freeze,read
from runners.stage9.scoring import brier,paired_interval


def features(stimulus,w):
    return stimulus['pos'][w]


def learned_rates(rows,scripts):
    counts=defaultdict(lambda:[0,0]);global_counts=defaultdict(lambda:[0,0])
    for row in rows:
        s=scripts[row['script_key']]
        for w,y in zip(s['support'],row['labels']):
            key=(row['goal'],features(s,w));counts[key][0]+=y;counts[key][1]+=1
            global_counts[row['goal']][0]+=y;global_counts[row['goal']][1]+=1
    return counts,global_counts


def probabilities(stimulus,goal,population,history=(),scripts=None):
    counts,globals_=population
    global_p=(globals_[goal][0]+1)/(globals_[goal][1]+2)
    individual=Counter();opportunities=Counter()
    for row in history:
        s=scripts[row['script_key']]
        for w,y in zip(s['support'],row['labels']):
            tag=features(s,w);individual[tag]+=y;opportunities[tag]+=1
    output=[]
    for w in stimulus['support']:
        tag=features(stimulus,w);chosen,total=counts[(goal,tag)]
        prior=(chosen+20*global_p)/(total+20)
        output.append((individual[tag]+20*prior)/(opportunities[tag]+20))
    return output


def ordinary(stimulus,mode):
    if mode=='uniform':weights=[1.]*len(stimulus['support'])
    elif mode=='frequency':weights=[float(stimulus['word_counts'][w]) for w in stimulus['support']]
    elif mode=='noun_adjective':weights=[1. if stimulus['pos'][w] in ('noun','proper noun','adj') else .02 for w in stimulus['support']]
    else:raise ValueError('unknown ordinary selection model')
    # Fixed instructed budget midpoint, never this target person's actual count.
    return [min(1.,17.5*w/sum(weights)) for w in weights]


def run():
    root=ROOT/'private/prepared/broll-v1';output=ROOT/'private/pilot-baseline/broll-v1'
    if (output/'COMPLETE.json').exists():return read(output/'COMPLETE.json')
    started=time.time();identity=read(root/'IDENTITY.json');scripts=read(root/'SCRIPTS.json')
    rows=read(root/'development.json')
    people=sorted({r['person'] for r in rows},key=lambda p:digest({'broll-development-fit':p}))
    fit_people=set(people[:2*len(people)//3]);test_people=set(people)-fit_people
    fit_scripts={s for s,v in identity['script_split'].items() if v=='discovery'}
    test_scripts={s for s,v in identity['script_split'].items() if v=='development'}
    training=[r for r in rows if r['person'] in fit_people and r['script_key'] in fit_scripts and r['usable']]
    population=learned_rates(training,scripts)
    by_person=defaultdict(list)
    for row in rows:by_person[row['person']].append(row)
    attempted=[r for r in rows if r['person'] in test_people and r['script_key'] in test_scripts]
    predictions=[];exclusions=Counter()
    for row in attempted:
        if not row['usable']:
            exclusions['target has unmatched selection fragments']+=1;continue
        history=sorted([r for r in by_person[row['person']] if r['trial']<row['trial'] and r['usable'] and r['script_key'] in fit_scripts],
                       key=lambda r:r['trial'])[-3:]
        wanted={r['script_key'] for r in history}
        wrong=None
        for person in sorted(fit_people,key=lambda p:digest({'broll-wrong-person':row['key'],'person':p})):
            candidates=[r for r in by_person[person] if r['script_key'] in wanted and r['goal']==row['goal'] and r['usable']]
            if len(candidates)==len(history):wrong=candidates;break
        if wrong is None:
            exclusions['no matched wrong-person history']+=1;continue
        s=scripts[row['script_key']]
        arms={mode:ordinary(s,mode) for mode in ('uniform','frequency','noun_adjective')}
        arms.update(population=probabilities(s,row['goal'],population),
                    individual=probabilities(s,row['goal'],population,history,scripts),
                    wrong_person=probabilities(s,row['goal'],population,wrong,scripts))
        predictions.append({'key':row['key'],'unit':row['person'],'script':row['script_key'],'goal':row['goal'],
                            'actual_earlier_trials':len(history),'earlier_keys':[r['key'] for r in history],
                            'wrong_earlier_keys':[r['key'] for r in wrong],
                            'probabilities':arms,'truth':row['labels']})
    # Immutable full predictions precede scoring. Raw human choices stay private.
    plan={'source_identity':digest(identity),'script_keys':{'fit':sorted(fit_scripts),'test':sorted(test_scripts)},
          'fit_people_sha256':digest(sorted(fit_people)),'test_people_sha256':digest(sorted(test_people)),
          'sources':closure([REPO/'runners/stage9'/n for n in ('broll_baseline.py','broll.py','scoring.py','common.py')]),
          'prior_strength':20,'ordinary_budget':17.5,'maximum_prior_trials':3,'scope':'development-only predictive baseline; not discovery or confirmation'}
    freeze(output/'IDENTITY.json',plan);freeze(output/'PREDICTIONS.json',predictions)
    scored=[]
    for r in predictions:
        scores={arm:brier(p,r['truth']) for arm,p in r['probabilities'].items()}
        scored.append({k:r[k] for k in ('key','unit','script','goal','actual_earlier_trials')}|{'scores':scores})
    summary={}
    for arm in ('frequency','noun_adjective','population','individual','wrong_person'):
        cells=[r|{'difference':r['scores']['uniform']-r['scores'][arm]} for r in scored]
        summary[arm+'_over_uniform']=paired_interval(cells,second_cluster='script')
    for rival in ('population','wrong_person'):
        summary['individual_over_'+rival]=paired_interval([r|{'difference':r['scores'][rival]-r['scores']['individual']} for r in scored],second_cluster='script')
    result={'identity_sha256':digest(plan),'training_trials':len(training),'training_people':len(fit_people),
            'attempted_test_trials':len(attempted),'completed_test_trials':len(scored),'exclusions':dict(exclusions),
            'tested_people':len({r['unit'] for r in scored}),'test_scripts':len(test_scripts),
            'scores':summary,'earlier_trial_doses':dict(Counter(r['actual_earlier_trials'] for r in scored)),
            'wall_seconds':time.time()-started,'completed_at':time.time(),'disposition':'DESCRIPTIVE',
            'scope':'local development prediction on two scripts; no paper-number reproduction, realized imagery, values or population-wide maker claim',
            'proper_score':'mean Bernoulli Brier over unique normalized script word types; positive difference means smaller prediction error',
            'dependency_limit':'two-way person/script bootstrap with only two held scripts; intervals are descriptive and do not establish broad stimulus generalization'}
    freeze(output/'SCORES.json',scored);freeze(output/'COMPLETE.json',result)
    freeze(ROOT/'intake/BROLL_BASELINE.json',result)
    return result


if __name__=='__main__':
    print(run())
