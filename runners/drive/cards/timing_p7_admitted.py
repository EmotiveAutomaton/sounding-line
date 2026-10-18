"""Authenticated, checkpointed P7 execution pilot; main needs later admission.

DESIGN CHECK: LESSONS 3-5 reread 2026-10-18. NULL and ALTERNATIVE scientific
effects do not enter this instrument's admission. Corrupt inputs/checkpoints,
missing completion, nonfinite losses, or >1e-4 cached/fresh error refuse. Exact
CPU float32 scoring must agree on native IDs and each loss, including revisions,
Unicode and overflow. Pilot completion is infrastructure only, not a hypothesis
result or permission to start main. No historical result or live source changes.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import time

from .timing_census import read, write, filehash
from .timing_p6 import gzread, gzwrite, write_equal
from .timing_p7 import CachedScorer, visible_prefixes, primary
from .timing_text import TOKEN, WORD

CONFIG = {"phase": "pilot"}
BLOCK = 50
MODEL_REVISION = "6dcaa7a952f72f9298047fd5137cd6e4f05f41da"
JESTER_REVISION = "4449c6e7f4a8d3644308f5c5edc7e11404ea808b"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False).encode("utf8")).hexdigest()


def bound_file(root, relative, expected):
    path = (Path(root) / relative).resolve()
    path.relative_to(Path(root).resolve())
    if filehash(path) != expected:
        raise ValueError("P7 source/completion binding changed: " + str(relative))
    return path


def source(inputs, config):
    if config != CONFIG or set(inputs) != {
        "p6_completion", "raw_roster", "repo_root", "model_manifest",
        "jester_texts", "jester_manifest", "jester_verified"
    }:
        raise ValueError("P7 only admits the fixed execution pilot configuration")
    root = Path(inputs["p6_completion"]).parent
    complete, plan = read(inputs["p6_completion"]), read(root / "PLAN.json")
    if (complete.get("status") != "COMPLETE" or not complete.get("fresh_process_verified")
            or complete.get("card") != "P6-recovery"
            or plan.get("module") != "runners.drive.cards.timing_p6_recovery"
            or plan.get("config") != {}):
        raise ValueError("P7 needs verified complete P6 recovery")
    outputs = complete["outputs"]
    for name in ("PLAN.json", "output/P6_INDEX.json", "output/P6_BINDINGS.json",
                 "output/RECOVERY_BINDING.json", "VERIFIED.json"):
        bound_file(root, name, outputs[name])
    if not read(root / "VERIFIED.json").get("verified"):
        raise ValueError("P7 P6 fresh verification absent")
    original = Path(plan["inputs"]["original_plan"])
    normalized_pins = {str(Path(p).resolve()): h for p, h in plan["pins"].items()}
    if filehash(original) != normalized_pins[str(original.resolve())]:
        raise ValueError("P7 original P6 plan changed")
    original_plan = read(original)
    bindings = read(root / "output/P6_BINDINGS.json")
    if (Path(original_plan["inputs"]["raw_roster"]).resolve() != Path(inputs["raw_roster"]).resolve()
            or bindings["inputs"]["raw_roster"] != filehash(inputs["raw_roster"])
            or bindings["repo_root"] != str(Path(inputs["repo_root"]).resolve())
            or bindings["index_sha256"] != filehash(root / "output/P6_INDEX.json")):
        raise ValueError("P7 roster does not match completed P6")
    p6 = read(root / "output/P6_INDEX.json")
    if not p6 or len({r["session"] for r in p6}) != len(p6):
        raise ValueError("P7 empty or duplicate P6 session identities")
    roster_rows = read(inputs["raw_roster"])
    roster = {r["session"]: r for r in roster_rows}
    if len(roster) != len(roster_rows):
        raise ValueError("P7 duplicate raw session identities")
    for row in p6:
        name = "output/" + row["file"]
        if outputs[name] != row["sha256"] or row["session"] not in roster:
            raise ValueError("P7 P6 score/roster linkage changed")
        bound_file(root, name, row["sha256"])
    manifest, verified = read(inputs["jester_manifest"]), read(inputs["jester_verified"])
    if (manifest["source_revision"] != JESTER_REVISION or manifest["jokes"] != 150
            or verified.get("jokes") != 150 or not verified.get("all_exact_strings_match_independent_xml_parser")
            or not verified.get("source_bytes_and_zip_crc_verified")
            or verified["text_manifest_sha256"] != filehash(inputs["jester_manifest"])
            or manifest["texts_sha256"] != filehash(inputs["jester_texts"])):
        raise ValueError("P7 Jester text admission changed")
    jokes = read(inputs["jester_texts"])
    if (len(jokes) != 150 or {r["joke_id"] for r in jokes} != set(range(1, 151))
            or any(not isinstance(r["text"], str) or not r["text"] for r in jokes)):
        raise ValueError("P7 needs all 150 original Jester identities")
    model = read(inputs["model_manifest"])
    if model.get("model") != "openai-community/gpt2-medium" or model.get("revision") != MODEL_REVISION:
        raise ValueError("P7 wrong model release")
    model_root = Path(model["model_path"]).resolve()
    required = {"config.json", "merges.txt", "model.safetensors", "tokenizer.json", "tokenizer_config.json", "vocab.json"}
    if (Path(model["tokenizer_path"]).resolve() != model_root
            or {Path(p).name for p in model["files"]} != required
            # HF snapshot entries are symlinks into its blob store. Check their
            # lexical snapshot membership, then authenticate resolved bytes below.
            or any(Path(p).absolute().parent != Path(model["model_path"]).absolute() for p in model["files"])
            or {p.name for p in model_root.iterdir() if p.is_file()} != required):
        raise ValueError("P7 model manifest does not cover exact local snapshot")
    for path, expected in model["files"].items():
        if filehash(path) != expected:
            raise ValueError("P7 model/tokenizer source changed")
    for package, expected in model["packages"].items():
        if importlib.metadata.version(package) != expected:
            raise ValueError("P7 model environment changed")
    selected = sorted(p6, key=lambda r: (r["word_count"], r["session"]))[len(p6)//2]
    joke = max(jokes, key=lambda r: (len(r["text"]), str(r["joke_id"])))
    # Census/length selection is frozen before scoring; no outcome selection.
    units = [dict(domain="typed", identity=selected["session"], source=selected),
             dict(domain="jester", identity=str(joke["joke_id"]), source=joke)]
    binding = dict(config=config, inputs={k: str(Path(v).resolve()) if k == "repo_root" else filehash(v)
                                         for k, v in inputs.items()}, units=units,
                   totals=dict(typed=sum(r["word_count"] for r in p6),
                               jester=sum(len(TOKEN.findall(r["text"])) for r in jokes)),
                   sessions=len(p6), jokes=len(jokes))
    return binding, roster, root / "output", model


def locations(unit, roster, p6_output, inputs):
    if unit["domain"] == "typed":
        row = unit["source"]
        record = gzread(bound_file(p6_output, row["file"], row["sha256"]))
        meta = roster[unit["identity"]]
        path = bound_file(inputs["repo_root"], meta["path"], meta["source_sha256"])
        with path.open(encoding="utf8") as stream:
            prefixes = visible_prefixes([json.loads(line) for line in stream], record["words"])
        if len(record["words"]) != row["word_count"]:
            raise ValueError("P7 P6 word count changed")
        return [dict(index=r["index"], is_word=r["is_word"], **prefixes[r["index"]]) for r in record["words"]]
    text = unit["source"]["text"]
    return [dict(index=i, is_word=bool(WORD.fullmatch(m.group())), prefix=text[:m.start()], target=m.group())
            for i, m in enumerate(TOKEN.finditer(text))]


def load_model(manifest):
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    torch.set_num_threads(2)
    tokenizer = AutoTokenizer.from_pretrained(manifest["tokenizer_path"], local_files_only=True, use_fast=True, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(manifest["model_path"], local_files_only=True,
                                               torch_dtype=torch.float32, use_safetensors=True, trust_remote_code=False).cpu().eval()
    if (model.config.model_type != "gpt2" or model.config.n_layer != 24 or model.config.n_embd != 1024
            or model.config.n_positions != 1024 or not tokenizer.is_fast
            or model.training or any(p.device.type != "cpu" or p.dtype != torch.float32 for p in model.parameters())):
        raise ValueError("P7 requires GPT-2 medium eval on CPU float32")
    return model, tokenizer, torch


def numerical_controls(model, tokenizer, torch):
    scorer = CachedScorer(model, tokenizer, torch)
    cases = [("The cat ", "sat"), ("The cat sat ", "here"), ("The dog ", "sat"),
             ("The dog ", "sat"), ("A café 😀 ", "opens"), ("word " * 1100, "again")]
    errors = [scorer.direct_check(p, t, scorer.score(p, t)) for p, t in cases]
    return dict(cases=len(errors), max_error=max(errors), tolerance=1e-4,
                covers=["prefix reuse", "revision", "identical reentry", "Unicode", "context overflow"])


def saved_blocks(output, unit, binding_hash, rows):
    folder = output / "parts" / unit["domain"] / unit["identity"]
    words, seconds, forward_tokens = [], 0., 0
    for number, path in enumerate(sorted(folder.glob("block-*.json.gz"))):
        if path.name != f"block-{number:05d}.json.gz":
            raise ValueError("P7 nonconsecutive saved block")
        receipt = read(path.with_suffix(".receipt.json"))
        if receipt["sha256"] != filehash(path):
            raise ValueError("P7 checkpoint hash changed")
        block = gzread(path)
        expected = rows[len(words):len(words)+BLOCK]
        if (not expected or block["binding"] != binding_hash or block["start"] != len(words)
                or block["locations_sha256"] != digest(expected) or len(block["words"]) != len(expected)):
            raise ValueError("P7 checkpoint input/coverage changed")
        for location, score in zip(expected, block["words"]):
            losses = score["native_token_nll"]
            if (score["index"] != location["index"] or score["is_word"] != location["is_word"]
                    or not losses or len(losses) != len(score["native_token_ids"])
                    or any(not math.isfinite(v) or v < 0 for v in losses)
                    or score["surprisal_nats"] != sum(losses)):
                raise ValueError("P7 saved score identity/reduction changed")
        if not math.isfinite(block["seconds"]) or block["seconds"] < 0:
            raise ValueError("P7 checkpoint timing invalid")
        words.extend(block["words"]); seconds += block["seconds"]; forward_tokens += block["forward_tokens"]
    return folder, words, seconds, forward_tokens


def execute(output, inputs, config):
    output = Path(output)
    started = time.monotonic()
    binding, roster, p6_output, manifest = source(inputs, config)
    write_equal(output / "INPUT_BINDING.json", binding)
    if (output / "OUTPUT_HASHES.json").exists():
        return verify(output, inputs, config)["primary"]
    prepared = [(u, locations(u, roster, p6_output, inputs)) for u in binding["units"]]
    bh = digest(binding)
    # Authenticate every retained block before loading the model or doing work.
    for unit, rows in prepared:
        saved_blocks(output, unit, bh, rows)
    model, tokenizer, torch = load_model(manifest)
    load_seconds = time.monotonic() - started
    controls = numerical_controls(model, tokenizer, torch)
    write_equal(output / "NUMERICAL_CONTROLS.json", controls)
    index, timings, forward = [], {}, 0
    total_targets = sum(len(rows) for _, rows in prepared)
    done_targets, scoring_seconds = 0, 0.
    for unit, rows in prepared:
        folder, words, seconds, previous_forward = saved_blocks(output, unit, bh, rows)
        done_targets += len(words); scoring_seconds += seconds
        scorer = CachedScorer(model, tokenizer, torch)
        for start in range(len(words), len(rows), BLOCK):
            tick = time.monotonic(); initial_forward = scorer.forward_tokens
            batch = []
            for row in rows[start:start+BLOCK]:
                score = scorer.score(row["prefix"], row["target"])
                batch.append(dict(index=row["index"], is_word=row["is_word"], **score))
            block = dict(binding=bh, start=start, locations_sha256=digest(rows[start:start+BLOCK]),
                         words=batch, seconds=time.monotonic()-tick,
                         forward_tokens=scorer.forward_tokens-initial_forward)
            dest = folder / f"block-{start//BLOCK:05d}.json.gz"
            gzwrite(dest, block)
            write(dest.with_suffix(".receipt.json"), dict(sha256=filehash(dest)))
            words.extend(batch); seconds += block["seconds"]
            done_targets += len(batch); scoring_seconds += block["seconds"]
            if done_targets >= math.ceil(total_targets/10) and not (output / "FIRST_TENTH.json").exists():
                write(output / "FIRST_TENTH.json", dict(completed_tokens=done_targets,
                      total_tokens=total_targets, primary_seconds=time.monotonic()-started,
                      projected_cpu_seconds=load_seconds+scoring_seconds*total_targets/done_targets,
                      scope="selected pilot units only; full-pass projection is separate"))
            if (output / "YIELD_REQUEST.json").exists():
                return dict(status="yielded", unit=unit["domain"], completed_tokens=len(words))
        errors = [scorer.direct_check(rows[i]["prefix"], rows[i]["target"], words[i])
                  for i in sorted({0, len(rows)//2, len(rows)-1})]
        dest = output / unit["domain"] / (unit["identity"] + ".json.gz")
        payload = dict(words=words, **({"session": unit["identity"]} if unit["domain"] == "typed"
                                      else {"joke_id": int(unit["identity"])}))
        if dest.exists():
            if gzread(dest) != payload:
                raise ValueError("P7 consolidated checkpoint changed")
        else:
            gzwrite(dest, payload)
        index.append(dict(domain=unit["domain"], file=dest.relative_to(output).as_posix(), sha256=filehash(dest),
                          words=len(words), total_nll=sum(w["surprisal_nats"] for w in words),
                          direct_errors=errors, **{k:v for k,v in payload.items() if k != "words"}))
        timings[unit["domain"]] = seconds
        forward += previous_forward + scorer.forward_tokens
    result = primary(index, True)
    timing = dict(pilot_only=True, model_load_seconds=load_seconds,
                  observed_scoring_seconds=timings, includes_source_checks=True,
                  projected_cpu_seconds=load_seconds+sum(timings[r["domain"]]*binding["totals"][r["domain"]]/r["words"] for r in index),
                  forward_tokens=forward, excludes_final_verification=True,
                  projection_basis="length-selected median typed session and longest joke; per-domain token-rate scaling; not a main admission")
    for name, data in (("P7_INDEX.json", index), ("P7_PRIMARY.json", result), ("P7_TIMING.json", timing)):
        write_equal(output / name, data)
    write(output / "OUTPUT_HASHES.json", {p.relative_to(output).as_posix():filehash(p)
          for p in output.rglob("*") if p.is_file() and p.name not in {"YIELD_REQUEST.json"}})
    return result


def verify(output, inputs, config):
    output = Path(output)
    binding, roster, p6_output, manifest = source(inputs, config)
    if read(output / "INPUT_BINDING.json") != binding:
        raise ValueError("P7 retained input binding changed")
    for name, expected in read(output / "OUTPUT_HASHES.json").items():
        bound_file(output, name, expected)
    index = read(output / "P7_INDEX.json")
    if len(index) != len(binding["units"]):
        raise ValueError("P7 saved unit coverage changed")
    model, tokenizer, torch = load_model(manifest)
    controls = numerical_controls(model, tokenizer, torch)
    direct_errors = []
    for unit, entry in zip(binding["units"], index):
        rows = locations(unit, roster, p6_output, inputs)
        _, words, _, _ = saved_blocks(output, unit, digest(binding), rows)
        expected_name = f"{unit['domain']}/{unit['identity']}.json.gz"
        if entry["file"] != expected_name or entry["domain"] != unit["domain"] or len(words) != len(rows):
            raise ValueError("P7 reconstructed source coverage mismatch")
        payload = gzread(bound_file(output, entry["file"], entry["sha256"]))
        identity_key = "session" if unit["domain"] == "typed" else "joke_id"
        if str(payload[identity_key]) != unit["identity"] or entry[identity_key] != payload[identity_key] or payload["words"] != words:
            raise ValueError("P7 saved unit identity changed")
        scorer = CachedScorer(model, tokenizer, torch)
        for row, saved in zip(rows, words):
            encoded = tokenizer(row["prefix"]+row["target"], add_special_tokens=False, return_offsets_mapping=True)
            positions = [i for i,(a,b) in enumerate(encoded["offset_mapping"]) if b>len(row["prefix"]) and a<len(row["prefix"]+row["target"])]
            if (saved["native_token_ids"] != [encoded["input_ids"][i] for i in positions]
                    or saved["prefix_tokens_dropped"] != max(0,len(encoded["input_ids"])+1-1024)):
                raise ValueError("P7 native token identity does not reconstruct")
        direct_errors.extend(scorer.direct_check(rows[i]["prefix"], rows[i]["target"], words[i])
                             for i in sorted({0,len(rows)//2,len(rows)-1}))
        if entry["words"] != len(words) or entry["total_nll"] != sum(w["surprisal_nats"] for w in words):
            raise ValueError("P7 saved unit reduction changed")
    result = primary(index, True)
    if result != read(output / "P7_PRIMARY.json"):
        raise ValueError("P7 primary does not recompute")
    return dict(verified=True, primary=result, fresh_source_reconstruction=True,
                cached_direct_max_error=max(direct_errors+[controls["max_error"]]),
                checked_targets=len(direct_errors), main_admitted=False)
