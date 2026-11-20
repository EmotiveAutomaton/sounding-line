"""LA6.s and LA6.sl on the two frozen onset windows of the original meetings.

DESIGN CHECK (LESSONS 3–5). Identical features give area 0.5. A feature
separating cases from controls must survive whole-meeting holdout. A missing
meeting cannot move another meeting to a different parent fold. Matching
support determines the length route before a score is computed. Missing act
support retains the parent's unavailable interval. Both windows and both
history arms stay in the return, including descriptive outcomes.
"""
from collections import Counter
from pathlib import Path
import time

import numpy as np
from sklearn.metrics import roc_auc_score

from . import week5_engine_export_io as seal
from . import week5_qualification_io as io
from . import week5_rr3_v1 as compare
from . import week6_la6_followups_v1 as follow
from . import week6_la6_runner_v2 as parent
from . import week6_la6_source_v1 as source
from . import week6_la6_v2 as model
from . import week6_laughter_followup_source_v1 as prepared

MODULE = "runners.drive.cards.week6_laughter_followup_fit_v1"
CARDS = ("LA6.s", "LA6.sl")
DRAWS = 2000


def fixed_folds(meetings):
    names = sorted(set(meetings))
    return {name: i % min(5, len(names)) for i, name in enumerate(names)}


def held_out(rows, folds, include_history):
    """Use the original assignment even when stricter matching loses meetings."""
    fold = np.asarray([folds[row["meeting"]] for row in rows])
    if len(set(fold)) < 2:
        raise ValueError("Held-out prediction requires two occupied parent folds")
    predictions = np.full(len(rows), np.nan)
    audit = []
    for number in sorted(set(fold)):
        train = [row for index, row in enumerate(rows) if fold[index] != number]
        indices = np.flatnonzero(fold == number)
        test = [rows[index] for index in indices]
        fit, template = model.fitted(train, include_history)
        matrix, _ = model.encoding(test, include_history, template)
        predictions[indices] = fit.decision_function(matrix)
        audit.append({"fold": int(number), "training_meetings": sorted({r["meeting"] for r in train}),
                      "test_meetings": sorted({r["meeting"] for r in test})})
    return float(roc_auc_score([row["label"] for row in rows], predictions)), predictions, audit


def point(rows, folds):
    result = {}
    for include in (True, False):
        area, scores, audit = held_out(rows, folds, include)
        fit, template = model.fitted(rows, include)
        result[str(include)] = dict(auc=area, predictions=scores.tolist(), folds=audit,
                                    categories=template[0], coefficients=fit.coef_[0][9 if include else 8:].tolist())
    return result


def samples(blocks, card):
    if card not in CARDS:
        raise ValueError("Unknown follow-up")
    series, audit = {}, {}
    for seconds in prepared.WINDOWS:
        total = Counter()
        for block in blocks:
            window = block["windows"][str(seconds)]
            total["utterances"] += block["source_utterances"]
            total["excluded_preexisting"] += window["excluded_preexisting"]
            for name in ("strict", "length_held"):
                pair = window[name]
                counts = pair["audit"]
                if (counts["matched"] != len(pair["pairs"]) or
                        counts["cases"] != counts["matched"] + len(counts["unsupported"])):
                    raise ValueError("Prepared case dispositions do not reconcile")
                for field in ("cases", "matched", "unique_controls", "reused_control_copies"):
                    total[name + "_" + field] += counts[field]
                total[name + "_unmatched"] += len(counts["unsupported"])
        route = follow.retained_route(total["strict_matched"], total["length_held_matched"])
        audit[str(seconds)] = dict(total, length_route=route)
        matched = card == "LA6.sl" and route == "matched"
        variant = "length_held" if matched else "strict"
        rows = [row for block in blocks for row in prepared.rows_for_window(block, seconds, variant)]
        series[f"{seconds}s_{variant}"] = rows
        if card == "LA6.sl" and route == "covariate":
            series[f"{seconds}s_strict_without_length"] = follow.omit_length(rows)
    return series, audit


def load(inputs):
    if set(inputs) != {"prepared_run", "prepared_complete_sha256"}:
        raise ValueError("An exact prepared run and terminal hash are required")
    directory = Path(inputs["prepared_run"])
    if io.sha(directory / "COMPLETE.json") != inputs["prepared_complete_sha256"]:
        raise ValueError("Registered meeting-source completion differs")
    path, plan, _ = seal.complete(directory, prepared.MODULE)
    summary = seal.read(path / "output/RESULT.json")
    manifest = path / "output/STATE.json"
    if not summary["complete_preparation"] or io.sha(manifest) != summary["manifest_sha256"]:
        raise ValueError("Incomplete strict-window source")
    blocks = []
    for record in seal.read(manifest)["parts"]:
        part = path / "output" / record["relative"]
        part.resolve().relative_to((path / "output").resolve())
        if io.sha(part) != record["sha256"]:
            raise ValueError("Prepared meeting differs")
        block = seal.read(part)
        if block["meeting"] != record["meeting"] or block["binding"] != summary["binding"]:
            raise ValueError("Meeting identity or preparation differs")
        blocks.append(block)
    original = Path(plan["inputs"]["original_preparation"])
    if io.sha(original / "COMPLETE.json") != plan["inputs"]["original_preparation_sha256"]:
        raise ValueError("Parent preparation differs")
    original_result = seal.read(original / "COMPLETE.json")
    table_path = original / "output/TABLE.json"
    if io.sha(table_path) != original_result["outputs"]["output/TABLE.json"]:
        raise ValueError("Parent meeting assignments have lost their original table")
    parent_rows = seal.read(table_path)["rows"]
    folds = fixed_folds(row["meeting"] for row in parent_rows)
    return blocks, folds, {"source_complete": inputs["prepared_complete_sha256"], "manifest": summary["manifest_sha256"],
                           "parent_table": original_result["outputs"]["output/TABLE.json"], "parent_folds": source.digest(folds)}


