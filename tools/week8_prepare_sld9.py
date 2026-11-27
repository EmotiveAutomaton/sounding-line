"""Rehearse and admit the single original wave-two trait and well-being study."""
import csv
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import week8_prepare_stressor_studies as earlier, week8_study_package as package
from runners.stage14.common import read,freeze,filehash

STATE,OLD=earlier.STATE,earlier.OLD
UNIT='SLD9-wave2-trait-wellbeing'
CARD='SLD9'
CAP=20000
MODULE='week8_sld9'


def main():
    import numpy as np
    from tools.week8_sealed import GATE
    sources=earlier.modules()
    node=earlier.LIB/(MODULE+'.py')
    sources[MODULE]=node.read_text('utf8')
    scratch=STATE/'fixtures'/('SLD9-'+uuid4().hex[:10])
    mount=scratch/'data'
    mount.mkdir(parents=True)
    native=OLD/'lattice-20261119/fixture-reader-native'
    sys.path.insert(0,str(native))
    import pyreadstat
    synthetic,n=earlier.invented(mount)
    meta=synthetic['M2']['survey']
    path=mount/meta['filename']
    frame,_=pyreadstat.read_sav(str(path))
    rng=np.random.default_rng(1995)
    neuro=rng.integers(1,5,size=n)
    other=rng.integers(1,5,size=n)
    frame['B1SNEURO']=neuro
    frame['B1SOPEN']=other
    for key in ('B1SAGREE','B1SEXTRA','B1SCONS1'):
        frame[key]=np.clip(neuro+rng.integers(-1,2,size=n),1,4)
    for letter in 'UEGRSA':
        frame['B1SPWB'+letter+'2']=25+3*other if letter=='G' else 10+2*neuro
    frame['B1SCTRL']=2+other
    frame['B1SGENER']=6+3*other
    frame['B1SE3']=11-(other+2)
    def configure():
        pyreadstat.write_sav(frame,str(path))
        meta.update(bytes=path.stat().st_size,sha256=filehash(path))
        return dict(files=synthetic,history={'count/1':n,'count/2':n},sld4={},draws=32)
    def invoke(label,config,code):
        prog=scratch/(label+'.py')
        prog.write_bytes(package.entry(sources,MODULE,config,CAP,True))
        out=scratch/label;out.mkdir()
        result=subprocess.run([sys.executable,'-B',str(prog),str(mount),str(out)],env=dict(os.environ,PYTHONPATH=str(native)),check=False)
        if result.returncode!=code:raise ValueError(f'{label} expected {code}, got {result.returncode}')
        if code and list(out.iterdir()):raise ValueError('Withheld run created output')
        return out
    cfg=configure()
    out=invoke('planted',cfg,0)
    package.gate(out)
    table=out/'correlations.csv'
    with table.open(newline='') as f:
        rows={(int(r['form']),int(r['trait']),int(r['scale'])):r for r in csv.DictReader(f)}
    for key in ((1,2,1),(1,5,3),(2,5,3),(1,5,9)):
        if abs(float(rows[key]['estimate'])-1)>1e-10 or int(rows[key]['n'])!=n:
            raise ValueError('Planted direction, conditional fit or complete count failed')
    if any(form==2 and trait==2 for form,trait,scale in rows):
        raise ValueError('Self-adjusted Neuroticism was estimable')
    # Purely Neuroticism-driven outcome leaves no adjusted rank variation.
    if any(form==2 and scale==1 for form,trait,scale in rows):
        raise ValueError('Constant residual reported')
    frame.loc[0,'B1SE3']=98
    invoke('one-person-complement',configure(),12)
    evidence=scratch/'REHEARSAL.json'
    freeze(evidence,dict(constructed=True,people=n,checks=['original-layout pair','known appearance of a spurious unadjusted association','conditional disappearance',
        'rank ties','self-partial undefined','standing direction','original-source replay','withheld one-person complement','installed gate'],result=filehash(table)))
    history,extra,docs=earlier.historical()
    current=earlier.LIB/'week6-sm-science/source_map.json'
    config=dict(files={'M2':read(current)['M2']},history=history,sld4=extra,draws=2000)
    closure=[node,Path(__file__),Path(earlier.__file__),Path(earlier.design.__file__),earlier.LIB/'week7_sld4.py',earlier.LIB/'week8_sld6.py',
             earlier.OLDSTATE/'MIB1_primary.entry.py',earlier.OLDSTATE/'MIB1_NUMERIC_QUALIFIED.json',current,STATE/'SLD_CODEBOOKS.json',
             STATE/'codebooks/wave2.txt',ROOT/'docs/design/stage-15/week8/SLD9.md',*docs,GATE]
    print(UNIT,package.admit(UNIT,CARD,'midus-m2-joined',CAP,['correlations.csv'],package.entry(sources,MODULE,config,CAP,False),evidence,closure))

if __name__=='__main__':
    main()
