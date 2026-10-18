"""D3 menu-latency reversal and D23 prompt-familiarity request contrasts.

Both use observed menu events, independently of TC pause admission. Session
word counts exclude prompt-origin text and include typed and accepted text.

DESIGN CHECK: LESSONS 3-5, October 18. Null equal outcomes produce zero;
planted fast reversal or first-prompt request excess is positive, reversed
plants negative. Outcome shuffles can fail these readings. Percentile intervals
and states_v2 partition signs; unsupported/ambiguous chronology is disclosed,
never substituted by a different contrast. Every fresh verification rebuilds
rows from completed P2 sources and authenticated metadata, not saved rows alone.
"""
from __future__ import annotations

import json
import math
import time
import hashlib
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

from runners.drive.cards import states_v2 as states
from runners.drive.cards.timing_census import read, write, filehash, session_paths
from runners.drive.cards.timing_text import WORD, TOKEN
from runners.drive.cards.timing_stats import regression, bind, check_binding
from runners.stage9.coauthor import units, text_of, delta_ops, apply_delta
from runners.stage14.common import atomic, freeze

FORECAST_SECONDS = 600


def accepted_lifetimes(events, expected_final=None):
    if not events or events[0]["eventName"] != "system-initialize":
        raise ValueError("D3 initialization required")
    doc = units(events[0]["currentDoc"])
    owners = [None] * len(doc)
    current, pending = None, None
    original, deleted, inserted = Counter(), defaultdict(set), Counter()
    for ordinal, event in enumerate(events):
        if event["eventName"] == "suggestion-open":
            current = ordinal
        if event["eventName"] == "suggestion-select":
            pending = current
        ops = delta_ops(event.get("textDelta"))
        if not ops:
            continue
        is_user = event.get("eventSource") == "user"
        position, next_owners = 0, []
        for op in ops:
            if "delete" in op:
                if is_user:
                    for identity in owners[position:position + op["delete"]]:
                        if identity is not None and identity[1] is not None:
                            deleted[identity[0]].add(identity[1])
                position += op["delete"]
            elif "retain" in op:
                next_owners.extend(owners[position:position + op["retain"]])
                position += op["retain"]
            else:
                inside = is_user and 0 < position < len(doc) and owners[position - 1] is not None and owners[position] is not None and owners[position - 1][0] == owners[position][0]
                if inside:
                    inserted[owners[position][0]] += len(units(op["insert"]))
                next_owners.extend([(owners[position][0], None) if inside else None] * len(units(op["insert"])))
        next_owners.extend(owners[position:])
        before, old_owners = text_of(doc), owners
        doc, owners, _ = apply_delta(doc, owners, event.get("textDelta"), insertion_owner=None)
        owners = next_owners
        if not is_user and pending is not None:
            after = text_of(doc)
            if not before.endswith("\n") or not after.startswith(before[:-1]) or not after.endswith("\n"):
                raise ValueError("accepted insertion is not canonical append")
            extra = len(doc) - len(old_owners)
            if extra <= 0 or original[pending]:
                raise ValueError("empty/repeated accepted span")
            original[pending] = extra
            owners = old_owners[:-1] + [(pending, i) for i in range(extra)] + old_owners[-1:]
            pending = None
    surviving = Counter(identity[0] for identity in owners if identity is not None and identity[1] is not None)
    if expected_final is not None and text_of(doc) != expected_final:
        raise ValueError("D3 final document differs from authenticated P2 replay")
    return {ordinal: dict(original_utf16=n, surviving_utf16=surviving[ordinal], deleted_original_utf16=len(deleted[ordinal]),
                          inserted_inside_utf16=inserted[ordinal],
                          reversed=surviving[ordinal] == 0 or len(deleted[ordinal]) + inserted[ordinal] >= n / 2)
            for ordinal, n in original.items()}


def session_words(timeline):
    text, source = "", []
    for span in timeline["final_spans"]:
        text += span["text"]
        source.extend([span["origin"] != "prompt"] * len(span["text"]))
    return sum(bool(WORD.fullmatch(m.group())) and all(source[m.start():m.end()]) for m in TOKEN.finditer(text))


def mean_contrast(values, config):
    values = np.array(values, float)
    if len(values) < 3 or not np.isfinite(values).all():
        return dict(state="invalid", reason="fewer than three independent supported writers")
    rng = np.random.default_rng(config["seed"])
    samples = np.array([values[rng.integers(0, len(values), len(values))].mean() for _ in range(config["bootstrap_draws"])])
    effect = float(values.mean())
    low, high = np.quantile(samples, [.025, .975]).tolist()
    se = float(samples.std(ddof=1))
    z = effect / se if se > 0 else None
    return dict(effect=effect, ci_low=low, ci_high=high, bootstrap_se=se, z=z,
                wald_p_two_sided=math.erfc(abs(z) / math.sqrt(2)) if z is not None else None,
                p_reference="descriptive two-sided normal Wald; state remains percentile-CI based",
                writers=len(values), state=states.contrast_state(effect, low, high),
                bootstrap_draws=config["bootstrap_draws"], seed=config["seed"])


