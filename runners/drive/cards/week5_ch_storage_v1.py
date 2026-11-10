"""Explicit lossless CH history storage; never a replacement for source replay.

DESIGN CHECK: CH_CENSUS_STORAGE_V1.md. Only the existing histories.payload
string is encoded. Schemas, primary keys, all other values and row order stay
unchanged. Unadapted readers must not be used with this marked representation.
This module does nothing until an explicitly admitted handler calls it.
"""
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
import hashlib
import re
import shutil
import sqlite3
import struct
import zlib

MAGIC = b'SLCHZ1\x00'
APPLICATION_ID = 0x534C4331
MAX_PAYLOAD_BYTES = 64 * 1024**2
DISK_FLOOR_BYTES = 20 * 1024**3
INSERT = re.compile(r'^\s*INSERT\s+(?:OR\s+(?:IGNORE|REPLACE)\s+)?INTO\s+(?:main\.)?histories\s+VALUES\s*\(\s*\?\s*,\s*\?\s*,\s*\?\s*\)\s*;?\s*$', re.I)
WRITE = re.compile(r'^\s*(?:INSERT|REPLACE|UPDATE|DELETE|ATTACH)\b', re.I)


def encode(value):
    if not isinstance(value, str):
        raise ValueError('History payload must be the original text value')
    raw = value.encode('utf8')
    if len(raw) > MAX_PAYLOAD_BYTES:
        raise ValueError('History exceeds reviewed indivisible payload memory bound')
    packed = MAGIC + struct.pack('>Q', len(raw)) + hashlib.sha256(raw).digest() + zlib.compress(raw, 1)
    # Tiny/incompressible values remain ordinary TEXT, with exact bytes.
    return packed if len(packed) < len(raw) else value


def decode(value):
    if isinstance(value, str):
        return value
    if not isinstance(value, bytes) or not value.startswith(MAGIC):
        raise ValueError('Unrecognized history payload representation')
    offset = len(MAGIC)
    if len(value) < offset + 40:
        raise ValueError('Truncated history storage envelope')
    length = struct.unpack('>Q', value[offset:offset+8])[0]
    if length > MAX_PAYLOAD_BYTES:
        raise ValueError('History envelope exceeds reviewed memory bound')
    expected = value[offset+8:offset+40]
    inflater = zlib.decompressobj()
    raw = inflater.decompress(value[offset+40:], length+1)
    if (len(raw) != length or not inflater.eof or inflater.unused_data
            or inflater.unconsumed_tail or hashlib.sha256(raw).digest() != expected):
        raise ValueError('History envelope length/checksum/stream differs')
    return raw.decode('utf8')


def row_factory(cursor, row):
    return tuple(decode(value) if column[0] == 'payload' and isinstance(value, bytes) else value
                 for column, value in zip(cursor.description, row))


def parameters(sql, values):
    if INSERT.fullmatch(sql):
        if len(values) != 3:
            raise ValueError('History insert arity differs')
        return (values[0], values[1], encode(values[2]))
    if WRITE.match(sql) and (re.search(r'\bhistories\b', sql, re.I) or re.match(r'^\s*ATTACH\b', sql, re.I)):
        raise ValueError('Unreviewed physical history mutation/attachment')
    return values


class Cursor(sqlite3.Cursor):
    def execute(self, sql, values=()):
        self.connection.storage_guard()
        return super().execute(sql, parameters(sql, values))

    def executemany(self, sql, rows):
        def bounded():
            for values in rows:
                self.connection.storage_guard()
                yield parameters(sql, values)
        return super().executemany(sql, bounded())


class Connection(sqlite3.Connection):
    def cursor(self, factory=Cursor):
        if factory is not Cursor:
            raise ValueError('Custom storage cursor is not qualified')
        return super().cursor(factory)

    def execute(self, sql, parameters=()):
        return self.cursor().execute(sql, parameters)

    def executemany(self, sql, parameters):
        return self.cursor().executemany(sql, parameters)

    def executescript(self, script):
        # Current frozen CH schema scripts contain only PRAGMA/CREATE. A future
        # payload-bearing script must not silently bypass the encoding path.
        if re.search(r'\b(?:INSERT|UPDATE|DELETE|REPLACE|ATTACH)\b', script, re.I):
            raise ValueError('Unreviewed mutating storage script')
        self.storage_guard(force=True)
        return super().executescript(script)

    def storage_guard(self, force=False):
        self._storage_operations += 1
        if self._storage_writable and (force or self._storage_operations % 100 == 0):
            if shutil.disk_usage(self._storage_path.parent).free < DISK_FLOOR_BYTES:
                raise OSError('CH storage disk floor reached; retained transaction must be recovered')

    def commit(self):
        self.storage_guard(force=True)
        return super().commit()


