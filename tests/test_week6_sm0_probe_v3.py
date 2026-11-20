import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from runners.drive.cards import week6_sm0_probe_v3 as p
from runners.drive.cards.week6_sealed_support_v1 import SealedFailure


class JoinedExitProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base/'source'; self.root.mkdir()
        self.out = self.base/'out'; self.out.mkdir()
        self.mapping = dict(schema_version=1, source_alias='midus-m2-joined',
            tables=[dict(path='a.csv', person_column='M2ID', role='daily')])

    def table(self, name='a.csv', people=12, repeat=1):
        path = self.root/name; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('M2ID,B2DDAY\n'+''.join(f'p{i},1\n'*repeat for i in range(people))+' ,1\n', encoding='utf8')
        return path

    def code(self, category, **kw):
        self.assertEqual(p.exit_code(self.root, self.out, self.mapping, **kw), p.ERROR_CODES[category])
        self.assertEqual(list(self.out.iterdir()), [])

    def status(self):
        with (self.out/'status.csv').open(newline='', encoding='utf8') as stream:
            return list(csv.DictReader(stream))

    def test_catalog_unique_documented_and_in_requested_range(self):
        codes = list(p.ERROR_CODES.values())
        self.assertEqual(len(codes), len(set(codes)))
        self.assertTrue(all(10 <= c <= 119 for c in codes))
        text = Path('docs/design/stage-15/week6/SM0_JOINED_RECOVERY_V2.md').read_text('utf8')
        for name, code in p.ERROR_CODES.items():
            self.assertIn(f'| {code} | `{name}` |', text)

    def test_all_mapping_errors_are_distinct_and_prevent_reads(self):
        self.table()
        changes = [({}, 'mapping_schema'),
            ({**self.mapping, 'source_alias':'midus'}, 'joined_alias'),
            ({**self.mapping, 'tables':[]}, 'table_roster'),
            ({**self.mapping, 'tables':[{}]}, 'table_declaration')]
        for field, value, category in [('path','C:\\a.csv','nonportable_path'),
                ('path','../a.csv','unsupported_or_escaping_path'),
                ('person_column','WRONG','unreviewed_key_or_role')]:
            changes.append(({**self.mapping,'tables':[{**self.mapping['tables'][0],field:value}]},category))
        changes.append(({**self.mapping,'tables':self.mapping['tables']*2},'duplicate_path'))
        with patch.object(p, 'inspect_table') as reader:
            for mapping, category in changes:
                with self.subTest(category=category):
                    self.assertEqual(p.exit_code(self.root,self.out,mapping),p.ERROR_CODES[category])
            reader.assert_not_called()

    def test_empty_source(self): self.code('empty_source')

    def test_archive_only(self):
        (self.root/'a.zip').write_bytes(b'constructed')
        self.code('archive_only')

    def test_no_supported_tables(self):
        (self.root/'README.txt').write_text('constructed')
        self.code('no_supported_table')

    def test_unavailable_source(self):
        self.root.rmdir(); self.code('source_unavailable')

    def test_listing_error_stops_reader(self):
        original = os.scandir
        def source_error(path):
            if Path(path) == self.root: raise PermissionError('private path')
            return original(path)
        with patch('runners.drive.cards.week6_sm0_probe_v2.os.scandir', side_effect=source_error), patch.object(p,'inspect_table') as reader:
            self.code('listing_error'); reader.assert_not_called()

    def test_listing_limit_stops_reader(self):
        self.table(); self.table('b.csv')
        with patch.object(p,'inspect_table') as reader:
            self.code('listing_limit', max_entries=1); reader.assert_not_called()

    def test_missing_mapped_file(self):
        self.table('not-mapped.csv'); self.code('mapped_file_missing')

    def test_real_distinct_counts_in_both_gate_tables(self):
        self.table(people=12, repeat=3)
        result = p.run(self.root,self.out,self.mapping)
        self.assertFalse(result['source_admitted'])
        self.assertFalse(result['metadata_channel_required'])
        self.assertEqual({x.name for x in self.out.iterdir()}, {'structure.csv','status.csv'})
        for file in self.out.iterdir():
            with file.open(newline='') as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0]['n'],'12')
        self.assertEqual(self.status()[0]['disposition'],'mapped_tables_loaded')
        self.assertLessEqual(sum(x.stat().st_size for x in self.out.iterdir()),262144)

    def test_partial_load_has_real_count_and_fixed_error_flag(self):
        self.table()
        (self.root/'bad.csv').write_text('NO_KEY\n1\n')
        self.mapping['tables'].append(dict(path='bad.csv', person_column='M2ID',role='survey'))
        p.run(self.root,self.out,self.mapping)
        row = self.status()[0]
        self.assertEqual((row['n'],row['loaded_tables'],row['failed_tables']),('12','1','1'))
        self.assertEqual(row['disposition'],'partial')
        self.assertEqual(row['error_person_field_absent'],'1')

    def test_all_small_populations_return_code_without_padding(self):
        self.table(people=10,repeat=10)
        self.code('all_loaded_populations_below_floor')

    def test_mixed_populations_keep_each_actual_count(self):
        for name, n in [('a.csv',11),('b.csv',19),('small.csv',10)]: self.table(name,people=n)
        self.mapping['tables']=[dict(path=name,person_column='M2ID',role='survey') for name in ('a.csv','b.csv','small.csv')]
        p.run(self.root,self.out,self.mapping)
        rows = self.status()
        self.assertEqual([int(row['n']) for row in rows],[11,19])
        self.assertEqual([row['table'] for row in rows],['table_001','table_002'])
        self.assertTrue(all(row['suppressed_tables']=='1' for row in rows))

    def test_read_allowance_code(self):
        self.table(); self.code('read_limit',max_read_bytes=1)

    def test_fixed_reader_failure_categories(self):
        self.table()
        errors=[(SealedFailure(12,message),category) for message,category in p.READER_ERRORS.items()]
        errors += [(OSError('sensitive'),'source_io'),(UnicodeError('sensitive'),'source_encoding'),
            (ValueError('sensitive'),'reader_value'),(csv.Error('sensitive'),'reader_csv'),
            (RuntimeError('sensitive'),'unclassified_reader'),(SealedFailure(99,'sensitive'),'other_reader_refusal')]
        for error,category in errors:
            with self.subTest(category=category),patch.object(p,'inspect_table',side_effect=error):
                self.code(category)

    def test_actual_process_returns_only_fixed_exit(self):
        command = 'from runners.drive.cards.week6_sm0_probe_v3 import exit_code;raise SystemExit(exit_code('+repr(str(self.root))+','+repr(str(self.out))+','+repr(self.mapping)+'))'
        done = subprocess.run([sys.executable,'-X','utf8','-B','-c',command],capture_output=True,text=True)
        self.assertEqual(done.returncode,p.ERROR_CODES['empty_source'])
        self.assertEqual(done.stdout,''); self.assertEqual(done.stderr,'')

    def test_destination_refusals_preserve_existing_evidence(self):
        saved=self.out/'saved.csv';saved.write_bytes(b'keep')
        self.assertEqual(p.exit_code(self.root,self.out,self.mapping),p.ERROR_CODES['output_not_fresh'])
        self.assertEqual(saved.read_bytes(),b'keep')
        inside=self.root/'out';inside.mkdir()
        self.assertEqual(p.exit_code(self.root,inside,self.mapping),p.ERROR_CODES['output_inside_source'])
        self.assertEqual(p.exit_code(self.root,self.base/'absent',self.mapping),p.ERROR_CODES['output_unavailable'])

    def test_bounds_are_not_silently_relaxed(self):
        for kw in ({'max_entries':True},{'max_entries':100001},{'max_read_bytes':2_000_000_001}):
            with self.subTest(kw=kw): self.code('invalid_bounds',**kw)

    def test_status_schema_and_output_writer_fail_closed(self):
        self.table()
        with patch.object(p,'status_payload',side_effect=ValueError('private')):self.code('status_schema')
        with patch.object(p,'write_tables',side_effect=SealedFailure(14,'private')):self.code('output_refusal')

    def test_unexpected_failure_returns_no_exception_text(self):
        with patch.object(p,'inventory',side_effect=RuntimeError('sensitive')):self.code('internal_failure')

    def test_multiple_failures_choose_lowest_fixed_code(self):
        self.table(people=5)
        self.mapping['tables'].append(dict(path='absent.csv',person_column='M2ID',role='daily'))
        self.code('mapped_file_missing')

    def test_no_source_names_or_error_text_in_partial_output(self):
        self.table('sensitive-name.csv')
        self.table('good.csv')
        self.mapping['tables']=[dict(path=name,person_column='M2ID',role='daily') for name in ('sensitive-name.csv','good.csv')]
        reader=p.inspect_table
        def fail_one(path,budget):
            if path.name=='sensitive-name.csv':raise RuntimeError('PRIVATE-DETAIL')
            return reader(path,budget)
        with patch.object(p,'inspect_table',side_effect=fail_one):p.run(self.root,self.out,self.mapping)
        text=''.join(x.read_text() for x in self.out.iterdir())
        for value in ('sensitive-name','good.csv','PRIVATE-DETAIL',str(self.root),'p11'):
            self.assertNotIn(value,text)


if __name__ == '__main__': unittest.main()
