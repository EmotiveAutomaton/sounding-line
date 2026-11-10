"""Packet-allowlisted AMI/ICSI annotation archives; private, no audio.

DESIGN CHECK: source gates are outcome-independent. Size, free disk, HTTPS
origin, ZIP CRC, traversal and symlink checks must pass before schema use.
Missing/ambiguous licence or missing schema is source-unsupported, not a null.
"""
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
import hashlib,json,shutil,stat,zipfile
import requests

SOURCES={
 'AMI':'https://groups.inf.ed.ac.uk/ami/AMICorpusAnnotations/ami_public_manual_1.6.2.zip',
 'ICSI-core':'https://groups.inf.ed.ac.uk/ami/ICSICorpusAnnotations/ICSI_core_NXT.zip',
 'ICSI-plus':'https://groups.inf.ed.ac.uk/ami/ICSICorpusAnnotations/ICSI_plus_NXT.zip',
}


def download(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True);receipts=[]
    for label,url in SOURCES.items():
        path=root/(label+'.zip')
        receipt=dict(source=label,url=url,checked_at=datetime.now(timezone.utc).isoformat())
        try:
            if not path.exists():
                if shutil.disk_usage(root).free<50*1024**3:raise ValueError('Download free-disk floor')
                response=requests.get(url,headers={'User-Agent':'SoundingLine-Research/Stage15-Week5'},
                                      timeout=(20,60),stream=True)
                receipt['http_status']=response.status_code
                response.raise_for_status()
                if response.url.split('/')[2]!='groups.inf.ed.ac.uk':raise ValueError('Unexpected download origin')
                temp=path.with_suffix('.part');size=0
                with temp.open('xb') as stream:
                    for chunk in response.iter_content(1024**2):
                        size+=len(chunk)
                        if size>256*1024**2:raise ValueError('Archive exceeds 256MiB bound')
                        stream.write(chunk)
                temp.replace(path)
            payload=path.read_bytes();receipt.update(bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest())
            with zipfile.ZipFile(path) as archive:
                if sum(i.file_size for i in archive.infolist())>2*1024**3:raise ValueError('Expansion exceeds 2GiB')
                for info in archive.infolist():
                    name=PurePosixPath(info.filename.replace('\\','/'))
                    if name.is_absolute() or '..' in name.parts or ':' in info.filename or stat.S_ISLNK(info.external_attr>>16):
                        raise ValueError('Unsafe archive path or symlink')
                if archive.testzip() is not None:raise ValueError('ZIP CRC failure')
                receipt.update(members=len(archive.infolist()),expanded_bytes=sum(i.file_size for i in archive.infolist()),
                               status='retrieved_crc_verified',licence='requires packaged or official source inspection')
        except Exception as error:
            receipt.update(status='source_unavailable',error=type(error).__name__+': '+str(error))
        receipts.append(receipt)
    (root/'RETRIEVAL.json').write_text(json.dumps(receipts,indent=2)+'\n',encoding='utf8')
    return receipts


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('root',type=Path)
    print(json.dumps(download(p.parse_args().root),indent=2))
