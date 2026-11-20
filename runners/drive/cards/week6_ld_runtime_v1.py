"""Original-source execute and independently reconstructed replay for LD1–LD3.

DESIGN CHECK: LESSONS 3–5. A constructed check never admits human rows. Each
phase authenticates its reviewed source and retained checkpoint. Refusing one
unidentified metric preserves all other metrics and every indexed draw.
"""
import json
import time
from pathlib import Path

from . import week6_ld_draws_v1 as draws
from .batch_runtime import filehash, freeze, read
from .week6_es_v2 import preserve_inherited_yield
from runners.stage14.common import atomic, now


def validate(card, inputs, config):
    if set(inputs) != {"source_path", "source_admission_path", "source_admission_sha256"}:
        raise ValueError("Unexpected diary source inputs")
    if set(config) != {"panel_config", "max_new_draws", "max_wall_seconds"}:
        raise ValueError("Unexpected diary execution settings")
    panel = config["panel_config"]
    if (set(panel) != {"card", "member", "source_pin", "missing_tokens", "draws", "source_seed"}
            or panel["card"] != card or card not in {"LD1", "LD2", "LD3"}
            or panel["draws"] != draws.DRAWS or panel["member"] not in draws.SOURCE_SEEDS
            or panel["source_seed"] != draws.SOURCE_SEEDS[panel["member"]]):
        raise ValueError("Unreviewed diary panel or draw bank")
    if (type(config["max_new_draws"]) is not int or not 1 <= config["max_new_draws"] <= draws.DRAWS
            or type(config["max_wall_seconds"]) not in (int, float)
            or not 0 < config["max_wall_seconds"] <= 6 * 3600):
        raise ValueError("Invalid operational bounds")
    review_path = Path(inputs["source_admission_path"])
    if filehash(review_path) != inputs["source_admission_sha256"]:
        raise ValueError("Diary source admission pin differs")
    review = read(review_path)
    source_path = Path(inputs["source_path"]).resolve()
    if (review.get("schema") != "LD_SOURCE_ADMISSION_V1" or review.get("owner_reviewed") is not True
            or review.get("panel_config") != panel or Path(review["source_path"]).resolve() != source_path
            or not review.get("authority") or not review.get("source_layout")
            or not review.get("rights")):
        raise ValueError("Diary source, rights or reviewed scope differs")
    for key in ("authority", "source_layout"):
        evidence = review[key]
        if filehash(Path(evidence["path"])) != evidence["sha256"]:
            raise ValueError("Diary review evidence differs: " + key)
    return panel, source_path


def operate(card, producer, output, inputs, config, *, verify):
    panel, source_path = validate(card, inputs, config)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    phase = "verify" if verify else "execute"
    directory = output / phase
    original = output / "execute"
    if not verify:
        preserve_inherited_yield(output)
    if verify and not (original / "ENGINE_RESULT.json").is_file():
        raise ValueError("Full execution required before independent replay")
    since = time.monotonic()
    next_marker_check = 0.

    def guard():
        nonlocal next_marker_check
        current = time.monotonic()
        if current - since >= config["max_wall_seconds"]:
            raise draws.RequestedYield("wall quantum")
        if current >= next_marker_check:
            next_marker_check = current + .5
            if any((output / name).is_file() for name in ("YIELD_REQUEST.json", "STOP_REQUEST.json")):
                raise draws.RequestedYield("runtime control")

    try:
        guard()
        prepared = producer.prepare(panel["member"], source_path, panel["source_pin"],
                                    panel["missing_tokens"], guard)
        def progress(done, elapsed):
            atomic(directory / "DRAW_PROGRESS.json", dict(at=now(), phase=phase, card=card,
                   member=panel["member"], committed_draws=done, target=draws.DRAWS,
                   current_phase_wall_seconds=elapsed, child_cpu_seconds=time.process_time()))
        result = draws.run_draws(directory, producer, prepared, panel["member"], guard,
                                 verify=verify, original=original,
                                 max_new_draws=config["max_new_draws"], progress=progress,
                                 source_digest=panel["source_pin"]["sha256"])
    except draws.RequestedYield as exc:
        return dict(status="yielded", verified=False, operation=phase, reason=str(exc),
                    scientific_result_complete=False)
    result["card"] = card
    result_path = directory / "ENGINE_RESULT.json"
    if result_path.exists():
        if read(result_path) != json.loads(json.dumps(result, allow_nan=False)):
            raise ValueError("Completed checkpoint changes on reconstruction")
    else:
        freeze(result_path, result)
    return dict(status="verified" if verify else "computed", verified=verify,
                requires_fresh_replay=not verify, scientific_result_complete=verify,
                engine_sha256=filehash(result_path), draw_count=draws.DRAWS)
