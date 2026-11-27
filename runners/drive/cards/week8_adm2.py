"""Week 8 ADM2. Census and admission of three specified open releases.

DESIGN CHECK (2026-11-27). Lessons read: LESSONS §§2–5, original-source
identity, scope of a structural gate, and independent replay.
Gates, null/alternative/direction: under the null of an absent or ambiguous
binding, a missing or duplicate header prevents admission. Under the
alternative of a fully documented source, its unique original fields and
archive hash reproduce. The failure direction is false admission from treating
an inventory entry as a scientific measurement or a repeated key as unique.
Verdict bands per arm, exhaustive: a verified source is admitted within
scope, a failed binding is void, and all other holdings retain prior scope.
The inventory has no scientific verdict.
"""
import csv
import io
from pathlib import Path
from zipfile import ZipFile

from scipy.io import whosmat
from runners.stage14.common import filehash, freeze, read

ROOT=Path(__file__).resolve().parents[3]
WORK=ROOT/'.agent-state/drive-20261127/week8'
UNIT='ADM2-store-census-and-open-bindings'
SLUGS=('volynets-world-embody','case-full','openesm-0046')
LICENCES=('CC BY 4.0','CC0','CC-BY-NC-4.0')
FIELDS=('id','day','beep','pa_self','na_self','pa_other','na_other','empathy_global','empathy_cog','empathy_aff')
FEELINGS=('Anger','Fear','Disgust','Happiness','Sadness','Surprise','Neutral','Anxiety','Love','Depression','Contempt','Pride','Shame','Envy')
ANNOT=('jstime','valence','arousal','video')
PHYS=('daqtime','ecg','bvp','gsr','rsp','skt','emg_zygo','emg_coru','emg_trap','video')

def data_root():
    return Path(read(ROOT/'.agent-state/data_collection_root.json')['root'])

def design(unit):
    if unit!=UNIT:
        raise ValueError('Unrecognized census')
    root=data_root()
    inputs=[WORK/'ADM2_VERIFIED_SOURCE_INVENTORY.json',ROOT/'tools/week8_prepare_adm2.py',ROOT/'docs/design/stage-15/week8/ADM2.md']
    for slug in SLUGS:
        inputs.extend(root/'open'/slug/k for k in ('SOURCE.json','SCHEMA.json'))
    inputs.extend([root/'open/openesm-0046/DOCUMENTED_METADATA.json',root/'open/volynets-world-embody/FIELD_CARD.md'])
    return dict(inputs=inputs,peak=.35,cap=20000,operations=['execute','verify'],
                source='Frozen archive metadata and three original open source releases')

def require(header, fields):
    if any(header.count(k)!=1 for k in fields):
        raise ValueError('Missing or repeated required column')

def public_rows(inventory, bindings=None):
    rows=[]
    for original in inventory:
        row={k:original[k] for k in ('source','title','terms','admission','use','reporting_class')}
        if bindings and row['source'] in bindings:
            ok=bindings[row['source']].get('status')=='admitted'
            row['admission']='Admitted within codebook and licence scope' if ok else 'Void at source binding'
        if row['source'].startswith('Restricted holding '):
            row.update(terms='Owner-only',title='Separately restricted holding')
        rows.append(row)
    return rows

def fixture():
    require(['time','value','unit'],['unit','time'])
    for bad in (['time','time','unit'],['unit']):
        try:
            require(bad,['time','unit'])
        except ValueError:
            continue
        raise AssertionError('Accepted an ambiguous header')
    r=dict(source='Restricted holding 1',title='masked',terms='sensitive',admission='held',use='unverified',reporting_class=None,holding='local')
    projected=public_rows([r])[0]
    assert 'holding' not in projected and projected['terms']=='Owner-only'
    assert len(FEELINGS)==14 and len(set(FIELDS))==len(FIELDS)
    return dict(ambiguous_and_absent_refused=True,restricted_metadata_projection=True,registered_open_sources=3)

