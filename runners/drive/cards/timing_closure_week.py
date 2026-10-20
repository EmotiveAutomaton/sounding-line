"""D24 saved-score continuation under the week packet's single S4 allowance.

DESIGN CHECK: LESSONS 3-5 read for this continuation. NULL/ALTERNATIVE:
unchanged original source, encoder, primary and control give identical results;
prior cost or a forecast cannot alter scores. Changed pins/checkpoints and
exhausted cumulative budget refuse execution. No repeated ceiling doubling.
The original explicit single outcome shuffle is retained, not certified as a
new repeated reference. New control extensions remain separate work.
"""
from __future__ import annotations
import hashlib, json, math, time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import numpy as np
from . import timing_closure_recovery as recovery
from . import timing_closure as original
from . import timing_closure_measure as measure
from .timing_census import read, filehash
from .timing_events import source_sessions, session_words, CooperativeYield
from .timing_stats import bind, check_binding
from runners.stage14.common import atomic, freeze

CONFIG=original.config_for('primary')
FORECAST_SECONDS=900
ORIGINAL_CAP_SECONDS=2700
CAP_SECONDS=5400
SOURCE_INPUTS=recovery.SOURCE_INPUTS
replay=recovery.replay


def duration(root, terminal):
    start=read(root/'PLAN.json')['at'];end=read(root/terminal)['at']
    seconds=(datetime.fromisoformat(end)-datetime.fromisoformat(start)).total_seconds()
    if not math.isfinite(seconds) or seconds<0:raise ValueError('invalid charged attempt duration')
    return seconds


def source(inputs, config):
    if set(inputs)!={'paused_plan','paused_record'} or config!=CONFIG:
        raise ValueError('exact paused continuation inputs/config required')
    plan_path=Path(inputs['paused_plan']);pause_path=Path(inputs['paused_record']);root=plan_path.parent
    if plan_path.name!='PLAN.json' or pause_path!=root/'PAUSED.json':raise ValueError('paused paths differ')
    plan,pause=read(plan_path),read(pause_path)
    if plan['module']!=recovery.__name__ or plan['config']!=config or pause['status']!='PAUSED':
        raise ValueError('original paused repaired attempt required')
    if (root/'COMPLETE.json').exists() or (root/'FAILED.json').exists():raise ValueError('ambiguous terminal')
    for p,h in plan['pins'].items():
        if filehash(p)!=h:raise ValueError('paused source pin changed')
    if filehash(root/'RESULT.json')!=pause['saved_result_sha256']:raise ValueError('paused result binding changed')
    src,old,original_identity=recovery.failure_identity(plan['inputs'],config)
    output=root/'output';progress=read(output/'CLOSURE_PROGRESS.json')
    if read(output/'RECOVERY_SOURCE.json')!=original_identity:raise ValueError('original recovery ancestry changed')
    expected=dict(config=config,source_sha256=filehash(recovery.__file__),inputs={k:str(Path(v).resolve()) if Path(v).is_dir() else filehash(v) for k,v in plan['inputs'].items()})
    if read(output/'RECOVERY_RUN_BINDINGS.json')!=expected:raise ValueError('paused run binding changed')
    retained={}
    for p in sorted((output/'sessions').glob('*.json')):
        if p.name.endswith('.receipt.json'):continue
        receipt=p.with_suffix('.receipt.json')
        if read(receipt)['sha256']!=filehash(p):raise ValueError('saved checkpoint changed')
        for q in (p,receipt):retained[q.relative_to(output).as_posix()]=filehash(q)
    if len(retained)!=2*progress['completed_scored_sessions']:raise ValueError('checkpoint coverage differs')
    for p,h in original_identity['retained_files'].items():
        if retained.get(p)!=h:raise ValueError('original checkpoint bytes differ')
    prior_without_pilot=max(original_identity['charged_prior_seconds']+duration(root,'PAUSED.json'),progress['active_seconds'])
    pilot_seconds=duration(Path(src['pilot_complete']).parent,'COMPLETE.json')
    prior=pilot_seconds+prior_without_pilot
    if not math.isfinite(prior) or prior<0 or prior>=CAP_SECONDS:raise ValueError('single cumulative allowance exhausted')
    identity=dict(paused_plan_sha256=filehash(plan_path),paused_record_sha256=filehash(pause_path),
        original_recovery_identity=original_identity,retained_files=retained,completed_sessions=progress['completed_scored_sessions'],
        pilot_seconds=pilot_seconds,prior_attempt_seconds=prior_without_pilot,charged_prior_seconds=prior,
        original_cap_seconds=ORIGINAL_CAP_SECONDS,single_S4_cap_seconds=CAP_SECONDS)
    return src,output,identity


