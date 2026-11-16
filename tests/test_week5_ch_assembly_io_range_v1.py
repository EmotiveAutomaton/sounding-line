"""Constructed exactness controls for the proposed metadata I/O successor."""
import ast
import hashlib
import importlib.util
import io
from pathlib import Path
import subprocess
import pytest
from runners.drive.cards import week5_ch_assembly_io_range_v1 as assembly

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('legacy_union_controls', REPO/'tests/test_week5_ch_assembly_range_v1.py')
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)
legacy.assembly = assembly
# Execute the original collection controls against the additive implementation;
# original source files are never patched or overwritten.
for name, value in vars(legacy).items():
    if name.startswith('test_'):
        globals()[name] = value


@pytest.mark.parametrize('size', [0, 1, 1023, 65536, 65537, 131091])
def test_every_byte_matches_literal_sha256(tmp_path, size):
    content = bytes(range(256))*(size//256) + bytes(range(size%256))
    path = tmp_path/'literal.bin'
    path.write_bytes(content)
    assert assembly.file_digest(path) == hashlib.sha256(content).hexdigest()


def test_tiny_file_read_buffer_is_bounded(tmp_path, monkeypatch):
    path = tmp_path/'tiny'
    path.write_bytes(b'abc')
    sizes = []
    class Probe(io.BytesIO):
        def readinto(self, buffer):
            sizes.append(len(buffer))
            return super().readinto(buffer)
    real_open = Path.open
    monkeypatch.setattr(Path, 'open', lambda p,*a,**kw: Probe(b'abc') if p==path else real_open(p,*a,**kw))
    assert assembly.file_digest(path) == hashlib.sha256(b'abc').hexdigest()
    assert sizes and max(sizes) == 4


@pytest.mark.parametrize('content', [b'ab', b'abcd'])
def test_changed_hash_stream_size_refuses(tmp_path, monkeypatch, content):
    path = tmp_path/'changing'
    path.write_bytes(b'abc')
    real_open = Path.open
    monkeypatch.setattr(Path, 'open', lambda p,*a,**kw: io.BytesIO(content) if p==path else real_open(p,*a,**kw))
    with pytest.raises(ValueError, match='changed'):
        assembly.file_digest(path)


def test_checkpoint_callback_remains_effective(tmp_path):
    path = tmp_path/'literal'
    path.write_bytes(b'x')
    def refuse(): raise RuntimeError('constructed guard')
    with pytest.raises(RuntimeError, match='constructed guard'):
        assembly.file_digest(path, refuse)


def test_aggregate_metadata_above_twenty_MB_still_accepted(tmp_path):
    assert assembly.METADATA_CAP == 256*1024**2
    path = tmp_path/'large-aggregate.json'
    with path.open('wb') as stream:
        stream.write(b' '*20_123_239)
        stream.write(b'{"constructed":true}')
    assert assembly.read(path) == {'constructed': True}


def test_unit_metadata_limit_remains_separate(tmp_path, monkeypatch):
    path = tmp_path/'unit.json'
    path.write_bytes(b'{"x":1}')
    monkeypatch.setattr(assembly, 'UNIT_METADATA_CAP', 6)
    with pytest.raises(ValueError, match='Queue metadata exceeds'):
        assembly.read_unit(path)
    assert assembly.read(path) == {'x': 1}


def test_complete_literal_inventory_and_no_outside_junction(tmp_path):
    root, outside = tmp_path/'root', tmp_path/'outside'
    root.mkdir(); outside.mkdir()
    for index in range(256):
        (root/f'{index:03}.json').write_text('{"literal":'+str(index)+'}', 'utf8')
    expected = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir()}
    assert assembly._file_inventory(root, lambda: None) == expected
    (outside/'escape').write_bytes(b'outside')
    junction = root/'junction'
    subprocess.run(['cmd', '/c', 'mklink', '/J', str(junction), str(outside)],
                   check=True, capture_output=True, timeout=10)
    # The exact path resolution used for each file must reject the external
    # target. No external directory target is cached or treated as internal.
    with pytest.raises(ValueError, match='escaped'):
        assembly._inside(root.resolve(), 'junction/escape')
    # Windows pathlib may enumerate junction contents; when it does, the full
    # inventory must reject. If it does not recurse, the outside file is absent.
    try:
        result = assembly._file_inventory(root, lambda: None)
    except ValueError as exc:
        assert 'escaped' in str(exc)
    else:
        assert result == expected


def test_original_unit_validation_predicates_preserved():
    old = ast.parse((REPO/'runners/drive/cards/week5_ch_queue_backhalf_v1.py').read_text('utf8'))
    new = ast.parse(Path(assembly.__file__).read_text('utf8'))
    original = next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=='check_unit')
    candidate = next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='check_unit_bounded')
    class Normalize(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            node.name='check_unit'
            return self.generic_visit(node)
        def visit_Name(self, node):
            if node.id=='read_unit': node.id='read'
            return node
        def visit_Attribute(self, node):
            if isinstance(node.value,ast.Name) and (node.value.id,node.attr) in [('queue','unit_files'),('ck','file_digest')]:
                return ast.copy_location(ast.Name(id=node.attr,ctx=node.ctx),node)
            return self.generic_visit(node)
    assert ast.dump(Normalize().visit(original),include_attributes=False) == ast.dump(Normalize().visit(candidate),include_attributes=False)


def test_worker_pin_change_after_unit_traversal_refuses(tmp_path, monkeypatch):
    inputs, config, _, _ = legacy.world(tmp_path, monkeypatch)
    old = assembly.queue.worker_pins
    initial = old()
    calls = [0]
    def changing():
        calls[0] += 1
        return initial if calls[0] == 1 else dict(initial, changed='not-a-pin')
    monkeypatch.setattr(assembly.queue, 'worker_pins', changing)
    with pytest.raises(ValueError, match='Frozen worker source changed'):
        assembly.calculate(inputs, config)
