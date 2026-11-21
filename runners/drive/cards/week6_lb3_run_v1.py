"""Native parent diary worker and complete fresh replay.

DESIGN CHECK (LESSONS 2–5). Either phase checks the reviewed packet, source
authorization, licence and codebook before projecting rows. A changed hash,
wrong member or unregistered seed prevents a fit. The native owner accounts
for every executed or resumed draw, including the independent replay.
"""
import time
from pathlib import Path

from runners.stage14.common import atomic, now
from . import week6_lb3_panel_v1 as panel
from . import week6_lb3_source_v1 as source
from . import week6_lb_bank_v1 as bank
from .batch_runtime import filehash, freeze, read
from .week6_es_v2 import preserve_inherited_yield
from .week6_ld_draws_v1 import DRAWS, RequestedYield


def validate(inputs,config):
    if (set(inputs)!={"source_path","source_admission_path","source_admission_sha256"}
            or set(config)!={"panel_config","max_new_draws","max_wall_seconds"}):
        raise ValueError("Unexpected LB3 input or configuration")
    cfg=config["panel_config"]
    if (set(cfg)!={"card","member","source_pin","source_seed","draws","missing_tokens"}
            or cfg["card"]!="LB3" or cfg["member"]!="0072" or cfg["draws"]!=DRAWS
            or cfg["source_seed"]!=source.SOURCE_SEED
            or cfg["source_pin"]!={"bytes":source.SOURCE_BYTES,"sha256":source.SOURCE_SHA256}
            or not isinstance(cfg["missing_tokens"],list) or not cfg["missing_tokens"]
            or not all(isinstance(v,str) for v in cfg["missing_tokens"])):
        raise ValueError("Unregistered LB3 source, bank or missing tokens")
    if (type(config["max_new_draws"]) is not int or not 1<=config["max_new_draws"]<=DRAWS
            or type(config["max_wall_seconds"]) not in (int,float) or not 0<config["max_wall_seconds"]<=21600):
        raise ValueError("Unbounded or unknown LB3 native quantum")
    path=Path(inputs["source_admission_path"])
    if filehash(path)!=inputs["source_admission_sha256"]:
        raise ValueError("LB3 source review changed")
    admission=read(path)
    if (admission["schema"]!="LB3_SOURCE_ADMISSION_V1" or admission["owner_reviewed"] is not True
            or admission["panel_config"]!=cfg or not admission["rights"]
            or admission["codebook"]["sha256"]!=source.CODEBOOK_SHA256
            or Path(admission["source_path"]).resolve()!=Path(inputs["source_path"]).resolve()):
        raise ValueError("Unreviewed LB3 source scope")
    for key in ("authority","design","codebook","source_layout","licence","source_record"):
        proof=admission[key]
        if filehash(Path(proof["path"]))!=proof["sha256"]:
            raise ValueError("Source admission evidence changed: "+key)
    return cfg


def operate(output,inputs,config,verify):
    cfg=validate(inputs,config)
    output=Path(output)
    original=output/"execute"
    phase="verify" if verify else "execute"
    directory=output/phase
    if verify and not (original/"ENGINE_RESULT.json").is_file():
        raise ValueError("Complete original bank required")
    if not verify:
        preserve_inherited_yield(output)
    start=time.monotonic()
    next_control_check=0.
    def guard():
        nonlocal next_control_check
        current=time.monotonic()
        if current-start>=config["max_wall_seconds"]:
            raise RequestedYield("wall quantum")
        if current>=next_control_check:
            next_control_check=current+.5
            if any((output/control).exists() for control in ("YIELD_REQUEST.json","STOP_REQUEST.json")):
                raise RequestedYield("runtime control")
    def progress(count,elapsed):
        atomic(directory/"DRAW_PROGRESS.json",dict(at=now(),phase=phase,card="LB3",member="0072",
               committed_draws=count,target=DRAWS,current_phase_wall_seconds=elapsed,
               child_cpu_seconds=time.process_time()))
    try:
        guard()
        data=panel.prepare(cfg["member"],inputs["source_path"],cfg["source_pin"],cfg["missing_tokens"],guard)
        result=bank.run(directory,panel,data,member=cfg["member"],source_digest=source.SOURCE_SHA256,
                        seed=cfg["source_seed"],guard=guard,verify=verify,execute_dir=original,
                        limit=config["max_new_draws"],progress=progress)
    except RequestedYield as exc:
        return dict(status="yielded",verified=False,operation=phase,reason=str(exc),scientific_result_complete=False)
    result["card"]="LB3"
    path=directory/"ENGINE_RESULT.json"
    if path.exists():
        if read(path)!=result:
            raise ValueError("LB3 completed evidence changed")
    else:
        freeze(path,result)
    return dict(status="verified" if verify else "computed",verified=verify,requires_fresh_replay=not verify,
                scientific_result_complete=verify,engine_sha256=filehash(path),draw_count=DRAWS)


def execute(output,inputs,config):
    return operate(output,inputs,config,False)


def verify(output,inputs,config):
    return operate(output,inputs,config,True)