def inspect_open(root,slug):
    base=root/'open'/slug
    receipt=read(base/'SOURCE.json')
    original,=receipt['local_files']
    file=root/original['path']
    if file.stat().st_size!=original['bytes'] or filehash(file)!=original['sha256']:
        raise ValueError('Original release differs from intake')
    licence=receipt.get('license') or receipt.get('licence')
    if isinstance(licence,dict):
        licence=licence['name']
    if licence!=LICENCES[SLUGS.index(slug)]:
        raise ValueError('Reviewed licence changed')
    result=dict(licence=licence,original_sha256=original['sha256'])
    if slug==SLUGS[0]:
        with ZipFile(file) as z:
            mats=[n for n in z.namelist() if n.endswith('.mat')]
            if len(mats)!=3954 or len(set(mats))!=len(mats):
                raise ValueError('Map archive roster differs')
            with z.open('pheno.csv') as f:
                header=next(csv.reader(io.TextIOWrapper(f,encoding='utf-8-sig')))
            require(header,['subjID',*(v+s for v in FEELINGS for s in ('.ms','.nop'))])
            desc={name:tuple(shape) for name,shape,_ in whosmat(io.BytesIO(z.read(mats[0])))}
            if desc.get('resmat')!=(522,171,14) or desc.get('resmat2')!=(522,171,14) or desc.get('times')!=(14,2):
                raise ValueError('Unexpected MATLAB schema')
            result.update(map_files=len(mats),grid=[522,171,14],feeling_names=len(FEELINGS),
                          scope='Body rasters and named paint metadata. BMP1 must bind the raster plane order independently.')
    elif slug==SLUGS[1]:
        with ZipFile(file) as z:
            pairs=[]
            for area,columns in [('annotations',ANNOT),('physiological',PHYS)]:
                prefix='CASE_full/data/interpolated/'+area+'/'
                members={n[len(prefix):]:n for n in z.namelist() if n.startswith(prefix) and n.endswith('.csv')}
                book=z.read(prefix+'README_'+area+'.txt').decode('utf8')
                if 'milliseconds' not in book or not all(k in book for k in columns):
                    raise ValueError('Clock or field missing from provider guide')
                for name in members.values():
                    with z.open(name) as f:
                        actual=f.readline().decode('utf-8-sig').strip().split(',')
                    if tuple(actual)!=columns:
                        raise ValueError('CASE column order or names changed')
                pairs.append(set(members))
            if len(pairs[0])!=30 or pairs[0]!=pairs[1]:
                raise ValueError('Unmatched subject files')
        result.update(subject_file_pairs=30,scope='Continuous self-rated valence and arousal and eight physiological channels. Link by subject, video and elapsed milliseconds, aligning the different sample clocks.')
    else:
        fields=read(base/'DOCUMENTED_METADATA.json')['features']
        require([f['name'] for f in fields],FIELDS)
        with file.open(encoding='utf-8-sig') as f:
            header=next(csv.reader(f,delimiter='\t'))
        require(header,FIELDS)
        result.update(columns=list(FIELDS),scope='Noncommercial internal use. Same reporter rates own affect and perceived other affect. No independently observed event or partner report for ATL.')
    return result

def run(unit,d,mode):
    if unit!=UNIT:
        raise ValueError('Unknown census')
    inventory=read(WORK/'ADM2_VERIFIED_SOURCE_INVENTORY.json')
    result={}
    for slug in SLUGS:
        try:
            result[slug]=dict(status='admitted',**inspect_open(data_root(),slug))
        except (ValueError, KeyError) as exc:
            result[slug]=dict(status='void',reason=str(exc))
    rows=public_rows(inventory['cells'],result)
    if len(set(r['source'] for r in rows))!=len(rows):
        raise ValueError('Repeated inventory label')
    freeze(d/(mode+'_CENSUS.json'),dict(bindings=result,cells=rows,registered=inventory['registered'],
           physical_directories=inventory['top_level_directories'],reporting_cards=inventory['reporting_cards']))

def check(unit,d):
    names=[d/(mode+'_CENSUS.json') for mode in ('execute','verify')]
    if read(names[0])!=read(names[1]):
        raise ValueError('Source inventory or independent binding replay differs')
    return {p.name:filehash(p) for p in names}
