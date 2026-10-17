"""P6: leave-writer-out interpolated Kneser-Ney word trigrams.

Training uses contiguous final user-typed spans, never joining across prompt/API
text. Targets are the production ledger, including later revised occurrences.
Hyperparameters are fixed: order 3, discount .75, vocabulary count cutoff 2.
"""
from __future__ import annotations

import gzip
import json
import math
import os
import time
from collections import Counter, defaultdict
from pathlib import Path

from runners.drive.cards import states
from runners.drive.cards.timing_census import read, write, filehash, session_paths
from runners.drive.cards.timing_text import replay_words, tokens


class KneserNey:
    def __init__(self, sequences, discount=.75):
        raw = Counter(word for seq in sequences for word in seq)
        self.vocabulary = {word for word, count in raw.items() if count >= 2} | {"<s>", "</s>", "<unk>"}
        self.word_counts = Counter()
        for word, count in raw.items():
            self.word_counts[self.lookup(word)] += count
        self.word_total = sum(raw.values())
        self.discount = discount
        self.three, self.two = Counter(), Counter()
        for seq in sequences:
            padded = ["<s>", "<s>"] + [self.lookup(w) for w in seq] + ["</s>"]
            for i in range(2, len(padded)):
                self.three[tuple(padded[i - 2:i + 1])] += 1
                self.two[tuple(padded[i - 1:i + 1])] += 1
        if not self.three:
            raise ValueError("empty Kneser-Ney training corpus")
        self.context_total, self.context_types = Counter(), Counter()
        self.lower = Counter()
        for (a, b, word), count in self.three.items():
            self.context_total[(a, b)] += count
            self.context_types[(a, b)] += 1
            self.lower[(b, word)] += 1
        self.lower_total, self.lower_types = Counter(), Counter()
        for (b, word), count in self.lower.items():
            self.lower_total[b] += count
            self.lower_types[b] += 1
        self.continuations = Counter(word for _, word in self.two)
        self.total_types = len(self.two)

    def lookup(self, word):
        return word if word in self.vocabulary else "<unk>"

    def score(self, word, context):
        word = self.lookup(word)
        context = ["<s>"] * max(0, 2 - len(context)) + [self.lookup(w) for w in context[-2:]]
        a, b = context
        p = self.continuations[word] / self.total_types
        if self.lower_total[b]:
            n = self.lower_total[b]
            p = max(self.lower[(b, word)] - self.discount, 0) / n + self.discount * self.lower_types[b] / n * p
        if self.context_total[(a, b)]:
            n = self.context_total[(a, b)]
            p = max(self.three[(a, b, word)] - self.discount, 0) / n + self.discount * self.context_types[(a, b)] / n * p
        if not math.isfinite(p) or not 0 <= p <= 1:
            raise ValueError("invalid Kneser-Ney probability")
        return p


def training_sequences(timeline):
    groups, current = [], ""
    spans = timeline["final_spans"]
    for span in spans:
        if span["origin"] == "typed":
            current += span["text"]
        elif current:
            groups.append(current)
            current = ""
    if current:
        groups.append(current)
    return [seq for text in groups for part in text.splitlines() if (seq := tokens(part))]


def gzwrite(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, allow_nan=False).encode("utf-8")
    with path.open("xb") as stream:
        stream.write(gzip.compress(payload, mtime=0))


def gzread(path):
    return json.loads(gzip.decompress(Path(path).read_bytes()))


def write_equal(path, value):
    if Path(path).exists():
        if read(path) != value:
            raise ValueError("P6 immutable checkpoint changed")
    else:
        write(path, value)


def gzip_equal(path, value):
    if Path(path).exists():
        if gzread(path) != value:
            raise ValueError("P6 immutable gzip checkpoint changed")
    else:
        gzwrite(path, value)


def progress(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".{os.getpid()}.tmp")
    with temp.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, sort_keys=True, allow_nan=False)
        stream.write("\n")
    os.replace(temp, path)


