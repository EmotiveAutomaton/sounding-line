"""Fixed-question scoring, writer balance and coverage, without a prose judge.

DESIGN CHECK: LESSONS 2-5. NULL: equal forecasts have zero contrast; all-unknown
cannot earn useful positive claims; invalids cannot vanish. ALTERNATIVE: a correct
supported positive increases yield and lowers finite proper loss. No episode-level
significance is inferred from dependent writer/session/prompt components.
"""
from collections import defaultdict,Counter
import math
from .common import digest
from .models import FIELDS,ACTIONS,SLOTS
from runners.stage11.report import components


def mean(values):return sum(values)/len(values) if values else None


def finite(p,truth,labels):
    if p is None:return dict(brier=1.,accuracy=0.,log_loss='infinite',choice='invalid',confidence=0.)
    target=labels.index(truth);chosen=max(range(len(p)),key=lambda i:p[i])
    return dict(brier=.5*sum((x-(i==target))**2 for i,x in enumerate(p)),accuracy=float(chosen==target),
        log_loss=-math.log(p[target]) if p[target]>0 else 'infinite',choice=labels[chosen],confidence=p[chosen])


def episode(row,forecast):
    facts=[];preds={f['slot']:f for f in forecast['facts']} if forecast else {}
    for truth in row['target']['facts']:
        slot=truth['slot'];p=preds.get(slot)
        scores={name:finite(p[name] if p else None,truth[name],labels) for name,labels in FIELDS.items()}
        a=set(p['span_ids']) if p else set();b=set(truth['span_ids'])
        exact=bool(p and a==b and p['span_state']==truth['span_state'])
        positive=bool(p and scores['operation']['choice'] not in ('unknown','absent'))
        useful=positive and truth['operation']!='absent' and all(s['accuracy'] for s in scores.values())
        covered=bool(p and scores['operation']['choice']!='unknown' and scores['operation']['confidence']>=.75)
        facts.append(dict(slot=slot,scores=scores,span_exact=float(exact),span_state_accuracy=float(bool(p and p['span_state']==truth['span_state'])),
            span_iou=len(a&b)/len(a|b) if a|b else float(exact),
            covered=covered,useful_positive=bool(useful),useful_positive_with_span=bool(useful and exact),
            positive=positive,contradicted=sum(s['choice'] not in ('unknown','invalid') and not s['accuracy'] for s in scores.values()),
            unresolved=bool(not p or scores['operation']['choice']=='unknown'),
            truth_operation=truth['operation'],tie=digest([row['key'],slot])))
    return dict(key=row['key'],writer=row['writer'],session=row['session'],prompt=row['prompt'],domain=row.get('domain','constructed'),
        facts=facts,invalid=forecast is None,handling=finite(forecast['handling'] if forecast else None,row['target']['handling'],ACTIONS),
        unsupported_attributes=sum(v!='unknown' for v in forecast['attributes'].values()) if forecast else 0)


def weighted(rows,value,group='writer'):
    groups=defaultdict(list)
    for r in rows:groups[r[group]].append(value(r))
    if any(v=='infinite' for xs in groups.values() for v in xs):return 'infinite'
    return mean([mean(xs) for xs in groups.values()])


def summarize(rows):
    if not rows:raise ValueError('empty comparison')
    result=dict(episodes=len(rows),writers=len({r['writer'] for r in rows}),sessions=len({r['session'] for r in rows}),
        prompt_components=components(rows),invalid=sum(r['invalid'] for r in rows),dimensions={})
    for name in FIELDS:
        metrics={}
        for metric in ('brier','accuracy','log_loss'):
            def value(r):
                vals=[f['scores'][name][metric] for f in r['facts']]
                return 'infinite' if 'infinite' in vals else mean(vals)
            metrics[metric]=weighted(rows,value)
        result['dimensions'][name]=metrics
    result['handling']={k:weighted(rows,lambda r:r['handling'][k]) for k in ('brier','accuracy','log_loss')}
    for name in ('span_exact','span_state_accuracy','span_iou','covered','unresolved'):
        result[name]=weighted(rows,lambda r:mean([f[name] for f in r['facts']]))
    for name in ('useful_positive','useful_positive_with_span','contradicted','positive'):
        result[name+'_per_episode']=weighted(rows,lambda r:sum(f[name] for f in r['facts']))
    result['unsupported_attributes_per_episode']=weighted(rows,lambda r:r['unsupported_attributes'])
    result['by_slot']={slot:{name:weighted(rows,lambda r:next(f for f in r['facts'] if f['slot']==slot)['scores'][name]['brier']) for name in FIELDS} for slot in SLOTS}
    # Fixed coverage fractions, stable outcome-independent tie breaking. Curves
    # include unknown/invalid predictions as errors, so abstention cannot win empty.
    ranked=sorted([dict(f,writer=r['writer']) for r in rows for f in r['facts']],
        key=lambda f:(-f['scores']['operation']['confidence'],f['tie']))
    risk=[]
    for fraction in (.1,.25,.5,.75,1.):
        chosen=ranked[:max(1,math.ceil(len(ranked)*fraction))]
        by=defaultdict(list)
        for f in chosen:by[f['writer']].append(1-f['scores']['operation']['accuracy'])
        risk.append(dict(requested_coverage=fraction,actual_coverage=len(chosen)/len(ranked),claims=len(chosen),writers=len(by),
            writer_mean_risk=mean([mean(v) for v in by.values()]),raw_risk=mean([1-f['scores']['operation']['accuracy'] for f in chosen])))
    result['operation_risk_at_fixed_coverage']=risk
    for factor in ('writer','session','prompt','domain'):
        groups=defaultdict(list)
        for r in rows:groups[r[factor]].append(r)
        # Sorted distributions preserve heterogeneity without exporting private IDs.
        result[factor+'_distribution']=sorted([dict(episodes=len(v),
            operation_brier=mean([mean([f['scores']['operation']['brier'] for f in r['facts']]) for r in v]),
            useful_positive_per_episode=mean([sum(f['useful_positive'] for f in r['facts']) for r in v])) for v in groups.values()],
            key=lambda x:(x['operation_brier'],x['episodes']))
    result['target_counts']={s:dict(Counter(f['truth_operation'] for r in rows for f in r['facts'] if f['slot']==s)) for s in SLOTS}
    return result
