"""CP1 exact sufficient-statistic kernel; fixed conversation permutation bank.

DESIGN CHECK: LESSONS 2--5, CONTROLS 1--7. The reply bundle is shuffled within
conversation, never the words. Identical deference/assertion gives exact zero.
Complementary versus convergent plants must reverse the primary; absent variance
or rank is unsupported, never a fitted zero. Whole-conversation bootstrap only.
"""
import hashlib
import math
import numpy as np

PERMUTATIONS=200
BOOTSTRAPS=2000
NULL_SEED=20261112
BOOT_SEED=20261107
MOMENTS=34
VARIANCE_EPS=64*np.finfo(np.float64).eps


def resolved_variance(second,mean):
    variance=second-mean*mean
    scale=np.maximum(np.abs(second),mean*mean)
    return np.where(variance>VARIANCE_EPS*scale,variance,0.0)
KEYS=('primary','assertion_to_deference','assertion_to_assertion','warmth_to_warmth','graded_edit_gap')
VIEWS=('all','admin-00','admin-01','admin-10','admin-11')


def seed(*parts):
    return int.from_bytes(hashlib.sha256('|'.join(map(str,parts)).encode()).digest()[:8],'big')


def permutation(n, conversation, index, view='all'):
    return np.random.Generator(np.random.PCG64(seed('CP1-null',NULL_SEED,view,conversation,index))).permutation(n)


def draw_counts(n, draw, view='all'):
    if n<1:raise ValueError('No conversation clusters')
    rng=np.random.Generator(np.random.PCG64(seed('CP1-bootstrap',BOOT_SEED,view,draw)))
    return np.bincount(rng.integers(0,n,size=n),minlength=n).astype(np.float64)


def pair_array(rows):
    """Columns: parent A, parent W, parent edits, reply W/D/A, reply edits."""
    value=np.asarray([[r['parent_assertion'],r['parent_warmth'],r['parent_edit_count'],
                       r['reply_warmth'],r['reply_deference'],r['reply_assertion'],r['reply_edit_count']]
                      for r in rows],dtype=np.float64)
    if value.ndim!=2 or value.shape[1]!=7 or not np.isfinite(value).all() or (value<0).any():
        raise ValueError('Invalid prepared reply-pair values')
    return value


def moment(rows, order=None):
    rows=np.asarray(rows,dtype=np.float64)
    if rows.ndim!=2 or rows.shape[1]!=7 or len(rows)==0:raise ValueError('Empty or malformed conversation')
    order=np.arange(len(rows)) if order is None else np.asarray(order)
    if sorted(order.tolist())!=list(range(len(rows))):raise ValueError('Reply permutation is not a bijection')
    x=rows[:,0]; warm=rows[:,1]; reply=rows[order,3:6]
    # Fixed scaling is only conditioning; reported interaction is fully standardized.
    gap=(rows[order,6]-rows[:,2])/1_000_000.0
    design=np.column_stack((np.ones(len(rows)),x,gap,x*gap))
    return np.concatenate(((design.T@design).reshape(-1),(design.T@reply).reshape(-1),
         np.sum(reply*reply,axis=0),np.array([np.sum(warm),warm@warm,warm@reply[:,0]])))


def conversation_bank(rows, conversation, view='all', check=None):
    if view not in VIEWS:raise ValueError('Unknown CP view')
    values=np.empty((PERMUTATIONS+1,MOMENTS),dtype=np.float64)
    values[0]=moment(rows)
    for index in range(PERMUTATIONS):
        if check:check()
        values[index+1]=moment(rows,permutation(len(rows),conversation,index,view))
    return values


