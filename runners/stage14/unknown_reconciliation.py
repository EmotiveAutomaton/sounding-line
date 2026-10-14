"""Keep an interrupted attempt unknown, with immutable identity-bound evidence.

DESIGN CHECK: LESSONS 3-5 reread 2026-10-11. NULL: changed evidence, live or
uninspectable identity refuses reconciliation. ALTERNATIVE: proved absence keeps
the attempt unknown without rewriting its timestamp or permitting a retry.
Scientific completion and failure remain separate producer-owned states.
"""
from datetime import datetime
from pathlib import Path
from .common import REPO, read, freeze, filehash, now
from .terminal_reconciliation import _identity

REASON = 'dispatched worker absent without complete/failed terminal; no restart'


def unknown_binding(out, card):
    out = Path(out)
    dispatch = read(out / 'DISPATCH.json')
    value = read(out / 'UNKNOWN.json')
    card_hash = filehash(card)
    _identity(dispatch['native'])
    if (any((out / name).exists() for name in ('COMPLETE.json', 'FAILED.json', 'TIMEOUT.json'))
            or value.get('status') != 'unknown' or value.get('reason') != REASON
            or dispatch.get('card_sha256') != card_hash
            or datetime.fromisoformat(value['at']) <= datetime.fromisoformat(dispatch['at'])):
        raise ValueError('unknown-attempt terminal/card binding mismatch')
    return dict(dispatch_sha256=filehash(out / 'DISPATCH.json'),
                unknown_sha256=filehash(out / 'UNKNOWN.json'),
                card_sha256=card_hash, native=dispatch['native'])


def check_unknown_binding(out, card, expected):
    if unknown_binding(out, card) != expected:
        raise ValueError('reconciled unknown attempt changed')


def record_unknown(out, card):
    """Caller must first establish native exit and allow terminal-write grace."""
    out = Path(out)
    if not (out / 'UNKNOWN.json').exists():
        freeze(out / 'UNKNOWN.json', dict(at=now(), status='unknown', reason=REASON))
    return unknown_binding(out, card)


def load_unknown(plan, raw):
    ref = plan.get('unknown_attempt_reconciliation')
    if ref is None:
        return {}
    path = REPO / ref['path']
    if filehash(path) != ref['sha256']:
        raise ValueError('unknown reconciliation changed')
    receipt = read(path)
    if receipt.get('schema') != 'stage14-unknown-exit-v1':
        raise ValueError('unknown reconciliation schema')
    result = {}
    for job, item in receipt['attempts'].items():
        if job not in plan['cards']:
            raise ValueError('unknown attempt outside plan')
        out = Path(raw) / 'jobs' / job
        binding = item['binding']
        check_unknown_binding(out, Path(raw) / 'cards' / (job + '.json'), binding)
        expected = _identity(binding['native'])
        path = REPO / item['observation_path']
        if filehash(path) != item['observation_sha256']:
            raise ValueError('unknown exit observation changed')
        proof = read(path)
        if (proof.get('query_succeeded') is not True or proof.get('pid') != expected[0]
                or proof.get('method') != 'native_identity' or 'observed' not in proof
                or datetime.fromisoformat(proof['inspected_at']) <= datetime.fromisoformat(read(out / 'UNKNOWN.json')['at'])):
            raise ValueError('unproved unknown exit')
        if proof['observed'] is not None:
            observed = _identity(proof['observed'])
            if observed[0] != expected[0] or observed[1] <= expected[1]:
                raise ValueError('unknown exit not established')
        result[job] = binding
    return result
