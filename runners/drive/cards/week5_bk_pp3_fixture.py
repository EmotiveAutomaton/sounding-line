"""Native full401-fit PP3.p1 continuation and fresh-source verification proof."""
from pathlib import Path
import argparse,json,shutil,subprocess,sys,time
import numpy as np
from threadpoolctl import threadpool_limits
from . import week5_bk_pp3_tree as card
from . import week4_pp3_project_cost as source
from .week5_bk_klicke_intake import read,write,digest
from .batch_runtime import REPO


def _known_checks():
    before=card.old.wide_fixture();selected,census=source.subset(before)
    assert len(selected[2])==270 and census['selected_projects']==3
    assert np.array_equal(np.unique(selected[3]),np.arange(3))
    assert np.array_equal(np.unique(selected[4]),np.arange(6))
    x,c,y,p,a=selected;d=card.old.designs(x,c,p,'p',1.)
    assert all(not np.any(p[train]==project) and np.all(p[test]==project) for project,train,test,_ in d)
    current=card.old.evaluate(d,y,p,a,True)
    assert card.model.f1(current['cm3'][0].sum(axis=0))>.95
    z=card.old.evaluate(card.old.designs(np.zeros_like(x),np.zeros_like(c),p,'p',1.),y,p,a,True)
    assert np.array_equal(z['cm3'][0],z['base3'])
    # Complete bank shapes, with known constant predictions: exact null both
    # against the prior and reassignment mean, not only a small tolerance.
    fixed=card.summarize(z,[[z for _ in range(200)] for _ in range(2)],p,a)
    assert all(r['effect']==0 and r['state']=='null' for r in fixed['primary'].values())
    restored=card.restored(card.serialized(current))
    assert all(np.array_equal(v,restored[k]) for k,v in current.items())
    # The authenticated human cost census has one retained author per selected
    # project. Exercise that shape without reading or scoring human rows.
    three=card.old.evaluate(d,y,p,p,True)
    assert np.array_equal(three['cm3'].sum(axis=1),current['cm3'].sum(axis=1))
    zero3=card.old.evaluate(card.old.designs(np.zeros_like(x),np.zeros_like(c),p,'p',1.),y,p,p,True)
    summary3=card.summarize(zero3,[[zero3 for _ in range(200)] for _ in range(2)],p,p)
    assert all(r['effect']==0 and r['state']=='null' for r in summary3['primary'].values())
    return dict(whole_project_membership=True,contiguous_project_scoped_authors=True,held_project_disjoint=True,
                separate_trees_known_signal=True,constant_full_bank_exact_null=True,loss_and_confusion_roundtrip=True,
                actual_three_author_shape_exact=True)


def known_checks():
    with threadpool_limits(limits=1):return _known_checks()


def run(root):
    root.mkdir(parents=True,exist_ok=False);start=time.process_time();checks=known_checks()
    config=dict(card='BK-PP3.p1',mode='constructed',max_new_draws=21)
    first=card.execute(root/'pause',{},config)
    assert first['status']=='yielded' and first['completed_units']==21 and first['new_fits']==21
    assert len(list((root/'pause/fits').glob('*.json.gz')))==21 and not (root/'pause/SUMMARY.json').exists()
    before={p.relative_to(root/'pause').as_posix():digest(p) for p in (root/'pause').rglob('*') if p.is_file()}
    shutil.copytree(root/'pause',root/'full');last=card.execute(root/'full',{},dict(config,max_new_draws=401))
    assert last['new_fits']==380 and last['complete_fits']==401
    assert before=={p.relative_to(root/'pause').as_posix():digest(p) for p in (root/'pause').rglob('*') if p.is_file()}
    child=subprocess.run([sys.executable,'-X','utf8','-B','-m',__spec__.name,'--output',str(root),'--replay'],capture_output=True,text=True)
    if child.returncode:raise RuntimeError(child.stderr[-3000:])
    replay=json.loads(child.stdout);assert replay['new_fits']==401
    false=root/'tampered';shutil.copytree(root/'full',false);path=false/'fits/real.json.gz';record=read(path)
    record['cm3'][0][0][0][0]+=1;path.unlink();write(path,record)
    try:card.verify(false,{},config)
    except ValueError:pass
    else:raise AssertionError('Tampered classifier checkpoint passed')
    checks.update(five_percent_actual_boundary=True,all401_native_fits=True,reused21_without_recompute=True,
                  independent401_fits=True,tampered_fit_refused=True,predecessor_unchanged=True)
    proof=dict(passed=True,constructed=True,checks=checks,full_native_replay=replay,
        cpu_seconds=time.process_time()-start+replay['fixture_process_cpu_seconds'],
        source_sha256={str(Path(m.__file__).relative_to(REPO)):digest(m.__file__) for m in (card,source,card.old,card.model)},fixture_sha256=digest(__file__))
    write(root/'FIXTURE.json',proof);return dict(passed=True,proof=str(root/'FIXTURE.json'),cpu_seconds=proof['cpu_seconds'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);p.add_argument('--replay',action='store_true');a=p.parse_args()
    if a.replay:
        result=card.verify(a.output/'full',{},dict(card='BK-PP3.p1',mode='constructed',max_new_draws=21))
        result['fixture_process_cpu_seconds']=time.process_time();print(json.dumps(result))
    else:print(json.dumps(run(a.output.resolve())))
