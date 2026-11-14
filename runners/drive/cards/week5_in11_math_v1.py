"""Fixed ordinal-duration IN11 crossover; independent weighted-row replay."""
import numpy as np

NEGATIVE = ('anger', 'disgust', 'fear', 'guilt', 'sadness', 'shame')
STYLE = ('familiarity', 'goal_relevance', 'chance_responsblt', 'self_responsblt', 'attention', 'effort')
JUMP = ('suddenness', 'predict_event')
NO_REMEDY = ('chance_control', 'self_control', 'accept_conseq')
RANKS = {'seconds': 1, 'minutes': 2, 'hours': 3, 'days': 4, 'weeks': 5}


def rank(value, emotion=False):
    if value in RANKS:
        return RANKS[value]
    if emotion and value == 'I had none':
        return None
    if value in ('', '--'):
        return None
    raise ValueError('Undocumented ordinal duration category; no elapsed-time conversion')


def z(values, independent=False):
    x = np.asarray(values, float)
    if len(x) < 2 or not np.isfinite(x).all():
        raise ValueError('Insufficient finite scale support')
    mean = sum(float(v) for v in x)/len(x) if independent else float(x.mean())
    sd = (sum((float(v)-mean)**2 for v in x)/(len(x)-1))**.5 if independent else float(x.std(ddof=1))
    if sd <= 1e-12:
        raise ValueError('Constant within-prompt index or outcome')
    return (x-mean)/sd


def prepare(frame, independent=False):
    frame = frame.loc[frame.emotion.isin(NEGATIVE) & frame.model_eligible].sort_values('text_id')
    present = sorted(frame.emotion.unique()); xs = []; ys = []; people = []
    counts = {}
    for prompt in present:
        rows = frame.loc[frame.emotion.eq(prompt)]; counts[prompt] = len(rows)
        jump = z(rows.suddenness.to_numpy()-rows.predict_event.to_numpy(), independent)
        remedy = z(rows.chance_control.to_numpy()-rows.self_control.to_numpy()-rows.accept_conseq.to_numpy(), independent)
        if independent:
            style = np.array([sum(float(row[k]) for k in STYLE)/6 for row in rows.to_dict('records')])
        else:
            style = rows[list(STYLE)].mean(axis=1).to_numpy(float)
        x = np.column_stack([*[np.full(len(rows), float(prompt == name)) for name in present],
            jump, remedy, rows.unpleasantness, rows.event_duration_rank, style])
        y = np.column_stack([z(rows.intensity.to_numpy(), independent), z(rows.emotion_duration_rank.to_numpy(), independent)])
        xs.append(x); ys.append(y); people.extend(rows.prolific_id.astype(str))
    if not xs:
        return None
    x = np.concatenate(xs); y = np.concatenate(ys); people = np.array(people)
    keys, code = np.unique(people, return_inverse=True)
    xx = np.zeros((len(keys), x.shape[1], x.shape[1])); xy = np.zeros((len(keys), x.shape[1], 2))
    np.add.at(xx, code, x[:, :, None]*x[:, None, :]); np.add.at(xy, code, x[:, :, None]*y[:, None, :])
    return {'x': x, 'y': y, 'people': people, 'keys': keys, 'code': code, 'xx': xx, 'xy': xy,
            'prompts': present, 'counts': counts, 'index_column': len(present)}


def evaluate(prepared, weights, independent=False):
    if prepared is None:
        return {'failure': 'no complete ordinal-duration rows'}
    try:
        if independent:
            row_weights = np.sqrt(weights[prepared['code']]); use = row_weights > 0
            x = prepared['x'][use]*row_weights[use, None]
            y = prepared['y'][use]*row_weights[use, None]
            beta, _, rank_, _ = np.linalg.lstsq(x, y, rcond=1e-11)
            if rank_ != x.shape[1]:
                return {'failure': 'rank deficient'}
        else:
            gram = np.einsum('n,nij->ij', weights, prepared['xx']); rhs = np.einsum('n,nij->ij', weights, prepared['xy'])
            if np.linalg.matrix_rank(gram, tol=1e-9) != gram.shape[0]:
                return {'failure': 'rank deficient'}
            beta = np.linalg.solve(gram, rhs)
        j = prepared['index_column']; a, b = beta[j]; c, d = beta[j+1]
        values = [float((a-b)+(d-c)), float(a), float(b), float(c), float(d)]
        if not np.isfinite(values).all():
            return {'failure': 'nonfinite coefficients'}
        return {'value': values}
    except np.linalg.LinAlgError:
        return {'failure': 'numerical linear algebra failure'}


def draw(size, index):
    rng = np.random.default_rng(np.random.SeedSequence([20261113, 11, index]))
    return np.bincount(rng.integers(0, size, size), minlength=size)


def interval_se(values, independent=False):
    a = np.asarray(values, float)
    if not independent:
        return np.quantile(a, [.025, .975], axis=0).T.tolist(), a.std(axis=0, ddof=1).tolist()
    intervals = []; errors = []
    for column in a.T:
        ordered = sorted(float(v) for v in column); answers = []
        for p in (.025, .975):
            at = (len(ordered)-1)*p; lo = int(at); hi = min(lo+1, len(ordered)-1)
            answers.append(ordered[lo]+(at-lo)*(ordered[hi]-ordered[lo]))
        mean = sum(ordered)/len(ordered)
        intervals.append(answers); errors.append((sum((v-mean)**2 for v in ordered)/(len(ordered)-1))**.5)
    return intervals, errors
