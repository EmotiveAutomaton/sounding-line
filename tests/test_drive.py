import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
from runners.drive.statistics import decomposition, half_brier, futility, extension
from runners.drive.timeline import rebuild


class StatisticsTests(unittest.TestCase):
    def test_exact_and_binned_closure(self):
        rng=np.random.default_rng(1); p=rng.dirichlet(np.ones(4),size=71); y=rng.integers(4,size=71)
        for exact in (False,True):
            r=decomposition(p,y,exact)
            self.assertAlmostEqual(r['half_brier'],float(half_brier(p,y).mean()))
            self.assertAlmostEqual(r['half_brier'],r['reconstructed'])
        self.assertIsNone(decomposition(p,y,True)['correction_iid'])
    def test_calibrated_constant_and_perfect(self):
        y=np.tile(np.arange(4),10); r=decomposition(np.ones((40,4))/4,y)
        self.assertEqual(r['resolution'],0); self.assertEqual(r['reliability'],0)
        r=decomposition(np.eye(4)[y],y,True); self.assertEqual(r['half_brier'],0)
        self.assertAlmostEqual(r['resolution'],r['uncertainty'])
    def test_covariance_residual_can_be_negative(self):
        p=np.array([[.41,.59],[.49,.51]]); y=np.array([1,0]); r=decomposition(p,y)
        self.assertLess(r['binning_residual'],0)
    def test_no_invalid_or_early_positive(self):
        self.assertEqual(futility(.2,1,.1)['action'],'CONTINUE')
        self.assertEqual(futility(.2,-.06,.1)['action'],'STOP_FUTILITY')
        self.assertEqual(futility(.5,-.001,.1)['action'],'STOP_FUTILITY')
        self.assertEqual(futility(.5,0,0)['action'],'STOP_FUTILITY')
        self.assertEqual(futility(.2,float('nan'),1)['action'],'STOP_INVALID')
        for args in [(0,[-1,1]),(-2,[-3,-1])]: self.assertFalse(extension(*args)['extend'])
        self.assertTrue(extension(.1,[-1,1])['extend'])
    def test_invalid_probabilities(self):
        with self.assertRaises(ValueError): half_brier([[.2,.3]],[0])


class TimelineTests(unittest.TestCase):
    def event(self,n,name,source='user',**kw):
        return dict(eventNum=n,eventTimestamp=1000+n*100,eventName=name,eventSource=source,**kw)
    def test_unicode_origins_timing_and_censor(self):
        es=[self.event(0,'system-initialize','api',currentDoc='A\n'),
            self.event(1,'text-insert',textDelta={'ops':[{'retain':1},{'insert':'😀'}]}),
            self.event(2,'suggestion-open'),self.event(3,'suggestion-select'),
            self.event(4,'text-insert','api',textDelta={'ops':[{'retain':3},{'insert':'xyz'}]}),
            self.event(5,'text-delete',textDelta={'ops':[{'retain':4},{'delete':1}]}),
            self.event(6,'suggestion-open'),self.event(7,'cursor-forward')]
        rows=[dict(key='a',ordinal=2,end_ordinal=6,handling='edit',menu=['xyz']),
              dict(key='b',ordinal=6,end_ordinal=8,handling='ignore',menu=['x','y'])]
        r=rebuild(es,rows)
        self.assertEqual(r['final_document'],'A😀xz\n')
        self.assertEqual(r['deltas'][0]['inserted_codepoints'],1)
        self.assertEqual(r['deltas'][0]['inserted_utf16'],2)
        self.assertEqual(r['decisions'][0]['latency_seconds'],.1)
        self.assertEqual(r['decisions'][1]['latency_kind'],'right_censored_at_next_menu_or_end')
        self.assertIn('accepted_edited',[s['origin'] for s in r['final_spans']])
        es[-1]['eventTimestamp']=1
        with self.assertRaises(ValueError): rebuild(es,rows)


class WorkerTests(unittest.TestCase):
    def test_finite_worker_and_reentry(self):
        from runners.drive import foundation as f
        from runners.stage14.common import freeze,filehash,read
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);freeze(root/'PLAN.json',dict(pins={},max_wall_seconds=10))
            def computed(dest,guard):
                # Stub only expensive corpus work; exercise actual worker terminals.
                guard('fixture',1);freeze(dest/'FIXTURE.json',dict(retained=True))
            original=f.freeze
            def monitored(path,value):
                result=original(path,value)
                if path.name=='OWNER.json':original(root/'MONITOR_READY.json',dict(owner_sha256=filehash(path)))
                return result
            with patch.object(f,'ROOT',root),patch.object(f,'compute',computed),patch.object(f,'freeze',monitored):
                f.run()
                done=read(root/'COMPLETE.json');self.assertEqual(done['status'],'COMPLETE')
                for rel,h in done['outputs'].items():self.assertEqual(filehash(root/rel),h)
                with self.assertRaises(FileExistsError):f.run()
    def test_source_drift_refuses_before_claim(self):
        from runners.drive import foundation as f
        from runners.stage14.common import freeze
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);freeze(root/'PLAN.json',dict(pins={'runners/drive/foundation.py':'0'*64},max_wall_seconds=10))
            with patch.object(f,'ROOT',root):
                with self.assertRaises(ValueError):f.run()
            self.assertFalse((root/'ATTEMPT.claim').exists())


if __name__=='__main__': unittest.main()
