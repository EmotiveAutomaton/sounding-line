"""Independent CH7 formula oracle, constructed data only.

DESIGN CHECK: LESSONS 3-5. This file does not import any CH7 production
function. Explicit columns, raw sums and dense dummy regressions provide
independent answers under null, signed alternatives and singular designs.
It is a qualification reference, never an alternative scientific estimator.
"""
import math
import numpy as np

MONTHS = ('2017-04', '2017-05', '2017-06')


def probabilities(gap, fraction):
    expectation = 1 / (1 + 10 ** (-float(gap) / 400))
    draw = fraction * 2 * min(expectation, 1-expectation)
    return expectation, [1-expectation-draw/2, draw, expectation-draw/2]


def row(play, post, reference, best, number, result, losing, gap, hour,
        control, gain, pace, eligible, provisional):
    distance = (post-reference)/20
    return [float(play), min(distance, 0), max(distance, 0), number,
            float(result == 1), float(result == 0), losing, gap/400,
            math.sin(2*math.pi*hour/24), math.cos(2*math.pi*hour/24), control,
            (post-max(best, post))/20, float(post > best),
            float(best-15 <= post <= best), gain, pace, float(eligible), float(provisional)]


def simulate(trace, parameters, seed):
    """A second scalar recurrence, including session and month reset.

    Trace columns are fixed independently here: control, month, time, rating,
    opponent, change, result, retained, censored, pace, provisional start.
    """
    rng = np.random.default_rng(seed)
    answer = []
    for key in sorted(parameters):
        control = int(key)
        history = [r for r in trace if r[0] == control]
        fit = parameters[key]
        rating = history[0][3]
        best = rating
        previous = False
        last_month = None
        for ordinal, game in enumerate(history, 1):
            if not previous or game[1] != last_month:
                reference, number, losing = rating, 0, 0
            number += 1
            expectation, p = probabilities(rating-game[4], fit['draw']['fraction'])
            outcome = int(rng.choice([-1, 0, 1], p=p))
            change = fit['update_scale'] * ((outcome+1)/2-expectation)
            post = rating+change
            losing = losing+1 if outcome == -1 else 0
            hour = game[2]/3600 % 24
            playfit = fit['play']
            if 'constant' in playfit:
                chance = playfit['constant']
            else:
                z = [1, number, float(outcome == 1), float(outcome == 0),
                     math.sin(2*math.pi*hour/24), math.cos(2*math.pi*hour/24)]
                eta = sum(z[k]/scale*beta for k, scale, beta in
                          zip(playfit['kept'], playfit['scale'], playfit['beta']))
                chance = 1/(1+math.exp(-eta))
            play = rng.random() < chance
            if game[7] and not game[8]:
                answer.append(row(play, post, reference, best, number, outcome,
                    losing, rating-game[4], hour, control, change, float('nan'),
                    ordinal > 30, game[10]))
            rating, best, previous, last_month = post, max(best, post), play, game[1]
    return np.asarray(answer, float).reshape(-1, 18)


