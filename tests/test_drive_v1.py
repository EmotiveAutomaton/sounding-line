import copy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from runners.drive import v1_phase0 as v

def fixture():
    sessions=[]
    for i in range(20):
        writer=str(i%4);start=i*100
        rows=[dict(key=f'{i}-{j}',writer=writer,prompt=str(i%3),session=str(i),session_time=start,
            open_at=start+j*3,resolved_at=start+j*3+2,handling='accept',document='alpha beta',menu=['alpha','delta'],decision_index=j) for j in range(4)]
        sessions.append(dict(session=str(i),writer=writer,prompt=str(i%3),timestamp=start,end_at=start+20,rows=rows))
    return sessions

class PlasmodeTests(unittest.TestCase):
    def test_null_invariant_to_original_outcomes(self):
        ss=fixture();base={r['key']:[.25]*4 for s in ss for r in s['rows']};cov=v.content_covariates(ss)
        a,q,t=v.construct(ss,base,cov,'habit',0,10)
        altered=copy.deepcopy(ss)
        for s in altered:
            for r in s['rows']:r['handling']='dismiss';r['previous_handling']='ignore'
        self.assertEqual(v.construct(altered,base,cov,'habit',0,10)[2],t)
        self.assertEqual(q,base)
    def test_pending_choice_does_not_enter_lag(self):
        ss=fixture();ss[0]['rows'][0]['resolved_at']=15
        base={r['key']:[.25]*4 for s in ss for r in s['rows']};_,_,trace=v.construct(ss,base,v.content_covariates(ss),'habit',.8,10)
        by={r['key']:r for r in trace};self.assertIsNone(by['0-1']['previous_handling'])
        self.assertEqual(by['0-2']['previous_handling'],by['0-1']['truth'])
    def test_offset_direction_and_multiclass_oracle(self):
        ss=fixture();base={r['key']:[.25]*4 for s in ss for r in s['rows']};_,q,_=v.construct(ss,base,v.content_covariates(ss),'offset',.8,10)
        self.assertEqual(sum(p[0]>.25 for p in q.values()),40)
        p=np.array(next(p for p in q.values() if p[0]>.25));b=np.full(4,.25)
        expected=sum(p[k]*(.5*np.sum((b-np.eye(4)[k])**2)-.5*np.sum((p-np.eye(4)[k])**2)) for k in range(4))
        self.assertAlmostEqual(expected,.5*np.sum((p-b)**2))
    def test_whole_pipeline_and_retention(self):
        ss=fixture();base={r['key']:[.25]*4 for s in ss for r in s['rows']};synthetic,q,_=v.construct(ss,base,v.content_covariates(ss),'offset',.8,10)
        predictions,fits=v.fit_world(synthetic,lambda *a:None)
        r=v.score_world(predictions,q,base);self.assertEqual(r['rows'],80);self.assertEqual(len(fits),20)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);phase=root/'source';v.freeze(phase/'prepared/SESSIONS.json',ss)
            v.freeze(phase/'T0c/PREDICTIONS.json',[dict(key=k,probabilities={'B-pop':p}) for k,p in base.items()])
            with patch.object(v,'ROOT',root/'result'),patch.object(v,'PHASE',phase):
                v.compute(dict(grid=[dict(effect='offset',delta=0.,seed=10,replicate=0)]),lambda *a:None)
                self.assertTrue(v.read(v.ROOT/'SUMMARY.json')['all_worlds_complete'])
                self.assertTrue((v.ROOT/'worlds/000/CONSTRUCTION.json').is_file())

if __name__=='__main__':unittest.main()
