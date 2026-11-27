"""Freeze the archive metadata and cite completed studies for the Week 8 census.

Read only the registry, per-source metadata and directory names immediately
under the two collection areas. The restricted census stays in the work area.
"""
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from runners.stage14.common import filehash, freeze, read

STATE = ROOT / '.agent-state/drive-20261127/week8'
REG = '_registry/REGISTRY.json'
RIGHTS = '_registry/REPORTING_R48_INDEX.json'
MEMBERS = {
    '0003':'S15-W7-ATL-ADM-EXTENSION','0010':'S15-W6-TRX1-0010-APPRAISAL',
    '0023':'S15-W6-BT-FORMS-0023','0042':'OPS-S15-W7-ATL-0042',
    '0043':'OPS-S15-W7-ATL-0043','0044':'OPS-S15-W7-ATL-0044',
    '0049':'OPS-S15-W7-LAG-0049','0055':'S15-W6-BT-FORMS-0055',
    '0056':'OPS-S15-W7-ATL-0056','0057':'OPS-S15-W7-ATL-0057',
    '0060':'OPS-S15-W7-ATL-0060','0062':'OPS-S15-W6-ANX1-0062',
    '0063':'OPS-S15-W7-ATL-0063','0064':'OPS-S15-W6-OVERNIGHT-DIARY-PILOTS',
    '0070':'OPS-S15-W7-ATL-0070','0072':'OPS-S15-W7-ATL-0072',
    '0073':'OPS-S15-W7-ATL-0073','0076':'OPS-S15-W7-ATL-0076'}
HISTORY = {'openesm-'+key:value for key,value in MEMBERS.items()}
HISTORY.update({
    'isear':'S15-W6-R1-I-ISEAR', 'repository-coauthor':'S15-W6-WLG1',
    'repository-scholawrite':'L353', 'repository-pan-style':'L3',
    'repository-rutledge':'S15-W6-RR4-D3-BE', 'repository-jangraw':'S15-W5-MD4',
    'repository-jester':'S15-CA5-R-H1', 'repository-dices':'S15-CA5',
    'repository-community-alignment':'OPS-S15-W5-GO3-COLLECTION-FINAL-REPLAY',
    'repository-lichess':'S15-TD-B4-EFFORT-SKILL',
    'repository-klicke':'OPS-S15-W5-KLICKE-SOURCE-COMPLETE',
    'repository-wikipedia-conversations':'S15-DRIVE-WIKIPEDIA',
    'repository-iterater':'OPS-S15-W5-EX2-COMPLETE', 'repository-goemotions':'L27',
    'repository-moral-machine':'S15-TD-B2-M-COMPONENTS',
    'repository-crowd-envent':'S15-W6-IN16-COMPLETE',
    'candor':'OPS-S15-W7-CAD2-ORIGINAL-WORD-RETURN',
    'midus-m1-joined':'OPS-S15-W8-SLD8-WAVE-ONE-STRUCTURE',
    'midus-m1m2m3-surveys':'S15-W7-SLD2-MARITAL-ROLE',
    'midus-m2-joined':'OPS-S15-W8-SLD6-WAVE2-STRUCTURE',
    'midus-m3-joined':'OPS-S15-W6-SM0-JOINED-COMPLETE',
    'midus-m2m3-joined':'OPS-S15-W7-MIB1', 'repository-ami-icsi':'S15-W7-LGH4-ICSI-CONTEXT',
    'ami-close-talk':'OPS-S15-W7-LGH5-AMI-171-FULL',
    'ami-close-talk-slr16':'OPS-S15-W7-LGH5-AMI-171-FULL',
    'icsi-close-talk':'S15-W7-LGH4-ICSI-CONTEXT',
    'atus-wellbeing':'S15-W7-ATL-ADM-EXTENSION', 'couples-daily-hassles':'S15-W7-ATL-ADM-EXTENSION',
    'emotions-everyday-life':'OPS-S15-W7-PSD2-EVERYDAY-CHECKLIST',
    'european-social-survey':'OPS-S15-W7-VAL1-OBSERVED-EXPORT',
    'speed-dating':'OPS-S15-W7-GAT2-RELATIVE-MEAN',
    'sacredness-prices-portugal':'OPS-S15-W7-SCR1-INTERNAL',
    'teacher-diary-dual-ratings':'OPS-S15-W7-RESTRICTED-REPLAY',
    'ultimatum-epe-2021':'OPS-S15-W7-UGM1-EPE-RESPONDERS',
    'hilton-moser-vocalizations':'OPS-S15-W7-CRV1-PAIRED',
    'rosslund-infant-directed-speech-2024':'OPS-S15-W7-CRV1-ROSSLUND-TIMING',
    'talkbank-sbcsae':'OPS-S15-W7-SBC60-SEALED-LAYOUT',
    'candor-cad2-aws2020':'OPS-S15-W7-CAD2-ORIGINAL-WORD-RETURN'})
