"""Exchangeable-action erasure: exact count recursion or known-density proposals.

DESIGN CHECK: M01/M04/X10; LESSONS 3--5. NULL: impossible marks have zero
mass; exchangeable slot names cannot change likelihood. ALTERNATIVE: grouped
recursion and every transition match independent action-level subset summation.
Bands: exact within the unchanged mark model when the count grid fits the budget;
otherwise explicitly sampled, with measured proposal uncertainty, never exact.

The existing mark model makes actions of one type in one section exchangeable:
their scores, outcomes and influence on future scores are identical. A transition
to that group therefore has multiplicity equal to its remaining OBSERVED marks.
Unobserved actions still enter the policy and failure-marginalization denominators.
Sequential sampling mixes equal probability over remaining observed marks with
probability proportional to exact edge masses, half each. Its exact known proposal
probability divides the chosen edge mass; rare required marks retain coverage.
"""
import itertools
import math
import random

from .artifact_view import TYPES,all_header_actions,validate_work
from .mark_program import requirements,validate
from .program_inference import log_probability,logsumexp


class Kernel:
    def __init__(self,program,work):
        p=validate(program);validate_work(work,'artifact')
        self.context=work['context']
        actions=all_header_actions(self.context)
        self.total=len(actions)
        sections=[s['name'] for s in self.context['sections']]
        groups={}
        for aid,action in actions.items():
            groups.setdefault((TYPES.index(action['type']),sections.index(action['section'])),[]).append(aid)
        self.groups=sorted(groups)
        self.capacity=[len(groups[g]) for g in self.groups]
        marks=set(work['marks'])
        observed=[sorted(marks & set(groups[g])) for g in self.groups]
        self.observed_groups=[i for i,ids in enumerate(observed) if ids]
        self.observed_marks=[observed[i] for i in self.observed_groups]
        self.maximum=tuple(len(ids) for ids in self.observed_marks)
        self.states=math.prod(v+1 for v in self.maximum)
        self.eps=p['action_noise']
        tools={k:self.context['tools'][k] if p['context'][k]=='follow' else p['context'][k]=='available'
               for k in self.context['tools']}
        self.active=[t in p['available_types'] and all(tools[k] for k in requirements(t)) for t in TYPES]
        self.success=[p['outcome_noise']/2+(1-p['outcome_noise'])*(p['expertise']['success'][t]
                      if all(self.context['tools'][k] for k in requirements(t)) else 0.) for t in TYPES]
        fluency=p['expertise']['fluency']
        self.base=[(p['purpose'][t]-p['expertise']['cost'][t]+p['history'][t])/fluency for t in TYPES]
        self.progress=[[p['expertise']['progress'][old+'>'+new]/(self.total*fluency) for old in TYPES] for new in TYPES]
        self.section=[p['section_bias']*(1-j/len(sections))/fluency for j in range(len(sections))]
        deadline=self.context['deadline'] if p['context']['deadline']=='follow' else p['context']['deadline']
        self.stop_base=p['stop']['intercept']+p['stop']['deadline']*float(deadline=='tight')
        self.stop_base+=p['stop']['self']*float(self.context['audience']=='self')
        self.stop_progress=p['stop']['progress']/self.total

    def representative_marks(self,state):
        return sorted(mark for ids,n in zip(self.observed_marks,state) for mark in ids[:n])

    def edges(self,state,budget):
        if len(state)!=len(self.maximum) or any(type(v) is not int or not 0<=v<=m for v,m in zip(state,self.maximum)):
            raise ValueError('invalid observed count state')
        budget.charge()
        removed=[0]*len(self.groups)
        counts=[0]*len(TYPES)
        for g,n in zip(self.observed_groups,state):
            removed[g]=n;counts[self.groups[g][0]]+=n
        completed=sum(state)
        remaining=[n-k for n,k in zip(self.capacity,removed)]
        utilities=[self.base[t]+math.fsum(a*b for a,b in zip(self.progress[t],counts)) for t in range(len(TYPES))]
        logits={g:utilities[t]+self.section[s] for g,(t,s) in enumerate(self.groups) if remaining[g] and self.active[t]}
        z=self.stop_base+self.stop_progress*completed
        if not math.isfinite(z) or any(not math.isfinite(v) for v in logits.values()):
            raise ValueError('nonfinite grouped execution')
        hazard=((1/(1+math.exp(-z))) if z>=0 else math.exp(z)/(1+math.exp(z))) if logits else 1.
        peak=max(logits.values(),default=0.)
        weights={g:math.exp(v-peak) for g,v in logits.items()}
        total=math.fsum(remaining[g]*w for g,w in weights.items())
        uniform=self.eps/(1+self.total-completed)
        stop=uniform+(1-self.eps)*hazard
        probabilities=[uniform+((1-self.eps)*(1-hazard)*weights.get(g,0.)/total if total else 0.)
                       for g in range(len(self.groups))]
        denominator=stop+math.fsum(remaining[g]*probabilities[g]*self.success[t] for g,(t,s) in enumerate(self.groups))
        if denominator<=0:
            raise ValueError('candidate cannot stop or produce a mark')
        return [(m-n)*probabilities[g]*self.success[self.groups[g][0]]/denominator
                for g,n,m in zip(self.observed_groups,state,self.maximum)]


