"""Hold out the latest eligible repeat play under curator amendment BE."""
import numpy as np
from scipy.special import expit, log_expit

from . import week5_md3 as choice
from . import week5_md_analysis as features

REFERENCES = ("play_start", "last_session_end", "best_observed_earlier_end")
PAIRS = ((2, 0), (2, 1), (1, 0))
TRIALS = 30
DRAWS = 2000
SEED = 20261107


def split(person, counter, history_ok):
    """Use metadata only. Returned indices always point into the original archive."""
    people, count, eligible = map(np.asarray, (person, counter, history_ok))
    if people.ndim != 1 or len(people) == 0 or count.shape != people.shape or eligible.shape != people.shape:
        raise ValueError("Misaligned player, counter and history arrays")
    if not np.isfinite(count).all() or (count <= 0).any() or (count != np.floor(count)).any():
        raise ValueError("Positive integer attempt numbers required")
    if not np.isin(eligible, [False, True]).all():
        raise ValueError("A binary repeat-history eligibility flag is required")
    flow = dict(source_players=0, source_saved_plays=len(people), ambiguous_or_missing_history=0,
                too_few_recorded_repeats=0, insufficient_repeats_with_preceding_attempt=0,
                repeat_plays_missing_preceding_attempt=0, gaps_among_included_histories=0,
                missing_attempts_among_included_histories=0, eligible_players=0, training_plays=0)
    result = []
    order = np.lexsort((count, people))
    boundaries = np.flatnonzero(np.diff(people[order]) != 0) + 1
    for indices in np.split(order, boundaries):
        attempts = count[indices].astype(np.int64)
        flow["source_players"] += 1
        if not eligible[indices].all() or len(np.unique(attempts)) != len(attempts):
            flow["ambiguous_or_missing_history"] += 1
            continue
        observed = set(attempts.tolist())
        usable = [int(i) for i, n in zip(indices, attempts) if n > 1 and n-1 in observed]
        n_repeats = int((attempts > 1).sum())
        flow["repeat_plays_missing_preceding_attempt"] += n_repeats - len(usable)
        if n_repeats < 3:
            flow["too_few_recorded_repeats"] += 1
            continue
        if len(usable) < 3:
            flow["insufficient_repeats_with_preceding_attempt"] += 1
            continue
        test = usable[-1]
        through_test = indices[count[indices] <= count[test]]
        gaps = np.diff(np.r_[0, count[through_test]]) - 1
        flow["gaps_among_included_histories"] += int(np.sum(gaps > 0))
        flow["missing_attempts_among_included_histories"] += int(gaps.sum())
        result.append((through_test.tolist(), usable[:-1], test))
        flow["training_plays"] += len(usable)-1
    flow["eligible_players"] = len(result)
    if sum(flow[k] for k in ("eligible_players", "ambiguous_or_missing_history",
                            "too_few_recorded_repeats","insufficient_repeats_with_preceding_attempt")) != flow["source_players"]:
        raise ValueError("Player flow does not reconcile")
    return result, flow


def reference_rows(groups, plays):
    """Update from each previous completed play only. Never ask for a test play's end."""
    tr_idx, te_idx, tr_refs, te_refs = [], [], [], []
    for history, train, test in groups:
        desired = set(train)
        best, last = None, None
        for i in history:
            if i in desired or i == test:
                if last is None:
                    raise ValueError("Repeat play missing a preceding ending")
                refs = (0., last, best)
                if i == test:
                    te_idx.append(i)
                    te_refs.append(refs)
                    break
                tr_idx.append(i)
                tr_refs.append(refs)
            last = float(np.sum(plays[i, :, 7], dtype=float))
            if not np.isfinite(last):
                raise ValueError("Previous ending is nonfinite")
            best = last if best is None else max(best, last)
    return (np.asarray(tr_idx,dtype=int),np.asarray(te_idx,dtype=int),
            np.asarray(tr_refs,dtype=float).reshape(-1,3),np.asarray(te_refs,dtype=float).reshape(-1,3))


def pair_name(left, right):
    return REFERENCES[left] + "_minus_" + REFERENCES[right]


def reference_counts(refs):
    return {pair_name(a,b): {"equal":int((refs[:,a] == refs[:,b]).sum()),
                             "differ":int((refs[:,a] != refs[:,b]).sum())}
            for a,b in PAIRS}


def intercepts(linear, codes, choices, independent=False):
    """The original fixed-intercept score equation for each informative training player."""
    n = np.bincount(codes)
    successes = np.bincount(codes, weights=choices)
    if np.any((successes == 0) | (successes == n)):
        raise ValueError("A finite player intercept requires both training choices")
    bound = float(np.max(np.abs(linear))) + 45
    if independent:
        from scipy.optimize import brentq
        order = np.argsort(codes, kind="stable")
        parts = np.split(order, np.cumsum(n)[:-1])
        return np.asarray([brentq(lambda a: expit(linear[ix]+a).sum()-successes[k],
                                  -bound, bound, xtol=1e-11) for k,ix in enumerate(parts)])
    low, high = np.full(len(n), -bound), np.full(len(n), bound)
    for _ in range(64):
        mid = (low + high) / 2
        pred = np.bincount(codes, weights=expit(linear + mid[codes]))
        low, high = np.where(pred < successes, mid, low), np.where(pred < successes, high, mid)
    return (low + high) / 2


