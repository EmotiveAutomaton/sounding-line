"""Constructed KLICKE full native source/child/runtime integration proof."""
from pathlib import Path
import argparse, json, shutil, subprocess, sys
from unittest.mock import patch
from . import week5_bk_klicke_intake_v2 as successor
from . import week5_bk_klicke_intake as source
from .week5_bk_intake_fixture import build
from .batch_runtime import REPO, freeze, read, filehash


def standalone(root):
    root.mkdir(parents=True, exist_ok=False)
    inputs = build(root / 'inputs')
    config = dict(card='BK-S4.k-intake', mode='constructed', expected_sessions=3, max_new_draws=1)
    first = successor.execute(root / 'pause', inputs, config)
    assert first['status'] == 'yielded'
    shutil.copytree(root / 'pause', root / 'complete')
    done = successor.execute(root / 'complete', inputs, {**config, 'max_new_draws': 3})
    assert done['new_sessions'] == 2 and done['reused_sessions'] == 1
    freeze(root / 'INPUTS.json', inputs); freeze(root / 'CONFIG.json', config)
    child = subprocess.run([sys.executable, '-X', 'utf8', '-B', '-m', __spec__.name,
                            '--replay', str(root)], capture_output=True, text=True)
    if child.returncode: raise RuntimeError(child.stderr[-3000:])
    for bad in ({'status': 'complete'}, {'status': 'yielded', 'independent_source_replay': True}):
        with patch.object(source, 'verify', return_value=bad):
            try: successor.verify(None, None, None)
            except ValueError: pass
            else: raise AssertionError('Unsuccessful replay certified')
    proof = dict(passed=True, constructed=True, independent_replay=json.loads(child.stdout),
                 missing_or_incomplete_replay_refused=True,
                 source_pins={str(Path(p).relative_to(REPO)):filehash(p) for p in
                              (Path(__file__), Path(source.__file__), Path(successor.__file__))})
    freeze(root / 'FIXTURE.json', proof)
    return root / 'FIXTURE.json'


def counted(root, commit, proof):
    from . import week5_policy_v2 as policy
    from .. import week5_launch_v5 as launch
    from .week5_runtime_v5_fixture import wait
    from .week5_resume_v2 import output_manifest
    from runners.theory_days.launch import closure
    from runners.stage9.process_identity import is_same_live_process
    sys.path.insert(0, str(REPO/'tools'))
    from tools.codex_watch import valid_json
    root.mkdir(parents=True, exist_ok=False)
    inputs = build(root / 'inputs')
    config = dict(card='BK-S4.k-intake', mode='constructed', expected_sessions=3, max_new_draws=1)
    module = 'runners.drive.cards.week5_bk_klicke_intake_v2'
    design = REPO / 'docs/design/stage-15/week5/BK_KLICKE_VERIFY.md'
    paths = list(closure([module, *launch.MODULES, 'runners.drive.week5_launch_v5']))
    paths += [design, proof, Path(inputs['archive']), Path(inputs['identity_salt'])]
    pins = {str(p.resolve()):filehash(p) for p in paths}
    plan = dict(campaign='S15-WEEK5', module=module, family='BK', inputs=inputs,
                config=config, design=str(design), reviewed_design_commit=commit,
                pins=pins, fixture_passed=True, owner_reviewed=True,
                validation_receipts=[str(proof)], paid=False, gpu=False, ollama=False,
                numerical_threads=2, max_cpu_seconds=300, max_wall_seconds=600,
                forecast_cpu_seconds=30, projected_peak_ram_GiB=.5,
                premortem=dict(case_and_check='Three constructed source sessions; actual counted pause and independent complete replay.',
                              smaller_route='Retain failure; no human source or statistical execution.'))
    old = policy.ROOT / (root.name+'-pause'); new = policy.ROOT / (root.name+'-resume')
    old.mkdir(); freeze(old/'PLAN.json', {**plan, 'card':old.name})
    freeze(root/'FIRST_LAUNCH.json', launch.launch(old))
    state, paused = wait(old)
    if state != 'PAUSED': raise ValueError('Expected pause: '+state)
    before = {p.relative_to(old).as_posix():filehash(p) for p in old.rglob('*') if p.is_file()}
    resumed = {**plan, 'card':new.name, 'config':{**config,'max_new_draws':3},
               'resume':dict(root=str(old),plan_sha256=filehash(old/'PLAN.json'),paused_sha256=filehash(old/'PAUSED.json'))}
    new.mkdir(); freeze(new/'PLAN.json', resumed)
    freeze(root/'SECOND_LAUNCH.json', launch.launch(new))
    state, complete = wait(new)
    if state != 'COMPLETE': raise ValueError('Expected complete: '+state)
    assert before == {p.relative_to(old).as_posix():filehash(p) for p in old.rglob('*') if p.is_file()}
    assert read(new/'RESUMED_FROM.json')['copied'] == paused['checkpoint_outputs'] == output_manifest(old/'output')
    assert read(new/'VERIFIED.json')['verified'] is True
    assert read(new/'VERIFIED.json')['new_sessions'] == 3
    assert read(new/'RESULT.json')['new_sessions'] == 2
    assert read(new/'RESULT.json')['reused_sessions'] == 1
    for name, digest in complete['outputs'].items(): assert filehash(new/name) == digest
    assert valid_json(old/'PAUSED.json') and valid_json(new/'COMPLETE.json')
    watch = read(REPO/'.agent-state/watch.json')
    for run in (old,new):
        native = read(run/'OWNER.json')['native']
        assert not is_same_live_process(native)
        assert not any(read(p).get('native') == native for p in policy.lease_paths())
        assert any(w['native'] == native for w in watch['process_watches'])
    receipt = dict(verified=True,constructed=True,full_native_independent_replay=True,
                   predecessor_unchanged=True,watcher_receipts_recognized=True,
                   monitor_registration_verified=True,owner_exited_and_lease_released=True,
                   old_root=str(old),new_root=str(new),charged_family='BK',
                   measured_cpu_seconds=paused['cpu_seconds']+complete['cpu_seconds'],
                   supervisor_accounting_allowance=60,
                   paused_sha256=filehash(old/'PAUSED.json'),complete_sha256=filehash(new/'COMPLETE.json'),
                   sources={str(p.relative_to(REPO)):filehash(p) for p in paths if p.suffix=='.py'})
    freeze(root/'FIXTURE.json',receipt)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);p.add_argument('--replay',type=Path)
    p.add_argument('--commit');p.add_argument('--proof',type=Path);a=p.parse_args()
    if a.replay:
        result=successor.verify(a.replay/'complete',read(a.replay/'INPUTS.json'),read(a.replay/'CONFIG.json'))
        assert result['verified'] is True and result['new_sessions']==3
        print(json.dumps(result))
    elif a.commit: print(json.dumps(counted(a.output.resolve(),a.commit,a.proof.resolve())))
    else: print(json.dumps(dict(proof=str(standalone(a.output.resolve())))))