def summary(index):
    n = sum(row["word_count"] for row in index)
    supported = sum(row["scored_count"] for row in index)
    return dict(card="P6", state=states.instrument_state(bool(index), usable=supported > 0), descriptive=True,
                sessions=len(index), writers=len({row["writer"] for row in index}),
                produced_tokens=n, scored_tokens=supported, zero_probability_tokens=n - supported,
                mean_surprisal_nats=sum(row["total_nll"] for row in index) / supported if supported else None,
                training="final contiguous user-typed spans only; recipient writer excluded in full",
                targets="completed produced word/punctuation occurrences including later revised spans",
                model="interpolated Kneser-Ney trigram; discount=.75; vocabulary count cutoff=2",
                timing_unit="logged text-delta event, not individual physical keypress")


def execute(output: Path, inputs: dict, config: dict) -> dict:
    if config:
        raise ValueError("P6 model and text policy are fixed; no configurable sample")
    output = Path(output)
    if (output / "P6_PRIMARY.json").exists():
        return verify(output, inputs, config)["primary"]
    bindings = dict(inputs={k: filehash(v) for k, v in inputs.items() if k != "repo_root"},
                    repo_root=str(Path(inputs["repo_root"]).resolve()), config=config)
    write_equal(output / "P6_RUN_BINDINGS.json", bindings)
    old_progress = read(output / "P6_PROGRESS.json") if (output / "P6_PROGRESS.json").exists() else {}
    previous_elapsed = old_progress.get("active_seconds", 0.)
    started = time.monotonic()
    def elapsed():
        return previous_elapsed + time.monotonic() - started
    def checkpoint(phase, completed, total):
        progress(output / "P6_PROGRESS.json", dict(phase=phase, completed=completed, total=total, active_seconds=elapsed()))
    def yielding(completed, total):
        if (output / "YIELD_REQUEST.json").exists():
            checkpoint("yielded", completed, total)
            return dict(status="yielded", card="P6", completed_sessions=completed, total_sessions=total,
                        reason="cooperative request at saved session boundary; remove request before resume")
        return None
    roster = {row["session"]: row for row in read(inputs["raw_roster"])}
    metadata = {row["session"]: row for row in read(inputs["prepared_sessions"])}
    sessions, training = [], defaultdict(list)
    for row, path in session_paths(inputs):
        timeline = read(path)
        raw = roster[row["session"]]
        source = (Path(inputs["repo_root"]) / raw["path"]).resolve()
        source.relative_to(Path(inputs["repo_root"]).resolve())
        if filehash(source) != raw["source_sha256"] or timeline["source_sha256"] != raw["source_sha256"]:
            raise ValueError("raw source hash mismatch")
        dest = output / "ledger" / (row["session"] + ".json.gz")
        receipt_path = output / "ledger_receipts" / (row["session"] + ".json")
        if receipt_path.exists():
            receipt = read(receipt_path)
            if receipt["sha256"] != filehash(dest) or receipt["source_sha256"] != raw["source_sha256"]:
                raise ValueError("P6 ledger checkpoint changed")
            record = gzread(dest)
        else:
            with source.open(encoding="utf-8") as stream:
                replay = replay_words([json.loads(line) for line in stream])
            if replay["final_document"] != timeline["final_document"]:
                raise ValueError("word ledger differs from authenticated P2 replay")
            meta = metadata[row["session"]]
            record = dict(session=row["session"], writer=row["writer"], prompt=timeline["prompt"],
                          timestamp=meta["timestamp"], end_at=meta["end_at"], words=replay["words"],
                          training_sequences=training_sequences(timeline))
            gzip_equal(dest, record)
            write_equal(receipt_path, dict(sha256=filehash(dest), source_sha256=raw["source_sha256"]))
        training[row["writer"]].extend(record["training_sequences"])
        sessions.append(dict(session=row["session"], writer=row["writer"], file=dest.relative_to(output).as_posix(), sha256=filehash(dest)))
        checkpoint("extraction", len(sessions), len(metadata))
        yielded = yielding(0, len(metadata))
        if yielded:
            return yielded
    if not (output / "P6_EXTRACTION_TIMING.json").exists():
        write(output / "P6_EXTRACTION_TIMING.json", dict(active_seconds=elapsed(), sessions=len(sessions)))
    extraction_seconds = read(output / "P6_EXTRACTION_TIMING.json")["active_seconds"]
    index = []
    for writer in sorted(training):
        model = None
        for row in sorted((s for s in sessions if s["writer"] == writer), key=lambda s: s["session"]):
            receipt_path = output / "score_receipts" / (row["session"] + ".json")
            if receipt_path.exists():
                receipt = read(receipt_path)
                if filehash(output / receipt["file"]) != receipt["sha256"]:
                    raise ValueError("P6 score checkpoint changed")
                index.append(receipt)
                continue
            if model is None:
                model = KneserNey([seq for donor in sorted(training) if donor != writer for seq in training[donor]])
            record = gzread(output / row["file"])
            total_nll, scored = 0., 0
            for word in record["words"]:
                probability = model.score(word["token"], word["context"])
                word["population_probability"] = probability
                word["population_surprisal"] = -math.log(probability) if probability else None
                word["population_log_frequency"] = math.log(max(model.word_counts[model.lookup(word["token"])], 1) / max(model.word_total, 1))
                if probability:
                    total_nll += word["population_surprisal"]
                    scored += 1
            dest = output / "scores" / (row["session"] + ".json.gz")
            gzip_equal(dest, record)
            receipt = dict(session=row["session"], writer=writer, file=dest.relative_to(output).as_posix(), sha256=filehash(dest),
                           word_count=len(record["words"]), scored_count=scored, total_nll=total_nll)
            write_equal(receipt_path, receipt)
            index.append(receipt)
            checkpoint("scoring", len(index), len(sessions))
            if len(index) >= math.ceil(.1 * len(sessions)) and not (output / "FIRST_TENTH.json").exists():
                total_elapsed = elapsed()
                projection = extraction_seconds + max(0, total_elapsed - extraction_seconds) * len(sessions) / len(index)
                write(output / "FIRST_TENTH.json", dict(card="P6", completed_scored_sessions=len(index), total_sessions=len(sessions),
                      active_seconds_from_first_start=total_elapsed, extraction_seconds=extraction_seconds,
                      projected_cpu_seconds=projection, forecast_cpu_seconds=3600,
                      projection_exceeds_twice_forecast=projection > 7200,
                      method="all extraction measured once plus observed complete model/scoring time per scored session"))
            yielded = yielding(len(index), len(sessions))
            if yielded:
                return yielded
    index.sort(key=lambda row: row["session"])
    result = summary(index)
    write_equal(output / "P6_INDEX.json", index)
    write_equal(output / "P6_BINDINGS.json", dict(bindings, index_sha256=filehash(output / "P6_INDEX.json")))
    write_equal(output / "P6_PRIMARY.json", result)
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output)
    binding = read(output / "P6_BINDINGS.json")
    if binding["config"] != config or binding["inputs"] != {k: filehash(v) for k, v in inputs.items() if k != "repo_root"}:
        raise ValueError("P6 input/config binding changed")
    if binding["repo_root"] != str(Path(inputs["repo_root"]).resolve()) or binding["index_sha256"] != filehash(output / "P6_INDEX.json"):
        raise ValueError("P6 root/index binding changed")
    index = read(output / "P6_INDEX.json")
    fresh = []
    for row in index:
        path = output / row["file"]
        if filehash(path) != row["sha256"]:
            raise ValueError("P6 intermediate changed")
        record = gzread(path)
        values = [-math.log(w["population_probability"]) for w in record["words"] if w["population_probability"] > 0]
        computed = dict(row, word_count=len(record["words"]), scored_count=len(values), total_nll=sum(values))
        if computed != row:
            raise ValueError("P6 saved reduction mismatch")
        fresh.append(computed)
    result = summary(fresh)
    if result != read(output / "P6_PRIMARY.json"):
        raise ValueError("P6 primary does not recompute")
    return dict(verified=True, primary=result)
