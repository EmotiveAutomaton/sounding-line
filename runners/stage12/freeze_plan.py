"""Versioned, manually enumerated next units for the existing queue.

DESIGN CHECK: LESSONS 3-5. NULL: frozen declarations are immutable. ALTERNATIVE:
source drift, repeated namespace or missing executable handler fails before
dispatch. This freezes operator-authored cards; it never generates research.
"""
from pathlib import Path
from .common import REPO,RAW,read,freeze,pin,filehash
from .prepare import source_files
from .worker import handler


def build(version,cards,queue_directory,raw=RAW):
    raw=Path(raw);pins=pin(source_files());capsule=raw/('source-'+version)
    if (raw/('PLAN-'+version+'.json')).exists():raise ValueError('plan already exists; inspect before new work')
    for name,h in pins.items():
        path=raw/('source-archive-'+version)/name;path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists() and filehash(path)!=h:raise ValueError('archive changed')
        if not path.exists():path.write_bytes((REPO/name).read_bytes())
        normalized=name.replace('\\','/')
        if normalized.startswith('runners/stage12/') or normalized=='runners/__init__.py':
            target=capsule/name;target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists() and filehash(target)!=h:raise ValueError('capsule changed')
            if not target.exists():target.write_bytes((REPO/name).read_bytes())
    freeze(raw/('SOURCES-'+version+'.json'),pins)
    identifiers=[];hashes={}
    for card in cards:
        handler(card['handler']);identifier=card['id']
        if identifier in identifiers:raise ValueError('duplicate card')
        card=dict(card,source_pins=pins,contract_sha256=filehash(raw/'CONTRACT.json'))
        cp=raw/'manifests'/(identifier+'.json');freeze(cp,card)
        hashes[identifier]=filehash(cp);identifiers.append(identifier)
    plan=dict(schema='s12.native-queue.1',cards=identifiers,source_pins=pins,manifest_hashes=hashes,
        source_capsule=str(capsule),queue_directory=queue_directory,contract_sha256=filehash(raw/'CONTRACT.json'))
    destination=raw/('PLAN-'+version+'.json');freeze(destination,plan);return destination
