"""WB1 full-population first-tenth cost probe, without a scientific verdict.

DESIGN CHECK: LESSONS 3-5, 2026-10-25. A cost probe counts actual positive
new work and includes both whole-session and time-third conditional controls.
Held-out coverage uses ALL eligible candidates, an upper-work approximation to
the eventual discovered subset; no pilot significance or routing is produced.
Fresh verification repeats the entire measured workload. Changed references or
sources refuse admission. Effects/model inference is explicitly not projected.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import time

from runners.drive.cards import week3_pieces_coverage as coverage
from runners.drive.cards import week3_pieces_stats as stats
from runners.drive.cards.timing_census import read
from runners.drive.cards.timing_p6 import write_equal
from runners.stage14.common import atomic


def measure(output,inputs,config):
    expected={"mode","coarse","seed","pilot_draws","minimum_occurrences","minimum_writers"}
    if set(config)!=expected or config["mode"] not in {"constructed","corpus"} or type(config["coarse"]) is not bool or config["seed"]!=stats.SEED:
        raise ValueError("frozen WB1 first-tenth configuration required")
    if type(config["pilot_draws"]) is not int or config["pilot_draws"]<1:
        raise ValueError("positive new-work timing denominator required")
    if config["mode"]=="corpus" and [config[k] for k in ("pilot_draws","minimum_occurrences","minimum_writers")]!=[20,30,10]:
        raise ValueError("full first tenth and original support thresholds required")
    start_cpu,start_wall=time.process_time(),time.monotonic()
    rows=coverage.load(inputs,config)
    discovery=[r for r in rows if r["side"]=="discovery"]
    test=[r for r in rows if r["side"]=="test"]
    candidate=stats.candidates(discovery,config["minimum_occurrences"],config["minimum_writers"])
    keys=sorted(candidate)
    candidates_cpu=time.process_time()-start_cpu
    digests=[]
    for thirds in (False,True):
        scope="thirds" if thirds else "whole"
        for draw in range(config["pilot_draws"]):
            counts=Counter()
            covered=[]
            for row in discovery:
                seq=stats.surrogate(row["symbols"],row["seconds"],row["duration"],stats.derived_seed(scope,draw,row["session"]),thirds)
                counts.update(piece for piece in stats.ngrams(seq) if piece in candidate)
            for row in test:
                seq=stats.surrogate(row["symbols"],row["seconds"],row["duration"],stats.derived_seed(scope,draw,row["session"]),thirds)
                covered.append(stats.greedy_cover(seq,keys)[0])
            digest=hashlib.sha256(json.dumps([[counts[k] for k in keys],covered],separators=(",",":")).encode()).hexdigest()
            digests.append(dict(scope=scope,draw=draw,sha256=digest))
            atomic(Path(output)/"PROGRESS.json",dict(phase="first_tenth",scope=scope,draws=draw+1,total=config["pilot_draws"],cpu_seconds=time.process_time()-start_cpu,wall_seconds=time.monotonic()-start_wall))
            if (Path(output)/"YIELD_REQUEST.json").exists():
                raise coverage.YieldRequested("completed pilot draw boundary")
    cpu=time.process_time()-start_cpu
    reference_cpu=cpu-candidates_cpu
    work=dict(sessions=len(rows),writers=len({r["writer"] for r in rows}),candidates=len(keys),
              scope_draws_per_session=config["pilot_draws"],scopes=2,reference_digests=digests,
              counted_work="both halves and both null scopes; held-out cover uses every candidate")
    timing=dict(cpu_seconds=cpu,wall_seconds=time.monotonic()-start_wall,setup_cpu_seconds=candidates_cpu,
                reference_cpu_seconds=reference_cpu,
                projected_combined_coverage_cpu_seconds=2*(candidates_cpu+reference_cpu*200/config["pilot_draws"]),
                includes_full_fresh_coverage_replay=True,
                excludes="previous attempt/pilot charges, effects and encoder, plus final bootstrap overhead; owner adds them before admission")
    return work,timing


def execute(output,inputs,config):
    try:
        work,timing=measure(output,inputs,config)
    except coverage.YieldRequested as exc:
        return dict(status="yielded",reason=str(exc),scientific_admission=False)
    result=dict(card="WB1-cost-pilot",status="cost_probe_complete",scientific_admission=False,work=work,timing=timing)
    write_equal(Path(output)/"PILOT_RESULT.json",result)
    return result


def verify(output,inputs,config):
    work,timing=measure(output,inputs,config)
    saved=read(Path(output)/"PILOT_RESULT.json")
    if saved["work"]!=work:
        raise ValueError("first-tenth complete reference replay differs")
    return dict(verified=True,full_probe_replay=True,scientific_admission=False,verification_timing=timing)
