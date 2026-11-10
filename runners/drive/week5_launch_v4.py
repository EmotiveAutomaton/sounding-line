"""Launch reviewed Week 5 plans with authenticated monitoring and native ownership.

DESIGN CHECK: LESSONS 3-5. Changed committed design, source, fixture or owner
fails under both scientific directions. Existing attempts never restart here.
"""
from pathlib import Path
import argparse,subprocess,time,json
from runners.stage14.common import REPO,read,atomic,freeze,filehash,now
from runners.stage9.process_identity import native_identity
from runners.theory_days.launch import closure
from runners.drive.cards.batch_runtime import check_files
from runners.drive.cards import week5_policy_v2 as policy

MODULES=['runners.drive.cards.week5_runtime_v4','runners.drive.cards.week5_policy_v2','runners.drive.cards.week5_child_v2']

def review(plan):
    check_files(plan['pins'])
    if not plan.get('owner_reviewed') or not plan.get('validation_receipts'):raise ValueError('Owner review and native fixtures required')
    for path in plan['validation_receipts']:
        if plan['pins'].get(path)!=filehash(path):raise ValueError('Unpinned native fixture')
    design=Path(plan['design']).resolve()
    rel=design.relative_to(REPO).as_posix()
    content=subprocess.run(['git','show',plan['reviewed_design_commit']+':'+rel],cwd=REPO,capture_output=True,check=True).stdout
    if content!=design.read_bytes():raise ValueError('Design is not the reviewed committed version')
    for p in closure([plan['module'],*MODULES]):
        if plan['pins'].get(str(p))!=filehash(p):raise ValueError('Missing source closure pin: '+str(p))

def launch(root):
    root=Path(root).resolve();root.relative_to(policy.ROOT)
    if (root/'ATTEMPT.claim').exists():raise ValueError('Existing attempt; inspect instead of relaunch')
    plan=read(root/'PLAN.json');review(plan);policy.admission(plan)
    return launch_monitored(root,'runners.drive.cards.week5_runtime_v4',plan['card'],['COMPLETE','FAILED','PAUSED','MONITOR_FAILED'],[plan['module'],*MODULES])

def launch_monitored(root,module,label,names,sources):
    root=Path(root).resolve();root.relative_to(REPO)
    if (root/'ATTEMPT.claim').exists():raise ValueError('Existing monitored attempt')
    config_path=REPO/'.agent-state/watch.json'
    paths=[(root/(n+'.json')).relative_to(REPO).as_posix() for n in names]
    config=read(config_path)
    for key in ('paths','urgent_paths'):config[key]=sorted(set(config.get(key,[])+paths))
    atomic(config_path,config)
    for path in closure(sources):
        dest=root/'source_capsule'/path.relative_to(REPO)
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(path.read_bytes())
    def quote(s):return "'"+str(s).replace("'","''")+"'"
    args=subprocess.list2cmdline(['-X','utf8','-B','-m',module,str(root)])
    cmd='Start-Process -WindowStyle Hidden -FilePath '+quote(REPO/'.venv/Scripts/python.exe')+' -ArgumentList '+quote(args)+' -WorkingDirectory '+quote(REPO)+' -RedirectStandardOutput '+quote(root/'stdout.log')+' -RedirectStandardError '+quote(root/'stderr.log')
    subprocess.run(['powershell','-NoProfile','-Command',cmd],check=True,timeout=30)
    deadline=time.monotonic()+30
    while not (root/'OWNER.json').exists():
        if time.monotonic()>deadline:raise TimeoutError('Native owner handshake')
        time.sleep(.2)
    owner=read(root/'OWNER.json')['native']
    if native_identity(owner['pid'])!=owner:raise ValueError('Native identity mismatch')
    config=read(config_path)
    config.setdefault('process_watches',[]).append(dict(label=label,native=owner,failure_output=paths[-1],terminal_paths=paths[:-1]))
    atomic(config_path,config)
    freeze(root/'MONITOR_READY.json',dict(at=now(),owner_sha256=filehash(root/'OWNER.json'),watch_config_sha256=filehash(config_path)))
    return dict(root=str(root),native=owner,plan_sha256=filehash(root/'PLAN.json'))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path)
    print(json.dumps(launch(parser.parse_args().root)))
