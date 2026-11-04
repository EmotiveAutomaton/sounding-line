"""T4 complete source packing, training-only scaling and independent replay.

DESIGN CHECK: LESSONS 3-5 reread November 2; CONTROLS 1-3. Input validity
does not depend on null or alternative. Padding never becomes an option;
later observations never alter training normalization. Inadequate support is
unsupported, not a null. This module computes no model likelihood or effect.
"""
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
from .timing_p6 import read, gzread, gzip_equal, write_equal
from .timing_pmap_source import completed
from . import week4_t4_variable as model


def configuration(mode):
    if mode not in ('constructed', 'full'): raise ValueError('Unknown input scope')
    return dict(card='T4-inputs', mode=mode, menus_per_half=20, writers=25)


def assemble(rows, menus_per_half=20, minimum_writers=25):
    if not rows or len({r['key'] for r in rows}) != len(rows):
        raise ValueError('Empty or duplicate source menus')
    counts=defaultdict(Counter); excluded=Counter(); eligible=[]
    session_halves={}
    for r in rows:
        if r['reasons']:
            excluded.update(r['reasons']); continue
        k=r['dismissal_index']; choice=r['choice']; half=r['half']
        f=np.asarray(r['features'],dtype=float); z=np.asarray(r['state'],dtype=float)
        if type(k)!=int or not 1<=k<=5 or f.shape!=(k+1,5) or z.shape!=(2,) or not np.isfinite(f).all() or not np.isfinite(z).all() or np.any(f[-1]!=0):
            raise ValueError('Malformed compact features or dismissal')
        if type(choice)!=int or not 0<=choice<=k or half not in ('train','test') or not np.isfinite(r['open_at']):
            raise ValueError('Invalid choice or temporal half')
        key=(r['writer'],r['session'])
        if key in session_halves and session_halves[key]!=half: raise ValueError('Session crosses halves')
        session_halves[key]=half; counts[r['writer']][half]+=1; eligible.append(r)
    writers=sorted(w for w,c in counts.items() if c['train']>=menus_per_half and c['test']>=menus_per_half)
    summary=dict(source_menus=len(rows),eligible_menus=len(eligible),supported_writers=len(writers),
                 required_writers=minimum_writers,excluded_writers=len(counts)-len(writers),
                 exclusions=dict(sorted(excluded.items())),support_pass=len(writers)>=minimum_writers,
                 scientific_effect_computed=False)
    if not summary['support_pass']: return dict(summary=summary,counts={w:dict(c) for w,c in sorted(counts.items())},writers=writers)
    indices={w:i for i,w in enumerate(writers)}
    selected=[r for r in eligible if r['writer'] in indices]
    for w in writers:
        early=[r['open_at'] for r in selected if r['writer']==w and r['half']=='train']
        late=[r['open_at'] for r in selected if r['writer']==w and r['half']=='test']
        if max(early)>=min(late): raise ValueError('Reversed temporal halves')
    parts={h:sorted((r for r in selected if r['half']==h),key=lambda r:(r['writer'],r['open_at'],r['key'])) for h in ('train','test')}
    real=np.asarray([v for r in parts['train'] for v in r['features'][:-1]],dtype=float)
    state=np.asarray([r['state'] for r in parts['train']],dtype=float)
    xm=real.mean(0); xs=real.std(0); zm=state.mean(0); zs=state.std(0)
    xs=np.where(xs>1e-12,xs,1.); zs=np.where(zs>1e-12,zs,1.)
    packed={}
    for half, rs in parts.items():
        x=np.zeros((len(rs),5,5)); mask=np.zeros((len(rs),5),bool)
        for i,r in enumerate(rs):
            k=r['dismissal_index']; x[i,:k]=(np.asarray(r['features'][:-1])-xm)/xs; mask[i,:k]=True
        d=dict(x=x,z=(np.asarray([r['state'] for r in rs])-zm)/zs,
               w=np.asarray([indices[r['writer']] for r in rs],dtype=int),
               y=np.asarray([5 if r['choice']==r['dismissal_index'] else r['choice'] for r in rs],dtype=int),mask=mask)
        if model.checked(d)!=len(writers): raise ValueError('Writer packing differs')
        packed[half]={k:v.tolist() for k,v in d.items()}
        packed[half]['keys']=[r['key'] for r in rs]
        packed[half]['sessions']=[r['session'] for r in rs]
        packed[half]['genres']=[r['genre'] for r in rs]
    summary.update(training_menus=len(parts['train']),test_menus=len(parts['test']),selected_menus=len(selected))
    return dict(summary=summary,writers=writers,counts={w:dict(c) for w,c in sorted(counts.items())},
                scaling=dict(x_mean=xm.tolist(),x_scale=xs.tolist(),z_mean=zm.tolist(),z_scale=zs.tolist()),**packed)


