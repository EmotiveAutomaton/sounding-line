"""Native entry for the LD4 two-context recipe bank and independent replay.

DESIGN CHECK (LESSONS 3–5). An original digest, immutable source review and
fixed member-specific 2,000-draw roster are required for either phase. A pause
keeps its indexed draws. Verify rebuilds source moments independently and
compares every weight, diagnostic and interpretation before declaring completion.
"""
import json
import time
from pathlib import Path

from runners.stage14.common import atomic, now
from . import week6_ld4_panel_v1 as producer
from . import week6_ld_draws_v1 as draws
from .batch_runtime import filehash, freeze, read
from .week6_es_v2 import preserve_inherited_yield
from .week6_ld4_recipes_v1 import summarize


def validate(inputs, config):
    expected = {"source_path", "source_admission_path", "source_admission_sha256"}
    if set(inputs)!=expected or set(config)!={"panel_config","max_new_draws","max_wall_seconds"}:
        raise ValueError("Unexpected LD4 source inputs or settings")
    panel = config["panel_config"]
    if (set(panel)!={"card","member","source_pin","missing_tokens","draws","source_seed"}
            or panel["card"]!="LD4" or panel["member"] not in draws.SOURCE_SEEDS or panel["draws"]!=draws.DRAWS
            or panel["source_seed"]!=draws.SOURCE_SEEDS[panel["member"]]):
        raise ValueError("Unexpected LD4 register or source draw bank")
    if (type(config["max_new_draws"]) is not int or not 1<=config["max_new_draws"]<=draws.DRAWS
            or type(config["max_wall_seconds"]) not in (float,int) or not 0<config["max_wall_seconds"]<=21600):
        raise ValueError("Invalid native yield limits")
    path = Path(inputs["source_admission_path"])
    if filehash(path)!=inputs["source_admission_sha256"]:
        raise ValueError("LD4 source admission differs")
    receipt = read(path)
    if (receipt.get("schema")!="LD4_SOURCE_ADMISSION_V1" or receipt.get("owner_reviewed") is not True
            or not receipt.get("rights") or receipt.get("panel_config")!=panel
            or Path(receipt["source_path"]).resolve()!=Path(inputs["source_path"]).resolve()):
        raise ValueError("LD4 source review or scope differs")
    for name in ("authority","design","codebook","source_layout","inherited_member_review"):
        item = receipt[name]
        if filehash(Path(item["path"]))!=item["sha256"]:
            raise ValueError("LD4 source evidence differs: "+name)
    return panel


def _operate(output, inputs, config, verifying):
    panel = validate(inputs,config)
    output = Path(output)
    phase = "verify" if verifying else "execute"
    directory = output/phase
    original = output/"execute"
    if verifying:
        if not (original/"ENGINE_RESULT.json").is_file():
            raise ValueError("Completed LD4 execution required for independent replay")
    else:
        preserve_inherited_yield(output)
    began = time.monotonic()
    next_check = 0.
    def guard():
        nonlocal next_check
        current = time.monotonic()
        if current-began >= config["max_wall_seconds"]:
            raise draws.RequestedYield("wall quantum")
        if current>=next_check:
            next_check = current+.5
            if any((output/name).exists() for name in ("YIELD_REQUEST.json","STOP_REQUEST.json")):
                raise draws.RequestedYield("runtime control")
    def progress(done,elapsed):
        atomic(directory/"DRAW_PROGRESS.json",dict(at=now(),phase=phase,card="LD4",member=panel["member"],
               committed_draws=done,target=draws.DRAWS,current_phase_wall_seconds=elapsed,
               child_cpu_seconds=time.process_time()))
    try:
        guard()
        data = producer.prepare(panel["member"],inputs["source_path"],panel["source_pin"],panel["missing_tokens"],
                                guard,reference=verifying)
        result = draws.run_draws(directory,producer,data,panel["member"],guard,verify=verifying,original=original,
                                 max_new_draws=config["max_new_draws"],progress=progress,source_digest=panel["source_pin"]["sha256"])
    except draws.RequestedYield as exc:
        return dict(status="yielded",verified=False,operation=phase,reason=str(exc),scientific_result_complete=False)
    result["card"] = "LD4"
    summarize(result,draws.load_blocks(directory,sorted(data.specs)),sorted(data.specs))
    if verifying:
        previous = read(original/"ENGINE_RESULT.json")
        if previous["registered_reading"]!=result["registered_reading"]:
            raise ValueError("Independent decision differs")
        for ctx in producer.CONTEXTS:
            for key in ("readable","directions","draws_at_or_above_15_or_singular"):
                if previous["context_checks"][ctx][key]!=result["context_checks"][ctx][key]:
                    raise ValueError("Independent context diagnostic differs")
    end = directory/"ENGINE_RESULT.json"
    if end.exists():
        if read(end)!=json.loads(json.dumps(result,allow_nan=False)):
            raise ValueError("Completed LD4 evidence differs on retry")
    else:
        freeze(end,result)
    return dict(status="verified" if verifying else "computed",verified=verifying,requires_fresh_replay=not verifying,
                scientific_result_complete=verifying,engine_sha256=filehash(end),draw_count=draws.DRAWS)


def execute(output,inputs,config):
    return _operate(output,inputs,config,False)


def verify(output,inputs,config):
    return _operate(output,inputs,config,True)
