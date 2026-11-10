"""GO3 source successor: authenticated extraction before XML projection.

DESIGN CHECK: incomplete or changed extracted files refuse before parsing.
The archive, source columns, labels, joins and full-row replay stay unchanged.
"""
from pathlib import Path
from types import FunctionType
import json,shutil,zlib
from . import week5_go_revisions as original

TARGETS=('Posts.xml','PostHistory.xml')


def member_crc(path):
    value=0
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):value=zlib.crc32(block,value)
    return value & 0xffffffff


def extract(archive,directory):
    import py7zr
    archive=Path(archive);directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    archive_sha=original.core.sha(archive);seal=directory/'EXTRACTION.json'
    with py7zr.SevenZipFile(archive,'r') as container:
        listed=container.list();metadata={}
        for name in TARGETS:
            matches=[m for m in listed if m.filename==name]
            if len(matches)!=1:raise ValueError('Unique expected XML archive members required')
            member=matches[0]
            if member.is_directory or not isinstance(member.uncompressed,int) or member.uncompressed<0 or not isinstance(member.crc32,int):
                raise ValueError('Explicit XML member size and CRC required')
            metadata[name]={'size':member.uncompressed,'crc32':member.crc32}
        bound={'archive_sha256':archive_sha,'metadata':metadata}
        if seal.exists():
            saved=json.loads(seal.read_text('utf8'))
            if saved.get('binding')!=bound or set(saved.get('sha256',{}))!=set(TARGETS):raise ValueError('Extraction provenance binding differs')
            for name in TARGETS:
                path=directory/name
                if not path.is_file() or path.is_symlink():raise ValueError('Sealed XML member missing or redirected')
                if path.stat().st_size!=metadata[name]['size'] or original.core.sha(path)!=saved['sha256'][name]:
                    raise ValueError('Sealed XML member bytes changed')
            return saved['sha256']
        if any((directory/name).exists() for name in TARGETS):
            raise ValueError('Unsealed extracted members retained; use a fresh immutable attempt')
        expanded=sum(m['size'] for m in metadata.values())
        if expanded+10*1024**3>shutil.disk_usage(directory).free:raise ValueError('insufficient extraction headroom')
        container.extract(path=directory,targets=list(TARGETS))
    hashes={}
    for name in TARGETS:
        path=directory/name
        if not path.is_file() or path.is_symlink():raise ValueError('Decoded XML member missing or redirected')
        path.resolve().relative_to(directory.resolve())
        if path.stat().st_size!=metadata[name]['size'] or member_crc(path)!=metadata[name]['crc32']:
            raise ValueError('Decoded XML member size or CRC differs from pinned archive')
        hashes[name]=original.core.sha(path)
    original.core.write(seal,dict(binding=bound,sha256=hashes))
    return hashes


project_site=FunctionType(original.project_site.__code__,dict(original.project_site.__globals__,extract=extract),
                         original.project_site.__name__,original.project_site.__defaults__,original.project_site.__closure__)
execute=FunctionType(original.execute.__code__,dict(original.execute.__globals__,project_site=project_site),
                    original.execute.__name__,original.execute.__defaults__,original.execute.__closure__)
verify=FunctionType(original.verify.__code__,dict(original.verify.__globals__,project_site=project_site),
                   original.verify.__name__,original.verify.__defaults__,original.verify.__closure__)
