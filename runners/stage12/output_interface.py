"""Versioned output-room repair, without changing evidence or score validity.

DESIGN CHECK: LESSONS 3-5. NULL: truncated, nonfinite or non-normalized
outputs remain invalid; a constant answer cannot pass the balanced canary.
ALTERNATIVE: a bounded explanation and larger completion allowance permit a
complete response. The original model, input evidence, labels and gate stay
fixed. This is one interface diagnosis, not a capability claim or retry loop.
"""
from copy import deepcopy
import json

VERSION = 'bounded-output-v1'
OUTPUT_TOKENS = 2048


def adapt(request, version=None):
    if version is None:
        return deepcopy(request)
    if version != VERSION:
        raise ValueError('unknown local output interface')
    req = deepcopy(request)
    if req['options']['num_ctx'] != 8192 or req['options']['num_thread'] != 2:
        raise ValueError('unreviewed local request profile')
    schema = req['format']
    if 'analysis' not in schema['properties'] or 'probabilities' not in schema['properties']:
        raise ValueError('unreviewed local response schema')
    schema['properties']['analysis']['maxLength'] = 1200
    req['options']['num_predict'] = OUTPUT_TOKENS
    req['messages'][-1]['content'] += (
        '\nOutput interface bounded-output-v1: keep analysis within 1200 characters; '
        'summarize the decisive evidence and remaining alternatives without replaying '
        'every example. Preserve the requested direct or account method. '
        'Use at most three decimal places for probabilities and check that their '
        'sum is exactly 1 before returning them. Complete every required field. '
        'The final JSON schema is: '+json.dumps(schema, separators=(',', ':')))
    # UTF-8 bytes conservatively bound input tokens; reserve actual output room.
    if sum(len(m['content'].encode()) for m in req['messages'])+OUTPUT_TOKENS > 8192:
        raise ValueError('repaired request cannot fit conservative context allowance')
    return req


def rows_for_card(rows, card):
    rows = deepcopy(rows)
    for row in rows:
        row['request'] = adapt(row['request'], card.get('output_interface'))
    if card.get('effective_requests_digest'):
        from .common import digest
        if digest(rows) != card['effective_requests_digest']:
            raise ValueError('effective request roster differs from frozen card')
    return rows


def profile_for_card(card, admission, default):
    from .common import read
    profile = card.get('profile', default)
    if card.get('output_interface'):
        ready = read(admission/'READER_READY.json')
        if ready.get('output_interface') != card['output_interface'] or ready['profile'] != profile:
            raise ValueError('reader admission belongs to a different interface')
    return profile
