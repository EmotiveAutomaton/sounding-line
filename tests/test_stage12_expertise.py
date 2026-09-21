"""Known forward laws, inverse ambiguity and complete E1 worker rehearsal."""
from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
import numpy as np
from runners.stage12 import expertise as E,native_shared as S,native_math as N


class Expertise(unittest.TestCase):
    def test_known_posteriors_and_failure_direction(self):
        self.assertTrue(all(E.controls().values()))
        truth=np.array([[[.8,.2],[.8,.2]],[[.2,.8],[.2,.8]]])
        p,_=E.posterior(truth)
        S.close(p[0,0],np.array([.8,.2]),1e-14)
        self.assertAlmostEqual(E.score(truth,truth)['half_brier'],.16)
        null=np.ones_like(truth)/2
        self.assertAlmostEqual(E.score(truth,null)['half_brier'],.25)

    def test_independent_native_path_enumeration_and_objective(self):
        world=N.law(-120921);kernel=S.production_kernel(world);actor=(0,1,0,0)
        for reward in E.REWARDS:
            pi=E.policy(kernel,reward);direct=np.zeros((2,8))
            for ctx,initial in enumerate(S.INITIAL):
                def walk(a,previous,step,mass):
                    if step==3:
                        direct[ctx,S.ARTIFACTS.index(a)]+=mass;return
                    goal=N.GOALS[pi[step,ctx,S.ARTIFACTS.index(a),S.ARTIFACTS.index(previous)]]
                    options=[(op,w) for g,op,w in N.choices(world,actor,a,step,N.CONTEXTS[ctx*2]) if g==goal]
                    total=sum(w for _,w in options)
                    for op,w in options:walk(N.execute(a,previous,op,actor),a,step+1,mass*w/total)
                walk(S.ARTIFACTS[initial],S.ARTIFACTS[initial],0,1.)
            S.close(E.endpoints(kernel,pi),direct,1e-12)
        corrupt=kernel.copy();corrupt.flat[0]=np.nan
        with self.assertRaises(ValueError):E.policy(corrupt,E.REWARDS[0])

    def test_complete_handler_reentry_and_changed_replay(self):
        # Synthetic models only; not a trained setting or a scientific roster.
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source=root/'source';out=root/'out'
            (source/'models').mkdir(parents=True);(source/'evaluator').mkdir();out.mkdir()
            cfg=dict(lineages=[-120921],training_draws=[1],policy_seeds=[2],budgets=[32,128,512])
            kernel=S.production_kernel(N.law(-120921))
            np.savez(source/'evaluator/law--120921.npz',kernel=kernel)
            for condition in ('matched-start','restricted-start'):
                for arm in ('active','replay','demonstration'):
                    np.savez(source/'models'/f'-120921-1-2-{condition}-512-{arm}.npz',counts=kernel*40+.5)
            with patch.object(S,'packet',return_value=(source,cfg)):
                result=E.run(out,{'episodes':512},lambda **kw:None,root)
                self.assertEqual(result['rows'],24);self.assertTrue(all(result['controls'].values()))
                self.assertEqual(result,E.run(out,{'episodes':512},lambda **kw:None,root))
                changed=kernel*40+.5;changed.flat[0]+=1
                np.savez(source/'models/-120921-1-2-matched-start-512-replay.npz',counts=changed)
                with self.assertRaises(ValueError):E.run(root,{'episodes':512},lambda **kw:None,root)


if __name__=='__main__':unittest.main()
