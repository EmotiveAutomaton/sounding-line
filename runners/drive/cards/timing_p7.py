"""P7: CPU GPT-2 medium word surprisal at the full visible prefix.

Separate raw replay recovers prefixes for the immutable P6 production ledger.
Exact shared-token prefixes reuse a cropped KV cache; context overflow uses the
last 1024 tokens and records the omitted prefix. No two-word substitution.

DESIGN CHECK: LESSONS sections 3-5 read 2026-10-17. Under prefix/cache corruption,
cached native-token losses disagree with a fresh forward on identical tokens;
maximum absolute error above 1e-4 refuses the pilot. Under exact CPU float32
prefix reuse, differences remain within this fixed numerical tolerance. Missing
tokens, incomplete prefixes, nonfinite losses and wrong model identity refuse.
"""
from __future__ import annotations

import json
import math
import time
from collections import defaultdict
from pathlib import Path

from runners.drive.cards import states_v2 as states
from runners.drive.cards.timing_census import read, write, filehash
from runners.drive.cards.timing_p6 import gzread, gzwrite
from runners.drive.cards.timing_stats import bind, check_binding
from runners.drive.cards.timing_text import TOKEN, WORD
from runners.stage9.coauthor import units, text_of, delta_ops, apply_delta


def visible_prefixes(events, targets):
    """Match immutable word identities by text, first-insert event and order."""
    by_event = defaultdict(list)
    for target in targets:
        by_event[target["completed_ordinal"]].append(target)
    doc = units(events[0]["currentDoc"])
    owners, inserted_ordinals = [-1] * len(doc), []
    out, used = {}, set()

    def candidates(document, provenance):
        text = text_of(document)
        matches = defaultdict(list)
        offsets = [0]
        for char in text:
            offsets.append(offsets[-1] + len(units(char)))
        for match in TOKEN.finditer(text):
            a, b = offsets[match.start()], offsets[match.end()]
            ids = tuple(dict.fromkeys(provenance[a:b]))
            if not ids or -1 in ids or ids in used:
                continue
            key = (match.group().casefold(), inserted_ordinals[ids[0]], len(match.group()))
            matches[key].append((ids, text[:match.start()], match.group()))
        return matches

    for ordinal, event in enumerate(events):
        before_doc, before_owners = doc, owners
        ops = delta_ops(event.get("textDelta"))
        if ops:
            next_owners, position = [], 0
            for op in ops:
                if "insert" in op:
                    for char in op["insert"]:
                        identity = -1
                        if event.get("eventSource") == "user":
                            identity = len(inserted_ordinals)
                            inserted_ordinals.append(ordinal)
                        next_owners.extend([identity] * len(units(char)))
                elif "retain" in op:
                    next_owners.extend(owners[position:position + op["retain"]])
                    position += op["retain"]
                else:
                    position += op["delete"]
            next_owners.extend(owners[position:])
            doc, _, _ = apply_delta(doc, owners, event.get("textDelta"))
            owners = next_owners
        if ordinal not in by_event:
            continue
        old_matches, new_matches = candidates(before_doc, before_owners), candidates(doc, owners)
        for target in sorted(by_event[ordinal], key=lambda r: r["index"]):
            key = (target["token"], target["ordinal"], target["length"])
            options = [v for v in old_matches[key] if v[0] not in used] or [v for v in new_matches[key] if v[0] not in used]
            if not options:
                raise ValueError("P7 cannot uniquely locate produced token at its completion event")
            ids, prefix, text = options[0]
            used.add(ids)
            out[target["index"]] = dict(prefix=prefix, target=text)
    if set(out) != {row["index"] for row in targets}:
        raise ValueError("P7 produced-word prefix coverage mismatch")
    return out