def histories(players=48, games=240, left=0., right=0., seed=418):
    """Independent primitive generation of the previously frozen three worlds.

    Rounded positive-K updates and clipped Bernoulli probabilities preserve the
    old construction, including its clipping diagnostic and fixed truth slopes.
    These worlds do not establish empirical power or exact Glicko fidelity.
    """
    rng = np.random.default_rng(seed)
    world = {}
    clipped = 0
    for player in range(players):
        rating = 1500+int(rng.normal(0, 100))
        start = 1500000000.+player*17
        play = False
        records = []
        for ordinal in range(games):
            month = MONTHS[min(2, 3*ordinal//games)]
            if not play or not records or records[-1]['month'] != month:
                number, reference = 0, rating
            number += 1
            opponent = rating+int(rng.normal(0, 110))
            expectation, p = probabilities(rating-opponent, .2)
            result = int(rng.choice([-1, 0, 1], p=p))
            change = int(round(18*((result+1)/2-expectation)))
            post = rating+change
            distance = (post-reference)/20
            chance = .65-.015*(number-1)+.02*result + left*min(distance,0)+right*max(distance,0)
            clipped += not .02 <= chance <= .98
            play = rng.random() < max(.02, min(.98, chance))
            pace = .06+.002*max(-distance, 0)
            records.append(dict(game=f'constructed-game-{player}-{ordinal}', month=month,
                start=start, end=None, rating=rating, opponent_rating=opponent,
                rating_change=change, result=result, initial=300, increment=2,
                time_control='blitz', first_clock=300, source_ordinal=ordinal,
                rows=[dict(ply=5, clock_before=300., think_time=300*pace),
                      dict(ply=7, clock_before=280., think_time=280*pace)]))
            rating = post
            start += 600 if play else 3600
        world[f'constructed-ch7-{player:05}'] = records
    return world, dict(players=players, games_per_player=games, planted_below_slope=left,
        planted_above_slope=right, probability_clipping_fraction=clipped/(players*games),
        constructed=True, expected_values_call_production=False)


def arrays(blocks, kind):
    selected = []
    for b in blocks:
        if kind == 'pace': b = b[np.isfinite(b[:,15])]
        elif kind == 'window_slope': b = b[b[:,16] == 1]
        elif kind == 'new_best': b = b[(b[:,16] == 1) & (b[:,4] == 1) & ((b[:,12]+b[:,13]) > 0)]
        elif kind == 'provisional_start': b = b[b[:,17] == 1]
        selected.append(b)
    gains = None
    if kind == 'new_best':
        possible = sorted({r[14] for b in selected for r in b})
        gains = [g for g in possible if {r[12] for b in selected for r in b if r[14] == g} == {0.,1.}]
        selected = [b[np.isin(b[:,14], gains)] for b in selected]
    answer = []
    for b in selected:
        nuisance = b[:,[3,4,5,6,7,8,9,10]]
        if kind == 'new_best':
            x = np.column_stack([b[:,12], nuisance, *[(b[:,14] == g).astype(float) for g in gains[1:]]])
            y = 1-b[:,0]
        elif kind == 'window_slope':
            x, y = np.column_stack([b[:,11], nuisance]), b[:,0]
        else:
            x = np.column_stack([b[:,[1,2]], nuisance])
            y = b[:,15] if kind == 'pace' else b[:,0]
        answer.append((x, y))
    return answer, gains


def raw_statistics(blocks, kind, kept):
    pairs, gains = arrays(blocks, kind)
    xx, xy = [], []
    for x, y in pairs:
        x = x[:,kept]
        if not len(y):
            xx.append(np.zeros((len(kept),len(kept))))
            xy.append(np.zeros(len(kept)))
            continue
        sx = x.sum(axis=0)
        xx.append(x.T@x-np.outer(sx,sx)/len(y))
        xy.append(x.T@y-sx*y.sum()/len(y))
    return np.asarray(xx), np.asarray(xy), gains


def dense_fit(blocks, kind, kept, copies=None):
    pairs, _ = arrays(blocks, kind)
    if copies is None: copies = np.ones(len(pairs), int)
    xs, ys, labels = [], [], []
    unit = 0
    for count, (x,y) in zip(copies, pairs):
        for _ in range(int(count)):
            if len(y):
                xs.append(x[:,kept]); ys.append(y); labels.extend([unit]*len(y)); unit += 1
    x, y = np.vstack(xs), np.concatenate(ys)
    dummy = np.eye(unit)[labels]
    answer, _, rank, _ = np.linalg.lstsq(np.column_stack([x,dummy]),y,rcond=None)
    if rank != x.shape[1]+unit: raise ValueError('Independent dummy design is singular')
    return answer[:x.shape[1]]


def weighted_fit(xx, xy, counts):
    # Direct raw cross-product solve; no production scaling or solver import.
    matrix = sum(int(n)*block for n,block in zip(counts,xx))
    target = sum(int(n)*block for n,block in zip(counts,xy))
    if np.linalg.matrix_rank(matrix) != len(target):
        raise ValueError('Independent weighted design is singular')
    return np.linalg.solve(matrix,target)


def interval(values):
    ordered = sorted(float(v) for v in values)
    def quantile(p):
        where = (len(ordered)-1)*p
        lo, hi = math.floor(where), math.ceil(where)
        return ordered[lo]+(where-lo)*(ordered[hi]-ordered[lo])
    mean = sum(ordered)/len(ordered)
    se = math.sqrt(sum((v-mean)**2 for v in ordered)/(len(ordered)-1))
    return [quantile(.025),quantile(.975)], se
