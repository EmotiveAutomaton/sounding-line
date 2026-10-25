"""FR1.h1: preserve repeated controls in the arm-label reference.

DESIGN CHECK: LESSONS3-5 and control dependence, 2026-10-25. Matching may reuse
a control. One sign per real writer keeps every reused control and occurrence
together. A writer duplicated100times must not acquire100independent labels.
All primary/fake rows, estimands and original random-bank consumption are kept;
only the arm-label assignment changes. Original comparison code is immutable.
"""
from contextlib import contextmanager
import numpy as np

from . import week3_frames_analysis as original
from . import week3_frames_stats as stats

CONFIG=original.CONFIG
PILOT=original.PILOT
CONSTRUCTED=original.CONSTRUCTED


def contrast(rows,profile_writers,rng,bootstraps,permutations):
    names=sorted({r['writer'] for r in rows})
    if not names:return dict(state='unsupported',rows=0,writers=0)
    ownership={w:i for i,w in enumerate(profile_writers)}
    matrix=np.asarray([r['delta_by_profile'] for r in rows],float)
    if matrix.shape!=(len(rows),len(profile_writers)) or not np.isfinite(matrix).all():raise ValueError('invalid same-row profile matrix')
    ids=np.asarray([names.index(r['writer']) for r in rows]);columns=np.asarray([ownership[r['writer']] for r in rows])
    own=matrix[np.arange(len(rows)),columns]
    average=lambda x:np.asarray([x[ids==i].mean() for i in range(len(names))])
    first=np.asarray([int(np.flatnonzero(ids==i)[0]) for i in range(len(names))])
    writer_own=average(own);observed=float(writer_own.mean());fake_bank=[];arm_bank=[]
    for _ in range(permutations):
        assignment=rng.permutation(len(profile_writers))
        fake_bank.append(average(matrix[np.arange(len(rows)),assignment[columns]]))
        # Consume the original bank size so all full-profile fake assignments
        # and paired bootstrap draws remain exactly the original ones.
        original_sign_bank=rng.choice([-1,1],len(rows))
        arm_bank.append(float((writer_own*original_sign_bank[first]).mean()))
    fake_bank=np.asarray(fake_bank);arms=np.asarray(arm_bank)
    sd=float(arms.std(ddof=1));mean=float(arms.mean())
    return dict(rows=len(rows),writers=len(names),primary=stats.interval(writer_own,rng,bootstraps),
        own_minus_fake=stats.interval(writer_own-fake_bank.mean(0),rng,bootstraps),fake_primary_mean=float(fake_bank.mean()),
        arm_label_reference=dict(mean=mean,sd=sd,ci95=np.quantile(arms,[.025,.975]).tolist(),
            one_sided_p=float((1+np.sum(arms>=observed))/(permutations+1)),biased_reference=bool(abs(mean)>.25*sd if sd else mean!=0),
            assignment='one sign per real writer; every paired occurrence and reused control stays together'),
        full_profile_fake_draws=permutations,arm_label_draws=permutations,variant='FR1.h1 cluster-preserving reference')


@contextmanager
def cluster_reference():
    previous=stats.contrast;stats.contrast=contrast
    try:yield
    finally:stats.contrast=previous


def execute(output,inputs,config):
    with cluster_reference():return original.execute(output,inputs,config)


def verify(output,inputs,config):
    with cluster_reference():return original.verify(output,inputs,config)
