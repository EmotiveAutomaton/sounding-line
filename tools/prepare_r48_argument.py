"""Qualify the aggregate-only retrospective D5.s recovery on constructed diaries."""
import csv
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import r48_retro as retro, week8_prepare_stressor_studies as old, week8_study_package as package
from runners.stage14.common import filehash, freeze, read


def main():
    import pandas as pd
    native=old.OLD/'lattice-20261119/fixture-reader-native'
    sys.path.insert(0,str(native))
    import pyreadstat
    path=retro.STATE
    scratch=path/('qualification-'+uuid4().hex[:12])
    modules=scratch/'modules'
    modules.mkdir(parents=True)
    sources=old.modules()
    library=old.LIB/'week6-sm-science'
    mapping=read(library/'source_map.json')
    for name in ('r48_forms','r48_argument','week7_mib3'):
        sources[name]=(old.LIB/(name+'.py')).read_text('utf8')
    for name,source in sources.items():
        (modules/(name+'.py')).write_text(source,encoding='utf8')
    sys.path[:0]=[str(modules),str(library)]
    import daily_fixture, mi_source_contract_v1
    data=daily_fixture.records()
    day=mi_source_contract_v1.fields('M2')['study_day']
    seen={}
    for row in data['diary']:
        if row['B2DF1']==1 and row[day]<8:
            person=row['M2ID']
            seen[person]=seen.get(person,0)+1
            row['B2DF1WC6']=1+(seen[person]-1)%2
    n=len(data['survey'])
    mount=scratch/'data'
    mount.mkdir()
    def save():
        local={}
        for role,items in data.items():
            dest=mount/mapping['M2'][role]['filename']
            pyreadstat.write_sav(pd.DataFrame(items).astype(float),str(dest))
            local[role]=dict(filename=dest.name,bytes=dest.stat().st_size,sha256=filehash(dest))
        return dict(files={'M2':local},history={'count/1':n},sld4={})
    demo=dict(sources)
    demo['argument_bank']=demo['argument_bank'].replace('DRAWS = 2000','DRAWS = 32')
    if demo['argument_bank']==sources['argument_bank']:
        raise ValueError('Constructed draw shortcut did not bind')
    def invoke(label, expected):
        fixture=save()
        prog=scratch/(label+'.py')
        prog.write_bytes(package.entry(demo,'r48_argument',fixture,retro.CAP,True))
        out=scratch/label
        out.mkdir()
        result=subprocess.run([sys.executable,'-B',str(prog),str(mount),str(out)],
             env=dict(os.environ,PYTHONPATH=str(native),OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2'))
        if result.returncode!=expected:
            raise ValueError(f'{label} returned {result.returncode}, expected {expected}')
        if expected:
            if list(out.iterdir()):
                raise ValueError('Withheld fixture emitted output')
            return
        package.gate(out)
        with (out/'argument.csv').open(newline='') as stream:
            rows=list(csv.DictReader(stream))
        if {int(r['comparison']) for r in rows}!={1,2,3} or any(int(r['n'])!=n for r in rows):
            raise ValueError('Constructed roster or registered forms differ')
    invoke('eligible',0)
    for row in data['diary']:
        if row['B2DF1']==1:
            row['B2DF1WC6']=1
    invoke('one-arm',12)
    entry=path/'run.py'
    historic,newer,files=old.historical()
    cfg=dict(files={'M2':mapping['M2']},history=historic,sld4=newer)
    payload=package.entry(sources,'r48_argument',cfg,retro.CAP,False)
    if entry.exists() and entry.read_bytes()!=payload:
        raise ValueError('Existing prospective entry differs')
    if not entry.exists():
        entry.write_bytes(payload)
    proof=scratch/'REHEARSAL.json'
    freeze(proof,dict(forms=['fine','coarse','summary'],distinct_people_checked=True,constructed_people=n,
           fixture_draws=32,real_draws=2000,eligible=filehash(scratch/'eligible/argument.csv'),one_arm_native=12))
    pins=[entry,proof,old.LIB/'r48_argument.py',old.LIB/'r48_forms.py',old.LIB/'week7_mib3.py',
          library/'source_map.json',Path(__file__),Path(retro.__file__),ROOT/'tools/r48_retro_queue.ps1',
          Path(package.__file__),Path(old.__file__),Path(retro.spark.__file__),retro.spark.HOST,
          retro.spark.GATE,retro.gear.RULING,old.OLDSTATE/'MIB1_primary.entry.py',*files]
    freeze(path/'REVIEW.json',dict(unit=retro.UNIT,source='midus-m2-joined',cap=retro.CAP,
           rehearsal=str(proof),ruling=retro.gear.RULING_SHA256,pins={str(p):filehash(p) for p in pins}))
    print('Retrospective D5.s qualified on complete and one-arm constructed diaries.')


if __name__=='__main__':
    main()
