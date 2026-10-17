"""D30: prompt-conditioned pervasiveness versus local writer markers.

The frozen primary is local minus pervasive log pause, adjusted within writer.
D30.v1 instead uses pervasive minus local revision, expected direction negative.
No direction-normalized number replaces the signed raw contrast.

DESIGN CHECK: LESSONS 3-5 reread 2026-10-17. NULL: within-writer marker
labels unrelated to timing give zero adjusted contrast. ALTERNATIVE: local
slowing gives a positive signed primary; the opposite direction stays negative.
Zero prompt frequency has no finite log-odds evidence, but remains in local
rate coverage. Insufficient support/undefined fits are invalid, not null.
Marker labels shuffle once per writer-marker, never per occurrence. Source
completion, receipt integrity and saved-boundary yield are fail-closed.
"""
from __future__ import annotations

import math
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from runners.drive.cards import states_v2 as states
from runners.drive.cards.timing_census import read, write, filehash
from runners.drive.cards.timing_p6 import gzread, gzwrite, write_equal, gzip_equal
from runners.drive.cards.timing_stats import bind, check_binding
from runners.drive.cards.timing_checkpoint import regression


FUNCTION_WORDS = frozenset("a an the and or but if as of to in on at by for with from into over under is are was were be been being do does did have has had can could shall should will would may might must this that these those i me my mine we us our ours you your yours he him his she her hers it its they them their theirs not no nor so than then when where why how all any each every some such both either neither who whom whose which what there here".split())


def occurrences(records, function_only=False):
    out = []
    for session in records:
        words = session["words"]
        for word in words:
            marker = ("word:" if word["is_word"] else "punct:") + word["token"]
            if not function_only or not word["is_word"] or word["token"] in FUNCTION_WORDS:
                out.append(dict(word, writer=session["writer"], prompt=session["prompt"], session=session["session"], session_timestamp=session.get("timestamp", session["session"]), marker=marker))
            previous = word.get("previous_typed_token_index")
            if previous is not None and word["is_word"] and words[previous]["is_word"]:
                first = words[previous]
                if function_only and not {first["token"], word["token"]} <= FUNCTION_WORDS:
                    continue
                bigram = dict(first, writer=session["writer"], prompt=session["prompt"], session=session["session"],
                              session_timestamp=session.get("timestamp", session["session"]),
                              marker="bigram:" + first["token"] + " " + word["token"],
                              length=first["length"] + 1 + word["length"], revised=first["revised"] or word["revised"])
                if "population_surprisal" in first and "population_surprisal" in word:
                    pair = [first["population_surprisal"], word["population_surprisal"]]
                    bigram["population_surprisal"] = sum(pair) if all(v is not None for v in pair) else None
                if "seconds" in first and "seconds" in word:
                    bigram["duration_seconds"] = word["seconds"] + word["duration_seconds"] - first["seconds"]
                out.append(bigram)
    # A bigram's frequency must not silently inherit its first word's frequency.
    # Use the same floor-one convention as P6, over other writers' observed
    # typed bigram occurrences. This nuisance is separate from label formation.
    pairs = [r for r in out if r["marker"].startswith("bigram:")]
    counts = Counter(r["marker"] for r in pairs)
    own = Counter((r["writer"], r["marker"]) for r in pairs)
    totals = Counter(r["writer"] for r in pairs)
    for row in pairs:
        row["population_log_frequency"] = math.log(max(counts[row["marker"]] - own[row["writer"], row["marker"]], 1)
                                                   / max(len(pairs) - totals[row["writer"]], 1))
    return out