def connect(path, *, writable=False):
    path = Path(path).resolve()
    existed = path.exists()
    if not writable and not existed:
        raise FileNotFoundError(path)
    if writable:
        path.parent.mkdir(parents=True, exist_ok=True)
    uri = path.as_uri() + ('?mode=rwc' if writable else '?mode=ro&immutable=1')
    con = sqlite3.connect(uri, uri=True, factory=Connection)
    con._storage_path = path
    con._storage_writable = writable
    con._storage_operations = 0
    con.row_factory = row_factory
    try:
        marker = con.execute('PRAGMA application_id').fetchone()[0]
        if marker not in (0, APPLICATION_ID):
            raise ValueError('Unknown SQLite storage application identity')
        if writable and existed and marker != APPLICATION_ID:
            raise ValueError('Never mutate an original uncompressed database; convert to a new file')
        if writable and not existed:
            con.execute('PRAGMA application_id='+str(APPLICATION_ID))
            con.execute('PRAGMA journal_mode=WAL')
            con.execute('PRAGMA synchronous=FULL')
            con.commit()
        if not writable and (Path(str(path)+'-wal').exists() or Path(str(path)+'-shm').exists()):
            raise ValueError('Read-only input must be a sealed standalone checkpoint')
        return con
    except BaseException:
        con.close()
        raise


@contextmanager
def bridge(modules, output, input_paths):
    """Patch named modules' sqlite namespace only, in this single native child.

    No global sqlite3 mutation, source edit, SQL function or implicit codec is
    installed. All external inputs are exact allowlisted read-only paths. Every
    writable database must be inside this attempt's output tree.
    """
    output = Path(output).resolve()
    inputs = {Path(p).resolve() for p in input_paths}
    previous = []

    def bounded_connect(path, *args, **kwargs):
        if args or kwargs:
            raise ValueError('Unreviewed SQLite connection options')
        target = Path(path).resolve()
        if target in inputs:
            return connect(target)
        if not target.is_relative_to(output):
            raise ValueError('Database is outside explicit storage scope')
        return connect(target, writable=True)

    facade = SimpleNamespace(**{name:getattr(sqlite3, name) for name in dir(sqlite3)
                               if not name.startswith('__')})
    facade.connect = bounded_connect
    try:
        for module in modules:
            if any(module is prior[0] for prior in previous):
                continue
            if getattr(module, 'sqlite3', None) is not sqlite3:
                raise ValueError('Nested or changed SQLite integration is not qualified')
            previous.append((module, module.sqlite3))
            module.sqlite3 = facade
        yield
    finally:
        for module, original in reversed(previous):
            module.sqlite3 = original


def compare(left_path, right_path, tables, check=None):
    left = connect(left_path)
    right = connect(right_path)
    counts = {}
    try:
        for table in tables:
            if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', table):
                raise ValueError('Invalid reviewed table')
            schema = left.execute('PRAGMA table_info('+table+')').fetchall()
            if not schema or schema != right.execute('PRAGMA table_info('+table+')').fetchall():
                raise ValueError('Logical schema differs: '+table)
            keys = [r[1] for r in sorted(schema, key=lambda r:r[5]) if r[5]]
            if not keys:
                raise ValueError('Exact comparison requires declared unique row identity')
            query = 'SELECT * FROM '+table+' ORDER BY '+','.join(keys)
            a, b = left.execute(query), right.execute(query)
            counts[table] = 0
            while True:
                if check is not None:
                    check()
                x, y = a.fetchmany(1), b.fetchmany(1)
                if x != y:
                    raise ValueError('Independent logical database differs: '+table)
                if not x:
                    break
                counts[table] += len(x)
    finally:
        left.close()
        right.close()
    return counts