class CachedScorer:
    def __init__(self, model, tokenizer, torch):
        self.model, self.tokenizer, self.torch = model, tokenizer, torch
        self.cache, self.ids, self.losses = None, [], []
        self.forward_tokens = 0

    def score(self, prefix, target):
        encoded = self.tokenizer(prefix + target, add_special_tokens=False, return_offsets_mapping=True)
        raw_ids, offsets = encoded["input_ids"], encoded["offset_mapping"]
        target_positions = [i + 1 for i, (a, b) in enumerate(offsets) if b > len(prefix) and a < len(prefix + target)]
        if not target_positions:
            raise ValueError("P7 target has no native tokens")
        all_ids = [self.tokenizer.eos_token_id] + raw_ids
        dropped = max(0, len(all_ids) - 1024)
        ids = all_ids[dropped:]
        positions = [i - dropped for i in target_positions]
        if min(positions) <= 0:
            raise ValueError("P7 target exceeds the model context")
        common = 0
        for old, new in zip(self.ids, ids):
            if old != new:
                break
            common += 1
        if common == len(ids) and self.cache is not None:
            self.cache.crop(len(ids))
            losses = self.losses[:len(ids)]
        else:
            reuse = max(0, common - 1)
            if self.cache is not None and reuse:
                self.cache.crop(reuse)
            else:
                self.cache = None
                reuse = 0
            tensor = self.torch.tensor([ids[reuse:]], dtype=self.torch.long, device="cpu")
            with self.torch.inference_mode():
                output = self.model(input_ids=tensor, past_key_values=self.cache, use_cache=True)
                nll = self.torch.nn.functional.cross_entropy(output.logits[0, :-1].float(), tensor[0, 1:], reduction="none").tolist()
            self.forward_tokens += len(ids) - reuse
            self.cache = output.past_key_values
            if not hasattr(self.cache, "crop"):
                raise ValueError("installed model cache lacks tested crop interface")
            losses = (self.losses[:reuse + 1] if reuse else [None]) + nll
        self.ids, self.losses = ids, losses
        native = [losses[i] for i in positions]
        if any(x is None or not math.isfinite(x) or x < 0 for x in native):
            raise ValueError("invalid P7 target log probability")
        return dict(surprisal_nats=sum(native), native_token_nll=native,
                    native_token_ids=[ids[i] for i in positions], prefix_tokens_dropped=dropped)

    def direct_check(self, prefix, target, actual):
        encoded = self.tokenizer(prefix + target, add_special_tokens=False, return_offsets_mapping=True)
        raw = [self.tokenizer.eos_token_id] + encoded["input_ids"]
        dropped = max(0, len(raw) - 1024)
        ids = raw[dropped:]
        positions = [i + 1 - dropped for i, (a, b) in enumerate(encoded["offset_mapping"]) if b > len(prefix) and a < len(prefix + target)]
        tensor = self.torch.tensor([ids], dtype=self.torch.long, device="cpu")
        with self.torch.inference_mode():
            output = self.model(input_ids=tensor, use_cache=False)
            nll = self.torch.nn.functional.cross_entropy(output.logits[0, :-1].float(), tensor[0, 1:], reduction="none").tolist()
        expected = [nll[i - 1] for i in positions]
        saved = actual["native_token_nll"]
        if (not expected or min(positions) <= 0 or len(expected) != len(saved)
                or actual["native_token_ids"] != [ids[i] for i in positions]
                or actual["prefix_tokens_dropped"] != dropped
                or any(not math.isfinite(x) or x < 0 for x in expected + saved)
                or actual["surprisal_nats"] != sum(saved)):
            raise ValueError("P7 cached/direct identity or finite-loss control failed")
        error = max(abs(a - b) for a, b in zip(expected, saved))
        if error > 1e-4:
            raise ValueError("P7 cached/direct numerical control failed")
        return error


def primary(index, pilot):
    count = sum(row["words"] for row in index)
    total = sum(row["total_nll"] for row in index)
    return dict(card="P7", state=states.instrument_state(count > 0), descriptive=True, pilot_only=pilot,
                units=len(index), words=count, total_nll=total, mean_word_surprisal=total / count if count else None,
                context="full visible prefix, left-truncated only at GPT-2's 1024-token context; native-token boundary overlap retained",
                model="GPT-2 medium, CPU float32", unit="sum of native token losses overlapping each word or punctuation token")


