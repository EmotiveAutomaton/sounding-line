"""BMP1. Bind original signed body-map planes before descriptive pooling.

DESIGN CHECK (2026-11-27). Lessons read: LESSONS §§2–5 on structural
identity, arm scope and source replay. Gates, null/alternative/direction:
under the null of arbitrary plane attribution, per-person durations do not
identify a common one-to-one label order. Under the alternative an exact
reordering is recovered, including when metadata columns use another order.
The failure direction is painting the right geometry under a wrong label.
Verdict bands per arm, exhaustive: ambiguous rasters or keys give a void
component. Bound means, pairwise correlations and regional averages are
descriptions with no predicted direction or test verdict.
"""
import csv
import io
from pathlib import Path
from zipfile import ZipFile
import numpy as np
from PIL import Image
from scipy.io import loadmat
from runners.stage14.common import filehash,freeze,read
from . import week8_adm2 as admission
from . import week8_gear as gear

ROOT=admission.ROOT
UNIT='BMP1-registered-body-map-means'
ADM=gear.ROOT/admission.UNIT
NAMES=admission.FEELINGS
SEED=2026112742
REGIONS={'head':(0,71,0,171),'chest':(109,171,45,126),'belly':(185,250,46,125),
         'legs':(305,522,0,171),'arms':(108,247,0,32),'hands':(261,304,0,31)}

def archive():
    root=admission.data_root()
    base=root/'open/volynets-world-embody'
    package=root/'_handoffs/repo-requests/DC-20261127-BMP1'
    source=read(base/'SOURCE.json')['local_files'][0]
    return root/source['path'],package,source

def design(unit):
    if unit!=UNIT:
        raise ValueError('Unknown body-map study')
    terminal=read(ADM/'COMPLETE.json')
    census=ADM/'execute_CENSUS.json'
    source,package,raw=archive()
    verified=read(census)['bindings']['volynets-world-embody']
    if not terminal['verified'] or terminal['unit']!=admission.UNIT or terminal['results'].get(census.name)!=filehash(census):
        raise ValueError('Source admission has no verified original-file replay')
    if verified.get('status')!='admitted' or verified['original_sha256']!=raw['sha256']:
        raise ValueError('Original body map did not pass ADM2')
    hashes=read(package/'DELIVERY.json')['files']
    names=['SPATIAL_SOURCE.md','TEMPLATE_MANIFEST.json','provider/matlab/mask.png','provider/matlab/embody_demo.m']
    inputs=[package/p for p in names]
    return dict(inputs=[*inputs,ADM/'COMPLETE.json',census,Path(admission.__file__),ROOT/'docs/design/stage-15/week8/BMP1.md'],
        expected={str(package/k):hashes[k] for k in names},peak=.75,cap=20000,operations=['execute','verify'],
        source='Volynets world emBODY original release, with independent acquisition and geometry receipts')

def masks(alpha):
    if alpha.shape!=(522,171):
        raise ValueError('Template geometry differs')
    body=alpha>=128
    rows,cols=np.indices(body.shape)
    regions={}
    for k,(y0,y1,x0,x1) in REGIONS.items():
        side=(cols>=x0)&(cols<x1)
        if k in ('arms','hands'):
            side|=cols>=body.shape[1]-x1
        regions[k]=body&(rows>=y0)&(rows<y1)&side
    if any(not a.any() for a in regions.values()) or np.any(sum(a.astype(int) for a in regions.values())>1):
        raise ValueError('Non-disjoint or empty anatomical core')
    return body,regions

def keymap(timings,reported,min_support):
    # Fixed unit conversions and direct, elapsed and summed timing interpretations.
    candidates=[]
    for sequence in (timings[:,:,0],timings[:,:,1],timings[:,:,1]-timings[:,:,0],timings.sum(axis=2)):
        for scale in (1.,1000.):
            values=sequence*scale
            order=[];support=[]
            for word in range(reported.shape[1]):
                ref=reported[:,word]
                unique=((np.abs(reported-ref[:,None])<=.5).sum(axis=1)==1)&np.isfinite(ref)&(ref>0)
                match=(np.abs(values-ref[:,None])<=.5)&unique[:,None]
                z=match.sum(axis=0)
                n=int(unique.sum())
                winners=np.flatnonzero(z>=.99*n)
                if n<min_support or len(winners)!=1:
                    break
                order.append(int(winners[0]));support.append(n)
            if len(set(order))==reported.shape[1]:
                candidates.append((tuple(order),min(support)))
    orders={item[0] for item in candidates}
    return list(next(iter(orders))) if len(orders)==1 else None

def raster_relation(first,second):
    if first.shape!=second.shape or not (np.isfinite(first).all() and np.isfinite(second).all()):
        return set()
    signed=np.any(first>0) and np.any(first<0)
    if not signed:
        return {'no signed evidence'} if not np.any(first) and not np.any(second) else set()
    possible=set()
    if np.all(second>=0):
        possible.add('only resmat is signed')
    # Equal positive scaling within each plane preserves which array supplies
    # the documented signed field. Use resmat in its native paint units.
    for k in range(first.shape[-1]):
        a=first[:,:,k];b=second[:,:,k]
        j=np.argmax(np.abs(a));a0=a.flat[j];b0=b.flat[j]
        if a0==0:
            if np.any(b):break
            continue
        scale=b0/a0
        if scale<=0 or not np.allclose(a*scale,b,rtol=1e-8,atol=1e-9):break
    else:
        possible.add('same signed geometry')
    return possible

