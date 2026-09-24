"""Deterministic CPU-only repair for the frozen revision interaction.

DESIGN CHECK: LESSONS 3-5. NULL: zero paired differences remain equivalent.
ALTERNATIVE: a constant signed interaction retains its direction and margin.
Missing/duplicate pairs fail; changing row order or Python hash seed must not
change any interval. No new observations, fits, thresholds or model calls.
The original consumer and its immutable outputs remain preserved.
"""
from collections import defaultdict
import statistics

from .program import disposition, interval


def canonical_primary(rows, *, alpha=.05):
    """Same paired estimand/bootstrap, with canonical units and cluster order."""
    diagnostic = [r for r in rows if r.get('update') == 'diagnostic']
    by = {}
    units = {r['unit'] for r in rows}
    if not units:
        raise ValueError('empty revision roster')
    for r in diagnostic:
        key = (r['unit'], r['method'], r['frame'], r['mode'])
        if key in by:
            raise ValueError('duplicate diagnostic pair member')
        by[key] = r
    groups = defaultdict(list)
    for unit in sorted(units):
        cluster = None
        for method in ('account', 'direct'):
            differences = {}
            for frame in ('false', 'true'):
                pair = []
                for mode in ('saved', 'fresh'):
                    key = (unit, method, frame, mode)
                    if key not in by:
                        raise ValueError('missing diagnostic pair member')
                    r = by[key]
                    if cluster is None:
                        cluster = r['cluster']
                    if r['cluster'] != cluster:
                        raise ValueError('one history has conflicting cluster identities')
                    pair.append(r['excess_half_brier'])
                differences[frame] = pair[0] - pair[1]
            groups[cluster].append(differences['false'] - differences['true'])
    values = [statistics.mean(groups[k]) for k in sorted(groups)]
    ci = interval(values, alpha=alpha)
    return dict(**ci, margin=.02, disposition=disposition(ci))