def likelihood(program,work,budget,*,exact_states=4096,draws=128,seed=0):
    if type(exact_states) is not int or exact_states<0 or type(draws) is not int or draws<2:
        raise ValueError('invalid grouped erasure envelope')
    kernel=Kernel(program,work)
    start=(0,)*len(kernel.maximum)
    if kernel.states<=exact_states:
        weights={start:0.}
        for state in itertools.product(*(range(n+1) for n in kernel.maximum)):
            if state==kernel.maximum:
                continue
            old=weights.get(state,-math.inf)
            if old==-math.inf:
                continue
            for j,edge in enumerate(kernel.edges(state,budget)):
                if edge<=0:
                    continue
                following=list(state);following[j]+=1;following=tuple(following)
                weights[following]=logsumexp([weights.get(following,-math.inf),old+math.log(edge)])
        return {'log_mass':weights.get(kernel.maximum,-math.inf),'exact':True,
                'algorithm':'exchangeable type-section count recursion','count_states':kernel.states,
                'relative_standard_error':0.,'effective_samples':None,'proposal_density_known':True}
    rng=random.Random(seed)
    logs=[]
    for _ in range(draws):
        state=list(start);log_weight=0.
        while tuple(state)!=kernel.maximum:
            edges=kernel.edges(state,budget)
            total=math.fsum(edges)
            if total<=0:
                log_weight=-math.inf;break
            left=[m-n for m,n in zip(kernel.maximum,state)]
            count=sum(left)
            proposal=[.5*n/count+.5*edge/total for n,edge in zip(left,edges)]
            pick=rng.random()
            chosen=max(j for j,q in enumerate(proposal) if q>0)
            for j,q in enumerate(proposal):
                if pick<q:
                    chosen=j;break
                pick-=q
            if edges[chosen]<=0:
                log_weight=-math.inf;break
            log_weight+=math.log(edges[chosen]/proposal[chosen])
            state[chosen]+=1
        logs.append(log_weight)
    total=logsumexp(logs)
    if total==-math.inf:
        relative,ess=None,0.
    else:
        square=math.fsum(math.exp(2*(v-total)) for v in logs)
        relative=math.sqrt(max(0.,(draws*square-1)/(draws-1)));ess=1/square
    return {'log_mass':total-math.log(draws),'exact':False,
            'algorithm':'half-uniform half-edge observed-group proposal with exact known density',
            'count_states':kernel.states,'draws':draws,'relative_standard_error':relative,
            'effective_samples':ess,'proposal_density_known':True}
