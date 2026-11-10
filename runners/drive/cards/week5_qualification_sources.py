"""Counted construction and independent replay of fixed SP3/MD3 fixture inputs.

No human source, empirical outcome, fit, optimization or data-selected scope
enters preparation. The immutable original constructors define every world.
"""
from pathlib import Path
import json
import numpy as np
import pyarrow.parquet as pq
from . import week5_sp3_ic_fixture as sp
from . import week5_md3_followup_fixture as md
from . import week5_qualification_io as publication


def execute(output, inputs, config):
    if inputs or set(config) != {'phase', 'family'} or config['phase'] != 'prepare' or config['family'] not in ('SP', 'MD'):
        raise ValueError('Exact fixed fixture-source construction contract required')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    destination = output / 'inputs'
    if config['family'] == 'SP':
        with publication.publication([(sp.parent, 'write')]):
            sp.prepare(destination)
        expected_cases = ['exact', 'high-noise']
        module = sp
    else:
        with publication.publication([(md.study.core, 'save_json')]):
            md.prepare(destination)
        expected_cases = [card + '-' + case for card, cases in md.CASES.items() for case in cases]
        module = md
    metadata = {path.stem: json.loads(path.read_text('utf8')) for path in destination.glob('*.json')}
    if set(metadata) != set(expected_cases) or any(value.get('constructed_only') is not True for value in metadata.values()):
        raise ValueError('Complete fixed constructed case roster differs')
    result = dict(constructed_only=True, source_only=True, family=config['family'], cases=expected_cases,
                  constructor_sha256=publication.sha(module.__file__), io_sha256=publication.sha(publication.__file__),
                  files={path.relative_to(output).as_posix(): publication.sha(path) for path in destination.rglob('*') if path.is_file()})
    publication.write_json(output / 'SOURCE.json', result)
    return result


def verify(output, inputs, config):
    output = Path(output)
    actual = execute(output / 'independent-replay', inputs, config)
    expected = json.loads((output / 'SOURCE.json').read_text('utf8'))
    if {k: v for k, v in actual.items() if k != 'files'} != {k: v for k, v in expected.items() if k != 'files'} or set(actual['files']) != set(expected['files']):
        raise ValueError('Complete constructed source declaration differs')
    for name, digest in expected['files'].items():
        a, b = output / name, output / 'independent-replay' / name
        if publication.sha(a) != digest or publication.sha(b) != actual['files'][name]:
            raise ValueError('Constructed source file changed')
        if a.suffix == '.npz':
            with np.load(a, allow_pickle=False) as left, np.load(b, allow_pickle=False) as right:
                if set(left.files) != set(right.files) or any(not np.array_equal(left[key], right[key], equal_nan=True) for key in left.files):
                    raise ValueError('Every complete constructed trajectory must replay')
        elif a.suffix == '.parquet':
            if not pq.read_table(a).equals(pq.read_table(b)):
                raise ValueError('Every constructed thermal source row must replay')
        elif a.suffix == '.json':
            left, right = json.loads(a.read_text('utf8')), json.loads(b.read_text('utf8'))
            for key in ('source_sha256', 'sha256'):
                left.pop(key, None)
                right.pop(key, None)
            if left != right:
                raise ValueError('Constructed source case/expectation differs')
    return dict(verified=True, constructed_only=True, complete_fixture_sources_independently_replayed=True)
