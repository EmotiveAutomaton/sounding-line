"""Offline complete-tranche scoring and transparent event audit.

DESIGN CHECK: null/effect sign checked with known vectors. Invalids cannot
improve all-attempt scores by disappearing. A partial cell cannot masquerade as
a complete contrast. Shared writer/prompt/session links determine components;
there is no event-level population confidence interval.
"""
from collections import defaultdict
from .core import *


def audit_event(proposal, row):
    """Audit only exact observable vocabulary; quote matching alone is not proof."""
    op=proposal['operation'].strip().lower();actor=proposal['actor'].strip().lower(); truth=row['truth']
    known={'propose':True,'select':truth in ('accept','edit'),'edit':truth=='edit',
           'dismiss':truth=='dismiss','leave':truth=='ignore'}
    # Edited outcome means editing verified insertion, not arbitrary document editing.
    expected_actor='model' if op=='propose' else 'human'
    supported=known.get(op)
    if supported is not None and actor!=expected_actor: supported=None
    return dict(**proposal, quote_match=bool(proposal['quote']) and any(proposal['quote'] in x for x in
                    (row['event']['end_document'],row['event']['document'],*[s['trimmed'] for s in row['event']['options']])),
                record_relation='unresolved' if supported is None else 'supported' if supported else 'contradicted',
                scope='normalized operation only; narrative intent/dependencies remain hypotheses')


def average(rows, key):
    by=defaultdict(list)
    for r in rows: by[r['writer']].append(r[key])
    if not rows: return None
    if any(v=='infinite' for vals in by.values() for v in vals): return 'infinite'
    return sum(sum(v)/len(v) for v in by.values())/len(by)


def components(rows):
    parent=list(range(len(rows)))
    def find(i):
        while parent[i]!=i: i=parent[i]
        return i
    seen={}
    for i,r in enumerate(rows):
        # Writer keys already include inherited duplicate-text connected components.
        for factor in ('writer','prompt','session'):
            k=(factor,r[factor])
            if k in seen: parent[find(i)]=find(seen[k])
            seen[k]=i
    return len({find(i) for i in range(len(rows))})


def attempt(root, lane, row, view, arm):
    return root/'calls'/lane/digest([row['key'],view,arm])[:24]


def reparse(directory, public, arm):
    request=read(directory/'REQUEST.json')
    if request['request']!=request_for(public,arm): raise ValueError('saved request differs from frozen evidence/settings')
    if (directory/'RAW.json').exists():
        raw=read(directory/'RAW.json')
        try: forecast=parse(raw,arm);error=None
        except (ValueError,TypeError,KeyError) as exc: forecast=None;error=str(exc)
    else:
        raw={};forecast=None;error='transport uncertain; no raw response'
    saved=read(directory/'ATTEMPT.json')
    if saved['raw_digest']!=(digest(raw) if raw else None) or saved['forecast']!=forecast or saved['error']!=error:
        raise ValueError('semantic reparse differs from saved forecast')
    return saved


def analyze(root=PRIVATE, write=True):
    cohort=read(root/'COHORT.json'); baseline=read(root/'BASELINES.json')
    prepared=read(root/'PREPARED.json')
    if prepared['cohort_digest']!=digest(cohort) or prepared['baseline_digest']!=digest(baseline): raise ValueError('frozen input mutation')
    cells=[];dispositions=[];paired=[]; rows=cohort['evaluation']
    for tranche in ('initial','extension'):
        own=[r for r in rows if r['tranche']==tranche]
        if not own: continue
        expected=[attempt(root,'evaluation',r,v,a)/'ATTEMPT.json' for r in own for v in VIEWS for a in ARMS]
        count=sum(p.exists() for p in expected)
        dispositions.append(dict(tranche=tranche,episodes=len(own),expected_calls=len(expected),retained_attempts=count,
                                 status='COMPLETE' if count==len(expected) else 'PARTIAL' if count else 'UNRUN'))
        if count!=len(expected): continue
        scores_by={}
        for view in VIEWS:
            for arm in ('prior','features',*ARMS):
                measured=[];cost=dict(wall_seconds=0.,input_tokens=0,output_tokens=0,server_seconds=0.)
                for row in own:
                    if arm in ARMS:
                        saved=reparse(attempt(root,'evaluation',row,view,arm),row['views'][view],arm)
                        p=saved['forecast']['probabilities'] if saved['forecast'] else None
                        for k in cost: cost[k]+=saved['cost'].get(k,0) or 0
                    else: p=predict(row['views'][view],view,baseline,arm)
                    measured.append(dict(key=row['key'],writer=row['writer'],prompt=row['prompt'],**scores(p,row['truth'])))
                scores_by[view,arm]=measured
                valid=[r for r in measured if r['valid']]
                cells.append(dict(tranche=tranche,view=view,arm=arm,episodes=len(own),writers=len({r['writer'] for r in own}),
                    components=components(own),**{k:average(measured,k) for k in ('brier','accuracy','log_loss')},
                    invalid_rate=1-average(measured,'valid'),invalid_count=len(measured)-len(valid),
                    valid_only={k:average(valid,k) for k in ('brier','accuracy','log_loss')},cost=cost))
            d=scores_by[view,'direct'];a=scores_by[view,'account']
            diff=[dict(writer=x['writer'],prompt=x['prompt'],effect=y['brier']-x['brier']) for x,y in zip(d,a)]
            spread={}
            for factor in ('writer','prompt'):
                grouped=defaultdict(list)
                for r in diff: grouped[r[factor]].append(r['effect'])
                # Safe aggregates only: no private group identifiers.
                spread[factor]=sorted(sum(v)/len(v) for v in grouped.values())
            paired.append(dict(tranche=tranche,view=view,account_minus_direct_brier=average(diff,'effect'),
                               observed_group_effects=spread,uncertainty='descriptive; no population interval'))
    attempts=list((root/'calls').rglob('ATTEMPT.json'))
    costs=[read(p)['cost'] for p in attempts]
    summary=dict(schema='stage11-comparison-1',cells=cells,paired=paired,dispositions=dispositions,
                 attempts=len(attempts),cost={k:sum(c.get(k,0) or 0 for c in costs) for k in
                    ('wall_seconds','input_tokens','output_tokens','server_seconds')},
                 inference='handling score does not validate richer event networks; exposed descriptive cohort',
                 replay='python -B -m runners.stage11.run report --verify')
    if write: freeze(root/'COMPARISONS.json',summary)
    return summary