def evaluate(total):
    """Return observed minus mean of exactly200 within-conversation shuffles."""
    total=np.asarray(total,dtype=np.float64)
    if total.shape!=(PERMUTATIONS+1,MOMENTS) or not np.isfinite(total).all():raise ValueError('Incomplete moment bank')
    b=total[:,:16].reshape(-1,4,4); c=total[:,16:28].reshape(-1,4,3)
    n=b[:,0,0]
    if (n<=0).any() or not np.array_equal(n,np.full_like(n,n[0])):raise ValueError('Permutation population changed')
    mx=b[:,0,1]/n; vx=resolved_variance(b[:,1,1]/n,mx)
    my=c[:,0,:]/n[:,None]; vy=resolved_variance(total[:,28:31]/n[:,None],my)
    slopes=np.full_like(my,np.nan)
    valid=(vx[:,None]>0)&(vy>0)
    numer=c[:,1,:]/n[:,None]-mx[:,None]*my
    np.divide(numer,np.sqrt(np.maximum(vx[:,None]*vy,0)),out=slopes,where=valid)
    mw=total[:,31]/n; vw=resolved_variance(total[:,32]/n,mw)
    warm=np.full_like(n,np.nan)
    np.divide(total[:,33]/n-mw*my[:,0],np.sqrt(np.maximum(vw*vy[:,0],0)),out=warm,where=(vw>0)&(vy[:,0]>0))
    def excess(values):
        return float(values[0]-np.mean(values[1:])) if np.isfinite(values).all() else None
    d=slopes[:,1]; a=slopes[:,2]
    primary=excess(d-a)
    result={'primary':primary,'assertion_to_deference':excess(d),'assertion_to_assertion':excess(a),
        'warmth_to_warmth':excess(warm),'graded_edit_gap':None,
        'observed':{'assertion_to_deference':float(d[0]) if np.isfinite(d[0]) else None,
                    'assertion_to_assertion':float(a[0]) if np.isfinite(a[0]) else None,
                    'warmth_to_warmth':float(warm[0]) if np.isfinite(warm[0]) else None},
        'null_mean':{'assertion_to_deference':float(np.mean(d[1:])) if np.isfinite(d[1:]).all() else None,
                    'assertion_to_assertion':float(np.mean(a[1:])) if np.isfinite(a[1:]).all() else None,
                    'warmth_to_warmth':float(np.mean(warm[1:])) if np.isfinite(warm[1:]).all() else None},
        'graded_invalid_permutations':0,'pairs':int(n[0])}
    # Conditional continuous-gap diagnostic. Recomputed after moving the complete
    # reply bundle, including reply edit-count; no fixed post-shuffle gap shortcut.
    mg=b[:,0,2]/n; vg=resolved_variance(b[:,2,2]/n,mg)
    okay=(vx>0)&(vg>0)&(vy[:,1]>0)&(vy[:,2]>0)
    result['graded_invalid_permutations']=int(np.sum(~okay))
    if not okay.all():return result
    sx=np.sqrt(vx); sg=np.sqrt(vg); t=np.zeros_like(b)
    t[:,0,0]=1;t[:,0,1]=-mx/sx;t[:,1,1]=1/sx;t[:,0,2]=-mg/sg;t[:,2,2]=1/sg
    t[:,0,3]=mx*mg/(sx*sg);t[:,1,3]=-mg/(sx*sg);t[:,2,3]=-mx/(sx*sg);t[:,3,3]=1/(sx*sg)
    norm=np.matmul(np.swapaxes(t,1,2),np.matmul(b,t))/n[:,None,None]
    eig=np.linalg.eigvalsh(norm)
    rank_ok=(eig[:,0]>1e-10*eig[:,-1])&(eig[:,-1]>0)
    result['graded_invalid_permutations']=int(np.sum(~rank_ok))
    if not rank_ok.all():return result
    centered=c[:,:,1:3]-b[:,:,0,None]*my[:,None,1:3]
    rhs=np.matmul(np.swapaxes(t,1,2),centered)/n[:,None,None]/np.sqrt(vy[:,None,1:3])
    coefficients=np.linalg.solve(norm,rhs)
    residual=np.max(np.abs(np.matmul(norm,coefficients)-rhs))
    if residual>1e-8:raise ValueError('Continuous-gap normal equation residual')
    result['graded_edit_gap']=excess(coefficients[:,3,0]-coefficients[:,3,1])
    return result


