"""Submit a single rehearsed Week 8 unit through the installed sealed launcher."""
import argparse
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runners.drive.cards import week8_gear as gear
from runners.stage14.common import filehash,freeze,now,read

STATE=ROOT/'.agent-state/drive-20261127/week8'
OLD=ROOT/'.agent-state/drive-20261115'
GATE=STATE/'installed_sealed_gate.py'
HOST=OLD/'full-week-extension/status-spark-20261120/SPARK_REVIEW.json'
SSH=['-o','BatchMode=yes','-o','ConnectTimeout=12']


def exec_ok(args):
    return subprocess.run(args,capture_output=True,text=True,check=True).stdout.strip()


def remote(cmd):
    return exec_ok(['ssh',*SSH,'spark',cmd])


def launch(unit):
    if not re.fullmatch('[a-zA-Z0-9-]+',unit):
        raise ValueError('Invalid job name')
    review=STATE/'reviews'/(unit+'.json')
    q=read(review)
    card,alias,job=q['card'],q['source'],'w8-'+unit.lower()
    if q['unit']!=unit or card not in gear.CARDS or not re.fullmatch('[a-zA-Z0-9-]+',alias):
        raise ValueError('Invalid review')
    d=gear.ROOT/unit
    entry=STATE/'sealed'/unit/'run.py'
    host=read(HOST)
    checks=remote('sha256sum /usr/local/bin/sealed-run /usr/local/lib/sealed-gate.py').splitlines()
    if [row.split()[0] for row in checks]!=[host['installed_runner_sha256'],host['installed_gate_sha256']] or filehash(GATE)!=host['installed_gate_sha256']:
        raise ValueError('Installed control or rehearsal gate differs')
    if host['image_digest'] not in remote('cat /srv/open/pins/sl-tabular-2026-11-16.txt').splitlines():
        raise ValueError('Sealed image pin differs')
    cap=q['cap']
    pins=q['pins']|{str(review):filehash(review)}
    if pins[str(entry)]!=filehash(entry) or not q['fixture_gate_passed']:
        raise ValueError('Entry lacks a matching rehearsal')
    with gear.admit(d,card=card,source=alias,requested=cap,peak=.5,sealed=True,pins=pins):
        try:
            dest='/home/agent/sealed-jobs/'+job
            remote('mkdir '+dest)
            exec_ok(['scp',*SSH,str(entry),'spark:'+dest+'/run.py'])
            if remote('sha256sum '+dest+'/run.py').split()[0]!=filehash(entry):
                raise ValueError('Remote entry differs')
            freeze(d/'SUBMITTED.json',dict(at=now(),job=job,source=alias,entry=filehash(entry),image=host['image_digest']))
            start=time.monotonic()
            result=subprocess.run(['ssh',*SSH,'spark','sudo -n sealed-run '+job+' '+alias],capture_output=True,text=True)
            freeze(d/'EXIT.json',dict(at=now(),code=result.returncode,elapsed_seconds=time.monotonic()-start))
            if result.returncode:
                raise RuntimeError('Sealed exit '+str(result.returncode))
            match=re.search(r'(/home/agent/sealed-totals/'+re.escape(job)+r'-[0-9]{8}T[0-9]{6})\s*$',result.stdout)
            if not match:
                raise RuntimeError('Unrecognized gated return')
            base=match.group(1)
            files=remote('ls -1 '+base).splitlines()
            if not files or not set(files)<=set(q['tables']) or not all(re.fullmatch('[a-z0-9_]+[.]csv',n) for n in files):
                raise ValueError('Unexpected table roster')
            out=d/'gated-return'
            out.mkdir()
            sums={}
            for name in files:
                loc=base+'/'+name
                digest=remote('sha256sum '+loc).split()[0]
                exec_ok(['scp',*SSH,'spark:'+loc,str(out/name)])
                if filehash(out/name)!=digest:
                    raise ValueError('Gated return differs on readback')
                sums[name]=digest
            if exec_ok([sys.executable,'-I','-B',str(GATE),str(out)])!='gate passed':
                raise RuntimeError('Local return gate refused')
            gear.settle(d,cap,'Conservative enforced CPU cap including independent replay')
            freeze(d/'COMPLETE.json',dict(at=now(),unit=unit,card=card,aggregates=sums,review=filehash(review),verified=True))
        except BaseException as exc:
            submitted=(d/'SUBMITTED.json').is_file()
            if not (d/'COST.json').exists():
                gear.settle(d,cap if submitted else 0,'Full reservation on submission',never_submitted=not submitted)
            freeze(d/'FAILED.json',dict(at=now(),reason=str(exc),submitted=submitted))
            raise


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('unit')
    launch(parser.parse_args().unit)