def d3(rows, config):
    by_writer = defaultdict(list)
    for row in rows:
        by_writer[row["writer"]].append(row)
    differences, null_differences, quintiles = [], [], []
    rng = np.random.default_rng(config["seed"])
    target = 4 if config["extension"] else 0
    for writer in sorted(by_writer):
        observations = sorted(by_writer[writer], key=lambda r: (r["session"], r["ordinal"]))
        latencies = np.array([row["latency"] for row in observations])
        # Ties share a quintile; arbitrary IDs cannot split identical latencies.
        groups = np.minimum(4, np.floor(5 * (rankdata(latencies, method="average") - .5) / len(latencies)).astype(int))
        outcome = np.array([row["reversed"] for row in observations], float)
        if not np.any(groups == target) or not np.any(groups == 2):
            continue
        differences.append(float(outcome[groups == target].mean() - outcome[groups == 2].mean()))
        shuffled = rng.permutation(outcome)
        null_differences.append(float(shuffled[groups == target].mean() - shuffled[groups == 2].mean()))
        quintiles.append(dict(writer=writer, counts=[int(sum(groups == q)) for q in range(5)],
                              reversal_rates=[float(outcome[groups == q].mean()) if np.any(groups == q) else None for q in range(5)]))
    result = mean_contrast(differences, config)
    result.update(card="D3", descriptive=True, extension=config["extension"],
                  contrast=("longest" if config["extension"] else "shortest") + " minus middle within-writer latency quintile reversal rate",
                  outcome="all original accepted units deleted, or original units deleted plus units inserted inside span >= half original UTF-16 length",
                  controls=dict(within_writer_reversal_shuffle=mean_contrast(null_differences, config)),
                  route="Short-latency excess supports the flow account; long-latency excess supports the near-tie account; both support a U shape, descriptively.")
    return result, quintiles


def d23(rows, config):
    by_writer = defaultdict(list)
    for row in rows:
        by_writer[row["writer"]].append(row)
    differences, null_differences, eligible = [], [], []
    rng = np.random.default_rng(config["seed"])
    excluded_tied_chronology = []
    for writer in sorted(by_writer):
        records = sorted(by_writer[writer], key=lambda r: (r["timestamp"], r["session"]))
        if len({r["timestamp"] for r in records}) != len(records):
            excluded_tied_chronology.append(writer)
            continue
        seen = set()
        retained = []
        for order, row in enumerate(records):
            first = row["prompt"] not in seen
            seen.add(row["prompt"])
            if row["words"] > 0:
                retained.append(dict(row, first=first, order=order, request_rate=100 * row["requests"] / row["words"]))
        prompt_differences, prompt_null = [], []
        for prompt in sorted({r["prompt"] for r in retained}):
            same_prompt = [r for r in retained if r["prompt"] == prompt]
            initial = [r["request_rate"] for r in same_prompt if r["first"]]
            repeated = [r["request_rate"] for r in same_prompt if not r["first"]]
            if initial and repeated:
                prompt_differences.append(float(np.mean(initial) - np.mean(repeated)))
                outcomes = rng.permutation([r["request_rate"] for r in same_prompt])
                prompt_null.append(float(np.mean([v for v, r in zip(outcomes, same_prompt) if r["first"]]) - np.mean([v for v, r in zip(outcomes, same_prompt) if not r["first"]])))
        if prompt_differences:
            differences.append(float(np.mean(prompt_differences)))
            null_differences.append(float(np.mean(prompt_null)))
        if len(retained) >= 2:
            eligible.extend(retained)
    if config["extension"]:
        if eligible:
            x, y, writers = [[-r["order"], int(r["first"])] for r in eligible], [r["request_rate"] for r in eligible], [r["writer"] for r in eligible]
            kwargs = dict(within=True, draws=config["bootstrap_draws"], seed=config["seed"])
            result = regression(x, y, writers, **kwargs)
            shuffled = np.array(y, float)
            for writer in sorted(set(writers)):
                ix = np.flatnonzero(np.array(writers) == writer)
                shuffled[ix] = rng.permutation(shuffled[ix])
            control = regression(x, shuffled, writers, **kwargs)
        else:
            result = dict(state="invalid", reason="no sessions support the chronological extension")
            control = dict(result)
    else:
        result = mean_contrast(differences, config)
        control = mean_contrast(null_differences, config)
    result.update(card="D23", descriptive=True, extension=config["extension"],
                  contrast="decline per chronological session controlling prompt novelty" if config["extension"] else "first-session minus repeat-session requests per 100 final nonprompt words, paired within prompt then averaged within writer",
                  controls=dict(within_writer_request_shuffle=control),
                  session_denominator="all final nonprompt words, including typed and accepted text; zero-word sessions disclosed and excluded",
                  excluded_zero_word_sessions=sum(r["words"] == 0 for r in rows),
                  excluded_writers_tied_session_times=len(excluded_tied_chronology),
                  route="A decline is compatible with familiarity reducing exploration; it does not identify uncertainty reduction or play as the cause.")
    return result, eligible


