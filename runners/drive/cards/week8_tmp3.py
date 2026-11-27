"""Count the local TP72 receiver rehearsal before any target-image start."""
import csv
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from . import week8_gear as gear
from runners.drive.sealed import week8_package as package
from runners.stage14.common import read, freeze, filehash
from tools.week8_sealed import STATE, OLD, GATE, HOST

UNIT = 'TMP3-TP72-dual-fixture-local'
TARGET = 'TMP3-TP72-dual-fixture-Spark'
DELIVERY = OLD/'week8/TP72-delivery-a'
INTAKE = STATE/'TP72_PRODUCER_REVIEW.json'
NOTE = gear.REPO/'docs/design/stage-15/week8/TP72_RECEIVER.md'
STUDY = package.LIB/'week8_tp72_job.py'
MODULES = [STUDY, *(package.LIB/(name+'.py') for name in (
    'week8_tp72_receiver','week8_tp72_fixture','week8_tp72_prior','week8_tmp2_source',
    'week8_tmp3_receiver','week8_lkg1','week8_lkg2','week6_sc2_source_v1','week6_sc1_counts_v1',
    'week7_tmp1_shell','r48_forms'))]
TARGET_CAP = 600


def configuration(mode,target):
    receipt = read(INTAKE)
    manifest = DELIVERY/'manifest.json'
    if not receipt['verified'] or receipt['manifest'] != filehash(manifest):
        raise ValueError('The producer receipt and manifest must agree')
    return dict(mode=mode,target=target,payload=read(manifest))


def inputs():
    cfg = configuration('fixture',False)
    return [INTAKE,DELIVERY/'manifest.json',DELIVERY/'producer-rehearsal.json',GATE,HOST,
            Path(package.__file__),package.SUPPORT,package.RELEASE,*MODULES,NOTE,
            *(DELIVERY/'payload'/key for key in cfg['payload'])]


def design(unit):
    if unit != UNIT:
        raise ValueError('Unknown constructed unit')
    files = inputs()
    expected = {str(DELIVERY/'payload'/k):v for k,v in configuration('fixture',False)['payload'].items()}
    return dict(inputs=files,expected=expected,peak=2.5,cap=600,operations=['execute'],
                source='invented-records-and-authenticated-TP72')


def target_entry():
    return package.package(STUDY,MODULES,configuration('fixture',True),TARGET_CAP)


def fixture():
    if read(INTAKE)['archive_mounts']['tp72-fixture']['files']!=27 or filehash(GATE)!=read(HOST)['installed_gate_sha256']:
        raise ValueError('Wrong fixture mount or disclosure gate')
    return dict(target_entry_sha256=hashlib.sha256(target_entry()).hexdigest(),scope='constructed only')


def run(unit,directory,mode):
    if (unit,mode)!=(UNIT,'execute'):
        raise ValueError('Unknown receiver rehearsal')
    cfg = configuration('fixture',False)
    with TemporaryDirectory(dir=directory) as work:
        root = Path(work)
        mount = root/'fixture'
        shutil.copytree(DELIVERY/'payload',mount/'payload')
        compiled = package.package(STUDY,MODULES,cfg,TARGET_CAP,fixture=True)
        if sys.platform=='win32':
            # Zipimport on Windows retains a handle after the job has returned.
            marker = b'    sys.path.insert(0,str(bundle))'
            if compiled.count(marker)!=1:
                raise ValueError('Unexpected package loader')
            compiled = compiled.replace(marker,b'    from zipfile import ZipFile\n'
                b'    with ZipFile(bundle) as sources:\n        sources.extractall(tmp)\n    sys.path.insert(0,tmp)')
        entry = root/'run.py'
        entry.write_bytes(compiled)
        out = root/'out'
        out.mkdir()
        subprocess.run([sys.executable,'-B',str(entry),str(mount),str(out)],check=True)
        if subprocess.check_output([sys.executable,'-I','-B',str(GATE),str(out)],text=True).strip()!='gate passed':
            raise ValueError('Local installed gate failed')
        if {p.name for p in out.iterdir()}!={'conversation_affect.csv'}:
            raise ValueError('Original-format synthetic receiver returned the wrong form')
        with (out/'conversation_affect.csv').open(newline='') as f:
            rows=list(csv.DictReader(f))
        if len(rows)!=12 or any(int(r['n'])!=12 or int(r['isoN'])!=200 or int(r['rotN'])!=200 for r in rows):
            raise ValueError('Constructed speaker support or matched controls failed')
        freeze(directory/'REHEARSAL.json',dict(forms=['fine','coarse','summary'],distinct_people_checked=True,
            installed_gate_passed=True,independent_replay=True,target_entry_sha256=fixture()['target_entry_sha256'],
            payload_manifest=read(INTAKE)['manifest'],invented_history_sizes=[48,32],invented_speakers=12,
            withheld_two_speakers=True,withheld_missing_trait_complement=True,output_sha256=filehash(out/'conversation_affect.csv')))


def check(unit,directory):
    p=directory/'REHEARSAL.json'
    if unit!=UNIT or not read(p)['independent_replay']:
        raise ValueError('No completed receiver rehearsal')
    return {p.name:filehash(p)}
