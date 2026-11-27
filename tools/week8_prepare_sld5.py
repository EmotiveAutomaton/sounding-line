"""Rehearse SLD5 on invented SPSS panels and freeze the exact private-source entry."""
import csv
import os
from pathlib import Path
from runpy import run_path
import subprocess
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.week8_sealed import GATE, HOST, OLD, STATE
from runners.drive.cards import week7_gear, week8_gear as gear
from runners.drive.sealed import week8_package as bundle
from runners.stage14.common import filehash, freeze, read

UNIT = 'SLD5-loss-comparison'
CAP = 3600
NATIVE = OLD/'lattice-20261119/fixture-reader-native'
MODULES = [bundle.LIB/n for n in ('week7_sld2.py', 'week7_sld2_original.py', 'week8_sld5.py')]
TEST = ROOT/'tests/test_week8_sld5.py'


def prepare():
    sys.path.insert(0, str(NATIVE))
    import pyreadstat
    source_receipt = Path(read(ROOT/'.agent-state/data_collection_root.json')['root'])/'_handoffs/repo-requests/DC-20261124-02/SLD2_SOURCE.json'
    source = read(source_receipt)
    if source['slug'] != 'midus-m1m2m3-surveys' or source['requested_access'] != 'read-only':
        raise ValueError('Survey source binding differs')
    panel_pins = [(Path(f['mount_path']).name,f['bytes'],f['sha256']) for f in sorted(source['local_files'],key=lambda f:f['wave'])]
    previous = week7_gear.ROOT/'SLD2-marital-role-20261124'
    released = previous/'gated-return/purpose.csv'
    if filehash(released) != read(previous/'COMPLETE.json')['aggregate']:
        raise ValueError('Prior gated roster table differs')
    with released.open(newline='') as stream:
        known = {}
        for item in csv.DictReader(stream):
            key = item['group']+'-'+item['reading']
            if known.setdefault(key,int(item['n'])) != int(item['n']):
                raise ValueError('Inconsistent roster count')
    if known != {'1-1':207,'1-2':129,'2-1':80,'2-2':36,'3-1':127,'3-2':93}:
        raise ValueError('Prior rosters differ')
    if filehash(GATE) != read(HOST)['installed_gate_sha256']:
        raise ValueError('Local rehearsal gate differs from installed gate')
    testroot = STATE/'fixtures'/(UNIT+'-'+uuid4().hex[:12])
    data, out, empty = (testroot/k for k in ('data','out','refusal'))
    for directory in (data,out,empty):
        directory.mkdir(parents=True)
    frames, known_synthetic = run_path(str(TEST))['panels']()
    fixture_pins = []
    for frame,(name,_,_) in zip(frames,panel_pins,strict=True):
        path = data/name
        pyreadstat.write_sav(frame.reset_index().astype(float), str(path))
        fixture_pins.append((name,path.stat().st_size,filehash(path)))
    study = MODULES[-1]
    config = dict(files=fixture_pins,known=known_synthetic,draws=48)
    example = testroot/'run.py'
    example.write_bytes(bundle.package(study,MODULES,config,CAP,fixture=True))
    env = dict(os.environ,PYTHONPATH=str(NATIVE))
    cmd = [sys.executable,'-B',str(example),str(data)]
    subprocess.run([*cmd,str(out)],env=env,check=True)
    gate = subprocess.run([sys.executable,'-I','-B',str(GATE),str(out)],capture_output=True,text=True,check=True)
    if gate.stdout.strip() != 'gate passed':
        raise ValueError('Rehearsal gate failed')
    with (out/'purpose.csv').open(newline='') as stream:
        result = list(csv.DictReader(stream))
    main = [r for r in result if int(r['group'])==1 and int(r['form'])==1]
    if len(main)!=3 or [int(r['n']) for r in main]!=[160]*3 or [round(float(r['estimate']),8) for r in main]!=[-1.,-1.,0.]:
        raise ValueError('Known-answer failed on original-layout fixture')
    with (data/fixture_pins[0][0]).open('ab') as stream:
        stream.write(b'changed constructed original')
    refused = subprocess.run([*cmd,str(empty)],env=env)
    if refused.returncode!=13 or any(empty.iterdir()):
        raise ValueError('Source-pin refusal failed')
    evidence = testroot/'REHEARSAL.json'
    freeze(evidence,dict(study='SLD5',all_data='constructed',entry=filehash(example),checks=['original SPSS layout','joint disclosure gate','paired reconstruction and bootstrap replay','planted changes','contributing people','tamper refusal'],source_refusal=13,table=filehash(out/'purpose.csv')))
    entry = STATE/'sealed'/UNIT/'run.py'
    entry.parent.mkdir(parents=True,exist_ok=True)
    payload = bundle.package(study,MODULES,dict(files=panel_pins,known=known,draws=2000),CAP)
    if entry.exists() and entry.read_bytes()!=payload:
        raise ValueError('Existing reviewed entry differs')
    if not entry.exists():
        entry.write_bytes(payload)
    paths = [gear.AUTHORITY,ROOT/'docs/design/stage-15/week8/SLD5.md',STATE/'SLD_CODEBOOKS.json',source_receipt,released,previous/'COMPLETE.json',
             Path(gear.__file__),Path(bundle.__file__),bundle.SUPPORT,bundle.RELEASE,*MODULES,Path(__file__).resolve(),
             ROOT/'tools/week8_sealed.py',ROOT/'tools/week8_spark.ps1',GATE,HOST,TEST,evidence,entry]
    freeze(STATE/'reviews'/(UNIT+'.json'),dict(card='SLD5',unit=UNIT,source=source['slug'],cap=CAP,
           tables=['purpose.csv'],fixture_gate_passed=True,fixture_sha256=filehash(evidence),pins={str(p):filehash(p) for p in paths}))
    print('SLD5 original-layout rehearsal and refusal check passed. Immutable entry',filehash(entry))


if __name__=='__main__':
    prepare()
