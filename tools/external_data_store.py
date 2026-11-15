"""Read an external collection registry without loading participant data.

Set SOUNDING_LINE_DATA_ROOT in the owner's local environment. This module never
downloads, admits an analysis, moves data, or selects an experiment population.

DESIGN CHECK: LESSONS section 2 (source roster versus admitted population) and
section 5's immutable-dependency and real-path checks informed this metadata
adapter. Valid constructed registry/manifests must resolve inside their declared
handling folder; malformed fields, class/path disagreement, duplicate keys and
escaping paths must refuse. These are integrity checks, not scientific gates.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re

class DataStore:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve(strict=True)
        registry = self._read_json(self._under('_registry/REGISTRY.json'))
        if registry.get('schema_version') != 1 or not isinstance(registry.get('sources'), list):
            raise ValueError('Unsupported registry schema')
        self.sources = {}
        for row in registry['sources']:
            if not isinstance(row, dict): raise ValueError('Invalid registry row')
            slug = row.get('slug', '')
            if not isinstance(slug, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,127}', slug) or slug in self.sources:
                raise ValueError('Invalid or duplicate source slug')
            if row.get('class') not in ('open-clean', 'open-tests-only', 'private'):
                raise ValueError('Invalid handling class')
            for field in ('title', 'status'):
                value = row.get(field)
                if not isinstance(value, str) or not value or len(value) > 512 or any(ord(c) < 32 for c in value):
                    raise ValueError('Invalid inventory text field')
            for field in ('bytes', 'files'):
                if type(row.get(field)) is not int or row[field] < 0:
                    raise ValueError('Invalid inventory count')
            folder = self._under(row['path'])
            prefix = 'private' if row['class'] == 'private' else 'open'
            if folder != self.root / prefix / slug:
                raise ValueError('Source folder does not match its handling class and slug')
            manifest = self._under(row['source'])
            if manifest.parent != folder or manifest.name != 'SOURCE.json':
                raise ValueError('Manifest is outside its source folder')
            self.sources[slug] = dict(row)

    @classmethod
    def from_environment(cls) -> 'DataStore':
        value = os.environ.get('SOUNDING_LINE_DATA_ROOT')
        if not value: raise ValueError('Set SOUNDING_LINE_DATA_ROOT to the collection directory')
        return cls(value)

    def _under(self, relative: str) -> Path:
        if not isinstance(relative, str) or not relative:
            raise ValueError('Expected a relative collection path')
        posix = PurePosixPath(relative.replace('\\', '/'))
        windows = PureWindowsPath(relative)
        if (posix.is_absolute() or windows.is_absolute() or windows.drive or '..' in posix.parts
                or ':' in relative or any(ord(c) < 32 for c in relative)
                or any(part.endswith((' ', '.')) for part in posix.parts)):
            raise ValueError('Unsafe collection path')
        path = (self.root / Path(*posix.parts)).resolve()
        if not path.is_relative_to(self.root): raise ValueError('Collection path escapes root')
        return path

    @staticmethod
    def _read_json(path: Path) -> dict:
        limit = 16 * 1024**2
        with path.open('rb') as f: data = f.read(limit + 1)
        if len(data) > limit: raise ValueError('Oversized metadata file')
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result: raise ValueError('Duplicate metadata key')
                result[key] = value
            return result
        value = json.loads(data.decode('utf8'), object_pairs_hook=unique)
        if not isinstance(value, dict): raise ValueError('Expected metadata object')
        return value

    def source_directory(self, slug: str) -> Path:
        return self._under(self.sources[slug]['path'])

    def manifest(self, slug: str) -> dict:
        source = self._read_json(self._under(self.sources[slug]['source']))
        if source.get('slug') != slug or source.get('class') != self.sources[slug]['class']:
            raise ValueError('Registry and source manifest disagree')
        return source

    def inventory(self) -> list[dict]:
        # Fixed metadata allowlist: never emit notes, examples, keys or raw rows.
        fields = ('slug', 'title', 'class', 'status', 'bytes', 'files', 'path')
        return [{k: row.get(k) for k in fields} for row in self.sources.values()]

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', help='Explicit collection root; otherwise use environment')
    args = parser.parse_args()
    store = DataStore(args.root) if args.root else DataStore.from_environment()
    print(json.dumps(store.inventory(), indent=2, ensure_ascii=False))

if __name__ == '__main__': main()
