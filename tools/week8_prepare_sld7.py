"""Qualify the three-wave gain comparison and reconstruct original published memberships."""
import csv
import os
from pathlib import Path
from runpy import run_path
import subprocess
import sys
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import week8_prepare_sld5 as parent,week8_study_package as package
from runners.stage14.common import read,freeze,filehash

UNIT='SLD7-three-wave-marriage-gain-DN'
CAP=20000
NODE=parent.bundle.LIB/'week8_sld7.py'


def counts(path,second):
    out={}
    with path.open(newline='') as f:
        for row in csv.DictReader(f):
            key=row['group']+('-'+row['reading'] if second else '')
            if out.setdefault(key,int(row['n']))!=int(row['n']):
                raise ValueError('Conflicting previously released memberships')
    return out


def main():
    sys.path.insert(0,str(parent.NATIVE))
    import numpy as np
    import pandas as pd
    import pyreadstat
    src=Path(read(ROOT/'.agent-state/data_collection_root.json')['root'])/'_handoffs/repo-requests/DC-20261124-02/SLD2_SOURCE.json'
    rec=read(src)
    if rec['slug']!='midus-m1m2m3-surveys' or rec['requested_access']!='read-only':raise ValueError('Original binding differs')
    pins=[(Path(f['mount_path']).name,f['bytes'],f['sha256']) for f in sorted(rec['local_files'],key=lambda v:v['wave'])]
    prev=parent.week7_gear.ROOT/'SLD2-marital-role-20261124'
    loss=parent.gear.ROOT/'SLD5-loss-comparison'
    p2=prev/'gated-return/purpose.csv';p5=loss/'gated-return/purpose.csv'
    if filehash(p2)!=read(prev/'COMPLETE.json')['aggregate'] or filehash(p5)!=read(loss/'COMPLETE.json')['aggregates']['purpose.csv']:
        raise ValueError('Published return changed')
    known,loss_counts=counts(p2,True),counts(p5,False)
    test=run_path(str(parent.TEST))
    old=test['study']
    frames,original=test['panels']()
    for i,f in enumerate(frames):
        new=f.loc[240:399].copy()
        new.index=pd.Index(np.arange(400,560),name='M2ID')
        new['M2FAMNUM']=new.index//2+1
        gain=new.index<480
        new[old.STATUS[i]]=np.where(gain & (i>0),1,5)
        y=2+3*(new.index%2)+(gain & (i==1)).astype(int)
        for j,k in enumerate(old.old.PURPOSE[i]):
            new[k]=8-y if j==0 else y
        frames[i]=pd.concat([f,new])
    code=[*parent.MODULES,NODE,parent.bundle.LIB/'r48_forms.py']
    scratch=parent.STATE/'fixtures'/('SLD7-'+uuid4().hex[:10])
    mount=scratch/'data';mount.mkdir(parents=True)
    source=[]
    for f,(name,_,_) in zip(frames,pins,strict=True):
        p=mount/name
        pyreadstat.write_sav(f.reset_index().astype(float),str(p))
        source.append((name,p.stat().st_size,filehash(p)))
    known_loss={'1':160,'2':80,'3':80,'4':80}
    cfg=dict(files=source,known=original,loss_counts=known_loss,draws=45)
    def rehearse(label,code_expected):
        path=scratch/(label+'.py');path.write_bytes(parent.bundle.package(NODE,code,cfg,CAP,fixture=True))
        out=scratch/label;out.mkdir()
        rc=subprocess.run([sys.executable,'-B',str(path),str(mount),str(out)],env=dict(os.environ,PYTHONPATH=str(parent.NATIVE))).returncode
        if rc!=code_expected or rc and any(out.iterdir()):raise ValueError('Incorrect native fixture disposition')
        return out
    out=rehearse('gain',0)
    package.gate(out)
    with (out/'purpose.csv').open(newline='') as f:rows=list(csv.DictReader(f))
    for kind in ('1','2'):
        selected=[r for r in rows if r['form']==kind]
        if [int(r['n']) for r in selected]!=[80]*3 or not np.allclose([float(r['estimate']) for r in selected],[1,0,-1]):
            raise ValueError('Known three-wave trajectory differs')
    cfg['loss_counts']=dict(known_loss,**{'1':159})
    rehearse('historical-mismatch',14)
    from independent_release import Entry,decide
    large=frozenset(range(50))
    if decide([(1,'test',[Entry({'n':49},frozenset(range(49)))])],large,[large])[0]:
        raise ValueError('Small complement disclosed')
    ev=scratch/'REHEARSAL.json'
    freeze(ev,dict(constructed=True,forms=['fine','coarse','summary'],distinct_people_checked=True,source_form='Three original-layout SPSS files',checks=['age weighting','three signed matched changes',
        'baseline-adjusted descriptions','loss membership reconstruction','small-complement suppression','independent replay','installed gate'],table=filehash(out/'purpose.csv')))
    real=dict(files=pins,known=known,loss_counts=loss_counts,draws=2000)
    closure=[Path(__file__),Path(parent.__file__),src,p2,p5,prev/'COMPLETE.json',loss/'COMPLETE.json',parent.TEST,
             ROOT/'docs/design/stage-15/week8/SLD7.md',ROOT/'docs/design/stage-15/week8/SLD5.md',parent.STATE/'SLD_CODEBOOKS.json',
             *code,Path(parent.bundle.__file__),parent.bundle.SUPPORT,parent.bundle.RELEASE]
    print(UNIT,package.admit(UNIT,'SLD7',rec['slug'],CAP,['purpose.csv'],parent.bundle.package(NODE,code,real,CAP),ev,closure))


if __name__=='__main__':
    main()
