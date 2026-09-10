"""The existing comparator hierarchy with bounded count-state filtering.

DESIGN CHECK: M01/M04/X10; LESSONS 3--5. The model, priors and prediction
operation stay unchanged. Only erased-artifact integration changes; the explicit
record likelihood remains exact. Complete independent replicates qualify precision.
"""
import copy
from .artifact_view import validate_work
from .erased_inference import process_likelihood
from .particle_erasure import likelihood
from .likelihood_table import Table
from .program_inference import identity


class ParticleTable(Table):
    def __init__(self,candidates,budget,*,particles=512,seed=0):
        super().__init__(candidates,budget,seed=seed);self.particles=particles

    def likelihood(self,cid,work,view):
        validate_work(work,view);key=(cid,view,identity(work))
        if key not in self._likelihoods:
            program=self.candidates[cid]
            self._likelihoods[key]=(process_likelihood(program,work,self.budget) if view=='process_record' else
                likelihood(program,work,self.budget,particles=self.particles,seed=str(self.seed)+':'+identity(work)))
        else:self.cache_hits+=1
        return copy.deepcopy(self._likelihoods[key])
