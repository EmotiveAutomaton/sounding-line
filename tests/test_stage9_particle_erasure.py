from collections import Counter
import math
import pytest
from runners.stage9.particle_erasure import likelihood,resample
from runners.stage9.erased_inference import artifact_likelihood
from runners.stage9.program_inference import Budget
from tests.test_stage9_erased_inference import A,B,marked,program
from tests.test_stage9_grouped_erasure import rich


def test_complete_forward_filter_equals_independent_subsets_and_fractions():
    for p,work in [(program(),marked([A,B])),(program(success=.5),marked([A,B])),rich()]:
        expected=artifact_likelihood(p,work,Budget(10000))
        actual=likelihood(p,work,Budget(10000),particles=1000)
        assert actual['exact'] and actual['resampling_steps']==0
        assert actual['log_mass']==pytest.approx(expected['log_mass'],abs=1e-12)
    assert math.exp(likelihood(program(),marked([A,B]),Budget(100))['log_mass'])==pytest.approx(9/16)


def test_systematic_resampling_preserves_mass_and_expected_weights():
    class Fixed:
        def __init__(self,x):self.x=x
        def random(self):return self.x
    weights={(0,):.2,(1,):.3,(2,):.5};total=Counter()
    for i in range(1000):
        actual=resample(weights,7,Fixed((i+.5)/1000))
        assert sum(actual.values())==pytest.approx(1)
        total.update(actual)
    assert {k:v/1000 for k,v in total.items()}==pytest.approx(weights,abs=1e-12)
    with pytest.raises(ValueError):resample({(0,):-.2,(1,):1.2},3,Fixed(.5))


def test_complete_filter_exact_randomization_mean_and_uncertainty_scope(monkeypatch):
    from collections import defaultdict
    import runners.stage9.particle_erasure as module
    from runners.stage9.grouped_erasure import Kernel
    p,work=rich();kernel=Kernel(p,work)
    exact=math.exp(artifact_likelihood(p,work,Budget(10000))['log_mass'])
    class Sequence:
        def __init__(self,values):self.values=iter(values)
        def random(self):return next(self.values)
    def paths(weights,offsets=(),probability=1.):
        if set(weights)=={kernel.maximum}:
            yield offsets,probability;return
        following=defaultdict(float)
        for state,weight in weights.items():
            for j,edge in enumerate(kernel.edges(state,Budget(1))):
                if edge>0:
                    target=list(state);target[j]+=1;following[tuple(target)]+=weight*edge
        z=math.fsum(following.values());normalized={s:w/z for s,w in following.items()}
        if len(normalized)<=2:
            yield from paths(normalized,offsets,probability);return
        ordered=sorted(normalized.items());cumulative=0.;cuts={0.,1.}
        for state,weight in ordered[:-1]:
            cumulative+=weight;cuts.add((2*cumulative)%1.)
        cuts=sorted(cuts)
        for a,b in zip(cuts,cuts[1:]):
            if b-a<1e-14:continue
            u=(a+b)/2;cumulative=0.;previous=0;next_weights={}
            # Independent integer-count formula for each systematic interval.
            for state,weight in ordered:
                cumulative+=weight;after=max(0,min(2,math.ceil(2*cumulative-u)))
                if after>previous:next_weights[state]=(after-previous)/2
                previous=after
            yield from paths(next_weights,offsets+(u,),probability*(b-a))
    expected=total=0.;values=[]
    for offsets,probability in paths({(0,)*len(kernel.maximum):1.}):
        with monkeypatch.context() as patch:
            patch.setattr(module.random,'Random',lambda seed:Sequence(offsets))
            actual=likelihood(p,work,Budget(1000),particles=2)
        expected+=probability*math.exp(actual['log_mass']);total+=probability;values.append(actual)
    assert total==pytest.approx(1,abs=1e-12)
    assert expected==pytest.approx(exact,rel=1e-12)
    assert max(v['log_mass'] for v in values)>min(v['log_mass'] for v in values)
    assert all(not v['exact'] and v['relative_standard_error'] is None for v in values)


def test_empty_impossible_and_budget_boundaries():
    assert likelihood(program(),marked([]),Budget(1))['log_mass']==0
    p=program();p['available_types']=['check']
    assert likelihood(p,marked([A]),Budget(10))['log_mass']==-math.inf
    with pytest.raises(ValueError,match='budget'):likelihood(*rich(),Budget(1))
    with pytest.raises(ValueError):likelihood(*rich(),Budget(100),particles=0)
