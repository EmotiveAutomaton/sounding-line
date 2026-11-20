"""Ten constructed checks of the exact delivered joined-wave file layouts.

DESIGN CHECK: LESSONS 2-5. Counts are unique synthetic people, never file rows.
All ten cases must pass; private source opens and enumeration are prohibited.
"""
import csv
import hashlib
import importlib.metadata as metadata
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

PEOPLE=tuple(range(20))


class LayoutFixture(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='joined-constructed-')
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.root=self.base/'source';self.root.mkdir()
        self.out=self.base/'out';self.out.mkdir()

    def files(self,index,*,people=20,repeat=1,missing=None):
        import pandas as pd
        import pyreadstat
        mapping=MAPPINGS[index]
        groups=sys.modules['runners.drive.cards.week6_sm0_probe_v1'].GROUPS
        for j,table in enumerate(mapping['tables']):
            kind='daily' if table['role']=='daily' else 'traits'
            names=groups[f'wave{index+2}_{kind}']
            frame=pd.DataFrame({name:([float(n) for n in PEOPLE[:people]]*repeat if name=='M2ID' else [1.]*(people*repeat)) for name in names})
            if missing is not None and j in missing:frame=frame.drop(columns='M2ID')
            path=self.root/table['path'];path.parent.mkdir(parents=True,exist_ok=True)
            pyreadstat.write_sav(frame,str(path))
        # Non-table source metadata exists beside the collector's staged SAVs.
        (self.root/'SOURCE.json').write_text('{}',encoding='utf8')
        return mapping

    def check(self,index,**kw):
        mapping=self.files(index,**kw)
        self.assertEqual(P.exit_code(self.root,self.out,mapping),0)
        with (self.out/'status.csv').open(newline='') as f:rows=list(csv.DictReader(f))
        self.assertEqual([r['n'] for r in rows],['20','20'])
        self.assertTrue(all(r['loaded_tables']=='2' and r['disposition']=='mapped_tables_loaded' for r in rows))
        with (self.out/'structure.csv').open(newline='') as f:shape=list(csv.DictReader(f))
        self.assertEqual([r[f'wave{index+2}_traits'] for r in shape],['1','0'])
        self.assertEqual([r[f'wave{index+2}_daily'] for r in shape],['0','1'])

    def test_wave2_layout(self):self.check(0)
    def test_wave3_layout(self):self.check(1)
    def test_person_days_are_not_people(self):self.check(0,repeat=8)

    def test_all_small(self):
        mapping=self.files(1,people=10,repeat=8)
        self.assertEqual(P.exit_code(self.root,self.out,mapping),38)
        self.assertEqual(list(self.out.iterdir()),[])

    def test_both_missing_keys(self):
        mapping=self.files(0,missing=(0,1))
        self.assertEqual(P.exit_code(self.root,self.out,mapping),26)
        self.assertEqual(list(self.out.iterdir()),[])

    def test_partial_real_denominator(self):
        mapping=self.files(1,missing=(0,))
        self.assertEqual(P.exit_code(self.root,self.out,mapping),0)
        with (self.out/'status.csv').open(newline='') as f:rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),1)
        self.assertEqual((rows[0]['n'],rows[0]['disposition'],rows[0]['error_person_field_absent']),('20','partial','1'))

    def test_archives(self):
        (self.root/'archive.zip').write_bytes(b'constructed')
        self.assertEqual(P.exit_code(self.root,self.out,MAPPINGS[0]),22)

    def test_empty(self):self.assertEqual(P.exit_code(self.root,self.out,MAPPINGS[1]),21)

    def test_read_cap(self):
        mapping=self.files(0)
        self.assertEqual(P.exit_code(self.root,self.out,mapping,max_read_bytes=1),25)
        self.assertEqual(list(self.out.iterdir()),[])

    def test_limits_and_threads(self):
        self.assertTrue(all(os.environ[k]=='2' for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS')))
        self.assertEqual(os.environ['CUDA_VISIBLE_DEVICES'],'')
        self.assertEqual(P.exit_code(self.root,self.out,MAPPINGS[0],max_entries=100001),42)


def main(out):
    started=time.monotonic();cpu=time.process_time()
    def private_guard(event,args):
        if event in ('open','os.listdir','os.scandir') and args and isinstance(args[0],(str,bytes,os.PathLike)):
            path=os.path.normpath(os.fsdecode(args[0])).replace('\\','/')
            if path in ('/data','/srv/private') or path.startswith(('/data/','/srv/private/')):
                raise RuntimeError('Constructed fixture cannot open private sources')
    sys.addaudithook(private_guard)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(LayoutFixture)
    if suite.countTestCases()!=10:raise RuntimeError('Incomplete fixture roster')
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun!=10 or not result.wasSuccessful() or result.skipped:raise SystemExit(21)
    S.write_tables(out,{'qualification':[dict(n=S.unique_people(PEOPLE),constructed_only=1,
        cases=10,failures=0,errors=0,skipped=0,private_source_reads=0,numerical_threads=2,
        probe_sha256=hashlib.sha256(SOURCES['runners.drive.cards.week6_sm0_probe_v3'].encode('utf8')).hexdigest(),
        python_version=sys.version.split()[0],numpy_version=metadata.version('numpy'),
        pandas_version=metadata.version('pandas'),pyreadstat_version=metadata.version('pyreadstat'),
        cpu_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-started)]})


if __name__=='__main__':main(Path(sys.argv[1]) if len(sys.argv)==2 else Path('/out'))
