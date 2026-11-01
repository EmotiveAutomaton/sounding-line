"""Lossless JSON storage for V4.c references; scientific bytes remain canonical.

DESIGN CHECK: LESSONS 3-5 reread 2026-10-30. Null and alternative both retain
every byte and original digest. Corruption, ambiguous representations, changed
immutable values and I/O errors refuse. No scoring or data selection occurs.
"""
from pathlib import Path
import lzma,hashlib,json,os,re,time,uuid
from runners.stage14 import common


def reference(path):
    path=Path(path)
    return path.parent.parent.name=='worlds' and re.fullmatch(r'null-[0-9]{3}\.json',path.name) is not None


def raw(path):
    path=Path(path);packed=Path(str(path)+'.xz')
    if reference(path) and packed.exists():
        if path.exists():raise ValueError('Ambiguous plain and compressed reference')
        return lzma.decompress(packed.read_bytes())
    return path.read_bytes()


def read(path):return json.loads(raw(path).decode('utf8'))


def logical_hash(path):return hashlib.sha256(raw(path)).hexdigest()


def retain_bytes(path,data):
    path=Path(path)
    if not reference(path):raise ValueError('Only full reference JSON is compressed')
    packed=Path(str(path)+'.xz')
    if path.exists():raise ValueError('Unexpected plain reference in compressed root')
    if packed.exists():
        if raw(path)!=data:raise ValueError('Immutable compressed reference changed')
        return
    path.parent.mkdir(parents=True,exist_ok=True)
    encoded=lzma.compress(data,preset=3)
    if lzma.decompress(encoded)!=data:raise ValueError('Compression changed bytes')
    # Match the validated v6 supervisor's exact atomic temporary-name contract.
    temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    temp.write_bytes(encoded)
    for attempt in range(51):
        try:os.replace(temp,packed);break
        except PermissionError:
            if attempt==50:raise
            time.sleep(.1)
    if raw(path)!=data:raise ValueError('Retained compression differs')


def freeze(path,value):
    if reference(path):
        retain_bytes(path,(common.canonical(value)+'\n').encode('utf8'))
        return value
    return common.freeze(path,value)
