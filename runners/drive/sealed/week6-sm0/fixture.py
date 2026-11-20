"""Portable, constructed-only rehearsal of the unchanged SM0 job.

DESIGN CHECK: LESSONS 2-5. Twenty-two fixed cases cover ordinary output,
distinct-person counting, malformed/unsupported input, the read and export
limits, and actual CSV/SPSS/Stata readers. All must pass without skips under
any scientific hypothesis. No private source is opened. This qualifies an
interface, not a scientific model or real population.
"""
import csv
import hashlib
import io
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

PROBE_SHA256 = '29d34d96e4ac85611a26081566d35e8274ee361ae0b1c5bbf68f02cb4ec7e449'
if 'PROBE_SOURCE' not in globals():
    PROBE_SOURCE = Path(__file__).with_name('run.py').read_text('utf8')
if hashlib.sha256(PROBE_SOURCE.encode('utf8')).hexdigest() != PROBE_SHA256:
    raise RuntimeError('Unexpected SM0 source')
P = {'__name__': 'sm0_constructed_fixture'}
exec(compile(PROBE_SOURCE, '<reviewed-sm0>', 'exec'), P)
Failure = P['SealedFailure']
PEOPLE = tuple(range(20))


class ProbeFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='sm0-constructed-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base/'data'; self.root.mkdir()
        self.out = self.base/'out'; self.out.mkdir()

    def table(self, ids=PEOPLE, header=('M2ID','B2DDAY','B2DWEEKD','B2DC17','B2DC19')):
        path = self.root/'synthetic_name.csv'
        with path.open('w', encoding='utf8', newline='') as stream:
            writer = csv.writer(stream); writer.writerow(header)
            writer.writerows([key]+[2]*(len(header)-1) for key in ids)
        return path

    def result(self):
        P['run'](self.root, self.out)
        text = (self.out/'structure.csv').read_text('utf8')
        self.assertNotIn('synthetic_name', text)
        return list(csv.DictReader(io.StringIO(text)))[0]

    def test_duplicate_people(self):
        self.table(PEOPLE*5); row = self.result()
        self.assertEqual({k:row[k] for k in ('table','n','wave2_daily','wave3_daily','wave2_traits','wave3_traits')},
                         dict(table='table_001',n='20',wave2_daily='1',wave3_daily='0',wave2_traits='0',wave3_traits='0'))
        self.assertEqual(row['present_M2ID'], '1'); self.assertEqual(row['present_C1SNEURO'], '0')

    def test_small_population(self):
        self.table(PEOPLE[:8])
        with self.assertRaisesRegex(Failure, 'No publishable'): P['run'](self.root, self.out)
        self.assertEqual(list(self.out.iterdir()), [])

    def test_missing_person(self):
        self.table(header=('record','value'))
        with self.assertRaisesRegex(Failure, 'person field'): P['run'](self.root, self.out)
        self.assertEqual(list(self.out.iterdir()), [])

    def test_input_cap(self):
        self.table()
        with self.assertRaisesRegex(Failure, 'allowance'): P['run'](self.root, self.out, max_bytes=1)
        self.assertEqual(list(self.out.iterdir()), [])

    def test_ambiguous_columns(self):
        with self.assertRaisesRegex(Failure, 'Ambiguous'): P['column_map'](['M2ID','m2id'])

    def test_archive_is_unsupported(self):
        (self.root/'file.zip').write_bytes(b'constructed archive placeholder')
        with self.assertRaisesRegex(Failure, 'archives'): P['run'](self.root, self.out)

    def test_outside_declared_root(self):
        path = self.table()
        with self.assertRaisesRegex(Failure, 'outside'): P['inspect_table'](path, P['ReadBudget'](self.out))

    def test_blank_ids(self):
        path = self.table(['']*100+list(PEOPLE[:11]))
        self.assertEqual(P['inspect_table'](path, P['ReadBudget'](self.root))['n'], 11)

    def test_malformed_row(self):
        path = self.table()
        with path.open('a') as stream: stream.write('1,2\n')
        with self.assertRaisesRegex(Failure, 'Malformed'): P['run'](self.root, self.out)
        self.assertEqual(list(self.out.iterdir()), [])

    def test_count_boundary(self):
        self.assertEqual(P['unique_people']([1]*100+[2]*100), 2)
        with self.assertRaises(Failure): P['write_tables'](self.out, {'status':[dict(n=2)]})
        self.assertEqual(list(self.out.iterdir()), [])
        with self.assertRaises(Failure): P['unique_people'](None)

    def test_suppression(self):
        receipt = P['write_tables'](self.out, {'status':[dict(n=10,state='small'),dict(n=11,state='present')]})
        self.assertEqual(receipt['dropped'], {'status':1})
        with (self.out/'status.csv').open() as stream:
            self.assertEqual(list(csv.DictReader(stream)), [dict(n='11',state='present')])

    def test_export_caps(self):
        for rows in ([dict(n=11)]*2001, [dict(n=11,value='x'*262144)]):
            with self.assertRaises(Failure): P['write_tables'](self.out, {'status':rows})
            self.assertEqual(list(self.out.iterdir()), [])

    def test_read_reservations(self):
        path = self.root/'test.csv'; path.write_bytes(b'0123456789')
        budget = P['ReadBudget'](self.root, maximum=20)
        self.assertEqual(budget.reserve(path, passes=2), path)
        with self.assertRaises(Failure): budget.reserve(path)
        outside = self.base/'outside'; outside.write_text('x')
        with self.assertRaises(Failure): budget.reserve(outside)

    def test_thread_limit(self):
        with patch.dict(os.environ, {'OPENBLAS_NUM_THREADS':'32'}):
            P['force_threads'](2)
            self.assertTrue(all(os.environ[k]=='2' for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS')))
            self.assertEqual(os.environ['CUDA_VISIBLE_DEVICES'], '')
            with self.assertRaises(ValueError): P['force_threads'](5)

    def test_packaged_csv(self):
        self.table(PEOPLE[:11], ('M2ID','C1SNEURO','C1SEXTRA','C1SAGREE'))
        row = self.result()
        self.assertEqual((row['n'], row['wave3_traits']), ('11','1'))

    def statistical_format(self, extension):
        import pandas as pd
        import pyreadstat
        frame = pd.DataFrame({'M2ID':[float(i) for i in PEOPLE[:11]]*3,
            'B2DDAY':[1.]*33,'B2DWEEKD':[2.]*33,'B2DC17':[1.]*33,'B2DC19':[2.]*33})
        getattr(pyreadstat,'write_'+extension)(frame,str(self.root/('data.'+extension)))
        row = self.result()
        self.assertEqual((row['n'], row['wave2_daily']), ('11','1'))

    def test_packaged_sav(self): self.statistical_format('sav')
    def test_packaged_dta(self): self.statistical_format('dta')


def invalid_count_case(value):
    def check(self):
        with self.assertRaises(Failure): P['write_tables'](self.out, {'status':[dict(n=value)]})
        self.assertEqual(list(self.out.iterdir()), [])
    return check


for index, value in enumerate((11.0, 11.9, True, -1, None)):
    setattr(ProbeFixture, f'test_invalid_count_{index}', invalid_count_case(value))


def main(out):
    started = time.monotonic(); cpu_started = time.process_time()
    if os.name == 'posix':
        import resource
        import signal
        resource.setrlimit(resource.RLIMIT_CPU, (600,600))
        signal.alarm(600)
    def no_private_reads(event, args):
        if event in ('open','os.listdir','os.scandir') and args and isinstance(args[0], (str,bytes,os.PathLike)):
            path = os.path.normpath(os.fsdecode(args[0])).replace('\\','/')
            if path in ('/data','/srv/private') or path.startswith(('/data/','/srv/private/')):
                raise RuntimeError('Constructed rehearsal may not read private sources')
    sys.addaudithook(no_private_reads)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ProbeFixture)
    if suite.countTestCases() != 22: raise RuntimeError('Incomplete fixture roster')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun != 22 or not result.wasSuccessful() or result.skipped:
        raise SystemExit(21)
    import importlib.metadata as metadata
    P['write_tables'](out, {'qualification':[dict(n=P['unique_people'](PEOPLE),
        constructed_only=1,cases=result.testsRun,failures=0,errors=0,skipped=0,
        private_source_reads=0,numerical_threads=2,probe_sha256=PROBE_SHA256,
        python_version=sys.version.split()[0],numpy_version=metadata.version('numpy'),
        pandas_version=metadata.version('pandas'),pyreadstat_version=metadata.version('pyreadstat'),
        cpu_seconds=time.process_time()-cpu_started,wall_seconds=time.monotonic()-started)]})


if __name__ == '__main__':
    main(Path(sys.argv[1]) if len(sys.argv)==2 else Path('/out'))