def classify_markers(rows):
    counts, totals, overall = Counter(), Counter(), Counter()
    prompts = defaultdict(set)
    for row in rows:
        w, p, marker = row["writer"], row["prompt"], row["marker"]
        kind = marker.split(":", 1)[0]
        counts[(w, p, marker)] += 1
        totals[(w, p, kind)] += 1
        overall[marker] += 1
        prompts[w].add(p)
    population = Counter()
    population_total = Counter()
    for (w, p, marker), n in counts.items():
        population[(p, marker)] += n
    for (w, p, kind), n in totals.items():
        population_total[(p, kind)] += n
    prior_total = Counter()
    for marker, n in overall.items():
        prior_total[marker.split(":", 1)[0]] += n
    by_writer = defaultdict(set)
    for w, _, marker in counts:
        by_writer[w].add(marker)
    labels, evidence = {}, []
    for writer in sorted(by_writer):
        if len(prompts[writer]) < 3:
            continue
        for marker in sorted(by_writer[writer]):
            kind = marker.split(":", 1)[0]
            own_count = sum(counts[(writer, p, marker)] for p in prompts[writer])
            if own_count < 5:
                continue
            over, rates = [], {}
            for prompt in sorted(prompts[writer]):
                a, n = counts[(writer, prompt, marker)], totals[(writer, prompt, kind)]
                b = population[(prompt, marker)] - a
                m = population_total[(prompt, kind)] - n
                # The informative prior is prompt-specific too. A pooled-across-
                # prompt prior would shrink the smaller writer sample further
                # than its larger donor baseline and invent overuse even when
                # their empirical prompt rates are identical.
                alpha = 1000 * population[(prompt, marker)] / population_total[(prompt, kind)] if population_total[(prompt, kind)] else 0
                if n <= 0 or m <= 0:
                    continue
                rates[prompt] = (a / n, b / m)
                if not 0 < alpha < 1000:
                    continue
                difference = math.log((a + alpha) / (n + 1000 - a - alpha)) - math.log((b + alpha) / (m + 1000 - b - alpha))
                z = difference / math.sqrt(1 / (a + alpha) + 1 / (b + alpha))
                if z >= 1.96:
                    over.append(prompt)
            label = None
            if len(over) >= 3:
                label = "pervasive"
            elif len(over) == 1 and len(rates) == len(prompts[writer]):
                target = over[0]
                others = [p for p in prompts[writer] if p != target]
                donor_target = rates[target][1]
                donor_n = sum(population_total[(p, kind)] - totals[(writer, p, kind)] for p in others)
                donor_count = sum(population[(p, marker)] - counts[(writer, p, marker)] for p in others)
                if all(rates[p][0] <= rates[p][1] for p in others) and donor_n and donor_target <= donor_count / donor_n:
                    label = "local"
            if label:
                labels[(writer, marker)] = dict(label=label, own_count=own_count, overused_prompts=over)
                evidence.append(dict(writer=writer, marker=marker, **labels[(writer, marker)]))
    return labels, evidence


def shuffle_marker_labels(eligible, rng):
    """Preserve each marker's repeated-occurrence membership under the null."""
    by_writer = defaultdict(dict)
    for row in eligible:
        prior = by_writer[row["writer"]].setdefault(row["marker"], row["label"])
        if prior != row["label"]:
            raise ValueError("writer-marker label changed across occurrences")
    shuffled = {}
    for writer in sorted(by_writer):
        markers = sorted(by_writer[writer])
        values = rng.permutation([by_writer[writer][m] for m in markers]).tolist()
        shuffled.update({(writer, marker): label for marker, label in zip(markers, values)})
    return [shuffled[row["writer"], row["marker"]] for row in eligible]