def score_rows(inputs, encoder, output=None, elapsed=None):
    by_writer = defaultdict(list)
    source = {k: inputs[k] for k in SOURCE_INPUTS}
    for index, timeline, _ in source_sessions(source, "raw_roster"):
        by_writer[index["writer"]].append(session_words(timeline))
    medians = {w: float(np.median(v)) for w, v in by_writer.items()}
    total = len(read(inputs["session_index"]))
    sessions, exclusions = [], []
    for done, (index, timeline, metadata) in enumerate(source_sessions(source, "raw_roster"), 1):
        raw_path = (Path(inputs["repo_root"]) / metadata["path"]).resolve()
        with raw_path.open(encoding="utf-8") as stream:
            raw = [json.loads(line) for line in stream]
        replayed = replay(raw, timeline)
        exclusions.extend(dict(session=index["session"], **r) for r in replayed["excluded_api_insertions"])
        session = dict(session=index["session"], writer=index["writer"], final_words=session_words(timeline),
                       median_final_words=medians[index["writer"]], duration_seconds=replayed["duration_seconds"],
                       requests=replayed["requests"], accepted_times=[r["seconds"] for r in replayed["entries"] if r["kind"] == "accepted"], entries=[])
        checkpoint = output / "sessions" / (hashlib.sha256(index["session"].encode()).hexdigest() + ".json") if output else None
        source_binding = dict(p2=index["sha256"], raw=metadata["source_sha256"])
        saved = None
        if checkpoint is not None and checkpoint.exists():
            saved = read(checkpoint)
            if saved["sources"] != source_binding or read(checkpoint.with_suffix(".receipt.json"))["sha256"] != filehash(checkpoint):
                raise ValueError("D24 scored session checkpoint changed")
        for entry in replayed["entries"]:
            median = session["median_final_words"]
            location = (entry["words_at_event"] - median) / median if median > 0 else None
            # All accepted event times remain for rates, even when no closure
            # score is needed. Score the fixed union of all registered windows.
            eligible = session["duration_seconds"] > 600 and (abs(entry["seconds"] - 600) <= 180 or location is not None and abs(location) <= .2)
            if eligible:
                record = dict(entry, median_location=location)
                if saved is not None:
                    position = len(session["entries"])
                    stored = saved["session"]["entries"][position]
                    if {k: stored[k] for k in record} != record:
                        raise ValueError("D24 checkpoint text/identity differs from raw source")
                    record["score"] = stored["score"]
                else:
                    record["score"] = encoder.score(entry["text"])
                session["entries"].append(record)
        if saved is not None and saved["session"] != session:
            raise ValueError("D24 checkpoint source reconstruction differs")
        if checkpoint is not None:
            freeze(checkpoint, dict(sources=source_binding, session=session))
            freeze(checkpoint.with_suffix(".receipt.json"), dict(sha256=filehash(checkpoint)))
        sessions.append(session)
        if output is not None:
            active = elapsed()
            atomic(output / "CLOSURE_PROGRESS.json", dict(completed_scored_sessions=done, total_sessions=total, active_seconds=active))
            overshoot = False
            if done == math.ceil(total / 10) and not (output / "FIRST_TENTH.json").exists():
                projection = 2 * active * total / done + 120
                overshoot = projection > 2 * FORECAST_SECONDS
                freeze(output / "FIRST_TENTH.json", dict(completed_scored_sessions=done, total_sessions=total,
                       elapsed_seconds=active, projected_cpu_seconds=projection, forecast_cpu_seconds=FORECAST_SECONDS,
                       includes_fresh_source_and_encoder_verification=True, reserved_statistics_seconds=120))
            if active > CAP_SECONDS:
                atomic(output / "YIELD_REQUEST.json", dict(reason="single_S4_cumulative_ceiling"))
                raise CooperativeYield("saved source-bound session at cumulative allowance")
            if (output / "YIELD_REQUEST.json").exists():
                if overshoot and not (output / "YIELD_REQUEST.json").exists():
                    atomic(output / "YIELD_REQUEST.json", dict(reason="first_tenth_projection_exceeds_twice_forecast"))
                raise CooperativeYield("saved fully scored source-bound session")
    return sessions, exclusions

