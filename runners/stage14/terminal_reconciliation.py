"""Bind explicitly reconciled failed attempts without repeatedly querying reused PIDs.

DESIGN CHECK: LESSONS 3-5 read 2026-10-11. NULL: missing, altered, unknown,
same-native or premature evidence refuses retirement. ALTERNATIVE: an exact
failed attempt with inspected exit evidence remains failed without redispatch.
This is operational evidence, never scientific admission or retry authority.
"""
from datetime import datetime
from pathlib import Path
from .common import REPO, read, filehash


def failed_binding(out, card):
    out = Path(out)
    dispatch = read(out / 'DISPATCH.json')
    failure = read(out / 'FAILED.json')
    card_hash = filehash(card)
    if ((out / 'COMPLETE.json').exists() or failure.get('status') != 'failed'
            or dispatch.get('card_sha256') != card_hash
            or failure.get('card_sha256') != card_hash):
        raise ValueError('failed-attempt terminal/card binding mismatch')
    return dict(dispatch_sha256=filehash(out / 'DISPATCH.json'),
                failed_sha256=filehash(out / 'FAILED.json'),
                card_sha256=card_hash, native=dispatch['native'])


def check_failed_binding(out, card, expected):
    if failed_binding(out, card) != expected:
        raise ValueError('reconciled failed attempt changed')


def _identity(value):
    if not isinstance(value, dict):
        raise ValueError('missing native identity')
    if (type(value.get('pid')) is not int or value['pid'] <= 0
            or type(value.get('created_ticks')) is not int or value['created_ticks'] <= 0
            or not isinstance(value.get('executable'), str) or not value['executable']):
        raise ValueError('incomplete native identity')
    return value['pid'], value['created_ticks'], value['executable'].replace('\\', '/').lower()


def load_reconciled(plan, raw):
    """Validate operator-produced, plan-pinned observations for exact failed attempts."""
    reference = plan.get('failed_attempt_reconciliation')
    if reference is None:
        return {}
    path = REPO / reference['path']
    if filehash(path) != reference['sha256']:
        raise ValueError('reconciliation receipt changed')
    receipt = read(path)
    if receipt.get('schema') != 'stage14-failed-exit-v1':
        raise ValueError('unrecognized reconciliation schema')
    result = {}
    for job, item in receipt['attempts'].items():
        if job not in plan['cards']:
            raise ValueError('reconciled attempt outside frozen plan')
        out = Path(raw) / 'jobs' / job
        card = Path(raw) / 'cards' / (job + '.json')
        binding = item['binding']
        check_failed_binding(out, card, binding)
        expected = _identity(binding['native'])
        proof_path = REPO / item['observation_path']
        if filehash(proof_path) != item['observation_sha256']:
            raise ValueError('exit observation changed')
        proof = read(proof_path)
        if (proof.get('query_succeeded') is not True or proof.get('pid') != expected[0]
                or proof.get('method') not in ('native_identity', 'Win32_Process exact PID query')):
            raise ValueError('unknown exit observation')
        inspected = datetime.fromisoformat(proof['inspected_at'])
        failed = datetime.fromisoformat(read(out / 'FAILED.json')['at'])
        if inspected <= failed:
            raise ValueError('observation predates failed terminal')
        if 'observed' not in proof:
            raise ValueError('missing exit observation')
        if proof['observed'] is not None:
            observed = _identity(proof['observed'])
            if observed[0] != expected[0] or observed[1] <= expected[1]:
                raise ValueError('observation does not prove a later process at this PID')
        result[job] = binding
    return result
