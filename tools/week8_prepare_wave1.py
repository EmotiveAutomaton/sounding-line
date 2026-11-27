"""Qualify the two first-wave MIDUS jobs with original-layout invented files."""
import argparse
import csv
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from runners.drive.cards import week8_gear as gear
from runners.drive.sealed import week7_sld3_build as original
from runners.stage14.common import read, freeze, filehash
from tools.week8_sealed import STATE, OLD, GATE, HOST

LIB = ROOT/'runners/drive/sealed'
NODE = LIB/'week8_wave1.py'
CAP = {'structure':300, 'matched':19700}
UNIT = {'structure':'SLD8-wave1-structure', 'matched':'SLD8-wave1-matched-SLD3-DN'}


def entry(sources, config, fixture):
    cap = CAP[config['mode']]
    guard = f"""import os,sys
from pathlib import Path
if os.name=='posix':
    import time,signal,resource
    hard=resource.getrlimit(resource.RLIMIT_CPU)[1]
    cap={cap} if hard==resource.RLIM_INFINITY else min(hard,{cap})
    resource.setrlimit(resource.RLIMIT_CPU,(cap,cap))
    remaining=int({int(gear.DRAIN.timestamp())}-time.time())
    if remaining<=0:sys.exit(20)
    signal.alarm(min(21600,remaining))
"""
    if fixture:
        guard += "if os.name=='nt':\n    import platform\n    platform.uname()\n"
        args = 'Path(sys.argv[1]), Path(sys.argv[2])'
    else:
        guard += "flags=[l.split()[5].split(',') for l in Path('/proc/self/mountinfo').read_text().splitlines() if l.split()[4]=='/data']\nif len(flags)!=1 or 'ro' not in flags[0]:sys.exit(13)\n"
        args = "Path('/data'), Path('/out')"
    guard += "def offline(e,a):\n    if e.startswith('socket.'):raise RuntimeError('Network refused')\nsys.addaudithook(offline)\n"
    call = ("from week6_sealed_support_v1 import SealedFailure\nfrom week8_wave1 import run\ntry:\n    run("
            + args + "," + repr(config) + ")\nexcept SealedFailure as exc:\n    sys.exit(exc.code)\n")
    if not fixture:
        call += "except Exception:\n    sys.exit(14)\n"
    return guard.encode() + original.build.single_file(sources,call)


