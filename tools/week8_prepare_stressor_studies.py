"""Qualify the SLD6 effect and shuffled-trait jobs on a planted original-layout diary."""
import ast
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.week8_sealed import GATE, HOST, OLD, STATE
from runners.drive.cards import week7_gear, week8_gear as gear
from runners.drive.sealed import week7_sld3_build as original
from runners.drive.sealed import week8_stressor_contract as design
from runners.stage14.common import read, filehash, freeze
LIB=ROOT/'runners/drive/sealed'
OLDSTATE=OLD/'week7-phase1'
CAP=3100
SHUFFLE_CAP=4100
assert CAP*5+SHUFFLE_CAP+300<=gear.ROW_LIMITS['SLD6']


def modules():
    path=OLDSTATE/'MIB1_primary.entry.py'
    if filehash(path)!=read(OLDSTATE/'MIB1_NUMERIC_QUALIFIED.json')['entry']:
        raise ValueError('Qualified historic implementation changed')
    assignment,=[a for a in ast.parse(path.read_bytes()).body if isinstance(a,ast.Assign) and getattr(a.targets[0],'id','')=='SOURCES']
    values=ast.literal_eval(assignment.value)
    contract=Path(design.__file__).read_text('utf8')
    values['week8_stressor_contract']=contract.replace('from runners.drive.cards.week6_sealed_support_v1 import','from week6_sealed_support_v1 import')
    for k in ('week7_sld4','week8_sld6'):
        values[k]=(LIB/(k+'.py')).read_text('utf8')
    return values


def program(sources,config,fixture):
    cap=SHUFFLE_CAP if config['mode']=='shuffle' else CAP
    guard="""import os,sys
from pathlib import Path
if os.name=='posix':
    import resource,signal,time
    cap=CAP_VALUE
    hard=resource.getrlimit(resource.RLIMIT_CPU)[1]
    if hard!=resource.RLIM_INFINITY:cap=min(hard,cap)
    resource.setrlimit(resource.RLIMIT_CPU,(cap,cap))
    remaining=int(DRAIN_VALUE-time.time())
    if remaining<=0:sys.exit(20)
    signal.alarm(min(21600,remaining))
""".replace('CAP_VALUE',str(cap)).replace('DRAIN_VALUE',str(int(gear.DRAIN.timestamp())))
    if not fixture:
        guard+="flags=[r.split()[5].split(',') for r in Path('/proc/self/mountinfo').read_text().splitlines() if r.split()[4]=='/data']\nif len(flags)!=1 or 'ro' not in flags[0]: sys.exit(13)\n"
    elif os.name=='nt':
        guard+="import platform\nplatform.uname()\n"
    guard+="def offline(event,args):\n    if event.startswith('socket.'):raise RuntimeError('Network refused')\nsys.addaudithook(offline)\n"
    args="Path(sys.argv[1]),Path(sys.argv[2])" if fixture else "Path('/data'),Path('/out')"
    call="from week6_sealed_support_v1 import SealedFailure\nfrom week8_sld6 import run\ntry:\n    run("+args+","+repr(config)+")\nexcept SealedFailure as exc:\n    sys.exit(exc.code)\n"
    if not fixture:
        call+="except Exception:\n    sys.exit(14)\n"
    return guard.encode()+original.build.single_file(sources,call)


def historical():
    bank=OLDSTATE/'MIB_RELEASED_COUNTS.json'
    docs=[bank]
    extra={}
    for trait,suffix in [('agreeableness','admission2'),('extraversion','transport2')]:
        root=week7_gear.ROOT/('SLD4-'+trait+'-wave2-20261123-'+suffix)
        term=read(root/'COMPLETE.json')
        if not term['verified']:raise ValueError('Prior trait study unverified')
        docs.append(root/'COMPLETE.json')
        if 'trait.csv' in term['aggregates']:
            prior=root/'gated-return/trait.csv'
            if filehash(prior)!=term['aggregates']['trait.csv']:raise ValueError('Earlier table differs')
            with prior.open(newline='') as stream:
                extra[trait]={'sld3/'+row['contrast']:int(row['n']) for row in csv.DictReader(stream)}
            docs.append(prior)
    return read(bank)['published_counts'],extra,docs