def validate_config(config):
    if set(config) != {"card", "extension", "bootstrap_draws", "seed"} or config.get("card") not in {"D3", "D23"} or type(config.get("extension")) is not bool or type(config.get("bootstrap_draws")) is not int or config["bootstrap_draws"] != 2000 or type(config.get("seed")) is not int or config["seed"] != 20261017:
        raise ValueError("frozen event-card configuration required")


def source_sessions(inputs, side_input):
    """Authenticate metadata through the exact foundation plan/complete chain."""
    root = Path(inputs["repo_root"]).resolve()
    complete, plan = read(inputs["foundation_complete"]), read(inputs["foundation_plan"])
    if complete.get("status") != "COMPLETE" or complete.get("plan_sha256") != filehash(inputs["foundation_plan"]):
        raise ValueError("foundation plan is not authenticated by completion")
    side = Path(inputs[side_input]).resolve()
    relative = side.relative_to(root).as_posix()
    if plan["pins"].get(relative) != filehash(side):
        raise ValueError("foundation metadata source changed")
    items = read(side)
    metadata = {row["session"]: row for row in items}
    if len(metadata) != len(items):
        raise ValueError("duplicate metadata session")
    for row, path in session_paths(inputs):
        timeline, meta = read(path), metadata[row["session"]]
        if (timeline["session"], timeline["writer"]) != (row["session"], row["writer"]):
            raise ValueError("P2 session/writer identity mismatch")
        if "writer" in meta and meta["writer"] != row["writer"]:
            raise ValueError("metadata writer identity mismatch")
        if "prompt" in meta and meta["prompt"] != timeline["prompt"]:
            raise ValueError("metadata prompt identity mismatch")
        if side_input == "prepared_sessions" and (isinstance(meta["timestamp"], bool) or not math.isfinite(float(meta["timestamp"]))):
            raise ValueError("invalid metadata timestamp")
        if "source_sha256" in meta and meta["source_sha256"] != timeline["source_sha256"]:
            raise ValueError("raw/P2 source identity mismatch")
        if side_input == "raw_roster":
            raw = (root / meta["path"]).resolve()
            raw.relative_to(root)
            if filehash(raw) != meta["source_sha256"]:
                raise ValueError("raw source changed")
        if "".join(span["text"] for span in timeline["final_spans"]) != timeline["final_document"]:
            raise ValueError("P2 final spans do not reconstruct final document")
        yield row, timeline, meta


def session_rows(inputs, card, row, timeline, source_meta):
    rows = []
    if card == "D3":
        source = (Path(inputs["repo_root"]) / source_meta["path"]).resolve()
        with source.open(encoding="utf-8") as stream:
            spans = accepted_lifetimes([json.loads(line) for line in stream], timeline["final_document"])
        for decision in timeline["decisions"]:
            if decision["handling"] not in {"accept", "edit"}:
                continue
            if decision["latency_kind"] != "observed_selection_or_close" or decision["ordinal"] not in spans:
                raise ValueError("accepted decision lacks observed latency/span")
            if not math.isfinite(decision["latency_seconds"]) or decision["latency_seconds"] < 0:
                raise ValueError("invalid observed decision latency")
            rows.append(dict(session=row["session"], writer=row["writer"], ordinal=decision["ordinal"],
                             latency=decision["latency_seconds"], **spans[decision["ordinal"]]))
    else:
        counts = timeline["event_counts"]
        if any(type(counts.get(key, 0)) is not int or counts.get(key, 0) < 0 for key in ("suggestion-get", "suggestion-open")):
            raise ValueError("invalid request/menu event counts")
        rows.append(dict(session=row["session"], writer=row["writer"], prompt=timeline["prompt"],
                         timestamp=source_meta["timestamp"], words=session_words(timeline),
                         requests=counts.get("suggestion-get", 0), shown_menus=counts.get("suggestion-open", 0),
                         hovers=sum(sum("hover" in i["event"] for i in d["interactions"]) for d in timeline["decisions"])))
    return rows