def analyze(rows, config, timing_mode, controls=True, on_tenth=None, checkpoint_dir=None, phase="primary"):
    if config["card"] == "D30.v2" and timing_mode == "invalid":
        return dict(card="D30.v2", state="blocked", reason="TC invalidates the function-word pause contrast"), []
    revision = config["card"] == "D30.v1" or (config["card"] == "D30" and timing_mode == "invalid")
    labels, marker_evidence = classify_markers(rows)
    eligible = []
    for row in rows:
        label = labels.get((row["writer"], row["marker"]))
        if label is None:
            continue
        if not revision and (row["pause_seconds"] is None or row["pause_seconds"] <= 0 or row["population_surprisal"] is None):
            continue
        if not revision and timing_mode == "per_character" and row["first_delta_characters"] != 1:
            continue
        eligible.append(dict(row, **label))
    supported = {w for w in {r["writer"] for r in eligible} if {r["label"] for r in eligible if r["writer"] == w} == {"local", "pervasive"}}
    eligible = [r for r in eligible if r["writer"] in supported]
    if len(supported) < 3:
        return dict(card=config["card"], state="invalid", reason="fewer than three writers with both marker classes",
                    effective_card="D30.v1" if revision else config["card"], eligible_occurrences=len(eligible)), marker_evidence
    x, y, writers = [], [], []
    for r in eligible:
        nuisance = [] if revision else [r["length"], r["population_log_frequency"], int(r["sentence_start"]), int(r["after_punctuation"]), r["population_surprisal"]]
        if config.get("extension"):
            nuisance.append(r["own_count"])
        x.append([int(r["label"] == ("pervasive" if revision else "local"))] + nuisance)
        y.append(float(r["revised"]) if revision else math.log(r["pause_seconds"]))
        writers.append(r["writer"])
    def compute(design, name, callback=None):
        return regression(design, y, writers, within=True, draws=config["bootstrap_draws"], seed=config["seed"],
                          direction=-1 if revision else 1, on_tenth=callback,
                          checkpoint=Path(checkpoint_dir) / name if checkpoint_dir is not None else None,
                          yield_requested=(lambda: (Path(checkpoint_dir) / "YIELD_REQUEST.json").exists()) if checkpoint_dir is not None else None)
    result = compute(x, phase, on_tenth)
    if result.get("status") == "yielded":
        return dict(result, phase=phase), marker_evidence
    rng = np.random.default_rng(config["seed"])
    shuffled = np.array(x, float)
    shuffled[:, 0] = [int(label == ("pervasive" if revision else "local")) for label in shuffle_marker_labels(eligible, rng)]
    control = compute(shuffled, "label-shuffle") if controls else None
    if control is not None and control.get("status") == "yielded":
        return dict(control, phase="label-shuffle"), marker_evidence
    writer_control = None
    if controls:
        sessions = sorted({r["session"] for r in rows})
        owner = {r["session"]: r["writer"] for r in rows}
        permutation = rng.permutation([owner[s] for s in sessions])
        permuted = dict(zip(sessions, permutation.tolist()))
        writer_control = analyze([dict(r, writer=permuted[r["session"]]) for r in rows], config, timing_mode, controls=False,
                                 checkpoint_dir=checkpoint_dir, phase="writer-shuffle")[0]
        if writer_control.get("status") == "yielded":
            return writer_control, marker_evidence
    within, onset = defaultdict(list), defaultdict(list)
    for r in rows:
        if r["marker"].startswith("word:"):
            within[r["writer"]].extend(t for t in r["within_intervals"] if t > 0)
            if r["pause_seconds"] is not None and r["pause_seconds"] > 0:
                onset[r["writer"]].append(r["pause_seconds"])
    timing_differences = [float(np.mean(onset[w]) - np.mean(within[w])) for w in sorted(within) if within[w] and onset[w]]
    repetition = defaultdict(list)
    for r in eligible:
        if r["label"] == "pervasive" and r["pause_seconds"] is not None and r["pause_seconds"] > 0:
            repetition[(r["writer"], r["marker"])].append(r)
    repetition_differences = []
    for key in sorted(repetition):
        ordered = sorted(repetition[key], key=lambda r: (r.get("session_timestamp", r["session"]), r["session"], r["ordinal"], r["index"]))
        if len(ordered) > 1:
            repetition_differences.append(math.log(ordered[0]["pause_seconds"]) - float(np.mean([math.log(r["pause_seconds"]) for r in ordered[1:]])))
    result.update(card=config["card"], effective_card="D30.v1" if revision else config["card"], descriptive=True,
                  raw_contrast="pervasive minus local revision rate" if revision else "local minus pervasive log pause",
                  extension=bool(config.get("extension")), timing_mode=timing_mode,
                  controls=dict(label_shuffle=control, writer_shuffle=writer_control,
                                timing_positive_control=dict(contrast="word-onset minus within-word interval seconds",
                                                             writer_mean_difference=float(np.mean(timing_differences)) if timing_differences else None,
                                                             supported_writers=len(timing_differences))),
                  secondary=dict(pervasive_revision_rate=float(np.mean([r["revised"] for r in eligible if r["label"] == "pervasive"])),
                                 local_revision_rate=float(np.mean([r["revised"] for r in eligible if r["label"] == "local"])),
                                 first_minus_later_log_pause=float(np.mean(repetition_differences)) if repetition_differences else None,
                                 repeated_writer_markers=len(repetition_differences),
                                 typing_rate_characters_per_second={label: float(np.mean([r["length"] / r["duration_seconds"] for r in eligible if r["label"] == label and r["duration_seconds"] > 0])) if any(r["label"] == label and r["duration_seconds"] > 0 for r in eligible) else None for label in ("local", "pervasive")}),
                  marker_policy="Dirichlet prior concentration 1000 over same-prompt pooled marker frequencies; same-prompt donors; z>=1.96; >=5 occurrences",
                  bigram_policy="summed two-token surprisal; first-to-last character duration; other-writer produced-bigram frequency with P6 floor-one convention",
                  label_shuffle_unit="one label per writer-marker, shared by all its occurrences",
                  local_consensus="other writers' marker rate on the overused prompt <= their pooled rate on this writer's other prompts",
                  record_as_run=["D30.v1"] if config["card"] == "D30" and timing_mode == "invalid" else [])
    if revision:
        routes = dict(positive="Recurring choices are revised less often: the habits panel may say they are seldom revisited, descriptively.",
                      negative="Recurring choices are revised more often: the attention panel may say attention catches recurring choices that misfire.",
                      null="Revision does not separate pervasive and local choices.")
    else:
        routes = dict(positive="Route recurring departures to habits and one-off departures to attention, citing this descriptive contrast.",
                      negative="Pervasive choices are slower, consistent with deliberate global policy; reverse the automaticity rule.",
                      null="Pervasiveness locates choices but does not diagnose automaticity; retain covariation without the word autocomplete.")
    routes.update(marginal="Use the one frozen extension when available; a ladder variant has none and counts as a null.",
                  invalid="The instrument cannot answer this contrast; retain its reason without a scientific claim.")
    result["route"] = routes[result["state"]]
    return result, marker_evidence