def arrays(packed,half):
    d=packed[half]
    result={k:np.asarray(d[k],dtype=bool if k=='mask' else int if k in ('w','y') else float) for k in ('x','z','w','y','mask')}
    model.checked(result)
    return result


def independently_check(rows,packed):
    if not packed['summary']['support_pass']: return
    original={r['key']:r for r in rows}; scale=packed['scaling']
    train=[original[k] for k in packed['train']['keys']]
    for j in range(5):
        v=[r['features'][i][j] for r in train for i in range(r['dismissal_index'])]
        mean=sum(v)/len(v); sd=(sum((a-mean)**2 for a in v)/len(v))**.5
        assert abs(mean-scale['x_mean'][j])<1e-10
        assert abs((sd if sd>1e-12 else 1)-scale['x_scale'][j])<1e-10
    for j in range(2):
        v=[r['state'][j] for r in train]; mean=sum(v)/len(v); sd=(sum((a-mean)**2 for a in v)/len(v))**.5
        assert abs(mean-scale['z_mean'][j])<1e-10
        assert abs((sd if sd>1e-12 else 1)-scale['z_scale'][j])<1e-10
    for half in ('train','test'):
        d=arrays(packed,half)
        for i,key in enumerate(packed[half]['keys']):
            r=original[key]; n=r['dismissal_index']
            assert packed['writers'][d['w'][i]]==r['writer'] and r['half']==half
            assert packed[half]['sessions'][i]==r['session'] and packed[half]['genres'][i]==r['genre']
            assert d['y'][i]==(5 if r['choice']==n else r['choice'])
            assert d['mask'][i].tolist()==[j<n for j in range(5)]
            for j in range(5):
                for k in range(5):
                    expected=(r['features'][j][k]-scale['x_mean'][k])/scale['x_scale'][k] if j<n else 0.
                    assert abs(d['x'][i,j,k]-expected)<1e-12
            for k in range(2): assert abs(d['z'][i,k]-(r['state'][k]-scale['z_mean'][k])/scale['z_scale'][k])<1e-12


def fixture():
    rows=[]
    for w in range(3):
        for half,start in (('train',0),('test',100)):
            for i in range(4):
                n=i%3+1
                rows.append(dict(key=f'{w}-{half}-{i}',writer=str(w),session=f'{w}-{half}',half=half,genre='constructed',
                    open_at=start+i,choice=n if i%2 else 0,dismissal_index=n,reasons=[],
                    features=[[float(w+i+j),float(i),2.,float(j),float(start)] for j in range(n)]+[[0.]*5],state=[i/4.,float(start+i)]))
    return rows


def known_answers():
    rows=fixture(); p=assemble(rows,2,3); independently_check(rows,p)
    assert p['summary']['training_menus']==12 and p['summary']['test_menus']==12
    assert p['scaling']['x_scale'][2]==1 and p['scaling']['x_mean'][4]==0
    assert np.all(arrays(p,'train')['x'][:,:,4]==0)
    assert np.all(arrays(p,'test')['x'][:,:,4][arrays(p,'test')['mask']]==100)
    assert not assemble(rows,5,3)['summary']['support_pass']
    return dict(compact_choices_preserved=True,training_only_scaling=True,padding_impossible=True,
                scalar_replay=True,support_floor_enforced=True)


def run(output,inputs,config,verification=False):
    if config!=configuration(config['mode']): raise ValueError('Frozen inputs configuration required')
    output=Path(output); checks=known_answers()
    if config['mode']=='constructed':
        if inputs: raise ValueError('Constructed inputs must be empty')
        rows=fixture(); value=assemble(rows,2,3)
    else:
        if set(inputs)!={'history_completion'}: raise ValueError('Exact history source required')
        c=Path(inputs['history_completion']); source=c.parent/'output'
        for n in ('FEATURES.json.gz','PRIVATE_SUPPORT.json','SUMMARY.json'): completed(c,source/n)
        if read(source/'SUMMARY.json')['mode']!='full': raise ValueError('Full history source required')
        rows=gzread(source/'FEATURES.json.gz');value=assemble(rows,config['menus_per_half'],config['writers'])
        if value['writers']!=read(source/'PRIVATE_SUPPORT.json')['supported_writers']: raise ValueError('Support roster changed')
    summary=dict(value['summary'],mode=config['mode'],checks=checks)
    if verification:
        if read(output/'SUMMARY.json')!=summary or gzread(output/'PRIVATE_DATA.json.gz')!=value: raise ValueError('Input replay differs')
        independently_check(rows,value)
        return dict(verified=True,complete_input_replay=True)
    gzip_equal(output/'PRIVATE_DATA.json.gz',value);write_equal(output/'SUMMARY.json',summary)
    return dict(status='complete',scientific_admission=False)


def execute(output,inputs,config): return run(output,inputs,config)
def verify(output,inputs,config): return run(output,inputs,config,True)