def stored(path):
    if io.sha(path) != seal.read(path.with_suffix(".seal.json"))["sha256"]:
        raise ValueError("Meeting checkpoint bytes differ")
    return seal.read(path)


def pooled(rows):
    result = {}
    if rows:
        for include in (True, False):
            fitted, template = model.fitted(rows, include)
            result[str(include)] = {"reference_act": template[0][0],
                                    "act_coefficients": fitted.coef_[0][9 if include else 8:].tolist()}
    return result


def operation(output, inputs, config):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if config.get("phase") not in CARDS or config.get("draws") != DRAWS:
        raise ValueError("A registered strict-window card and all 2,000 draws are required")
    limit, seconds = parent.settings(dict(config, phase="LA6"))
    start = time.monotonic()
    card = config["phase"]
    blocks, folds, identity = load(inputs)
    series, audit = samples(blocks, card)
    binding = source.digest(dict(identity, card=card, runner=io.sha(__file__), parent=io.sha(parent.__file__)))
    state_path = output / "STATE.json"
    state = seal.state(state_path, binding, {"completed": 0})
    active, descriptions = {}, {}
    for name, rows in series.items():
        meetings = {row["meeting"] for row in rows}
        if not meetings.issubset(folds):
            raise ValueError("Strict sample contains a meeting outside the parent's fold assignment")
        if len({folds[m] for m in meetings}) < 2:
            descriptions[name] = dict(status="below floor, descriptive", meetings=len(meetings),
                                      reason="fewer than two occupied original folds", pooled_descriptive=pooled(rows))
            continue
        path = output / (name + "_point.json")
        if not path.exists():
            seal.checkpoint(path, dict(binding=binding, value=point(rows, folds)))
        saved = stored(path)
        if saved["binding"] != binding:
            raise ValueError("Stored fold predictions have a different identity")
        active[name] = (rows, saved["value"], len(meetings))
    target = DRAWS if active else 0
    cursor = state["completed"]
    if type(cursor) is not int or not 0 <= cursor <= target:
        raise ValueError("Invalid draw cursor")
    bank = []
    for index in range(target):
        path = output / "draws" / f"{index:04d}.json"
        if index >= cursor:
            if index - cursor >= limit or source.requested(output, start, seconds):
                return {"status": "yielded", "verified": False, "completed": index, "total": target}
            values = {name: parent.one_draw(rows, baseline, index) for name, (rows, baseline, _) in active.items()}
            record = dict(index=index, binding=binding, series=values)
            if path.exists() and path.with_suffix(".seal.json").exists():
                compare.compare_record(stored(path), record)
            else:
                seal.checkpoint(path, record)
            seal.checkpoint(state_path, dict(binding=binding, completed=index + 1))
        record = stored(path)
        if record["index"] != index or record["binding"] != binding or set(record["series"]) != set(active):
            raise ValueError("Draw ordinal, series or source differs")
        bank.append(record["series"])
    result = dict(card=card, complete_computation=True, draws=target, source_identity=identity, audit=audit,
                  record_kind="claim", theory_tags=["H18-S5"], by_construction=False, activation=[], series=descriptions)
    for name, (_, baseline, n) in active.items():
        result["series"][name] = dict(meetings=n, arms=parent.summarize(baseline, [row[name] for row in bank], n))
    io.write_json(output / "RESULT.json", result)
    return result


def execute(output, inputs, config):
    return operation(output, inputs, config)


def verify(output, inputs, config):
    output = Path(output)
    replay = output / "independent-replay"
    result = operation(replay, inputs, config)
    if result.get("status") == "yielded":
        return result
    compare.compare_record(seal.read(output / "RESULT.json"), result)
    for index in range(result["draws"]):
        name = Path("draws") / f"{index:04d}.json"
        compare.compare_record(stored(output / name), stored(replay / name))
    for path in output.glob("*_point.json"):
        compare.compare_record(stored(path), stored(replay / path.name))
    return dict(verified=True, matched_windows_replayed=True, all_draws_replayed=True,
                registered_history_arms_replayed=True)
