"""Same comparator hierarchy with explicit grouped-erasure evaluation.

DESIGN CHECK: M01/X10; LESSONS 3--5. Both evaluators must agree on exact
fixtures. Only the declared erasure calculation changes; process records and
the full evidence/current-purpose hierarchy retain their original meaning.
"""
import copy
from .artifact_view import validate_work
from .erased_inference import process_likelihood
from .grouped_erasure import likelihood
from .likelihood_table import Table
from .program_inference import identity


class GroupedTable(Table):
    def __init__(self,candidates,budget,*,exact_states=4096,draws=128,seed=0):
        super().__init__(candidates,budget,seed=seed)
        self.exact_states,self.draws=exact_states,draws

    def likelihood(self,cid,work,view):
        validate_work(work,view)
        key=(cid,view,identity(work))
        if key not in self._likelihoods:
            program=self.candidates[cid]
            self._likelihoods[key]=(process_likelihood(program,work,self.budget) if view=='process_record' else
                likelihood(program,work,self.budget,exact_states=self.exact_states,draws=self.draws,
                           seed=str(self.seed)+':'+identity(work)))
        else:
            self.cache_hits+=1
        return copy.deepcopy(self._likelihoods[key])
