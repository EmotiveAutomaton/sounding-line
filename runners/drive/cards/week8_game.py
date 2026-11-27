"""Fixed-player-split phone-game models using whole-player sufficient statistics."""
from pathlib import Path
import numpy as np
from scipy.signal import lfilter
from . import week5_md as md, week8_gear as gear
from runners.stage14.common import read, freeze, filehash

SEED=2026112708
ROOT=gear.REPO
SRC=gear.ROOT.parent/'drive-week5-20261107/MD-source.h1/output'
HASH='6b64993bf3335eaa819bf9ecd896b0a405267ae4691b38795a0e0077653cd221'
GRID=md.GAMMAS


def design(card,unit):
    if unit!=card+'-first-plays':raise ValueError('Unknown player roster')
    verified=read(SRC/'VERIFIED.json')
    if not verified['verified'] or verified['first_plays_checked']!=42380 or verified['task_sha256']!=HASH:
        raise ValueError('Unverified first-play population')
    path=SRC/'task.npz'
    return dict(inputs=[path,SRC/'SOURCE.json',SRC/'VERIFIED.json',Path(__file__),
                Path(md.__file__),ROOT/'docs/design/stage-15/week8/ACC1_ADP1.md'],expected={str(path):HASH},peak=1.3,
                cap=20000,operations=['execute','verify'],source='Rutledge verified attempted first plays')


def clock(plays):
    observed=np.isfinite(plays[:,:,9])
    if not (observed.sum(axis=1)==12).all() or not observed[:,0].all():
        raise ValueError('Unexpected first-play clock')
    people=np.arange(len(plays))[:,None]
    idx=np.nonzero(observed)[1].reshape(-1,12)
    y=plays[people,idx,9]
    after=idx+1
    after[:,0]=0
    return y,after


def histories(plays,base_rates,sign_rates):
    y,after=clock(plays)
    people=np.arange(len(plays))[:,None]
    gamble=plays[:,:,6]
    outcome=plays[:,:,7]
    ev=(plays[:,:,3]+plays[:,:,4])/2
    surprise=(outcome-ev)*gamble
    a=np.zeros((len(plays),31))
    a[:,3:]=outcome[:,2:]-2*outcome[:,1:-1]+outcome[:,:-2]
    values=[y,a[people,after]]
    groups=[]
    for signal,rates in [(plays[:,:,2]*(1-gamble),base_rates),(ev*gamble,base_rates),
                         (np.maximum(surprise,0),sign_rates),(np.minimum(surprise,0),sign_rates)]:
        groups.append(np.arange(len(values),len(values)+len(rates)))
        for rate in rates:
            h=np.zeros((len(plays),31))
            h[:,1:]=lfilter([1.],[1.,-rate],signal,axis=1)
            values.append(h[people,after])
    z=np.stack(values,axis=2)
    z-=z.mean(axis=1,keepdims=True)
    return z,groups


def moments(plays,index,base,sign,per_player):
    rows=[]
    agg=None
    for start in range(0,len(index),384):
        z,groups=histories(plays[index[start:start+384]],base,sign)
        if per_player:
            g=z.transpose(0,2,1)@z
            tri=np.triu_indices(g.shape[1])
            rows.append(g[:,tri[0],tri[1]])
        else:
            a=z.reshape(-1,z.shape[-1])
            item=a.T@a
            agg=item if agg is None else agg+item
    if not len(index):raise ValueError('No eligible players')
    return (np.concatenate(rows) if per_player else agg[None]),groups


def parameters(G,c,e,p,n,acc=False):
    # Each design has one signed surprise coefficient on P(g+) + N(g-).
    cols=[(c,),(e,),(p,n)]
    if acc:cols.append((np.ones_like(c),))
    rhs=np.stack([sum(G[:,i,0] for i in a) for a in cols],axis=-1)
    gram=np.stack([np.stack([sum(G[:,i,j] for i in a for j in b) for b in cols],axis=-1)
                   for a in cols],axis=-2)
    scale=np.sqrt(np.maximum(np.diagonal(gram,axis1=-2,axis2=-1),1e-24))
    normal=gram/scale[...,None]/scale[...,None,:]
    ok=np.linalg.det(normal)>1e-11
    valid=np.flatnonzero(ok)
    beta=np.full_like(rhs,np.nan)
    if len(valid):
        beta[ok]=np.linalg.solve(normal[ok],(rhs/scale)[ok,...,None])[...,0]/scale[ok]
    score=np.where(ok,np.sum(beta*rhs,axis=-1),-np.inf)
    return score,beta


def rates(G,groups,base_index=None):
    c,e,p,n=groups
    if base_index is None:
        score,_=parameters(G,c,e,p,n)
        idx=score.argmax(axis=1)
        if not np.isfinite(score[np.arange(len(G)),idx]).all():raise ValueError('Unidentified standard rate')
        return idx
    a,b=np.meshgrid(np.arange(len(p)),np.arange(len(n)),indexing='ij')
    a,b=a.ravel(),b.ravel()
    score,_=parameters(G,np.full_like(a,c[base_index]),np.full_like(a,e[base_index]),p[a],n[b])
    idx=score.argmax(axis=1)
    if not np.isfinite(score[np.arange(len(G)),idx]).all():raise ValueError('Unidentified split rates')
    return a[idx],b[idx]


def training(plays,index,grid):
    G,cols=moments(plays,index,grid,grid,False)
    ci=int(rates(G,cols)[0])
    a,b=rates(G,cols,ci)
    return [float(grid[k]) for k in (ci,a[0],b[0])]


