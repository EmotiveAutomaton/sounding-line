"""Constructed metadata fixtures only; no source data or NAS is required."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

MODULE = Path(__file__).parents[1] / 'tools/external_data_store.py'
spec = importlib.util.spec_from_file_location('external_data_store', MODULE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class TestExternalDataStore(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / '_registry').mkdir()
        (self.root / 'open/example/raw').mkdir(parents=True)
        self.row = dict(slug='example', title='Constructed example',
                        **{'class':'open-clean'}, status='held', bytes=0, files=0,
                        path='open/example', source='open/example/SOURCE.json')
        self.write([self.row])
        (self.root/'open/example/SOURCE.json').write_text(
            json.dumps({'slug':'example','class':'open-clean','notes':'DO_NOT_EMIT'}),encoding='utf8')

    def write(self, rows, version=1):
        (self.root/'_registry/REGISTRY.json').write_text(
            json.dumps({'schema_version':version,'sources':rows}),encoding='utf8')

    def test_reads_metadata_without_opening_raw(self):
        (self.root/'open/example/raw/never-read.json').write_text('invalid data sentinel',encoding='utf8')
        store=module.DataStore(self.root)
        self.assertEqual(store.source_directory('example'),self.root/'open/example')
        self.assertEqual(store.manifest('example')['slug'],'example')
        self.assertNotIn('DO_NOT_EMIT',json.dumps(store.inventory()))

    def test_traversal_refused(self):
        self.write([dict(self.row,path='../escape')])
        with self.assertRaises(ValueError): module.DataStore(self.root)

    def test_windows_absolute_paths_refused(self):
        for value in ['C:\\escape',r'\\server\share\escape','/escape','C:relative']:
            self.write([dict(self.row,path=value)])
            with self.assertRaises(ValueError): module.DataStore(self.root)

    def test_duplicate_slug_refused(self):
        self.write([self.row,self.row])
        with self.assertRaises(ValueError): module.DataStore(self.root)

    def test_manifest_outside_source_refused(self):
        self.write([dict(self.row,source='open/other/SOURCE.json')])
        with self.assertRaises(ValueError): module.DataStore(self.root)

    def test_manifest_class_mismatch_refused(self):
        (self.root/'open/example/SOURCE.json').write_text('{"slug":"example","class":"private"}',encoding='utf8')
        with self.assertRaises(ValueError): module.DataStore(self.root).manifest('example')

    def test_unknown_schema_refused(self):
        self.write([self.row],version=99)
        with self.assertRaises(ValueError): module.DataStore(self.root)

    def test_environment_is_explicit(self):
        with patch.dict(os.environ,{'SOUNDING_LINE_DATA_ROOT':str(self.root)}):
            self.assertEqual(module.DataStore.from_environment().root,self.root)
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(ValueError): module.DataStore.from_environment()

    def test_nested_inventory_values_refused(self):
        for field in ('title', 'status', 'bytes', 'files'):
            self.write([dict(self.row, **{field: {'unexpected': 'synthetic sentinel'}})])
            with self.assertRaises(ValueError): module.DataStore(self.root)

    def test_private_class_cannot_point_to_open_folder(self):
        self.write([dict(self.row, **{'class': 'private'})])
        with self.assertRaises(ValueError): module.DataStore(self.root)

    def test_negative_and_boolean_counts_refused(self):
        for value in (-1, True, 1.5, '2'):
            self.write([dict(self.row, bytes=value)])
            with self.assertRaises(ValueError): module.DataStore(self.root)

    def test_duplicate_json_keys_refused(self):
        (self.root/'_registry/REGISTRY.json').write_text(
            '{"schema_version":1,"sources":[],"sources":[]}', encoding='utf8')
        with self.assertRaises(ValueError): module.DataStore(self.root)

    def test_windows_stream_and_trailing_alias_refused(self):
        for value in ('open/example:stream', 'open/example.', 'open/example '):
            self.write([dict(self.row, path=value)])
            with self.assertRaises(ValueError): module.DataStore(self.root)

    def test_symlink_escape_refused(self):
        with tempfile.TemporaryDirectory() as outside:
            link = self.root/'escape'
            try: link.symlink_to(outside, target_is_directory=True)
            except OSError: self.skipTest('Symlink creation unavailable')
            self.write([dict(self.row, path='escape')])
            with self.assertRaises(ValueError): module.DataStore(self.root)

    def test_metadata_read_is_bounded(self):
        with patch.object(module.Path, 'open', return_value=__import__('io').BytesIO(b' ' * (16*1024**2+1))):
            with self.assertRaisesRegex(ValueError, 'Oversized'): module.DataStore(self.root)

if __name__=='__main__': unittest.main()
