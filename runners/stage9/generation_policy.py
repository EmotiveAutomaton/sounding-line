"""Frozen generation overrides beside the complete inherited model configuration.

DESIGN CHECK: C02/X07. Historical sampling left top-k and EOS inherited. A named
legacy mode must preserve those defaults; a greedy run is a different package.
NULL: an unregistered override fails. ALTERNATIVE: inherited defaults remain intact.
"""
GREEDY = {'do_sample': False}
UNRESTRICTED = {'do_sample': True, 'temperature': 1.0, 'top_p': 1.0, 'top_k': 0}
LEGACY = {'mode': 'stage8_sample_log'}


def overrides(requested):
    if requested == LEGACY:
        return {'do_sample': True, 'temperature': 1.0, 'top_p': 1.0}
    if requested in (GREEDY, UNRESTRICTED):
        return dict(requested)
    raise ValueError('unregistered generation semantics')


def policy(requested, inherited, tokenizer_eos, tokenizer_pad):
    args = overrides(requested)
    args['pad_token_id'] = tokenizer_pad
    if requested != LEGACY:
        args['eos_token_id'] = tokenizer_eos
    effective = {**inherited, **args}
    return {'requested': requested, 'inherited': inherited, 'overrides': args,
            'effective': effective,
            'scope': 'sampling settings; precision and model identity remain separate'}
