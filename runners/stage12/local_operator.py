"""Varied-operation consumer of the unchanged frozen Ghost finite world.

DESIGN CHECK: LESSONS 2-5, CONTROLS 6-7. NULL: artifact aliases preserve
compatible histories; supplied observations must never reveal unobserved goals.
ALTERNATIVE: witnessed edits have independently checkable passage locations.
Eight distinct endpoints cover four first-operation types by construction,
not by reader outcomes. This is descriptive support in one finite source law.
"""
from collections import defaultdict
from .common import read, freeze, digest, filehash
from .ghost_bridge import load_source
from .local_interpretation import request, score_claims

OPERATIONS = ('edit-claim','repair-evidence','replace-presentation','accept-tool')
TIERS = ('E0','E1','E2-full')


def select_paths(model, records):
    pools = {op:[] for op in OPERATIONS}
    for record in records:
        event = record['steps'][0]
        if event['operation'] in pools and event['before'] != event['after']:
            pools[event['operation']].append(record)
    for pool in pools.values():
        pool.sort(key=lambda r:digest(['S12-operation-20260923',r]))
    order = list(OPERATIONS)*2
    def choose(i, endpoints, chosen):
        if i == len(order):
            return chosen
        seen = set()
        for row in pools[order[i]]:
            endpoint = tuple(row['final'])
            if endpoint in endpoints or endpoint in seen:
                continue
            seen.add(endpoint)
            result = choose(i+1, endpoints|{endpoint}, chosen+[row])
            if result is not None:
                return result
        return None
    selected = choose(0, set(), [])
    if selected is None:
        raise ValueError('cannot realize balanced edits with distinct endpoints')
    return selected


def compile(out, card, pulse, raw):
    model = load_source(card['generator_source'])
    records = model.enumerate_world(model.law(card['lineage']))
    if len(records) != 13824 or abs(sum(r['probability'] for r in records)-1)>1e-10:
        raise ValueError('native world normalization')
    selected = select_paths(model, records)
    requests, targets, references, controls = [], [], [], []
    for group, actual in enumerate(selected):
        for tier_index, tier in enumerate(TIERS):
            public = model.project(actual, tier); model.validate_public(public)
            exact = model.infer(public, records)
            template = model.infer(public, records, False)
            matches = [r for r in records if model.project(r,tier)==public]
            if not matches or not any(r==actual for r in matches):
                raise ValueError('actual record excluded by public projection')
            source = group*len(TIERS)+tier_index
            supplied_goal = actual['steps'][0]['goal']
            baseline = {'analysis':'source projection','probabilities':[], 'unknown':tier!='E2-full',
                        'next_evidence':'An operation record for a missing step; independent goal evidence remains needed.',
                        'claims':[dict(role='process',status='observed',step=e['step'],value=e['operation'],
                            span_ids=['unit-'+str(i) for i,(a,b) in enumerate(zip(e['before'],e['after'])) if a!=b],
                            evidence_refs=['observation:'+str(e['step'])]) for e in public['inputs'].get('observations',[])]}
            metrics = score_claims(baseline, public, exact)
            if tier=='E2-full' and metrics['correctly_located_useful_events'] < 1:
                raise ValueError('known edit failed useful-location ruler')
            controls.append(dict(source=source, group=group, tier=tier, metrics=metrics))
            references.append(dict(source=source,group=group,tier=tier,public=public,exact=exact,template=template,actual=actual))
            for direction in ('reverse-local-goal','reverse-process','forward-given-goal'):
                field = 'goal' if direction=='reverse-local-goal' else 'operation'
                labels = list(model.GOALS if field=='goal' else model.OPERATIONS)
                subset = matches if direction!='forward-given-goal' else [r for r in matches if r['steps'][0]['goal']==supplied_goal]
                if not subset:
                    raise ValueError('empty forward support')
                mass = sum(r['probability'] for r in subset)
                target = [sum(r['probability'] for r in subset if r['steps'][0][field]==v)/mass for v in labels]
                cheap = [sum(r['steps'][0][field]==v for r in subset)/len(subset) for v in labels]
                question = ('Infer the selected local goal at step 0; it is not observed.' if direction=='reverse-local-goal' else
                    'Infer the operation at step 0.' if direction=='reverse-process' else
                    'Given that the selected local goal at step 0 was '+supplied_goal+', predict its operation. This goal is supplied, not recovered.')
                for method in ('direct','coherent-account'):
                    ident = digest(['S12-operator-v1',source,direction,method])
                    requests.append(dict(id=ident,source=source,group=group,public=public,direction=direction,
                        method=method,labels=labels,request=request(public,question,labels,method)))
                    targets.append(dict(id=ident,oracle_family_target=target,uniform_template_target=cheap,
                        reference=exact,target_role='g_t' if field=='goal' else 'process',source_case=str(source)))
            pulse(phase='varied-operation-reference',completed=source+1,total=24)
    freeze(out/'REQUESTS.json',requests);freeze(out/'EVALUATOR_ONLY.json',targets)
    freeze(out/'REFERENCES.json',references);freeze(out/'CHEAP_ROWS.json',controls)
    return dict(status='complete',kind='infrastructure',distinct_paths=8,distinct_public_views=24,requests=144,
        scope='One existing finite Ghost law, balanced recorded edits and distinct endpoints; no new fitting or human evidence',
        controls=dict(public_projection_only=True,all_rivals=True,exact_reference=True,known_located_edits=True,
            distinct_endpoints=len({tuple(r['final']) for r in selected})==8),
        files={n:filehash(out/n) for n in ('REQUESTS.json','EVALUATOR_ONLY.json','REFERENCES.json','CHEAP_ROWS.json')})