def evaluate_reference(total):
    """Independent centered-moment / least-squares implementation for full replay."""
    total=np.asarray(total,dtype=np.float64)
    if total.shape!=(201,34):raise ValueError('Incomplete independent bank')
    all_metrics=[]
    for row in total:
        b=row[:16].reshape(4,4); c=row[16:28].reshape(4,3); n=b[0,0]
        mx=b[0,1]/n; my=c[0]/n; vx=b[1,1]/n-mx**2; vy=row[28:31]/n-my**2
        if vx<=64*np.finfo(float).eps*max(abs(b[1,1]/n),mx**2):vx=0.0
        for j in range(3):
            if vy[j]<=64*np.finfo(float).eps*max(abs(row[28+j]/n),my[j]**2):vy[j]=0.0
        values={}
        for label,col in [('assertion_to_deference',1),('assertion_to_assertion',2)]:
            values[label]=(c[1,col]/n-mx*my[col])/math.sqrt(vx*vy[col]) if vx>0 and vy[col]>0 else None
        mw=row[31]/n; vw=row[32]/n-mw**2
        if vw<=64*np.finfo(float).eps*max(abs(row[32]/n),mw**2):vw=0.0
        values['warmth_to_warmth']=(row[33]/n-mw*my[0])/math.sqrt(vw*vy[0]) if vw>0 and vy[0]>0 else None
        values['primary']=values['assertion_to_deference']-values['assertion_to_assertion'] if all(values[k] is not None for k in ('assertion_to_deference','assertion_to_assertion')) else None
        mg=b[0,2]/n; vg=b[2,2]/n-mg**2; interaction=None
        if vg<=64*np.finfo(float).eps*max(abs(b[2,2]/n),mg**2):vg=0.0
        if vx>0 and vg>0 and min(vy[1:])>0:
            sx,sg=math.sqrt(vx),math.sqrt(vg)
            t=np.array([[1,-mx/sx,-mg/sg,mx*mg/(sx*sg)],[0,1/sx,0,-mg/(sx*sg)],[0,0,1/sg,-mx/(sx*sg)],[0,0,0,1/(sx*sg)]])
            gram=t.T@b@t/n
            eigen=np.linalg.eigvalsh(gram)
            if eigen[0]>1e-10*eigen[-1] and eigen[-1]>0:
                difference=(c[:,1]-my[1]*b[:,0])/math.sqrt(vy[1])-(c[:,2]-my[2]*b[:,0])/math.sqrt(vy[2])
                rhs=t.T@difference/n
                coefficient,_,rank,_=np.linalg.lstsq(gram,rhs,rcond=1e-10)
                if rank==4 and np.max(np.abs(gram@coefficient-rhs))<=1e-8:interaction=float(coefficient[3])
        values['graded_edit_gap']=interaction;all_metrics.append(values)
    result={}
    for key in KEYS:
        vals=[m[key] for m in all_metrics]
        result[key]=vals[0]-math.fsum(vals[1:])/200 if all(x is not None for x in vals) else None
    return result


def uncertainty(point, draws, below_floor=False):
    out={}
    for key in KEYS:
        values=[row[key] for row in draws]; good=[v for v in values if v is not None and math.isfinite(v)]
        bar=.02 if key=='primary' else None
        if below_floor or len(good)!=BOOTSTRAPS or point[key] is None:
            out[key]={'estimate':point[key],'interval':None,'se':None,'bar':bar,'sees':None,'supports_at':None,
                'valid_draws':len(good),'status':'below_floor_descriptive' if below_floor else 'unsupported_or_incomplete_uncertainty'}
            continue
        lo,hi=np.quantile(np.asarray(good),[.025,.975],method='linear');se=float(np.std(good,ddof=1))
        status='secondary_descriptive'
        if bar is not None:
            status='positive_candidate' if lo>bar else 'negative_candidate' if hi<-bar else 'within_practical_band' if lo>=-bar and hi<=bar else 'inconclusive'
        out[key]={'estimate':point[key],'interval':[float(lo),float(hi)],'se':se,'bar':bar,'sees':2.8*se,
            'supports_at':bar+2.8*se if bar is not None else None,'valid_draws':BOOTSTRAPS,'status':status}
    return out
