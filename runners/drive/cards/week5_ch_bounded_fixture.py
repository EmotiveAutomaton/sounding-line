"""Actual counted CH1 execute-pause, verify-pause and full replay fixture.

DESIGN CHECK: LESSONS 3-5. Only constructed chess boards enter this proof.
All Stockfish descendant CPU remains in the native job and CH accounting.
Original score bytes, watcher registration and native release are inspected.
"""
from pathlib import Path
import argparse
import json
import sys
import time
import chess
from .batch_runtime import REPO, freeze, read, filehash, atomic
from .week5_ch_collection import write_rows, collect
from .week5_ch_engine import score_key
from . import week5_ch_batch_planner_v2 as planner


def build(root, engine):
    root.mkdir(parents=True, exist_ok=False)
    one = chess.Board('8/8/8/8/8/1k6/r7/K7 w - - 0 1')
    mate = chess.Board('6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1')
    mating = []
    for move in mate.legal_moves:
        test = mate.copy(); test.push(move)
        if test.is_checkmate(): mating.append(move)
    assert one.legal_moves.count() == 1 and len(mating) == 1
    boards = [(one, next(iter(one.legal_moves))), (mate, mating[0])]
    board = chess.Board()
    for san in ('e4', 'e5', 'Nf3', 'Nc6', 'Bb5', 'a6'):
        move = board.parse_san(san)
        boards.append((board.copy(), move)); board.push(move)
    rows = [dict(fen=b.fen(), uci=m.uci(), ordinal=i, player='constructed-'+str(i//2),
                 month='2017-04' if i < 4 else '2026-07', rating=1600)
            for i, (b, m) in enumerate(boards)]
    source = root/'PRIVATE_POSITIONS.jsonl.gz'
    write_rows(source, rows)
    inputs = {k:dict(path=str(p),sha256=filehash(p)) for k,p in [('positions',source),('engine',engine)]}
    freeze(root/'KNOWN_ANSWERS.json', dict(single_legal=score_key(rows[0],1000000),
                                         unique_mate=score_key(rows[1],1000000)))
    return inputs


def manifest(root):
    return {p.relative_to(root).as_posix():filehash(p) for p in root.rglob('*') if p.is_file()}


def wait(root, request_verify=False):
    deadline = time.monotonic()+650
    sent = False
    while time.monotonic() < deadline:
        for state in ('COMPLETE', 'FAILED', 'PAUSED', 'MONITOR_FAILED'):
            file = root/(state+'.json')
            if file.exists():
                return state, read(file), sent
        progress = root/'output/VERIFY_PROGRESS.json'
        if request_verify and not sent and progress.exists() and read(progress)['verified_positions'] >= 2:
            atomic(root/'output/YIELD_REQUEST.json',dict(reason='constructed owner verification pause',at=time.time()))
            sent = True
        time.sleep(.05)
    raise TimeoutError('Counted fixture terminal receipt absent')


def run(root, commit, engine):
    from . import week5_policy_v2 as policy
    from .. import week5_launch_v6 as launch
    from .week5_resume_v2 import output_manifest
    from runners.theory_days.launch import closure
    from runners.stage9.process_identity import is_same_live_process
    sys.path.insert(0, str(REPO/'tools'))
    from tools.codex_watch import valid_json
    root.mkdir(parents=True, exist_ok=False)
    inputs = build(root/'inputs', engine)
    module = planner.MODULE
    design = REPO/'docs/design/stage-15/week5/CH_FILLER_BOUNDED.md'
    prior_proof = REPO/'.agent-state/drive-20261107/ch-native-fixture-v8/COMPLETE.json'
    paths = list(closure([module, *launch.MODULES, 'runners.drive.week5_launch_v6']))
    paths += [design, prior_proof, Path(__file__), Path(inputs['positions']['path']), engine]
    pins = {str(p.resolve()):filehash(p) for p in paths}
    config = dict(offset=0,max_positions=8,nodes=1000000,wall_seconds=600,
                  max_new_draws=2,constructed_fixture=True)
    base = dict(campaign='S15-WEEK5',module=module,family='CH',inputs=inputs,config=config,
                design=str(design),reviewed_design_commit=commit,pins=pins,fixture_passed=True,
                owner_reviewed=True,validation_receipts=[str(prior_proof)],paid=False,gpu=False,
                ollama=False,numerical_threads=2,max_cpu_seconds=300,max_wall_seconds=600,
                forecast_cpu_seconds=60,projected_peak_ram_GiB=1,
                premortem=dict(case_and_check='Eight constructed legal boards, native execution and verification pauses, exact full replay.',
                              smaller_route='Retain interruption and all CPU; no human scientific launch.'))
    attempts = []
    prior = None
    originals = {}
    for suffix, quantum, desired, verify_pause in [('execute-pause',2,'PAUSED',False),
                                                  ('verify-pause',8,'PAUSED',True),
                                                  ('complete',8,'COMPLETE',False)]:
        runroot = policy.ROOT/(root.name+'-'+suffix)
        runroot.mkdir(exist_ok=False)
        plan = {**base,'card':runroot.name,'config':{**config,'max_new_draws':quantum}}
        if prior is not None:
            plan['resume'] = dict(root=str(prior),plan_sha256=filehash(prior/'PLAN.json'),
                                  paused_sha256=filehash(prior/'PAUSED.json'))
        freeze(runroot/'PLAN.json',plan)
        freeze(root/(suffix+'-LAUNCH.json'),launch.launch(runroot))
        print(json.dumps(dict(launched=suffix,root=str(runroot))),flush=True)
        state, receipt, sent = wait(runroot,verify_pause)
        freeze(root/(suffix+'-TERMINAL.json'),dict(state=state,receipt=receipt))
        if state != desired: raise ValueError('Expected '+desired+', found '+state)
        if verify_pause and (not sent or receipt['paused_operation'] != 'verify'):
            raise ValueError('Actual verification owner pause not exercised')
        if prior is not None:
            assert manifest(prior) == originals[str(prior)]
            assert read(runroot/'RESUMED_FROM.json')['copied'] == output_manifest(prior/'output')
        if state == 'PAUSED': originals[str(runroot)] = manifest(runroot)
        attempts.append((runroot,receipt))
        prior = runroot
    final = attempts[-1][0]
    assert read(final/'RESULT.json')['reused_positions'] == 8
    proof = read(final/'VERIFIED.json')
    assert proof['verified'] is True and proof['verified_positions'] == 8 and proof['fresh_from_ordinal_zero']
    before_pause = attempts[1][0]
    for old in [attempts[0][0],before_pause]:
        assert manifest(old) == originals[str(old)]
        for file in (old/'output/PRIVATE_SCORES').glob('*.json'):
            assert filehash(file) == filehash(final/'output/PRIVATE_SCORES'/file.name)
    known = read(root/'inputs/KNOWN_ANSWERS.json')
    for key in known.values(): assert read(final/'output/PRIVATE_SCORES'/(key+'.json'))['engine']['k50'] == 1
    spec = dict(path=str(final/'COMPLETE.json'),sha256=filehash(final/'COMPLETE.json'))
    segment = planner.segments(inputs['positions'],segment_positions=8)[0]
    assert planner.continuation(segment,[spec])['segment_complete']
    planner.collection_manifest([spec],root/'collection')
    rows, _ = collect(inputs['positions']['path'],read(root/'collection/BATCHES.json')['batches'])
    assert len(rows) == 8
    watches = read(REPO/'.agent-state/watch.json')['process_watches']
    for runroot, receipt in attempts:
        native = read(runroot/'OWNER.json')['native']
        deadline = time.monotonic()+10
        while is_same_live_process(native) and time.monotonic()<deadline: time.sleep(.05)
        assert not is_same_live_process(native)
        assert not any(read(p).get('native') == native for p in policy.lease_paths())
        assert any(w['native'] == native for w in watches)
        assert valid_json(runroot/('COMPLETE.json' if receipt['status']=='COMPLETE' else 'PAUSED.json'))
    receipt = dict(passed=True,constructed=True,charged_family='CH',positions=8,
                   execute_checkpoint_verified=True,actual_owner_verify_pause=True,
                   native_fresh_replay_from_zero=True,engine_single_thread=True,
                   single_legal_and_unique_mate_known_answers=True,predecessors_byte_identical=True,
                   completed_roster_collection_verified=True,native_exits_and_lease_release=True,
                   watcher_registration_and_terminal_schema=True,
                   measured_cpu_seconds=sum(v['cpu_seconds'] for _,v in attempts),
                   supervisor_accounting_allowance=90,
                   attempts=[dict(root=str(r),status=v['status'],cpu_seconds=v['cpu_seconds']) for r,v in attempts],
                   pins=pins)
    freeze(root/'FIXTURE.json',receipt)
    return receipt


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path)
    p.add_argument('--commit',required=True);p.add_argument('--engine',required=True,type=Path)
    args=p.parse_args()
    try:
        result=run(args.output.resolve(),args.commit,args.engine.resolve())
        print(json.dumps(result))
    except BaseException as exc:
        if args.output.exists(): freeze(args.output/'FAILED_FIXTURE.json',dict(error=repr(exc),constructed=True))
        raise