def execute(output: Path, inputs: dict, config: dict) -> dict:
    if config not in ({"phase": "pilot"}, {"phase": "main"}):
        raise ValueError("P7 requires fixed pilot or main phase")
    output = Path(output)
    pilot = config["phase"] == "pilot"
    overall_started = time.monotonic()
    manifest = read(inputs["model_manifest"])
    for path, expected in manifest["files"].items():
        if filehash(path) != expected:
            raise ValueError("P7 model/tokenizer source changed")
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    torch.set_num_threads(2)
    tokenizer = AutoTokenizer.from_pretrained(manifest["tokenizer_path"], local_files_only=True, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(manifest["model_path"], local_files_only=True, torch_dtype=torch.float32).cpu().eval()
    if model.config.model_type != "gpt2" or model.config.n_layer != 24 or model.config.n_embd != 1024:
        raise ValueError("P7 manifest is not GPT-2 medium")
    p6_path = Path(inputs["p6_index"])
    p6_index = read(p6_path)
    roster = {row["session"]: row for row in read(inputs["raw_roster"])}
    jokes = read(inputs["jester_texts"])
    if not jokes or len({row["joke_id"] for row in jokes}) != len(jokes):
        raise ValueError("P7 jokes need unique frozen identities")
    chosen_sessions = sorted(p6_index, key=lambda row: (row["word_count"], row["session"]))
    chosen_jokes = sorted(jokes, key=lambda row: (len(row["text"]), str(row["joke_id"])))
    if pilot:
        chosen_sessions = [chosen_sessions[len(chosen_sessions) // 2]]
        chosen_jokes = [chosen_jokes[-1]]
    started = time.monotonic()
    model_load_seconds = started - overall_started
    index, forward_tokens, control_errors = [], 0, []
    for row in chosen_sessions:
        path = p6_path.parent / row["file"]
        if filehash(path) != row["sha256"]:
            raise ValueError("P7 production-ledger source changed")
        record = gzread(path)
        source_meta = roster[row["session"]]
        source = (Path(inputs["repo_root"]) / source_meta["path"]).resolve()
        source.relative_to(Path(inputs["repo_root"]).resolve())
        if filehash(source) != source_meta["source_sha256"]:
            raise ValueError("P7 raw source changed")
        with source.open(encoding="utf-8") as stream:
            prefixes = visible_prefixes([json.loads(line) for line in stream], record["words"])
        scorer = CachedScorer(model, tokenizer, torch)
        words = []
        for wi, word in enumerate(record["words"]):
            location = prefixes[word["index"]]
            score = scorer.score(location["prefix"], location["target"])
            words.append(dict(index=word["index"], is_word=word["is_word"], **score))
            if pilot and wi in {0, len(record["words"]) // 2, len(record["words"]) - 1}:
                control_errors.append(scorer.direct_check(location["prefix"], location["target"], score))
        dest = output / "typed" / (row["session"] + ".json.gz")
        gzwrite(dest, dict(session=row["session"], words=words))
        index.append(dict(domain="typed", session=row["session"], file=dest.relative_to(output).as_posix(), sha256=filehash(dest),
                          words=len(words), total_nll=sum(word["surprisal_nats"] for word in words)))
        forward_tokens += scorer.forward_tokens
    typed_seconds = time.monotonic() - started
    jokes_started = time.monotonic()
    for joke in chosen_jokes:
        scorer = CachedScorer(model, tokenizer, torch)
        words = [dict(index=i, start=match.start(), end=match.end(), text=match.group(), is_word=bool(WORD.fullmatch(match.group())),
                      **scorer.score(joke["text"][:match.start()], match.group())) for i, match in enumerate(TOKEN.finditer(joke["text"]))]
        identity = str(joke["joke_id"])
        if not identity.isalnum():
            raise ValueError("P7 joke ID must be filename-safe alphanumeric")
        dest = output / "jester" / (identity + ".json.gz")
        gzwrite(dest, dict(joke_id=joke["joke_id"], words=words))
        index.append(dict(domain="jester", joke_id=joke["joke_id"], file=dest.relative_to(output).as_posix(), sha256=filehash(dest),
                          words=len(words), total_nll=sum(word["surprisal_nats"] for word in words)))
        forward_tokens += scorer.forward_tokens
    joke_seconds = time.monotonic() - jokes_started
    observed_typed = sum(row["words"] for row in index if row["domain"] == "typed")
    observed_jokes = sum(row["words"] for row in index if row["domain"] == "jester")
    total_typed = sum(row["word_count"] for row in p6_index)
    total_jokes = sum(len(TOKEN.findall(joke["text"])) for joke in jokes)
    projection = model_load_seconds + typed_seconds * total_typed / max(observed_typed, 1) + joke_seconds * total_jokes / max(observed_jokes, 1)
    result = primary(index, pilot)
    write(output / "P7_INDEX.json", index)
    write(output / "P7_PRIMARY.json", result)
    write(output / "P7_TIMING.json", dict(wall_seconds=time.monotonic() - overall_started, forward_tokens=forward_tokens,
          scored_sessions=len(chosen_sessions), total_sessions=len(p6_index), scored_jokes=len(chosen_jokes), total_jokes=len(jokes),
          pilot_only=pilot, model_load_seconds=model_load_seconds, typed_seconds=typed_seconds, joke_seconds=joke_seconds,
          projected_cpu_seconds=projection, cached_direct_max_error=max(control_errors) if control_errors else None,
          cached_direct_checked_targets=len(control_errors), includes_model_load=True))
    bind(output, inputs, config, ["P7_PRIMARY.json", "P7_INDEX.json", "P7_TIMING.json"])
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    check_binding(output, inputs, config)
    index = read(Path(output) / "P7_INDEX.json")
    fresh = []
    for row in index:
        path = Path(output) / row["file"]
        if filehash(path) != row["sha256"]:
            raise ValueError("P7 retained native losses changed")
        words = gzread(path)["words"]
        if any(word["surprisal_nats"] != sum(word["native_token_nll"]) for word in words):
            raise ValueError("P7 word-loss reduction mismatch")
        fresh.append(dict(row, words=len(words), total_nll=sum(sum(word["native_token_nll"]) for word in words)))
    result = primary(fresh, config["phase"] == "pilot")
    if result != read(Path(output) / "P7_PRIMARY.json"):
        raise ValueError("P7 primary does not recompute")
    return dict(verified=True, primary=result)