def fitted_scores(plays, people, indices, refs, gamma, scale, independent=False):
    tr, te = indices
    y = plays[tr,:,6].ravel()
    if not np.isin(y,[0.,1.]).all():
        raise ValueError("Invalid training choices")
    ids, codes = np.unique(np.repeat(people[tr], TRIALS), return_inverse=True)
    n = np.bincount(codes)
    left = np.bincount(codes,weights=y)
    informative = ids[(left > 0) & (left < n)]
    good_tr = np.isin(people[tr],informative)
    good_te = np.isin(people[te],informative)
    tr, te = tr[good_tr], te[good_te]
    y = plays[tr,:,6].ravel()
    ids, codes = np.unique(np.repeat(people[tr], TRIALS), return_inverse=True)
    checks = {"players_lacking_both_training_choices":int((~good_te).sum()),"arms":{}}
    if len(ids)<2:
        return None, good_te, dict(checks,reason="too few informative training players")
    test_codes = np.searchsorted(ids,people[te])
    assert np.array_equal(ids[test_codes],people[te])
    predictions = []
    for j, name in enumerate(REFERENCES):
        xx = (features.dynamic_features(plays[tr],gamma,refs[0][good_tr,j])/scale).reshape(-1,8)
        model = choice.grouped_logit(xx,y,codes)
        checks["arms"][name] = {"status":model["status"],"requested_slopes":8,
                                "players":len(ids),"estimated_free_parameters":None}
        if model["status"] != "ok":
            means = np.column_stack([np.bincount(codes, weights=xx[:,k]) for k in range(8)])/np.bincount(codes)[:,None]
            rank = int(np.linalg.matrix_rank(xx-means[codes]))
            checks["arms"][name]["within_player_design_rank"] = rank
            checks["arms"][name]["identifiable_design_dimension"] = rank+len(ids)
            predictions.append(None)
            continue
        beta = model["beta"]
        alpha = intercepts(xx@beta,codes,y,independent=independent)
        checks["arms"][name]["estimated_free_parameters"] = len(beta)+len(alpha)
        tx = features.dynamic_features(plays[te],gamma,refs[1][good_te,j])/scale
        predictions.append(tx@beta+alpha[test_codes,None])
    outcome = plays[te,:,6]
    if outcome.shape != (len(te),TRIALS) or not np.isin(outcome,[0.,1.]).all():
        raise ValueError("A complete binary 30-trial test play is required for every player")
    scores = []
    for eta in predictions:
        if eta is None:
            scores.append(np.full(len(te),np.nan))
            continue
        trial_ll = np.where(outcome==1,log_expit(eta),log_expit(-eta)) if independent else outcome*eta-np.logaddexp(0,eta)
        scores.append(trial_ll.sum(axis=1))
    return np.column_stack(scores),good_te,checks


def paired_scores(scores,refs):
    if scores.shape != refs.shape or scores.ndim != 2 or scores.shape[1]!=3 or not np.isfinite(refs).all() or np.isinf(scores).any():
        raise ValueError("Three finite held-out scores and references per player required")
    delta=np.column_stack([scores[:,a]-scores[:,b] for a,b in PAIRS])
    differ=np.column_stack([refs[:,a]!=refs[:,b] for a,b in PAIRS])
    return delta,differ


def draw_statistic(delta,differ,weights):
    columns=[]
    for j in range(len(PAIRS)):
        for mask in (differ[:,j],np.ones(len(weights),dtype=bool)):
            w=weights[mask]
            valid = w.sum() and np.isfinite(delta[mask,j]).all()
            columns.append(float(w @ delta[mask,j]/w.sum()) if valid else None)
    return columns


def summarize(scores,refs,bank):
    delta,differ=paired_scores(scores,refs)
    if len(bank)!=DRAWS or any(len(row)!=6 for row in bank):
        raise ValueError("Incomplete shared 2,000-player draw bank")
    point=draw_statistic(delta,differ,np.ones(len(scores)))
    result={}
    for j,(a,b) in enumerate(PAIRS):
        stats=reference_counts(refs)[pair_name(a,b)]
        stats["scored_differ"] = int((differ[:,j] & np.isfinite(delta[:,j])).sum())
        for k,subset in enumerate(("differing","all_plays")):
            col=2*j+k
            vals=[row[col] for row in bank]
            adequate=(subset=="all_plays" or stats["scored_differ"]>=100)
            interval=np.quantile(vals,[.025,.975]).tolist() if adequate and all(v is not None for v in vals) else None
            stats[subset]=dict(log_likelihood_difference_per_play=point[col],interval=interval)
        interval=stats["differing"]["interval"]
        stats["disposition"]=("could not say" if interval is None else
                              "above zero" if interval[0]>0 else "below zero" if interval[1]<0 else "inconclusive")
        result[pair_name(a,b)]=stats
    primary=[result[pair_name(a,b)]["disposition"] for a,b in PAIRS[:2]]
    disposition=("could not say" if "could not say" in primary else
                 "supports" if all(x=="above zero" for x in primary) else
                 "against" if "below zero" in primary else "inconclusive")
    return {"comparisons":result,"primary":disposition}
