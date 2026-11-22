"""Build and run member 0003 inside its counted supervisor, with independent replay."""
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
import pandas as pd
from . import week6_bt_hawks_v1 as hawks
from . import week6_bt_pool_v1 as pooling
from . import week6_br_v1 as br
from .batch_runtime import filehash, freeze, read

MANIFEST='cf12c0ef8dba575f82ceeebbe16a14df1ebaa82cc50e62c3d3eac82f98d2af69'
SOURCE='afe3321ce2717b590eb4b602c1050c4f8f0b8f7a8607d5bbc43cf7c717808233'


def fixture():
    rng=np.random.default_rng(53)
    n=50
    a=rng.normal(size=n)
    common=rng.normal(size=n)
    groups={}
    for label, slope in [('argument_stress/afraid',a),('other_stress/scared',a+.3*common),('health_stress/nervous',a+.2*rng.normal(size=n))]:
        level=rng.normal(size=n)
        spread=rng.uniform(size=n)
        sides=[dict(b=slope+.05*rng.normal(size=n),L=level.copy(),S=spread.copy(),n1=np.full(n,4)) for _ in range(2)]
        groups[label]={'PST1':sides}
    singles={k:{'PST1':{'reading':'stable'}} for k in groups}
    check=hawks.different_events(groups,singles,n,True,lambda:None)
    assert len(check['pairs'])==3 and check['pool']['qualifying_pairs']==3 and check['pool']['reading']=='one'
    extra='argument_stress/nervous'
    groups[extra]=groups['argument_stress/afraid'];singles[extra]={'PST1':{'reading':'could not say'}}
    check=hawks.different_events(groups,singles,n,False,lambda:None)
    assert len(check['pairs'])==5 and check['pool']['qualifying_pairs']==3
    x=np.tile([1,2,3,4],24)
    frame=pd.DataFrame(dict(id=np.repeat(np.arange(8),12),day=np.tile(np.arange(1,13),8)))
    for event in hawks.EVENTS:frame[event]=np.tile([1,2,1,3],24)
    for feeling in (*hawks.FEELINGS,hawks.SADNESS):frame[feeling]=x
    frame['worried']=6-x
    prepared=hawks.prepare(frame,True)
    assert len(prepared)==30 and len(prepared['argument_stress/afraid'])==3
    assert all(np.all(s['n0']+s['n1']==6) for s in prepared['argument_stress/afraid']['PST1'])
    data=hawks.forms.project(frame,{e:frame[e].to_numpy(float)-1 for e in hawks.EVENTS},hawks.FEELINGS)
    prior=hawks.forms.prepare(*data,True)
    for form, sides in prior['argument_stress/afraid'].items():
        fixed=prepared['argument_stress/afraid'][form]
        for old,new in zip(sides,fixed):
            for k in ('b','L','S'):
                ok=np.isfinite(new['b'])
                np.testing.assert_allclose(old[k][ok],new[k][ok],atol=1e-12)
    xx=np.array([0,1,3,3,0],dtype=np.int64);yy=np.array([1,4,2,3,1],dtype=np.int64)
    assert hawks.centered_products(xx,yy,False)==hawks.centered_products(xx,yy,True)
    for replay in (False,True):
        scores=hawks.anxiety(frame,replay,lambda:None)
        for name,expected in [('worried',-1),('nervous',1)]:
            np.testing.assert_allclose(scores[name]['slope']['interval'],[expected,expected],atol=1e-9)
    frame.loc[0,'health_stress']=0
    try:hawks.prepare(frame,False)
    except ValueError:pass
    else:raise AssertionError('Undocumented event code accepted')
    value=dict(people=32,mean=dict(estimate=3.,interval=[2.,4.]),variance_over_squared_mean=dict(estimate=2.,bootstrap_sd=1.))
    values={k:{'PST1':value} for k,_ in pooling.MOOD_0073.values()}
    for family,rule in pooling.MOOD_0073.items():
        v=pooling.select(values,[rule],'PST1')
        assert v['mean']['interval']==([-4.,-2.] if family=='unpleasant' else [2.,4.]) and v['ratio']==value['variance_over_squared_mean']
    second=dict(v,ratio=dict(estimate=4.,bootstrap_sd=2.))
    pool=pooling.pool({'003':v,'073':second})
    np.testing.assert_allclose([pool['estimate'],pool['Q']],[2.4,.8])
    print('Constructed cross-event pool, same-event exclusion, common-support fits, clinical coding, both anxiety solvers and PST9 orientation passed.')


def run(phase, dest):
    cfg=read(Path('.agent-state/data_collection_root.json'));root=Path(cfg['root'])
    if (not cfg['repair_hold'] or root.drive.lower()!='c:' or root.name!=br.ROOT_NAME or filehash(root/'DRT1_MANIFEST.json')!=br.MANIFEST):
        raise ValueError('Temporary source identity changed')
    d=root/'incoming/openesm-0003';mf=d/'MANIFEST.json'
    if filehash(mf)!=MANIFEST:raise ValueError('Changed release manifest')
    m=read(mf)
    assert m['member']=='0003' and m['licence']=='cc-by-nc-4.0' and m['release_doi']=='10.5281/zenodo.17347390'
    for f in m['files']:
        assert f['file']==Path(f['file']).name and filehash(d/f['file'])==f['sha256']
    p=d/'0003_hawks_ts.tsv'
    assert filehash(p)==SOURCE
    frame=pd.read_csv(p,sep='\t',usecols=hawks.COLUMNS,dtype={'id':str})
    replay=phase=='verify'
    panels=hawks.prepare(frame,replay)
    support={key:{k:int((np.isfinite(s[0]['b'])&np.isfinite(s[1]['b'])).sum()) for k,s in bank.items()} for key,bank in panels.items()}
    def guard():
        if (dest/'STOP_REQUEST.json').exists():raise RuntimeError('Stop requested')
    if replay:assert read(dest/'SUPPORT.json')==support
    else:freeze(dest/'SUPPORT.json',support)
    rows=hawks.forms.score(panels,'0003',guard)
    pairs=hawks.different_events(panels,rows,frame.id.nunique(),replay,guard)
    result=dict(member='0003',rows=rows,support=support,PST3=pairs,ANX1=hawks.anxiety(frame,replay,guard),people=frame.id.nunique(),reports=len(frame))
    if replay:br.verify_metric_tree(read(dest/'ORIGINAL.json'),result)
    freeze(dest/('AUDIT.json' if replay else 'ORIGINAL.json'),result)


if __name__=='__main__':
    if sys.argv[1:]==['--fixture']:
        fixture()
    elif sys.argv[1:] in (['execute'],['verify']):
        run(sys.argv[1],Path(os.environ['PST8_RESULT']).parent)
    elif not sys.argv[1:]:
        for phase in ('execute','verify'):
            subprocess.run([sys.executable,'-B','-m',__spec__.name,phase],check=True)
    else:
        raise SystemExit('Unknown operation')

