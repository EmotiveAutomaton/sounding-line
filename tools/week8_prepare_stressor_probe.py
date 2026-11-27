"""Rehearse the SLD6 SPSS header check and freeze its original-edition entry."""
import csv
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.week8_sealed import STATE, OLD, HOST, GATE
from runners.drive.cards import week8_gear as gear
from runners.drive.sealed import week8_package as bundle, week8_stressor_contract as spec
from runners.stage14.common import filehash, freeze, read

UNIT='SLD6-wave2-structure'
CAP=300
STUDY=Path(spec.__file__)


def main():
    native=OLD/'lattice-20261119/fixture-reader-native'
    sys.path.insert(0,str(native))
    import pandas as pd
    import pyreadstat
    src=bundle.LIB/'week6-sm-science/source_map.json'
    files=read(src)['M2']
    previous=OLD/'lattice-20261120/spark-smf1-bm-main-20261122'
    released=previous/'gated-return/counts.csv'
    terminal=read(previous/'COMPLETE.json')
    if terminal['aggregate_sha256'][released.name]!=filehash(released) or not terminal['verified']:
        raise ValueError('Previous census differs')
    with released.open(newline='') as stream:
        survey_n,=[int(row['n']) for row in csv.DictReader(stream) if row['count_group']=='2']
    archive=Path(read(ROOT/'.agent-state/data_collection_root.json')['root'])
    books=[archive/'private/midus/raw/M2_P1/M2_P1_Codebook_20210129.pdf',
           archive/'private/midus/raw/M2_P2/M2_P2_Codebook_20220505.pdf']
    if [filehash(p) for p in books]!=['5640e11298d3f82b88d9868eb856bbc97169218a665dfcb34af19aa91ad813a8','48727f67a9c111ebbbebf50729a8d759a565b4021e6b0bece8b1546cf7078b10']:
        raise ValueError('Source dictionary changed')
    if filehash(GATE)!=read(HOST)['installed_gate_sha256']:
        raise ValueError('Rehearsal gate changed')
    directory=STATE/'fixtures'/(UNIT+'-'+uuid4().hex[:10])
    data=directory/'data'
    data.mkdir(parents=True)
    ids=list(range(1,33))
    columns=['B2DDAY',*['B2DF'+str(n) for n in range(1,8)],*['B2DC'+str(n) for n in spec.NEGATIVE]]
    diary=pd.DataFrame(dict(M2ID=ids,**{k:[1.]*32 for k in columns}))
    survey=pd.DataFrame(dict(M2ID=ids,M2FAMNUM=ids,**{k:[2.]*32 for k in spec.TRAITS.values()}))
    def check(case, frame, expected, optional=True):
        pins={}
        out=directory/case
        out.mkdir()
        for role,df in [('survey',frame),('diary',diary)]:
            p=data/files[role]['filename']
            pyreadstat.write_sav(df.astype(float),str(p))
            pins[role]=dict(filename=p.name,bytes=p.stat().st_size,sha256=filehash(p))
        sample=directory/(case+'.py')
        sample.write_bytes(bundle.package(STUDY,[STUDY],dict(files=pins,survey_people=32),CAP,fixture=True))
        env=dict(os.environ,PYTHONPATH=str(native))
        result=subprocess.run([sys.executable,'-B',str(sample),str(data),str(out)],env=env)
        if result.returncode!=expected:
            raise ValueError('Wrong fixture exit: '+case+' '+str(result.returncode))
        if expected:
            if any(out.iterdir()):raise ValueError('Unexpected output after refusal')
        else:
            if subprocess.check_output([sys.executable,'-I','-B',str(GATE),str(out)],text=True).strip()!='gate passed':
                raise ValueError('Fixture failed installed gate')
            with (out/'structure.csv').open(newline='') as stream:
                row,=csv.DictReader(stream)
            if int(row['n'])!=32 or any(int(row[k])!=int(k!='openness' or optional) for k in spec.TRAITS):
                raise ValueError('Unexpected header result')
    check('all',survey,0)
    check('missing_optional',survey.drop(columns='B1SOPEN'),0,False)
    check('duplicate_person',pd.concat([survey,survey.iloc[[0]]]),22)
    if [spec.day_class(v) for v in ([2]*7,[1,7,2,2,2,2,2],[1,2,1,2,2,2,2],[2,2,2,2,2,1,2],[2,2,2,2,7,2,2])]!=[0,1,None,3,None]:
        raise ValueError('Exclusive stressor classification differs')
    evidence=directory/'REHEARSAL.json'
    freeze(evidence,dict(all_data='constructed',assembled=filehash(directory/'all.py'),checks=['full survey roster','optional absence','ambiguous person refusal','pure and mixed days','joint gate','repeat']))
    entry=STATE/'sealed'/UNIT/'run.py'
    entry.parent.mkdir(exist_ok=True,parents=True)
    program=bundle.package(STUDY,[STUDY],dict(files=files,survey_people=survey_n),CAP)
    if entry.exists() and entry.read_bytes()!=program:raise ValueError('Existing entry differs')
    if not entry.exists():entry.write_bytes(program)
    pins=[gear.AUTHORITY,ROOT/'docs/design/stage-15/week8/SLD6.md',*books,src,previous/'COMPLETE.json',released,
          STUDY,Path(__file__).resolve(),Path(gear.__file__),Path(bundle.__file__),bundle.SUPPORT,bundle.RELEASE,HOST,GATE,
          ROOT/'tools/week8_sealed.py',ROOT/'tools/week8_spark.ps1',evidence,entry]
    freeze(STATE/'reviews'/(UNIT+'.json'),dict(card='SLD6',unit=UNIT,source='midus-m2-joined',cap=CAP,
           tables=['structure.csv'],fixture_gate_passed=True,fixture_sha256=filehash(evidence),pins={str(f):filehash(f) for f in pins}))
    print('SLD6 original-layout header check and refusal rehearsed.',filehash(entry))

if __name__=='__main__':
    main()
