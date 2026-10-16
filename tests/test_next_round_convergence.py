"""Known-answer and leakage checks for the numerical successor."""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
from runners.next_round.convergence import optimized_shift, certificate, shift_terms, solve_fold, analyze, comparisons
from runners.next_round.statistics import outer_fold
from runners.stage14.common import freeze, filehash, read

class ConvergenceTests(unittest.TestCase):
    def test_constant_evidence_has_no_information(self):
        p=np.tile([.1,.2,.3,.4],(12,1))
        q,c=optimized_shift(p,p[0])
        np.testing.assert_allclose(q,p,atol=1e-12)
        self.assertEqual(c['ratio_rank'],1)
        self.assertLess(c['gap'],1e-12)

    def test_known_interior(self):
        # Each class's identical symmetric evidence repeated equally: uniform is optimal.
        p=np.eye(4)*.8+.05
        q,c=optimized_shift(p,[.25]*4)
        np.testing.assert_allclose(c['prior'],[.25]*4,atol=1e-8)
        np.testing.assert_allclose(q,p,atol=1e-8)

    def test_boundary_optimum(self):
        p=np.tile([.7,.1,.1,.1],(20,1))
        q,c=optimized_shift(p,[.25]*4)
        np.testing.assert_allclose(c['prior'],[1,0,0,0],atol=1e-8)
        self.assertLess(c['gap'],1e-7)

    def test_certificate_can_fail(self):
        r=shift_terms(np.tile([.7,.1,.1,.1],(20,1)),[.25]*4)
        _,c=certificate(r,[.25]*4)
        self.assertGreater(c['gap'],1.)

    def test_invalid_refused(self):
        for p,s in [([[.4]*4],[.25]*4),([[.25]*4],[0,.3,.3,.4]),([[np.nan]*4],[.25]*4),([], [.25]*4)]:
            with self.assertRaises(ValueError): optimized_shift(p,s)

    def test_outer_labels_do_not_change_predictions(self):
        rng=np.random.default_rng(42); groups=np.repeat(['a','b','c','d'],8)
        y=rng.integers(4,size=32); p=rng.dirichlet(np.ones(4),size=32)
        base=np.tile([.25]*4,(32,1)); valid=np.ones(32,bool); valid[0]=False
        old=outer_fold(p,base,y,groups,'a','EM_TS',valid)
        original=dict(heldout_writer='a',outer_fit_writers=['b','c','d'],**old)
        result=solve_fold(p,base,y,groups,valid,original)
        changed=y.copy(); changed[groups=='a']=(changed[groups=='a']+1)%4
        result2=solve_fold(p,base,changed,groups,valid,original)
        np.testing.assert_allclose(result['stacked'],result2['stacked'],atol=0)
        np.testing.assert_allclose(result['stacked'][0],base[0],atol=1e-12)
        self.assertEqual(len(result['audit']),3)

    def test_complete_handler_reentry(self):
        # Balanced nonconstant constructed evidence exercises every output and contrast.
        groups=np.repeat(['a','b','c'],8); y=np.tile(np.arange(4),6)
        p=np.tile(np.eye(4)*.8+.05,(6,1)); base=np.full((24,4),.25)
        rows=[dict(key=str(i),writer=g,prompt=str(i%2)) for i,g in enumerate(groups)]
        saved={r['key']:{b:dict(probabilities=base[i].tolist(),scores=dict(half_brier=.375))
            for b in ('B-mixlogit','B-pop','B-writer','B-last','P04-effort-features','P04-E','P04-E-shuffle')}
            for i,r in enumerate(rows)}
        predictions={}; fits={}; summaries={}; valid=np.ones(24,bool)
        for arm in ('R27.H0','R27.H1','R27.H2','R27.H3'):
            for i,r in enumerate(rows): saved[r['key']][arm]=dict(probabilities=p[i].tolist(),valid=True)
            for mode in ('EM_TS','BCTS'):
                cp=np.zeros_like(p); sp=np.zeros_like(p); fs=[]
                for g in sorted(set(groups)):
                    f=outer_fold(p,base,y,groups,g,mode,valid); m=groups==g
                    cp[m]=f.pop('corrected'); sp[m]=f.pop('stacked')
                    fs.append(dict(heldout_writer=g,outer_fit_writers=sorted(set(groups[~m])),**f))
                name=arm+'.'+mode; predictions[name],summaries[name]=comparisons(rows,saved,base,cp,sp,y,valid); fits[name]=fs
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); old=root/'old'; out=root/'new'
            freeze(old/'FITS.json',fits); freeze(old/'PREDICTIONS.json',predictions)
            freeze(old/'SUMMARY.json',dict(comparisons=summaries,limits=['constructed fixture']))
            freeze(old/'COMPLETE.json',dict(status='COMPLETE',outputs={p.name:filehash(p) for p in old.glob('*.json')}))
            with patch('runners.next_round.convergence.OLD',old),patch('runners.next_round.phase0.saved',return_value=(rows,saved,y)):
                analyze(out,lambda progress:None)
                first={p.name:filehash(p) for p in out.glob('*.json')}
                analyze(out,lambda progress:None)
                self.assertEqual(first,{p.name:filehash(p) for p in out.glob('*.json')})
                self.assertEqual(len(read(out/'SUMMARY.json')['comparisons']),10)
                self.assertTrue(read(out/'SUMMARY.json')['original_replay_verified'])

if __name__=='__main__': unittest.main()