class CooperativeYield(Exception):
    pass


def extract_rows(inputs, card, output=None, elapsed=None):
    side_input = "raw_roster" if card == "D3" else "prepared_sessions"
    expected_inputs = {"session_index", "foundation_complete", "foundation_plan", "repo_root", side_input}
    if set(inputs) != expected_inputs:
        raise ValueError("exact event-card input set required")
    rows, total = [], len(read(inputs["session_index"]))
    for done, (row, timeline, source_meta) in enumerate(source_sessions(inputs, side_input), 1):
        if output is not None:
            checkpoint = output / "sessions" / (hashlib.sha256(row["session"].encode()).hexdigest() + ".json")
            if checkpoint.exists():
                if read(checkpoint.with_suffix(".receipt.json"))["sha256"] != filehash(checkpoint):
                    raise ValueError("event session checkpoint changed")
                saved = read(checkpoint)
                if saved["source_sha256"] != row["sha256"] or saved["session"] != row["session"]:
                    raise ValueError("event session checkpoint source changed")
                unit = saved["rows"]
            else:
                unit = session_rows(inputs, card, row, timeline, source_meta)
                write(checkpoint, dict(session=row["session"], source_sha256=row["sha256"], rows=unit))
                write(checkpoint.with_suffix(".receipt.json"), dict(sha256=filehash(checkpoint)))
        else:
            unit = session_rows(inputs, card, row, timeline, source_meta)
        rows.extend(unit)
        if output is not None:
            active = elapsed()
            atomic(output / "EVENT_PROGRESS.json", dict(completed_sessions=done, total_sessions=total, active_seconds=active))
            overshoot = False
            if done == math.ceil(total / 10) and not (output / "FIRST_TENTH.json").exists():
                # Includes a second source pass at verification and a fixed 30s
                # budget for both small sufficient-statistic/bootstrap passes.
                projection = 2 * active * total / done + 30
                overshoot = projection > 2 * FORECAST_SECONDS
                write(output / "FIRST_TENTH.json", dict(completed_sessions=done, total_sessions=total, elapsed_seconds=active,
                      projected_cpu_seconds=projection, forecast_cpu_seconds=FORECAST_SECONDS, forecast_overshoot=overshoot,
                      includes_fresh_source_verification=True, reserved_statistics_seconds=30))
            if active > 3 * FORECAST_SECONDS:
                raise RuntimeError("event-card threefold active-time ceiling")
            if overshoot or (output / "YIELD_REQUEST.json").exists():
                raise CooperativeYield("saved authenticated session checkpoint")
    return rows


def execute(output: Path, inputs: dict, config: dict) -> dict:
    validate_config(config)
    if (Path(output) / "TIMING_BINDINGS.json").exists():
        return verify(output, inputs, config)["primary"]
    output = Path(output)
    freeze(output / "EVENT_RUN_BINDINGS.json", dict(config=config, source_sha256=filehash(__file__),
           inputs={key: str(Path(value).resolve()) if Path(value).is_dir() else filehash(value) for key, value in inputs.items()}))
    prior = read(output / "EVENT_PROGRESS.json")["active_seconds"] if (output / "EVENT_PROGRESS.json").exists() else 0.
    started = time.monotonic()
    elapsed = lambda: prior + time.monotonic() - started
    try:
        rows = extract_rows(inputs, config["card"], output, elapsed)
    except CooperativeYield as exc:
        return dict(status="yielded", card=config["card"], reason=str(exc))
    result, details = d3(rows, config) if config["card"] == "D3" else d23(rows, config)
    if elapsed() > 3 * FORECAST_SECONDS:
        raise RuntimeError("event-card threefold active-time ceiling")
    write(Path(output) / "EVENT_ROWS.json", rows)
    write(Path(output) / "EVENT_DETAILS.json", details)
    write(Path(output) / "EVENT_PRIMARY.json", result)
    write(Path(output) / "EVENT_TIMING.json", dict(wall_seconds=elapsed(), forecast_cpu_seconds=FORECAST_SECONDS))
    bind(output, inputs, config, ["EVENT_ROWS.json", "EVENT_DETAILS.json", "EVENT_PRIMARY.json"])
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    validate_config(config)
    check_binding(output, inputs, config)
    rows = read(Path(output) / "EVENT_ROWS.json")
    if rows != extract_rows(inputs, config["card"]):
        raise ValueError("event rows do not reconstruct from authenticated sources")
    result, details = d3(rows, config) if config["card"] == "D3" else d23(rows, config)
    if result != read(Path(output) / "EVENT_PRIMARY.json") or details != read(Path(output) / "EVENT_DETAILS.json"):
        raise ValueError("event-card primary does not recompute")
    return dict(verified=True, primary=result)