ALIASES = {
    'ami-close-talk-slr16':('AMI OpenSLR supplementary microphones','Modified CC BY-NC-SA 2.0'),
    'seamless-interaction-transcript-vad-annotations':('Seamless annotation holding','Parent source-specific terms'),
    'TalkBank':('Parent of the registered TalkBank media holding','Per-corpus access and terms'),
    'midus':('MIDUS original deposits and codebooks','ICPSR and MIDUS Conditions of Use'),
    'candor-cad2-aws2020':('CANDOR original word-timing projection','BetterUp CANDOR v2.1'),
    'talkbank-sbcsae':('Santa Barbara sealed projection','TalkBank corpus-specific terms'),
    'sm-family-fixture-v2':('Constructed solver fixture','Constructed data, fixture only'),
    'tmp1-tp58-delivery-a':('Frozen reader rehearsal fixture','Producer package, fixture only'),
    'midus-m1-joined':('First-wave joined MIDUS source','ICPSR and MIDUS Conditions of Use'),
    'pandora-tmp2':('PANDORA original archives, sealed alias','Provider terms, aggregate only'),
    'pandora-tmp2-tp58':('PANDORA archives with frozen reader, sealed alias','Provider terms, aggregate only')}
ADMIT = {'case-full','volynets-world-embody','openesm-0046'}

def safe_meta(root, rel):
    target=(root/rel).resolve()
    target.relative_to(root.resolve())
    if target.name != 'SOURCE.json':
        raise ValueError('Unexpected metadata filename')
    return read(target) if target.is_file() else {}

def licence(meta, fallback):
    value=meta.get('license') or meta.get('licence')
    if isinstance(value,dict):
        value=value.get('name') or value.get('type') or value.get('status')
    if not isinstance(value,str) or not value.strip():
        return fallback
    value=' '.join(value.split())
    if len(value)>200 or any(x in value for x in ('\\\\','@','file:/')):
        return fallback
    return value

def build():
    root=Path(read(ROOT/'.agent-state/data_collection_root.json')['root'])
    registry=read(root/REG)['sources']
    rights={r['slug']:r for r in read(root/RIGHTS)['sources']}
    subjects={r['slug']:r for r in registry}
    registered={r['path'] for r in registry}
    physical=[(area,p.name) for area in ('open','private') for p in (root/area).iterdir() if p.is_dir()]
    for area,slug in sorted(physical):
        if area+'/'+slug in registered:
            continue
        title,terms=ALIASES.get(slug,('Separately restricted holding','Owner-only, unavailable for research'))
        if slug in subjects:
            raise ValueError('Two physical holdings share a registry name')
        subjects[slug]=dict(slug=slug,title=title,path=area+'/'+slug,status='separate physical holding',terms=terms)
    findings=(ROOT/'FINDINGS.md').read_text('utf8')
    headings=re.findall(r'(?m)^#{2,3} ([^\n]+)',findings)
    cells=[]
    redacted=0
    for slug,row in sorted(subjects.items()):
        receipt=rights.get(slug,{})
        evidence=HISTORY.get(slug)
        if evidence and not any(re.match(re.escape(evidence)+r'(?:\b|[- ])',h) for h in headings):
            raise ValueError('Missing filed result '+evidence)
        restricted=(row.get('terms','').startswith('Owner-only'))
        if restricted:
            redacted+=1
        marker='Restricted holding '+str(redacted) if restricted else slug
        location=row['path']
        if not restricted and not (root/location).is_dir():
            raise ValueError('Registered holding not physically present: '+slug)
        meta=safe_meta(root,row['source']) if row.get('source') else {}
        fallback=row.get('terms') or ('See retained source terms at '+str(receipt.get('terms_evidence')).rsplit('/',1)[-1] if receipt.get('terms_evidence') else 'No binding terms recorded')
        release_class=receipt.get('r48_class')
        cells.append(dict(source=marker,holding=location,title=row['title'],terms=licence(meta,fallback),
            archive_state=row['status'],reporting_class=release_class,
            reporting_bar=receipt.get('reporting_bar') or 'Consult source-specific terms',
            admission='Designated for codebook and licence review' if slug in ADMIT else
            'Prior study scope only' if evidence else 'No Week 8 scientific admission',
            use=evidence or 'No prior study use verified',
            terms_card_sha256=receipt.get('card_sha256'),metadata_digest=filehash(root/row['source']) if meta else None))
    return dict(registry_hash=filehash(root/REG),rights_hash=filehash(root/RIGHTS),
                registered=len(registry),reporting_cards=len(rights),top_level_directories=len(physical),cells=cells)

if __name__=='__main__':
    result=build()
    output=STATE/'ADM2_VERIFIED_SOURCE_INVENTORY.json'
    freeze(output,result)
    print(len(result['cells']),'source and alias rows;',sum(r['use']!='No prior study use verified' for r in result['cells']),'with located study evidence;',filehash(output))
