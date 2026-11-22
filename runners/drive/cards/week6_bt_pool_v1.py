"""Select one prespecified contribution per diary, family and form."""
import numpy as np

FORMS = ('PST1', 'PST4', 'PST5')
MOOD_0073 = {
    'unpleasant': ('negative_event/affect_grid_x', -1),
    'pleasant': ('positive_event/affect_grid_x', 1),
}


def contribution(name, value, direction=1):
    mean = value.get('mean')
    ratio = value.get('variance_over_squared_mean')
    oriented = None
    if mean and mean['interval']:
        oriented = dict(estimate=mean['estimate']*direction,
                        interval=sorted(direction*x for x in mean['interval']))
    return dict(slope=name, people=value['people'], direction=direction,
                mean=oriented, ratio=ratio)


def select(rows, candidates, form):
    """Break equal support by frozen candidate order, independently of estimates."""
    eligible = [(name, direction) for name,direction in candidates if name in rows]
    if not eligible:
        return None
    name,direction = max(eligible, key=lambda pair: rows[pair[0]][form]['people'])
    result = contribution(name, rows[name][form], direction)
    result['support_ties'] = [k for k,_ in eligible if rows[k][form]['people']==result['people']]
    return result


def pool(entries):
    available = {k:v for k,v in entries.items() if v and v['ratio'] and
                 v['ratio']['bootstrap_sd'] and np.isfinite(v['ratio']['bootstrap_sd'])
                 and v['ratio']['estimate'] is not None}
    if len(available)<2:
        return dict(entries=entries, contributors=list(available), reading='insufficient independent diaries')
    estimates=np.array([v['ratio']['estimate'] for v in available.values()])
    weights=1/np.square([v['ratio']['bootstrap_sd'] for v in available.values()])
    point=float(np.average(estimates,weights=weights))
    half=1.95996398454/np.sqrt(weights.sum())
    return dict(entries=entries, contributors=list(available), estimate=point,
                interval=[float(point-half),float(point+half)],
                Q=float(weights@np.square(estimates-point)),df=len(weights)-1,
                reading='above zero' if point-half>0 else 'does not clear')