def execute(output,inputs,config):
    output=Path(output);start=time.monotonic();src,old,identity=source(inputs,config)
    if (output/'TIMING_BINDINGS.json').exists():return verify(output,inputs,config)['primary']
    freeze(output/'CONTINUATION_SOURCE.json',identity)
    for name,h in identity['retained_files'].items():
        target=output/name
        if target.exists():
            if filehash(target)!=h:raise ValueError('retained continuation bytes differ')
        else:
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((old/name).read_bytes())
    if (old/'FIRST_TENTH.json').exists():freeze(output/'ORIGINAL_FIRST_TENTH.json',read(old/'FIRST_TENTH.json'))
    prior=read(output/'CLOSURE_PROGRESS.json')['active_seconds'] if (output/'CLOSURE_PROGRESS.json').exists() else identity['charged_prior_seconds']
    if prior<identity['charged_prior_seconds']:raise ValueError('continuation cost regressed')
    elapsed=lambda:prior+time.monotonic()-start
    original.authorize_pilot(src)
    try:sessions,exclusions=score_rows(src,measure.Encoder(src),output,elapsed)
    except CooperativeYield as exc:return dict(status='yielded',card='D24',reason=str(exc))
    result,details=original.summarize(sessions,config)
    if elapsed()>CAP_SECONDS:raise RuntimeError('single S4 allowance exhausted before output')
    files={'CLOSURE_ROWS.json':sessions,'CLOSURE_PRIMARY.json':result,'CLOSURE_DETAILS.json':details,'CLOSURE_SOURCE_EXCLUSIONS.json':exclusions}
    for name,value in files.items():freeze(output/name,value)
    freeze(output/'CLOSURE_TIMING.json',dict(cumulative_seconds=elapsed(),prior_seconds=identity['charged_prior_seconds'],original_cap_seconds=ORIGINAL_CAP_SECONDS,single_S4_cap_seconds=CAP_SECONDS))
    bind(output,inputs,config,list(files)+['CONTINUATION_SOURCE.json','CLOSURE_TIMING.json'])
    return result


def verify(output,inputs,config):
    output=Path(output);start=time.monotonic();check_binding(output,inputs,config);src,_,identity=source(inputs,config)
    if read(output/'CONTINUATION_SOURCE.json')!=identity:raise ValueError('continuation identity differs')
    original.authorize_pilot(src)
    sessions,exclusions=score_rows(src,measure.Encoder(src))
    result,details=original.summarize(sessions,config)
    for name,value in [('CLOSURE_ROWS.json',sessions),('CLOSURE_PRIMARY.json',result),('CLOSURE_DETAILS.json',details),('CLOSURE_SOURCE_EXCLUSIONS.json',exclusions)]:
        if read(output/name)!=value:raise ValueError('continuation fresh replay differs')
    total=read(output/'CLOSURE_TIMING.json')['cumulative_seconds']+time.monotonic()-start
    if total>CAP_SECONDS:raise RuntimeError('single S4 execute/replay allowance exhausted')
    return dict(verified=True,primary=result,retained_checkpoint_files=len(identity['retained_files']),cumulative_seconds=total,single_S4_cap_seconds=CAP_SECONDS)
