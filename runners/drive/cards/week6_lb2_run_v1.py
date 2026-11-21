"""Native execution and fresh replay of the three registered status-diary rows.

DESIGN CHECK (LESSONS 3–5). Bind each cohort's own source, rights and seed.
Every original and replay draw uses the same whole-person counts. Wrong
bindings fail before outcomes. Complete support and all replay cells must
match, including missing cells, before the worker can report verification.
"""
import time
from pathlib import Path

from runners.stage14.common import atomic, now
from . import week6_lb2_panel_v1 as panel
from . import week6_lb2_source_v1 as source
from . import week6_lb_bank_v1 as bank
from .batch_runtime import filehash, freeze, read
from .week6_es_v2 import preserve_inherited_yield
from .week6_ld_draws_v1 import DRAWS, RequestedYield


def validate(inputs, config):
    if set(inputs) != {"source_path", "source_admission_path", "source_admission_sha256"}:
        raise ValueError("Unexpected LB2 input")
    if set(config) != {"panel_config", "max_new_draws", "max_wall_seconds"}:
        raise ValueError("Unexpected LB2 configuration")
    cfg = config["panel_config"]
    spec = source.MEMBERS.get(cfg.get("member"))
    if spec is None or cfg != dict(card="LB2", member=cfg["member"], source_pin=spec.pin,
                                    source_seed=spec.seed, draws=DRAWS, missing_tokens=["", "NA"]):
        raise ValueError("Unregistered LB2 cohort, seed, source or missing convention")
    if (type(config["max_new_draws"]) is not int or not 1 <= config["max_new_draws"] <= DRAWS
            or type(config["max_wall_seconds"]) not in (int, float)
            or not 0 < config["max_wall_seconds"] <= 21600):
        raise ValueError("Unbounded LB2 quantum")
    record = Path(inputs["source_admission_path"])
    if filehash(record) != inputs["source_admission_sha256"]:
        raise ValueError("LB2 source review changed")
    admission = read(record)
    if (admission["schema"] != "LB2_SOURCE_ADMISSION_V1" or admission["owner_reviewed"] is not True
            or admission["panel_config"] != cfg or not admission["rights"]
            or admission["codebook"]["sha256"] != spec.codebook
            or Path(admission["source_path"]).resolve() != Path(inputs["source_path"]).resolve()):
        raise ValueError("Unreviewed LB2 source")
    for key in ("authority", "design", "codebook", "source_layout", "licence", "source_record"):
        proof = admission[key]
        if filehash(Path(proof["path"])) != proof["sha256"]:
            raise ValueError("Changed source review component: " + key)
    return cfg


def operate(output, inputs, config, verify):
    cfg = validate(inputs, config)
    member = cfg["member"]
    output = Path(output)
    original = output / "execute"
    phase = "verify" if verify else "execute"
    directory = output / phase
    if verify and not (original / "ENGINE_RESULT.json").is_file():
        raise ValueError("Complete original bank required for replay")
    if not verify:
        preserve_inherited_yield(output)
    start = time.monotonic()
    next_check = 0.0

    def guard():
        nonlocal next_check
        current = time.monotonic()
        if current - start >= config["max_wall_seconds"]:
            raise RequestedYield("wall quantum")
        if current >= next_check:
            next_check = current + .5
            if any((output / control).exists() for control in ("STOP_REQUEST.json", "YIELD_REQUEST.json")):
                raise RequestedYield("runtime control")

    def progress(count, elapsed):
        atomic(directory / "DRAW_PROGRESS.json",
               dict(at=now(), phase=phase, card="LB2", member=member, committed_draws=count,
                    target=DRAWS, current_phase_wall_seconds=elapsed, child_cpu_seconds=time.process_time()))

    try:
        data = panel.prepare(member, inputs["source_path"], cfg["source_pin"], cfg["missing_tokens"], guard)
        result = bank.run(directory, panel, data, member=member, source_digest=cfg["source_pin"]["sha256"],
                          seed=cfg["source_seed"], guard=guard, verify=verify, execute_dir=original,
                          limit=config["max_new_draws"], progress=progress)
    except RequestedYield as exc:
        return dict(status="yielded", verified=False, operation=phase, reason=str(exc),
                    scientific_result_complete=False)
    result["card"] = "LB2"
    path = directory / "ENGINE_RESULT.json"
    if path.exists():
        if read(path) != result:
            raise ValueError("Completed interaction-diary evidence changed")
    else:
        freeze(path, result)
    return dict(status="verified" if verify else "computed", verified=verify,
                requires_fresh_replay=not verify, scientific_result_complete=verify,
                engine_sha256=filehash(path), draw_count=DRAWS)


def execute(output, inputs, config):
    return operate(output, inputs, config, False)


def verify(output, inputs, config):
    return operate(output, inputs, config, True)
