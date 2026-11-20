"""Versioned diary entry point for the Round 32 additions.

Existing registered rows delegate to the original pinned producer. Stage one
uses the same indexed whole-person draw engine and independent arithmetic.
"""
from pathlib import Path
import time

from runners.stage14.common import atomic, now
from . import week6_diary_rows_v1 as legacy
from . import week6_ld_draws_v1 as draws
from . import week6_nt1_stage1_v1 as nt
from .batch_runtime import filehash, freeze, read
from .week6_es_v2 import preserve_inherited_yield


def validate(inputs, config):
    if set(inputs) != {"source_path", "source_admission_path", "source_admission_sha256"}:
        raise ValueError("Unexpected stage-one source inputs")
    if set(config) != {"panel_config", "max_new_draws", "max_wall_seconds"}:
        raise ValueError("Unexpected stage-one configuration")
    panel = config["panel_config"]
    if (set(panel) != {"card", "member", "source_pin", "missing_tokens", "draws", "source_seed"}
            or (panel["card"], panel["member"], panel["draws"], panel["source_seed"])
            != ("NT1.d", "0057", draws.DRAWS, draws.SOURCE_SEEDS["0057"])
            or not isinstance(panel["missing_tokens"], list) or not panel["missing_tokens"]):
        raise ValueError("Unregistered population or draw bank")
    if (type(config["max_new_draws"]) is not int or not 1 <= config["max_new_draws"] <= draws.DRAWS
            or type(config["max_wall_seconds"]) not in (int, float) or not 0 < config["max_wall_seconds"] <= 21600):
        raise ValueError("Invalid operational bounds")
    review_file = Path(inputs["source_admission_path"])
    if filehash(review_file) != inputs["source_admission_sha256"]:
        raise ValueError("Stage-one source review differs")
    review = read(review_file)
    path = Path(inputs["source_path"]).resolve()
    if (review.get("schema") != "NT1_STAGE_ONE_SOURCE_V1" or review.get("owner_reviewed") is not True
            or review.get("panel_config") != panel or Path(review["source_path"]).resolve() != path
            or not review.get("rights")):
        raise ValueError("Source rights, registration or owner review differs")
    legacy.reviewed_file(review["authority"])
    return review, panel, path


def run(output, inputs, config, checking):
    if config["panel_config"]["card"] in legacy.OPERATORS:
        return (legacy.verify if checking else legacy.execute)(output, inputs, config)
    review, panel, path = validate(inputs, config)
    output = Path(output)
    output.mkdir(exist_ok=True, parents=True)
    phase = "verify" if checking else "execute"
    original = output/"execute"
    target = output/phase
    if checking and not (original/"ENGINE_RESULT.json").is_file():
        raise ValueError("Complete execution required before replay")
    if not checking:
        preserve_inherited_yield(output)
    started = time.monotonic()
    next_check = 0.
    def guard():
        nonlocal next_check
        tick = time.monotonic()
        if tick-started >= config["max_wall_seconds"]:
            raise draws.RequestedYield("wall quantum")
        if tick >= next_check:
            next_check = tick + .5
            if any((output/n).is_file() for n in ("YIELD_REQUEST.json", "STOP_REQUEST.json")):
                raise draws.RequestedYield("runtime control")
    def progress(n, wall):
        atomic(target/"DRAW_PROGRESS.json", dict(at=now(),phase=phase,card="NT1.d",member="0057",
               committed_draws=n,target=draws.DRAWS,current_phase_wall_seconds=wall,child_cpu_seconds=time.process_time()))
    try:
        prepared = nt.assemble(review, panel, path, output, checking, guard)
        if prepared.metadata["supported"]:
            result = draws.run_draws(target, nt, prepared, panel["member"], guard, verify=checking,
                     original=original, max_new_draws=config["max_new_draws"], progress=progress,
                     source_digest=panel["source_pin"]["sha256"])
        else:
            result = {"status":"unsupported", "support":prepared.metadata, "draws":0}
    except draws.RequestedYield as exc:
        return dict(status="yielded", verified=False, operation=phase, reason=str(exc), scientific_result_complete=False)
    if checking and result["status"] == "unsupported" and read(original/"ENGINE_RESULT.json") != result:
        raise ValueError("Fresh support disposition differs")
    if checking and result["status"] == "complete":
        b1, b2 = result["metrics"]["B1"], result["metrics"]["B2"]
        result["stage_two_eligible"] = nt.stage_two_gate(b1["estimate"], b2["estimate"], b2["interval"])
    target.mkdir(exist_ok=True)
    receipt = target/"ENGINE_RESULT.json"
    if receipt.exists():
        if read(receipt) != result:
            raise ValueError("Rebuilt result differs from its checkpoint")
    else:
        freeze(receipt, result)
    return dict(status="verified" if checking else "computed", verified=checking,
                scientific_result_complete=checking, requires_fresh_replay=not checking,
                engine_sha256=filehash(receipt), draw_count=result["draws"])


def execute(output, inputs, config):
    return run(output, inputs, config, False)


def verify(output, inputs, config):
    return run(output, inputs, config, True)