def invented(destination):
    import numpy as np
    import pyreadstat
    fixture=OLD/'lattice-20261120/spark-family-constructed-v2'
    source=read(fixture/'MANIFEST.json')
    if not source['constructed_only'] or source['private_source_reads']!=0:
        raise ValueError('Expected the invented diary')
    n=source['people']
    records={}
    for role,pin in source['sources']['M2'].items():
        path=fixture/pin['filename']
        if filehash(path)!=pin['sha256']:raise ValueError('Constructed SPSS template changed')
        frame,_=pyreadstat.read_sav(str(path),user_missing=True)
        if role=='survey':
            for key in design.TRAITS.values():
                frame[key]=1.+frame.M2ID.astype(int)%3
        else:
            slot=(frame.B2DDAY.astype(int)-1)%4
            person=frame.M2ID.astype(int)
            for number in range(1,8):
                frame['B2DF'+str(number)]=np.where(slot=={1:1,3:2,6:3}.get(number,-1),1.,2.)
            base=(person//3)%2
            conflict=(1.+(person%3==2))
            increase=np.where(slot==1,conflict,np.where(slot==0,0.,1.))
            for item in design.NEGATIVE:
                frame['B2DC'+str(item)]=(base+increase).astype(float)
        out=destination/pin['filename']
        pyreadstat.write_sav(frame,str(out))
        records[role]=dict(filename=out.name,bytes=out.stat().st_size,sha256=filehash(out))
    return dict(M2=records),n


def main():
    if filehash(GATE)!=read(HOST)['installed_gate_sha256']:raise ValueError('Wrong gate')
    probe=gear.ROOT/'SLD6-wave2-structure'
    headers=probe/'gated-return/structure.csv'
    if filehash(headers)!=read(probe/'COMPLETE.json')['aggregates'][headers.name]:raise ValueError('Missing gated structure check')
    with headers.open(newline='') as stream:fields,=csv.DictReader(stream)
    available=[k for k in design.TRAITS if fields[k]=='1']
    sources=modules()
    hist,extra,prior=historical()
    current=LIB/'week6-sm-science/source_map.json'
    source={'M2':read(current)['M2']}
    scratch=STATE/'fixtures'/('SLD6-kinds-'+uuid4().hex[:10])
    mount=scratch/'data'
    mount.mkdir(parents=True)
    native=OLD/'lattice-20261119/fixture-reader-native'
    sys.path.insert(0,str(native))
    synthetic,n=invented(mount)
    for mode in ('agreeableness','shuffle'):
        entry=scratch/(mode+'.py')
        out=scratch/mode;out.mkdir()
        spec=dict(mode=mode,files=synthetic,available=available,history={'count/1':n,'count/2':n},sld4={},draws=50)
        entry.write_bytes(program(sources,spec,True))
        subprocess.run([sys.executable,'-B',str(entry),str(mount),str(out)],env=dict(os.environ,PYTHONPATH=str(native)),check=True)
        if subprocess.check_output([sys.executable,'-I','-B',str(GATE),str(out)],text=True).strip()!='gate passed':
            raise ValueError('Fixture gate refused')
        table='shuffle.csv' if mode=='shuffle' else 'trait.csv'
        with (out/table).open(newline='') as stream:rows=list(csv.DictReader(stream))
        planted={int(row['measure']):float(row['estimate']) for row in rows if row['trait']=='1'}
        if len(planted)!=4 or planted[1]<.1 or abs(planted[4]-planted[1])>1e-8 or abs(planted[2])+abs(planted[3])>1e-8 or any(int(row['n'])!=n for row in rows):
            raise ValueError('Planted effect or roster differs')
        if mode=='shuffle' and any(float(r['percentile'])<.95 for r in rows if r['measure'] in ('1','4')):
            raise ValueError('Shuffled trait control missed the planted difference')
    evidence=scratch/'REHEARSAL.json'
    freeze(evidence,dict(constructed=True,checks=['original SPSS pair','source and roster reconstruction','three exclusive event kinds','point and interval replay','known trait contrast','whole-person shuffled trait reference','installed gate'],
        original_fixture=filehash(scratch/'agreeableness/trait.csv'),shuffle=filehash(scratch/'shuffle/shuffle.csv')))
    for mode in [*available,'shuffle']:
        unit='SLD6-wave2-'+mode
        path=STATE/'sealed'/unit/'run.py'
        path.parent.mkdir(exist_ok=True,parents=True)
        options=dict(mode=mode,files=source,available=available,history=hist,sld4=extra,draws=1000 if mode=='shuffle' else 2000)
        payload=program(sources,options,False)
        if path.exists() and path.read_bytes()!=payload:raise ValueError('Existing reviewed entry differs')
        if not path.exists():path.write_bytes(payload)
        pins=[*prior,probe/'COMPLETE.json',headers,gear.AUTHORITY,ROOT/'docs/design/stage-15/week8/SLD6.md',
              Path(gear.__file__),Path(__file__).resolve(),Path(design.__file__),LIB/'week8_sld6.py',LIB/'week7_sld4.py',current,
              OLDSTATE/'MIB1_primary.entry.py',OLDSTATE/'MIB1_NUMERIC_QUALIFIED.json',Path(original.build.__file__),
              ROOT/'tools/week8_sealed.py',ROOT/'tools/week8_spark.ps1',GATE,HOST,evidence,path]
        freeze(STATE/'reviews'/(unit+'.json'),dict(unit=unit,card='SLD6',source='midus-m2-joined',cap=SHUFFLE_CAP if mode=='shuffle' else CAP,
               tables=['shuffle.csv' if mode=='shuffle' else 'trait.csv'],fixture_gate_passed=True,fixture_sha256=filehash(evidence),pins={str(p):filehash(p) for p in pins}))
    print('Qualified five trait entries and one shuffled control.')


if __name__=='__main__':
    main()
