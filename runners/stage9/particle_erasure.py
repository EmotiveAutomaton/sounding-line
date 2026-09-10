"""Bounded count-state filtering for the unchanged erased-mark model.

DESIGN CHECK: M01/M04/X10; LESSONS 3--5. NULL: impossible observations have
zero mass and exact small grids match independent subset summation. ALTERNATIVE:
complete forward transition expansion sums paths, with an explicitly approximate
particle representation only when the next count-state layer exceeds its cap.
The product of layer normalizers estimates the observation likelihood, not a
normalized maker posterior. Systematic resampling has known probabilities; no
unknown language-model proposal density is used. Independent runs gate precision.
"""
from collections import defaultdict
import math
import random

from .grouped_erasure import Kernel


def resample(weights,count,rng):
    """One unbiased systematic-resampling step, coalescing repeated count states."""
    if (type(count) is not int or count<1 or not weights or
        any(not math.isfinite(v) or v<0 for v in weights.values()) or abs(math.fsum(weights.values())-1)>1e-10):
        raise ValueError('normalized nonempty weights and positive particle count required')
    items=sorted(weights.items());selected=defaultdict(int)
    offset=rng.random()/count;j=0;total=items[0][1]
    for i in range(count):
        target=offset+i/count
        while target>=total and j<len(items)-1:
            j+=1;total+=items[j][1]
        selected[items[j][0]]+=1
    return {state:n/count for state,n in selected.items()}


def likelihood(program,work,budget,*,particles=512,seed=0):
    if type(particles) is not int or not 1<=particles<=65536:
        raise ValueError('particle count outside fixed envelope')
    kernel=Kernel(program,work);start=(0,)*len(kernel.maximum)
    weights={start:1.};log_mass=0.;rng=random.Random(seed)
    resampling_steps=0;maximum_layer=1;visited=0;normalizers=[]
    for depth in range(sum(kernel.maximum)):
        following=defaultdict(float)
        for state,weight in weights.items():
            edges=kernel.edges(state,budget);visited+=1
            for j,edge in enumerate(edges):
                if edge<=0:continue
                next_state=list(state);next_state[j]+=1
                following[tuple(next_state)]+=weight*edge
        normalizer=math.fsum(following.values());normalizers.append(normalizer)
        if normalizer<=0:
            return {'log_mass':-math.inf,'exact':resampling_steps==0,'algorithm':'count-state forward filter',
                    'count_states':kernel.states,'particles':particles,'resampling_steps':resampling_steps,
                    'maximum_expanded_layer':maximum_layer,'visited_states':visited,'proposal_density_known':True,
                    'relative_standard_error':None,'effective_samples':None,'normalizers':normalizers}
        log_mass+=math.log(normalizer)
        weights={state:weight/normalizer for state,weight in following.items()}
        maximum_layer=max(maximum_layer,len(weights))
        if len(weights)>particles:
            weights=resample(weights,particles,rng);resampling_steps+=1
    if set(weights)!={kernel.maximum}:raise AssertionError('terminal count state did not reconcile')
    return {'log_mass':log_mass,'exact':resampling_steps==0,'algorithm':'count-state forward filter with systematic resampling',
            'count_states':kernel.states,'particles':particles,'resampling_steps':resampling_steps,
            'maximum_expanded_layer':maximum_layer,'visited_states':visited,'proposal_density_known':True,
            'relative_standard_error':None,'effective_samples':None,'normalizers':normalizers,
            'uncertainty':'requires independent complete-filter replicates; within-filter particles are dependent'}
