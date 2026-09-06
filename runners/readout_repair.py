"""Isolated all-option readout v1; not installed into closed Stage 7/8 capsules.

DESIGN CHECK (2026-09-06)
lessons read: LESSONS sections 3, 4, 5; CONTROLS sections 5, 6.
NULL: equal sequence likelihoods give a uniform distribution at every candidate count.
ALTERNATIVE: a known larger likelihood wins regardless of input order or former group.
gates: missing/nonfinite/mismatched component evidence invalidates the entire readout;
never synthesize a uniform fallback. bands: valid complete common-rule evidence or invalid.
This measurement amendment changes readout semantics, not old scientific thresholds.
"""
from __future__ import annotations

import hashlib
import math

VERSION = 'all-option-sum-logprob-20260906.1'
IDENTITY_FIELDS = ('model', 'revision', 'adapter_sha256', 'scorer_sha256', 'information_sha256')

def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def readout(prefix, options, score, identity):
    """Score every continuation under ONE prefix with summed token log probabilities.

    score(prefix, ordered_options) returns one record per option: option_id, logprob,
    prefix_sha256, continuation_sha256, semantics, identity. The transport must retain
    actual model/scorer identity and fail if any component is absent. Scores are a
    distribution conditional on this offered set, not calibrated outcome probabilities.
    Input labels never become model-facing letter choices; option texts are continuations.
    The caller freezes operative information separately and supplies its hash in identity.
    """
    receipt={'version':VERSION,'input_order':list(options),'scoring_order':sorted(options),
             'prefix_sha256':digest(prefix),'identity':dict(identity),'components':None}
    try:
        if not options or any(not isinstance(k,str) or not k or not isinstance(v,str) or not v for k,v in options.items()):
            raise ValueError('nonempty string option ids and continuations required')
        if any(not isinstance(identity.get(k),str) or not identity[k] for k in IDENTITY_FIELDS):
            raise ValueError('complete explicit model/scorer/information identity required')
        ordered={k:options[k] for k in sorted(options)}
        rows=score(prefix,ordered);receipt['components']=rows
        if not isinstance(rows,list) or len(rows)!=len(options):raise ValueError('missing component scores')
        vals={}
        for r in rows:
            if not isinstance(r,dict):raise ValueError('malformed component')
            k=r.get('option_id')
            if k not in options or k in vals:raise ValueError('unknown or duplicate option')
            if r.get('valid') is not True:raise ValueError('invalid component')
            if r.get('identity')!=identity:raise ValueError('component identity mismatch')
            if r.get('prefix_sha256')!=digest(prefix) or r.get('continuation_sha256')!=digest(options[k]):raise ValueError('component input mismatch')
            if r.get('semantics')!='sum_log_probability':raise ValueError('incompatible score semantics')
            value=r.get('logprob')
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value>0:raise ValueError('invalid sequence log probability')
            vals[k]=float(value)
        maximum=max(vals.values())
        weights={k:math.exp(v-maximum) for k,v in vals.items()}
        total=math.fsum(weights.values());probs={k:weights[k]/total for k in sorted(weights)}
        ties=sorted(k for k,v in vals.items() if v==maximum)
        return dict(receipt,valid=True,reason='complete common-rule evidence',probs=probs,pred=ties[0] if len(ties)==1 else None,ties=ties)
    except (ValueError,TypeError,KeyError,OverflowError) as exc:
        return dict(receipt,valid=False,reason=str(exc),probs=None,pred=None,ties=[])