def fixture():
    rng=np.random.default_rng(891);n=90;words=14
    order=rng.permutation(words)
    durations=rng.integers(1000,9000000,(n,words)).astype(float)
    times=np.stack([durations[:,order],rng.uniform(3,90,(n,words))],axis=2)
    assert keymap(times,durations,64)==np.argsort(order).tolist()
    assert keymap(times,durations[::-1],64) is None
    times[:,:,1]=durations[:,order[::-1]]
    assert keymap(times,durations,64) is None
    a=rng.normal(size=(8,5,4))
    assert 'same signed geometry' in raster_relation(a,2*a)
    assert not raster_relation(a,-a)
    alpha=np.full((522,171),255,dtype=np.uint8);_,r=masks(alpha)
    assert r['arms'][175,15] and r['arms'][175,155] and not r['chest'][175,15]
    assert r['hands'][280,14] and r['legs'][340,90] and not r['head'][100,85]
    return dict(scrambled_labels_recovered=True,coinciding_or_unrelated_keys_refused=True,
                reversed_sign_refused=True,regions_disjoint=True)

def aggregate(d,mode):
    file,package,pin=archive()
    if file.stat().st_size!=pin['bytes'] or filehash(file)!=pin['sha256']:
        raise ValueError('Original source digest changed')
    with Image.open(package/'provider/matlab/mask.png') as im:
        body,regions=masks(np.asarray(im.convert('L')))
    counts={k:int(v.sum()) for k,v in regions.items()}
    info=dict(source_sha256=pin['sha256'],body_pixels=int(body.sum()),regional_pixels=counts,
              map_units='mean net painted signal, original resmat units')
    def void(reason):
        return dict(status='void',reason=reason,**info)
    with ZipFile(file) as z:
        entries={Path(name).stem:name for name in z.namelist() if name.endswith('.mat')}
        with z.open('pheno.csv') as f:
            table=csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig',newline=''))
            admission.require(table.fieldnames,['subjID',*[k+'.ms' for k in NAMES]])
            duration={}
            for row in table:
                key=row['subjID'].strip()
                if key in duration:
                    return void('Duplicate participant join key')
                def number(text):
                    try:return float(text)
                    except (TypeError,ValueError):return np.nan
                duration[key]=[number(row[k+'.ms']) for k in NAMES]
        if set(duration)!=set(entries) or len(entries)!=3954:
            return void('The metadata-to-MAT keys do not match exactly')
        keys=sorted(entries)
        sample=np.random.default_rng(SEED).choice(keys,96,replace=False)
        times=[]
        relations={'only resmat is signed','same signed geometry'}
        informative=0
        for key in sample:
            a=loadmat(io.BytesIO(z.read(entries[key])),variable_names=['times','resmat','resmat2'])
            if a['times'].shape!=(14,2) or a['resmat'].shape!=(522,171,14):
                return void('Unbound source geometry')
            times.append(a['times'])
            same=raster_relation(a['resmat'],a['resmat2'])
            if same!={'no signed evidence'}:
                relations &= same
                informative+=1
        order=keymap(np.asarray(times),np.asarray([duration[k] for k in sample]),64)
        info.update(binding_sample=len(sample),unique_timing_crosswalk=(order is not None),
                    signed_field_corroborated=bool(relations) and informative>=64)
        if order is None or not info['signed_field_corroborated']:
            return void('Named planes or signed array could not be identified in the fixed crosswalk')
        accum=np.zeros((*body.shape,14),np.float64)
        all_times=[]
        for key in keys:
            a=loadmat(io.BytesIO(z.read(entries[key])),variable_names=['times','resmat','resmat2'])
            if a['resmat'].shape!=accum.shape or a['times'].shape!=(14,2):
                return void('Geometry changed outside binding sample')
            relation=raster_relation(a['resmat'],a['resmat2'])
            if relation!={'no signed evidence'}:
                relations &= relation
                if not relations:return void('Signed-field binding failed on the full source')
            accum+=a['resmat'][:,:,order]
            all_times.append(a['times'])
        if keymap(np.asarray(all_times),np.asarray([duration[k] for k in keys]),64)!=order:
            return void('Named-plane binding failed on the full source')
    means=accum/len(keys)
    values=means[body]
    with np.errstate(invalid='ignore',divide='ignore'):
        corr=np.corrcoef(values,rowvar=False)
    stats={name:[float(v) for v in means[area].mean(axis=0)] for name,area in regions.items()}
    means[~body]=0
    np.save(d/(mode+'_MEAN_MAPS.npy'),means,allow_pickle=False)
    return dict(status='descriptive',map_order=list(NAMES),n=len(keys),regional_means=stats,
                correlations=[[float(v) if np.isfinite(v) else None for v in row] for row in corr],**info)

def run(unit,d,mode):
    freeze(d/(mode+'_MAPS.json'),aggregate(d,mode))

def check(unit,d):
    a=d/'execute_MAPS.json';b=d/'verify_MAPS.json'
    if read(a)!=read(b):
        raise ValueError('Body-map source replay differs')
    paths=[a,b]
    if read(a)['status']=='descriptive':
        maps=[d/(mode+'_MEAN_MAPS.npy') for mode in ('execute','verify')]
        if filehash(maps[0])!=filehash(maps[1]):raise ValueError('Mean raster replay differs')
        paths+=maps
    return {p.name:filehash(p) for p in paths}