def unpack(flat,dimension):
    rows=np.empty((len(flat),dimension,dimension))
    i,j=np.triu_indices(dimension)
    rows[:,i,j]=rows[:,j,i]=flat
    return rows


def evaluation(plays,index,train,grid,card,draws,seed):
    gp,gn=train[1:]
    used=np.unique(train) if card=='ACC1' else grid
    flat,cols=moments(plays,index,[train[0]],used,True)
    d=int(cols[-1][-1])+1
    rng=np.random.default_rng(seed)
    results=[]
    def calculate(group):
        if card=='ADP1':
            a,b=rates(group,cols,0)
            return (grid[b]-grid[a])[:,None]
        c,e,p,n=cols
        ix=lambda value:int(np.flatnonzero(used==value)[0])
        aa=np.array([ix(train[0]),ix(gp)])
        bb=np.array([ix(train[0]),ix(gn)])
        _,coef=parameters(group,np.repeat(c,2),np.repeat(e,2),p[aa],n[bb],True)
        return coef[:,:,3]
    point=calculate(unpack(flat.sum(axis=0,keepdims=True),d))[0]
    prob=np.full(len(index),1/len(index))
    for offset in range(0,draws,16):
        rng_weights=rng.multinomial(len(index),prob,size=min(16,draws-offset))
        results.append(calculate(unpack(rng_weights@flat,d)))
    bank=np.concatenate(results)
    output=[]
    for j,value in enumerate(point):
        if not np.isfinite(value) or not np.isfinite(bank[:,j]).all():
            output.append({'status':'unidentified'})
            continue
        bounds=np.quantile(bank[:,j],[.025,.975])
        output.append(dict(estimate=float(value),lower=float(bounds[0]),upper=float(bounds[1]),se=float(bank[:,j].std(ddof=1))))
    return output


def split(n):
    order=np.random.default_rng(SEED).permutation(n)
    return np.sort(order[:int(.7*n)]),np.sort(order[int(.7*n):])


def study(plays,card,draws=2000,grid=GRID):
    train,test=split(len(plays))
    y,_=clock(plays)
    if y.min()<0 or y.max()>100:raise ValueError('Rating scale differs')
    keep=((y==0)|(y==100)).sum(axis=1)<=3
    rows={}
    for k,trim in enumerate((False,True)):
        tt=train[keep[train]] if trim else train
        vv=test[keep[test]] if trim else test
        frozen=training(plays,tt,grid)
        values=evaluation(plays,vv,frozen,grid,card,draws,SEED+1+k)
        if trim and card=='ACC1':values=values[:1]
        rows['endpoint_sensitivity' if trim else 'all_players']=dict(train=len(tt),test=len(vv),development_rates=frozen,values=values)
    return dict(card=card,players=len(plays),train_players=len(train),test_players=len(test),seed=SEED,draws=draws,panels=rows)


def fixture():
    rng=np.random.default_rng(1508)
    n=240
    p=np.zeros((n,30,15));p[:,:,9]=np.nan
    p[:,:,2]=rng.uniform(1,10,(n,30));p[:,:,3]=rng.uniform(5,13,(n,30));p[:,:,4]=rng.uniform(-9,-1,(n,30))
    p[:,:,6]=rng.integers(2,size=(n,30));p[:,:,7]=np.where(p[:,:,6],np.where(rng.integers(2,size=(n,30)),p[:,:,3],p[:,:,4]),p[:,:,2])
    slots=[0,3,5,8,10,13,15,18,20,23,26,29];p[:,slots,9]=50.
    grid=np.array([.2,.5,.8])
    signed,g=histories(p,grid,grid)
    old,_=md.rating_history(p,.5)
    old-=old.mean(axis=1,keepdims=True)
    assert np.allclose(signed[:,:,g[0][1]],old[:,:,0])
    assert np.allclose(signed[:,:,g[2][1]]+signed[:,:,g[3][1]],old[:,:,2])
    common=.35*signed[:,:,g[0][1]]+.22*signed[:,:,g[1][1]]
    p[:,slots,9]=50+common+.8*(signed[:,:,g[2][0]]+signed[:,:,g[3][2]])+.08*signed[:,:,1]
    planted=study(p,'ACC1',24,grid)['panels']['all_players']
    assert planted['development_rates'][1:]==[.2,.8] and abs(planted['values'][1]['estimate']-.08)<.01
    asym=study(p,'ADP1',24,grid)['panels']['all_players']['values'][0]
    assert asym['lower']>.4
    tr,te=split(n)
    r=training(p,tr,grid)
    p[te[:,None],slots,9]=50
    assert training(p,tr,grid)==r
    p[0,slots[:4],9]=0
    y,_=clock(p)
    assert ((y[0]==0)|(y[0]==100)).sum()>3
    return dict(passed=True,checks=['MD1 clock','frozen positive acceleration','asymmetric rates','held-out tampering','scale-end rule'])


def run(card,d,mode):
    verified=read(SRC/'VERIFIED.json')
    with np.load(SRC/'task.npz',allow_pickle=False) as saved:plays=saved['first']
    if len(plays)!=verified['first_plays_checked']:raise ValueError('Original roster differs')
    freeze(d/(mode+'_SUMMARY.json'),study(plays,card))


def check(d):
    a=d/'execute_SUMMARY.json';b=d/'verify_SUMMARY.json'
    if a.read_bytes()!=b.read_bytes():raise ValueError('Independent fit differs')
    return {a.name:filehash(a),b.name:filehash(b)}
