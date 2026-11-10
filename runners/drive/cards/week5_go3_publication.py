"""Isolated publication and module-identity adapter; no numerical changes."""
from contextlib import contextmanager
from pathlib import Path
import json
from . import week5_qualification_io as io

IDENTITY = 'PUBLICATION_IDENTITY.json'
SEAL = 'PUBLICATION_IDENTITY.seal.json'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def identity(module, sources, inputs, config):
    # Only the existing operational wall quantum may differ across reentry.
    paths = [Path(__file__), Path(io.__file__), *map(Path, sources)]
    return dict(publication_spec='GO3-UUID-1', module=module,
                sources={str(path.resolve()): io.sha(path) for path in paths},
                inputs=inputs, semantic_config={key: value for key, value in config.items() if key != 'max_wall_seconds'},
                writer='existing UUID atomic JSON with bounded Windows replace retries',
                numerical_semantics='unchanged frozen delegates')


def bind(output, module, sources, inputs, config):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    expected = identity(module, sources, inputs, config)
    path, seal = output / IDENTITY, output / SEAL
    if path.exists() or seal.exists():
        if not path.is_file() or not seal.is_file() or read(seal).get('sha256') != io.sha(path):
            raise ValueError('Unsealed publication identity is not resumable')
        if read(path) != expected:
            raise ValueError('Publication module/source/input/semantic identity changed')
    else:
        if any(item.name != 'YIELD_REQUEST.json' for item in output.iterdir()):
            raise ValueError('Unbound predecessor output cannot migrate to this publication adapter')
        io.write_json(path, expected)
        io.write_json(seal, dict(sha256=io.sha(path)))
    return expected


@contextmanager
def alias(module, name, value):
    """The one fixture's exact expected-producer identity; restored on all exits."""
    before = getattr(module, name)
    try:
        setattr(module, name, value)
        yield
    finally:
        setattr(module, name, before)


def invoke(function, output, inputs, config, *, module, sources, core, verify=False):
    output = Path(output)
    expected = bind(output, module, sources, inputs, config)
    if verify:
        bind(output / 'independent-replay', module, sources, inputs, config)
    # All frozen GO3 layers share this exact inherited core module object.
    # No estimator, array writer, supervisor or temporary-file rule is replaced.
    with io.publication([(core, 'write')]):
        result = function(output, inputs, config)
    if verify and result.get('status') != 'yielded':
        if result.get('verified') is not True:
            raise ValueError('Publication adapter cannot promote incomplete verification')
        if read(output / IDENTITY) != expected or read(output / 'independent-replay' / IDENTITY) != expected:
            raise ValueError('Independent publication identity did not replay')
        result = result | dict(publication_identity_replayed=True, publication_spec='GO3-UUID-1')
    return result


def require_complete_identity(root, *, module, sources):
    """Authenticate only the added identity; frozen consumer checks all data."""
    root = Path(root).resolve()
    done, plan, verified = (read(root / name) for name in ('COMPLETE.json', 'PLAN.json', 'VERIFIED.json'))
    if done.get('status') != 'COMPLETE' or done.get('fresh_process_verified') is not True:
        raise ValueError('Complete independently replayed publication producer required')
    if any((root / name).exists() for name in ('FAILED.json', 'PAUSED.json')):
        raise ValueError('Ambiguous publication producer terminal')
    if plan.get('module') != module or verified.get('publication_identity_replayed') is not True or verified.get('publication_spec') != 'GO3-UUID-1':
        raise ValueError('Exact qualified publication producer identity required')
    for name in ('PLAN.json', 'VERIFIED.json'):
        if done['outputs'].get(name) != io.sha(root / name):
            raise ValueError('Publication native metadata changed')
    expected = identity(module, sources, plan['inputs'], plan['config'])
    for directory in ('output', 'output/independent-replay'):
        for name in (IDENTITY, SEAL):
            relative = directory + '/' + name
            path = root / relative
            if path.is_symlink() or done['outputs'].get(relative) != io.sha(path):
                raise ValueError('Publication identity absent from complete output manifest')
        if read(root / directory / SEAL).get('sha256') != io.sha(root / directory / IDENTITY):
            raise ValueError('Publication identity seal changed')
        if read(root / directory / IDENTITY) != expected:
            raise ValueError('Complete publication source or semantic identity differs')
    return expected
