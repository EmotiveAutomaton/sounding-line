"""Within-player short-minus-long after-loss contrast, physical wait minutes.

DESIGN CHECK: LESSONS 3-5. Null identical outcomes give exactly zero, not a
negative rounding residue. Planted negative fading is negative. Each player's
four required cells has ≥5 rows; never pool people to manufacture that support.
Opposite signed intervals are the curator-approved peer-priority trigger.
"""
from collections import defaultdict, Counter
import math
import numpy as np
from .week6_ch_riders_fields_v1 import finite, wait_bin


def player_summary(rows, wait='wait', outcome='outcome', loss_kind='all', reference=False):
    eligible=[r for r in rows if r['analysis'] and r['previous_score'] in (0.,1.) and
              finite(r.get(outcome)) and wait_bin(r.get(wait)) is not None and
              (outcome!='berserk' or r['berserk_admitted'])]
    # Outcome centering is within the same player and metric. It cancels exactly
    # from each loss-win contrast; compute differences directly to avoid residue.
    baseline=math.fsum(r[outcome] for r in eligible)/len(eligible) if eligible else None
    cells=defaultdict(list)
    for row in eligible:
        if loss_kind!='all':
            e=row.get('previous_E')
            if not finite(e) or (loss_kind=='favourite' and e<.65) or (loss_kind=='underdog' and e>.35): continue
        cells[(wait_bin(row[wait]),int(row['previous_score']==0))].append(row[outcome])
    def mean(values):
        if not values:return None
        return sum(values)/len(values) if reference else math.fsum(values)/len(values)
    def contrast(bins):
        losses=[v for b in bins for v in cells[(b,1)]]
        wins=[v for b in bins for v in cells[(b,0)]]
        return (mean(losses)-mean(wins) if len(losses)>=5 and len(wins)>=5 else None,
                [len(losses),len(wins)])
    short,short_n=contrast([0]);long,long_n=contrast([4,5])
    curve=[contrast([b]) for b in range(6)]
    return dict(contrast=short-long if short is not None and long is not None else None,
        short_shift=short,long_shift=long,counts=dict(short=short_n,long=long_n),
        curve=[v[0] for v in curve],curve_counts=[v[1] for v in curve],
        outcome_baseline=baseline,eligible_pairs=len(eligible))


def prepare(pairs, reference=False):
    groups=defaultdict(list)
    for row in pairs:
        if row['analysis']:groups[row['player']].append(row)
    return prepare_grouped(groups,reference)


def prepare_grouped(groups, reference=False, check=lambda:None):
    names=sorted(groups); metrics=defaultdict(list); census=Counter();donors=Counter()
    for player in names:
        check();rows=groups[player]
        census['analysis_pairs']+=len(rows)
        census['pairs_without_peer']+=sum(r['pool_wait'] is None for r in rows)
        donors.update(r['pool_donors'] for r in rows)
        for metric,outcome,kind in [('primary','outcome','all'),('favourite','outcome','favourite'),
                                  ('underdog','outcome','underdog'),('departure','departure','all'),
                                  ('berserk','berserk','all')]:
            for wait in ('wait','pool_wait'):
                metrics[metric+'_'+wait].append(player_summary(rows,wait,outcome,kind,reference))
    # Keep every registered metric even for a wholly unsupported population.
    for metric,outcome,kind in [('primary','outcome','all'),('favourite','outcome','favourite'),
                              ('underdog','outcome','underdog'),('departure','departure','all'),
                              ('berserk','berserk','all')]:
        for wait in ('wait','pool_wait'):metrics.setdefault(metric+'_'+wait,[])
    return dict(names=names,metrics=dict(metrics),census=dict(census,
        peer_scope='other players in original salted 2% sample',
        donor_counts={str(k):v for k,v in sorted(donors.items())}))


def draw(prepared, weights, reference=False):
    def average(values):
        terms=[(w,v) for w,v in zip(weights,values) if w>0 and v is not None]
        if not terms:return None
        numerator=sum(w*v for w,v in terms) if reference else math.fsum(w*v for w,v in terms)
        return numerator/sum(w for w,v in terms)
    return {name:dict(point=average([r['contrast'] for r in rows]),
            curve=[average([r['curve'][i] for r in rows]) for i in range(6)])
            for name,rows in prepared['metrics'].items()}


def signed_interval(interval):
    if interval is None:return 0
    return 1 if interval[0]>0 else -1 if interval[1]<0 else 0


def priority(own,peer):
    disagreement=signed_interval(own)*signed_interval(peer)==-1
    return dict(selected='pool_wait' if disagreement else 'wait',
        opposite_excluding_zero=disagreement,
        peer_unsupported=peer is None,
        interpretation='wait was chosen; sampled-peer comparison takes priority' if disagreement else
            'own-WAIT primary retained; self-selection remains a limit')


def result(prepared, draws):
    point=draw(prepared,np.ones(len(prepared['names'])))
    summaries={}
    for name,rows in prepared['metrics'].items():
        people=sum(r['contrast'] is not None for r in rows)
        samples=[d[name]['point'] for d in draws]
        valid=[v for v in samples if v is not None and math.isfinite(v)]
        supported=people>=20
        ci=np.quantile(valid,[.025,.975]).tolist() if supported and len(valid)==len(samples) and len(samples)>0 else None
        curve=[]
        for i in range(6):
            vals=[d[name]['curve'][i] for d in draws]
            n=sum(r['curve'][i] is not None for r in rows)
            curve.append(dict(point=point[name]['curve'][i],players=n,
                interval=np.quantile(vals,[.025,.975]).tolist() if n>=20 and vals and all(v is not None for v in vals) else None))
        p=point[name]['point']
        classification=('below floor, descriptive' if not supported else 'uncertainty unavailable' if ci is None else
            'negative fade beyond bar' if p<=-.010 and ci[1]<0 else
            'opposite direction' if ci[0]>0 else 'inside practical band' if ci[0]>=-.010 and ci[1]<=.010 else 'inconclusive')
        summaries[name]=dict(point=p,interval=ci,players=people,required_players=20,
            valid_draws=len(valid),invalid_draws=len(samples)-len(valid),
            classification=classification if name.startswith('primary_') else 'descriptive secondary',curve=curve)
    decision=priority(summaries['primary_wait']['interval'],summaries['primary_pool_wait']['interval'])
    return dict(card='CH13',bar=-.010,metrics=summaries,priority=decision,census=prepared['census'],
        draws=len(draws),centering='within-player outcome baseline; physical waits unchanged',
        limitations=['A public rating is not standing in a room; next score is not feeling.',
            'Clock-estimated ends omit two first-move latencies.',
            'Sampled-peer waits are not the complete tournament pool and may themselves be chosen.',
            'Bootstrap treats measured peer waits and the fitted forecast as fixed; it does not model arena dependence.'])
