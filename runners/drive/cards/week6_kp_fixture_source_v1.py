"""Literal constructed source for native plumbing; no human file access.

DESIGN CHECK: LESSONS 3-5. Balanced Walsh columns make every held-out fold's
base/donor MSE5/16 and own MSE1/16, hence KP2 contrast80 exactly in arithmetic.
Repeated writer/session patterns are intentional known answers, not sampled data.
"""
from .timing_d33_supported_stats import NAMES


def walsh(i,j):return 1. if (i&j).bit_count()%2==0 else -1.


def corpus():
    names=tuple(n for n in NAMES if n!='intercept');rows=[]
    for writer in range(20):
        for session in range(2):
            for index in range(16):
                values={name:walsh(index,k+1) for k,name in enumerate(names)}
                values['sentence_start']=(1+values['sentence_start'])/2
                values['after_punctuation']=(1+values['after_punctuation'])/2
                deletion=int(walsh(index,11)>0)
                rows.append(dict(values,writer=f'constructed-w{writer:02d}',
                    session=f'constructed-w{writer:02d}-s{session}',index=index,
                    log_pause=.5*walsh(index,1)+.25*walsh(index,10)+writer/8.,
                    deletion=deletion,deletion_earlier_typed=deletion,
                    deletion_word_or_following=deletion,deletion_prompt_or_api=0,
                    deletion_mixed_typed_provenance=0,
                    continuation_surprise=2.+.02*walsh(index,10),
                    log_earlier_count=1.+.1*walsh(index,12),
                    log1p_hours_since_last_use=1.+.1*walsh(index,13),
                    kp1_exclusions=[],continuation_exclusions=[],kp3_exclusions=[]))
    return dict(rows=rows,frozen_fit=dict(coefficients={'own_surprise':.5,'intercept':0.},
                variance_ratio=0.),coverage=dict(constructed_only=True,writers=20,sessions=40,words=640),
                dispositions={},source_completion_sha256='constructed-literal-walsh-v1')
