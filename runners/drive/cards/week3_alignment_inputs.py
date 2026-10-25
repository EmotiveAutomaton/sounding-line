"""CA1 private turn table and prompt/conversation-disjoint split preparation.

DESIGN CHECK: LESSONS 2-5 and CONTROLS 1-7. Intake counts must match completed
CA0, including incomplete-history exclusions. Splits use only prompt and
conversation membership, never choice/explanation labels. Connected components
prevent the same prompt or any part of one conversation crossing halves. An
unsplittable annotator is unsupported, not assigned a fabricated independent test.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
from pathlib import Path

from .menus_io import assert_equal, input_hashes, read, write, sha256
from .week3_choice_intake import TURNS, OPTIONS, prompt_id

SEED = 20261026
SOURCE_HASH = "4e472530005e86aa847078fe188c41e0efde96f5d31c31fdc15501548ef73954"


def hashed(value):
    return hashlib.sha256(value.encode("utf8")).hexdigest()


def iter_turns(path):
    csv.field_size_limit(16 * 1024 * 1024)
    conversations = set()
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            conversation, writer = row["conversation_id"].strip(), row["annotator_id"].strip()
            if not writer or not conversation or conversation in conversations: raise ValueError("missing or duplicate conversation identity")
            conversations.add(conversation); history = []; earlier = True
            for number, turn in enumerate(TURNS, 1):
                prefix = turn + "_turn_"; prompt = row[prefix + "prompt"].strip()
                choice = row[prefix + "preferred_response"].strip()
                options = [row[prefix + option].strip() for option in OPTIONS]
                feedback = row[prefix + "feedback"].strip()
                present = bool(prompt or choice or any(options) or feedback)
                valid = present and prompt and choice in OPTIONS and all(options) and earlier and row["annotator_country"].strip() and row["assigned_lang"].strip()
                if not valid:
                    earlier = False; continue
                yield {"writer": hashed("annotator:" + writer), "conversation": hashed("conversation:" + conversation),
                       "turn": number, "prompt": prompt_id(prompt), "prompt_text": prompt,
                       "context_text": "\n\n".join([*history, prompt]), "candidates": options,
                       "choice": OPTIONS.index(choice), "explanation": feedback,
                       "country": row["annotator_country"].strip(), "language": row["assigned_lang"].strip(),
                       "wave": row["wave"].strip()}
                history.extend([prompt, options[OPTIONS.index(choice)]])


class UnionFind:
    def __init__(self): self.parent = {}
    def find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]; x = self.parent[x]
        return x
    def join(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b: self.parent[max(a, b)] = min(a, b)


def partitions(metadata, seed=SEED):
    grouped = defaultdict(list)
    for row in metadata: grouped[row["writer"]].append(row)
    split = {}; exclusions = Counter(); details = {}
    for writer, group in sorted(grouped.items()):
        prompts = {r["prompt"] for r in group}
        if len(group) < 20 or len(prompts) < 10:
            exclusions["below_CA0_population_threshold"] += 1; continue
        uf = UnionFind()
        for r in group: uf.join("p:" + r["prompt"], "c:" + r["conversation"])
        components = defaultdict(set)
        for prompt in prompts: components[uf.find("p:" + prompt)].add(prompt)
        if len(components) < 2:
            exclusions["single_connected_prompt_conversation_component"] += 1; continue
        # Largest components first, seed breaks size ties; greedy half balancing.
        ordered = sorted(components, key=lambda c: (-len(components[c]), hashed(f"{seed}:{writer}:{c}")))
        counts = [0, 0]; assigned = {}
        for component in ordered:
            half = 0 if counts[0] <= counts[1] else 1
            assigned[component] = half; counts[half] += len(components[component])
        for r in group: split[(writer, r["conversation"])] = assigned[uf.find("c:" + r["conversation"])]
        details[writer] = {"prompts_per_half": counts, "comparisons_per_half":
                           [sum(split[(writer, r["conversation"])] == h for r in group) for h in (0, 1)],
                           "connected_components": len(components)}
    return split, dict(sorted(exclusions.items())), details


class Lines:
    def __init__(self, path, saving):
        self.hash = hashlib.sha256(); self.count = 0; self.file = None
        if saving:
            self.raw = Path(path).open("xb"); self.file = gzip.GzipFile(filename="", fileobj=self.raw, mode="wb", mtime=0)
    def append(self, value):
        data = (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode("utf8")
        self.hash.update(data); self.count += 1
        if self.file is not None: self.file.write(data)
    def close(self):
        if self.file is not None: self.file.close(); self.raw.close()
        return {"records": self.count, "uncompressed_sha256": self.hash.hexdigest()}


def bind_ca0(inputs):
    report = read(inputs["ca0_summary"]); completion = read(inputs["ca0_complete"])
    if report.get("card") != "CA0" or not report.get("counts", {}).get("counts_only"):
        raise ValueError("completed counts-only CA0 required")
    path = Path(inputs["ca0_summary"]).resolve(); base = Path(inputs["ca0_complete"]).resolve().parent
    if completion.get("status") != "COMPLETE" or completion.get("fresh_process_verified") is not True:
        raise ValueError("CA0 fresh complete receipt absent")
    if completion.get("outputs", {}).get(path.relative_to(base).as_posix()) != sha256(path):
        raise ValueError("CA0 summary not bound by completion")
    if report["input_hashes"]["source"] != sha256(inputs["source"]): raise ValueError("CA0 source differs")
    return report


def calculate(output, inputs, config, saving):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    if not config.get("fixture", False) and sha256(inputs["source"]) != SOURCE_HASH: raise ValueError("frozen CA source changed")
    prior = bind_ca0(inputs)
    metadata = [{k: r[k] for k in ("writer", "conversation", "turn", "prompt", "country", "language", "wave")}
                for r in iter_turns(inputs["source"])]
    if len(metadata) != prior["counts"]["turn_counts"].get("valid_comparisons", 0): raise ValueError("CA0/CA1 valid turn count differs")
    split, exclusions, details = partitions(metadata, int(config.get("seed", SEED)))
    if len(details) > prior["counts"]["eligible_annotators"]: raise ValueError("CA1 eligibility exceeds CA0")
    countries = defaultdict(set)
    for r in metadata: countries[r["writer"]].add(r["country"])
    if any(len(c) != 1 for c in countries.values()): raise ValueError("annotator country not constant")
    text_index = {}; prompt_map = {}; rows = Lines(output / "COMPARISONS.jsonl.gz", saving)
    texts = Lines(output / "TEXTS.jsonl.gz", saving); explanation_count = 0
    def text_id(text):
        digest = hashed(text)
        if digest not in text_index:
            text_index[digest] = len(text_index)
            texts.append({"index": text_index[digest], "sha256": digest, "text": text})
        return text_index[digest]
    try:
        for turn in iter_turns(inputs["source"]):
            key = (turn["writer"], turn["conversation"])
            if key not in split: continue
            prompt_map[turn["prompt"]] = text_id(turn["prompt_text"])
            explanation = turn["explanation"]
            explanation_count += bool(explanation)
            rows.append({"writer": turn["writer"], "conversation": turn["conversation"], "turn": turn["turn"],
                         "prompt": turn["prompt"], "country": turn["country"], "language": turn["language"],
                         "wave": turn["wave"], "half": split[key], "choice": turn["choice"],
                         "candidates": [text_id(t) for t in turn["candidates"]],
                         "context_text": turn["context_text"], "explanation": explanation})
    finally:
        row_receipt = rows.close(); text_receipt = texts.close()
    private = {"writer_splits": details, "prompt_text_indices": prompt_map}
    if saving: write(output / "SPLITS.json", private)
    else: assert_equal(private, read(output / "SPLITS.json"))
    return {"card": "CA1-inputs", "state": "inputs_ready", "input_hashes": input_hashes(inputs),
            "valid_comparisons_before_split": len(metadata), "split_supported_annotators": len(details),
            "split_exclusions": exclusions, "comparisons": row_receipt, "texts": text_receipt,
            "comparisons_with_explanations": explanation_count, "permutation_route": prior["counts"]["permutation_route"],
            "split_rule": "annotator prompt/conversation connected components, outcome-blind seeded greedy prompt balance",
            "private_outputs": ["COMPARISONS.jsonl.gz", "TEXTS.jsonl.gz", "SPLITS.json"],
            "public_scope": "Counts only; prepared labels/text remain private; no value direction fitted."}


def execute(output, inputs, config):
    report = calculate(output, inputs, config, True)
    report["output_hashes"] = {name: sha256(Path(output) / name) for name in report["private_outputs"]}
    write(Path(output) / "SUMMARY.json", report)
    return report


def verify(output, inputs, config):
    expected = read(Path(output) / "SUMMARY.json")
    report = calculate(output, inputs, config, False)
    report["output_hashes"] = {name: sha256(Path(output) / name) for name in report["private_outputs"]}
    assert_equal(report, expected)
    return {"verified": True, "fresh_full_turn_and_split_replay": True}
