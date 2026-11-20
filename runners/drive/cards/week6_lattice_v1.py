"""Frozen Round 29 lattice aggregation; consumes completed aggregate rows only.

DESIGN CHECK: LESSONS 3-5. Repeated rows from one source cannot multiply primary
votes. All 44 registered rows survive, including unsupported and missing rows.
A zero-touching interval is undecided under either sign; a source tie is not a
predicted-side majority. MIDUS waves share one vote. Independent-source fair-coin
symmetry is an assumption, not established by these numerical checks.
"""
from collections import defaultdict
from math import comb, isfinite


def coin_tail(k, n):
    if type(k) is not int or type(n) is not int or not 0 <= k <= n:
        raise ValueError('Integer counts with 0 <= k <= n required')
    return None if n == 0 else sum(comb(n, j) for j in range(k, n + 1)) / 2**n


def validate_register(register):
    if [r['row'] for r in register] != list(range(1, 45)):
        raise ValueError('The complete ordered 44-row prospective register is required')
    for r in register:
        if r['direction'] not in (-1, 1) or not r['source'] or not r['claims']:
            raise ValueError('Source, claim and signed prediction required')
        if r['source'].startswith('midus-') and r['source_group'] != 'midus':
            raise ValueError('MIDUS waves must share their original source group')
    return register


def aggregate(register, completed):
    """The owner-approved source-majority primary; row counts are descriptive.

    A completed row is inferentially eligible only when its consumer explicitly
    supplies ``valid_inference: True``. Missing, invalid and below-floor rows
    remain visible without turning a preserved diagnostic into a valid interval.
    """
    validate_register(register)
    actual = {}
    for r in completed:
        if type(r.get('row')) is not int or r['row'] not in range(1, 45) or r['row'] in actual:
            raise ValueError('Unknown or duplicated lattice row')
        actual[r['row']] = r
    rows = []
    sources = defaultdict(list)
    source_claim = defaultdict(list)
    for prediction in register:
        r = actual.get(prediction['row'])
        out = dict(prediction, result_id=None, verdict='not run', reason='No fully landed result',
                   estimate=None, interval=None, decided=False, on_predicted_side=False)
        if r is not None:
            for key in ('result_id', 'verdict', 'reason', 'estimate', 'interval', 'limit'):
                out[key] = r.get(key)
            if r.get('valid_inference') is True:
                interval = r.get('interval')
                if not interval or len(interval) != 2:
                    raise ValueError('A valid row requires its complete interval')
                lo, hi = interval
                if not all(isinstance(x, (int, float)) and not isinstance(x, bool)
                           and isfinite(x) for x in (lo, hi, r.get('estimate'))):
                    raise ValueError('Finite aggregate estimate and limits required')
                if lo > hi or not r.get('result_id') or not r.get('limit'):
                    raise ValueError('Ordered interval, result identity and limit required')
                out['decided'] = lo > 0 or hi < 0
                out['on_predicted_side'] = (lo > 0 if prediction['direction'] == 1 else hi < 0)
        rows.append(out)
        if out['decided']:
            sources[prediction['source_group']].append(out['on_predicted_side'])
            for claim in prediction['claims']:
                source_claim[(prediction['source_group'], claim)].append(out['on_predicted_side'])
    votes = [dict(source=s, decided=len(v), predicted=sum(v), share=sum(v)/len(v),
                  majority=sum(v)*2 > len(v), tie=sum(v)*2 == len(v)) for s, v in sorted(sources.items())]
    n, k = len(votes), sum(v['majority'] for v in votes)
    decided = sum(r['decided'] for r in rows)
    predicted = sum(r['on_predicted_side'] for r in rows)
    p = coin_tail(k, n)
    final_dispositions = len(actual) == 44 and all(
        r.get('valid_inference') is True or bool(r.get('reason')) for r in actual.values())
    grouped = [dict(source=s, claim=c, decided=len(v), predicted=sum(v),
                    majority=sum(v)*2 > len(v), tie=sum(v)*2 == len(v))
               for (s, c), v in sorted(source_claim.items())]
    return dict(
        rows=rows,
        primary=dict(method='one source, one majority vote', sources=votes, n=n, k=k,
                     p=p, passes=(p is not None and p <= .05) if final_dispositions else None,
                     final_dispositions=final_dispositions,
                     assumptions=['Sources are independent and signs are symmetric under the null.',
                                  'MIDUS waves count once; 0057 and 0056 count separately by owner ruling.',
                                  'A tied source remains in the denominator without a success.']),
        descriptive=dict(decided_rows=decided, predicted_rows=predicted,
                         row_coin_tail=coin_tail(predicted, decided),
                         source_claim_groups=grouped,
                         source_claim_coin_tail=coin_tail(sum(g['majority'] for g in grouped), len(grouped)),
                         inferential_status='descriptive; rows and source-claim groups are dependent'),
    )


def diary_reference(blocks, *, seed=20261119):
    """Optional reference from existing, jointly indexed, whole-person draws.

    No fitting or source reads. Each block contains an effects matrix B x rows,
    observed estimates, fixed signs and provenance asserting common draws. Draws
    are mean-centred by column. A null draw would be positive-decided when its
    translated percentile interval is wholly positive. Entire vectors stay
    together within a source; fixed independent permutations combine sources.
    """
    import numpy as np
    rng = np.random.default_rng(seed)
    counts = None
    observed = 0
    seen = set()
    for block in sorted(blocks, key=lambda b: b['source_group']):
        source = block['source_group']
        if source in seen or not block.get('common_draw_bank_sha256'):
            raise ValueError('One proven joint draw bank per source is required')
        seen.add(source)
        draws = np.asarray(block['draws'], dtype=float)
        signs = np.asarray(block['directions'], dtype=float)
        points = np.asarray(block['estimates'], dtype=float)
        if (draws.ndim != 2 or draws.shape[0] != 2000 or draws.shape[1] == 0 or
                draws.shape[1:] != signs.shape or signs.shape != points.shape or
                not np.isfinite(draws).all() or not np.isfinite(points).all() or
                not np.isin(signs, [-1, 1]).all()):
            raise ValueError('All 2000 valid paired draws are required; no deletion or redraw')
        oriented = draws * signs
        errors = oriented - oriented.mean(axis=0)
        offsets = np.quantile(errors, [.025, .975], axis=0)
        # Counts only predicted-side decisions, exactly as the owner requested.
        null_counts = ((errors + offsets[0]) > 0).sum(axis=1)
        observed += int((np.quantile(oriented, .025, axis=0) > 0).sum())
        shuffled = null_counts[rng.permutation(2000)]
        counts = shuffled if counts is None else counts + shuffled
    if counts is None:
        raise ValueError('No compatible joint diary draws; report the primary alone')
    return dict(method='recentered joint whole-person diary reference', seed=seed,
                sources=sorted(seen), observed_count=observed,
                reference_counts=counts.tolist(),
                p=(1+int((counts >= observed).sum()))/2001,
                new_data_pass=False, new_model=False)