def make_fixture(directory, real, bad=None):
    import numpy as np
    import pandas as pd
    import pyreadstat
    n=120
    ids=np.arange(1,n+1)
    fam=(ids-1)//2+1
    traits=('A1SNEURO','A1SEXTRA','A1SAGREE','A1SCONS','A1SOPEN')
    survey=pd.DataFrame(dict(M2ID=ids,M2FAMNUM=fam,**{name:1+ids%3 for name in traits}))
    people=np.repeat(ids,8)
    days=np.tile(np.arange(1,9),n)
    exposed=days%2==0
    diary=pd.DataFrame(dict(M2ID=people,M2FAMNUM=np.repeat(fam,8),A2DDAY=days))
    for i in range(1,8):
        diary['A2DF'+str(i)]=np.where(exposed,1,2) if i==1 else 2
    for pos,i in enumerate((2,4,6,7,9,10)):
        level=(people//3)%2
        lift=1+(people%3==2) if pos==0 else 1
        diary['A2DC'+str(i)]=5-level-lift*exposed
    if bad=='duplicate':diary=pd.concat([diary,diary.iloc[[0]]],ignore_index=True)
    if bad=='family':diary.loc[0,'M2FAMNUM']+=1
    if bad=='missing':diary.drop(columns=['A2DC9'],inplace=True)
    if bad=='range':diary.loc[0,'A2DC2']=6
    # The last trait can be absent without changing the registered six-channel study.
    if bad=='optional':survey.drop(columns=['A1SOPEN'],inplace=True)
    pins={}
    for role,df in [('survey',survey),('diary',diary)]:
        path=directory/real[role]['filename']
        pyreadstat.write_sav(df.astype(float),str(path))
        pins[role]=dict(filename=path.name,bytes=path.stat().st_size,sha256=filehash(path))
    return pins,n


def prepare():
    arc=Path(read(ROOT/'.agent-state/data_collection_root.json')['root'])
    receipt=arc/'_handoffs/repo-requests/DC-20261127-SLD8/SOURCE_RECEIPT.json'
    if filehash(receipt)!='78e5f3eadbc22637f1b8b2ad83e22209417c59f6039edea3451cba6362d76cae':
        raise ValueError('Original edition receipts changed')
    items=read(receipt)['contents']
    real={role:dict(filename=rec['path'],bytes=rec['bytes'],sha256=rec['sha256']) for role,rec in zip(('survey','diary'),items,strict=True)}
    if filehash(GATE)!=read(HOST)['installed_gate_sha256']:raise ValueError('Wrong gate')
    native=OLD/'lattice-20261119/fixture-reader-native'
    sys.path.insert(0,str(native))
    sources=original.modules()
    sources[NODE.stem]=NODE.read_text('utf8')
    selector=LIB/'r48_forms.py'
    sources[selector.stem]=selector.read_text('utf8')
    f=STATE/'fixtures'/('SLD8-'+uuid4().hex[:12])
    data=f/'data'
    data.mkdir(parents=True)
    good={}
    cases=[('structure',None,0),('matched',None,0),('structure','family',22),
           ('structure','duplicate',22),('structure','missing',22),('structure','optional',0),
           ('matched','range',24),('structure','hash',13)]
    for mode,bad,expected in cases:
        pins,n=make_fixture(data,real,bad)
        if bad=='hash':pins['diary']['sha256']='0'*64
        config=dict(mode=mode,files=pins,draws=40,survey_people=n)
        test=f/(mode+'-'+str(bad));test.mkdir()
        exe=f/(test.name+'.py')
        exe.write_bytes(entry(sources,config,True))
        r=subprocess.run([sys.executable,'-B',str(exe),str(data),str(test)],env=dict(os.environ,PYTHONPATH=str(native)))
        if r.returncode!=expected:raise ValueError(f'{test.name} expected {expected}, got {r.returncode}')
        if expected:
            if any(test.iterdir()):raise ValueError('Unexpected fixture output')
            continue
        subprocess.run([sys.executable,'-B','-I',str(GATE),str(test)],check=True,stdout=subprocess.DEVNULL)
        path=test/('trait.csv' if mode=='matched' else 'structure.csv')
        with path.open(newline='') as stream:rows=list(csv.DictReader(stream))
        if any(int(row['n'])!=n for row in rows):raise ValueError('Wrong roster')
        if mode=='structure':
            row,=rows
            if int(row['matched'])!=6 or int(row['openness'])!=int(bad!='optional'):raise ValueError('Wrong header check')
        else:
            estimates={int(v['contrast']):float(v['estimate']) for v in rows}
            if len(rows)!=21 or estimates[1]<=.1 or abs(estimates[2])>1e-8 or abs(estimates[18]-estimates[1])>1e-8:
                raise ValueError('Planted effect, original signs or paired contrasts differ')
        if bad is None:good[mode]=filehash(path)
    proof=f/'REHEARSAL.json'
    freeze(proof,dict(all_invented=True,forms=['fine','coarse','summary'],distinct_people_checked=True,checks=cases,outputs=good))
    for mode in ('matched',):
        unit=UNIT[mode]
        job=STATE/'sealed'/unit/'run.py'
        job.parent.mkdir(parents=True,exist_ok=True)
        payload=entry(sources,dict(mode=mode,files=real,draws=2000,survey_people=7108),False)
        if job.exists() and job.read_bytes()!=payload:raise ValueError('Reviewed source changed')
        if not job.exists():job.write_bytes(payload)
        files=[gear.AUTHORITY,ROOT/'docs/design/stage-15/week8/SLD8.md',Path(__file__).resolve(),NODE,selector,LIB/'week7_sld3.py',
               receipt,HOST,GATE,Path(gear.__file__),Path(original.__file__),Path(original.build.__file__),
               ROOT/'tools/week8_spark.ps1',ROOT/'tools/week8_sealed.py',proof,job]
        folder=STATE/('reviews' if mode=='structure' else 'pending-structure')
        folder.mkdir(exist_ok=True)
        freeze(folder/(unit+'.json'),dict(unit=unit,card='SLD8',source='midus-m1-joined',cap=CAP[mode],
             tables=['structure.csv' if mode=='structure' else 'trait.csv'],fixture_gate_passed=True,
             fixture_sha256=filehash(proof),pins={str(p):filehash(p) for p in files},
             r48=dict(entry_sha256=filehash(job),rehearsal=str(proof),ruling=gear.RULING_SHA256)))
    print('Wave-one structure and six SLD3 channels qualified on eight original-format cases.')


def release():
    prior=gear.ROOT/UNIT['structure']
    done=read(prior/'COMPLETE.json')
    path=prior/'gated-return/structure.csv'
    if not done['verified'] or filehash(path)!=done['aggregates'][path.name]:raise ValueError('Missing verified structure')
    with path.open(newline='') as stream:row,=csv.DictReader(stream)
    if row['n']!='7108' or row['matched']!='6' or row['neuroticism']!='1':raise ValueError('Binding did not pass')
    unit=UNIT['matched']
    q=read(STATE/'pending-structure'/(unit+'.json'))
    for p,h in q['pins'].items():
        if filehash(Path(p))!=h:raise ValueError('Candidate pin changed')
    q['pins'][str(path)]=filehash(path)
    q['pins'][str(prior/'COMPLETE.json')]=filehash(prior/'COMPLETE.json')
    freeze(STATE/'reviews'/(unit+'.json'),q)
    print('SLD8 matched channels ready after genuine structure check.')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['qualify','release'])
    if parser.parse_args().action=='qualify':prepare()
    else:release()
