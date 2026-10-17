"""Complete D39's retained secondary; never change the hover primary or route.

DESIGN CHECK: LESSONS 3-5 read October 17. NULL: equal paired latencies yield
zero; ALTERNATIVE: longer model-associated latency yields a positive difference.
Only observed selection/close endpoints enter; absent endpoints remain missing,
never zero. Ambiguous source identity or nonfinite/negative latency refuses.
The original matches and writer weighting are frozen. Secondary only, no gate.
"""
import math
from collections import defaultdict
from .events_d39 import paired_primary


def summarize(failures,matches,bootstrap=2000,seed=20261017):
    lookup=defaultdict(list)
    for row in failures:
        lookup[(row['session'],row['ordinal'],row['kind'])].append(row)
    pairs=[];missing_model=missing_own=missing_either=0
    def latency(session,ordinal,kind):
        values=[]
        for row in lookup[(session,ordinal,kind)]:
            if not row['next_menus']:
                raise ValueError('Matched failure lacks its next menu')
            menu=row['next_menus'][0]
            value=menu['observed_latency_seconds']
            if value is not None and (menu['latency_kind']!='observed_selection_or_close'
                    or not math.isfinite(value) or value<0):
                raise ValueError('Invalid observed latency')
            values.append(value)
        if not values or any(v!=values[0] for v in values):
            raise ValueError('Missing or ambiguous retained match identity')
        return values[0]
    for match in matches:
        model=latency(match['model_session'],match['model_ordinal'],'model')
        own=latency(match['own_session'],match['own_ordinal'],'own')
        missing_model+=model is None;missing_own+=own is None
        if model is None or own is None:
            missing_either+=1;continue
        pairs.append(dict(writer=match['writer'],hover_difference=model-own))
    result=paired_primary(pairs,bootstrap,seed)
    return dict(effect_seconds=result['effect'],ci95_seconds=result['ci95'],writers=result['writers'],
                observed_pairs=len(pairs),original_pairs=len(matches),missing_model=missing_model,
                missing_own=missing_own,missing_either=missing_either,secondary_only=True,
                method='same retained matches; complete observed endpoints; equal-writer means and writer bootstrap',
                primary_route_unchanged=True)