def execute(output: Path, inputs: dict, config: dict) -> dict:
    started = time.monotonic()
    if config.get("card") not in {"D30", "D30.v1", "D30.v2"} or config.get("bootstrap_draws") != 2000 or config.get("seed") != 20261017:
        raise ValueError("D30 configuration differs from frozen family")
    if type(config.get("extension")) is not bool or (config["card"] != "D30" and config["extension"]):
        raise ValueError("ladder variants have no extension")
    output = Path(output)
    validate_inputs(inputs)
    write_equal(output / "D30_RUN_BINDINGS.json", dict(inputs={k: filehash(v) for k, v in inputs.items()}, config=config))
    if (output / "D30_PRIMARY.json").exists():
        return verify(output, inputs, config)["primary"]
    mode = read(inputs["tc_primary"])["timing_mode"]
    rows = input_occurrences(inputs, config)
    def first_tenth(receipt):
        elapsed = time.monotonic() - started
        projection = elapsed - receipt["primary_seconds"] + receipt["primary_seconds"] * 30
        if (output / "FIRST_TENTH.json").exists():
            return
        write(output / "FIRST_TENTH.json", dict(card=config["card"], active_seconds=elapsed, **receipt,
              projected_cpu_seconds=projection, forecast_cpu_seconds=3600, projection_exceeds_twice_forecast=projection > 7200,
              method="all preparation observed plus first tenth primary bootstrap projected over primary and two shuffled controls"))
    gzip_equal(output / "D30_INTERMEDIATES.json.gz", dict(rows=rows, config=config, timing_mode=mode))
    result, markers = analyze(rows, config, mode, on_tenth=first_tenth, checkpoint_dir=output)
    write_equal(output / "D30_MARKERS.json", markers)
    if result.get("status") == "yielded":
        return dict(result, card=config["card"], scientific_admission=False)
    write(output / "D30_PRIMARY.json", result)
    write(output / "D30_TIMING.json", dict(wall_seconds=time.monotonic() - started, occurrences=len(rows), forecast_cpu_seconds=3600))
    bind(output, inputs, config, ["D30_PRIMARY.json", "D30_MARKERS.json", "D30_INTERMEDIATES.json.gz"])
    return result


def validate_inputs(inputs):
    for name, terminal in (("p6_index", "p6_completion"), ("tc_primary", "tc_completion")):
        complete = Path(inputs[terminal])
        record = read(complete)
        if record.get("status") != "COMPLETE" or not record.get("fresh_process_verified"):
            raise ValueError("D30 dependency is not verified complete")
        path = Path(inputs[name]).resolve()
        relative = path.relative_to(complete.parent.resolve()).as_posix()
        if record["outputs"].get(relative) != filehash(path):
            raise ValueError("D30 dependency completion binding changed")


def input_occurrences(inputs, config):
    index_path = Path(inputs["p6_index"])
    records = []
    for row in read(index_path):
        path = index_path.parent / row["file"]
        path.resolve().relative_to(index_path.parent.resolve())
        if filehash(path) != row["sha256"]:
            raise ValueError("P6 source changed")
        records.append(gzread(path))
    return occurrences(records, config["card"] == "D30.v2")


def verify(output: Path, inputs: dict, config: dict) -> dict:
    validate_inputs(inputs)
    check_binding(output, inputs, config)
    saved = gzread(Path(output) / "D30_INTERMEDIATES.json.gz")
    if config != saved["config"] or saved["timing_mode"] != read(inputs["tc_primary"])["timing_mode"]:
        raise ValueError("D30 config/timing changed")
    if input_occurrences(inputs, config) != saved["rows"]:
        raise ValueError("D30 source-derived occurrences changed")
    result, markers = analyze(saved["rows"], config, saved["timing_mode"])
    if result != read(Path(output) / "D30_PRIMARY.json") or markers != read(Path(output) / "D30_MARKERS.json"):
        raise ValueError("D30 saved primary mismatch")
    return dict(verified=True, primary=result)
