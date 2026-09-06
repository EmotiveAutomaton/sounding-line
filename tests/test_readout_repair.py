"""Known answers for the isolated measurement amendment; no model/server calls."""
import math
import random

from runners.readout_repair import digest, readout

IDENTITY={k:'fixture-'+k for k in ('model','revision','adapter_sha256','scorer_sha256','information_sha256')}

def backend(weights, mutate=None):
    def score(prefix,options):
        total=sum(weights.values())
        rows=[dict(option_id=k,logprob=math.log(weights[k]/total),valid=True,
                   identity=dict(IDENTITY),prefix_sha256=digest(prefix),
                   continuation_sha256=digest(v),semantics='sum_log_probability') for k,v in options.items()]
        return mutate(rows) if mutate else rows
    return score

def test_every_position_and_permutation_has_a_scoring_path():
    for n in (1,2,6,7,12,18,21,25,64):
        keys=[str(i) for i in range(n)]
        for best in keys:
            weights={k:10 if k==best else 1 for k in keys}
            random.Random(int(best)).shuffle(keys)
            out=readout('fixed evidence',{k:'answer '+k for k in keys},backend(weights),IDENTITY)
            assert out['valid'] and out['pred']==best
            assert set(out['probs'])==set(keys)
            assert abs(sum(out['probs'].values())-1)<1e-12
            assert all(abs(out['probs'][k]-weights[k]/sum(weights.values()))<1e-12 for k in keys)

def test_uniform_ties_and_extreme_logs():
    weights={str(i):1 for i in range(65)};options={k:'answer '+k for k in weights}
    out=readout('prefix',options,backend(weights),IDENTITY)
    assert out['valid'] and out['pred'] is None and len(out['ties'])==65
    assert all(abs(v-1/65)<1e-12 for v in out['probs'].values())
    def extremes(rows):
        for r in rows:r['logprob']=-1e9
        return rows
    assert readout('prefix',options,backend(weights,extremes),IDENTITY)['valid']

def test_invalidity_propagates_and_never_returns_probabilities():
    options={'a':'alpha','b':'beta'};weights={'a':2,'b':1}
    mutations=[lambda r:r[:-1],lambda r:r+[r[0]],lambda r:None]
    for field,value in [('logprob',float('nan')),('logprob',float('inf')),('logprob',0.1),('logprob',True),('valid',False),('option_id','missing'),('identity',{}),('prefix_sha256','wrong'),('continuation_sha256','wrong'),('semantics','mean_log_probability')]:
        mutations.append(lambda rows,f=field,v=value:[dict(rows[0],**{f:v}),rows[1]])
    for change in mutations:
        out=readout('prefix',options,backend(weights,change),IDENTITY)
        assert not out['valid'] and out['probs'] is None and out['pred'] is None
    assert not readout('prefix',options,backend(weights),{})['valid']
    assert not readout('prefix',{},backend(weights),IDENTITY)['valid']
