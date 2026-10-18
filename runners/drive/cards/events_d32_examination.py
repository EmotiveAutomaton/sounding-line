"""D32's single examination extension on frozen primary offers and D6 events.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-4 reread 2026-10-18.
NULL: equal paired group rates give zero. ALTERNATIVE: more unmarked short
displays outside repertoire gives positive; reverse exclusion is negative.
Missing bindings, malformed joins and fewer than three paired writers fail
closed. Unknown/censored observations are counted exclusions, never zeros.
No logged target is not proof of no examination. Default-first policies are
hypothetical, and the frozen two-second cutoff is an operational choice.
"""
from __future__ import annotations

import math
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from .events_p5 import read, write, freeze_or_equal, filehash
from .states_v2 import contrast_state

CONFIG = dict(card="D32-examination", bootstrap=2000, seed=20261018,
              permutation_seed=20261019, short_seconds=2., sensitivity_seconds=[1., 5.])
ARMS = {"primary": 1, "hovered": -1, "targeted": -1, "hover_only_short": 1,
        "explicit_targets_short": 1, "default_argumentative_short": 1,
        "short_1s": 1, "short_5s": 1}


def source(inputs, config):
    if set(inputs) != {"d32_completion", "d6_completion"} or config != CONFIG:
        raise ValueError("frozen extension inputs/config differ")
    bindings, sources = {}, {}
    for key, module, names in (
        ("d32_completion", "runners.drive.cards.events_d32", ["output/ROWS_k50.json"]),
        ("d6_completion", "runners.drive.cards.events_d6", ["output/ROWS.json", "output/INTERFACE_AUDIT.json"])):
        path = Path(inputs[key]); terminal = read(path)
        if terminal.get("status") != "COMPLETE" or not terminal.get("fresh_process_verified"):
            raise ValueError("source is not verified complete")
        bindings[str(path)] = filehash(path)
        for name in ["PLAN.json"] + names:
            child = path.parent / name
            actual = filehash(child)
            if terminal["outputs"].get(name) != actual:
                raise ValueError("source completion binding changed: " + name)
            bindings[str(child)] = actual
        plan = read(path.parent / "PLAN.json")
        if plan["module"] != module:
            raise ValueError("wrong source module")
        expected = dict(bootstrap=2000, seed=20261017)
        if key == "d32_completion": expected["clusters"] = [50, 20, 100]
        if plan["config"] != expected:
            raise ValueError("wrong source primary configuration")
        sources[key] = read(path.parent / names[0])
    return sources["d32_completion"], sources["d6_completion"], bindings


def menu_lookup(menus):
    lookup = {}
    for m in menus:
        n = m["menu_size"]
        if m["key"] in lookup or type(n) is not int or n < 1:
            raise ValueError("duplicate menu or invalid menu size")
        for field in ("hovered", "navigated", "targeted", "default_all", "default_argumentative"):
            if len(m[field]) != n or any(type(v) is not bool for v in m[field]):
                raise ValueError("malformed target vector")
        if (type(m["hover_target_complete"]) is not bool or type(m["dwell_observed"]) is not bool
            or isinstance(m["dwell_seconds"], bool) or not math.isfinite(m["dwell_seconds"])
            or m["dwell_seconds"] < 0):
            raise ValueError("invalid observation state/duration")
        selected = m["selected"]
        if selected is not None and (type(selected) is not int or not 0 <= selected < n):
            raise ValueError("invalid selected position")
        for i in range(n):
            targeted = m["hovered"][i] or m["navigated"][i] or selected == i
            if (m["targeted"][i] != targeted or m["default_all"][i] != (targeted or i == 0)
                or m["default_argumentative"][i] != (targeted or (i == 0 and m["domain"] == "argumentative"))):
                raise ValueError("inconsistent target/default reconstruction")
        lookup[m["key"]] = m
    return lookup


def join(offers, menus):
    lookup = menu_lookup(menus)
    seen, rows, audit = set(), [], Counter()
    for offer in sorted(offers, key=lambda r: (r["writer"], r["session"], r["key"], r["position"])):
        m = lookup.get(offer["key"]); pos = offer["position"]
        identity = (offer["key"], pos)
        if identity in seen or m is None or type(pos) is not int or not 0 <= pos < m["menu_size"]:
            raise ValueError("missing menu or duplicate/invalid offer position")
        seen.add(identity)
        if m["writer"] != offer["writer"] or m["session"] != offer["session"]:
            raise ValueError("writer/session join differs")
        if offer["accepted"] not in (0, 1) or int(m["selected"] == pos) != offer["accepted"]:
            raise ValueError("selected position disagrees with acceptance")
        if offer["outside"] not in (0, 1):
            raise ValueError("nonbinary repertoire label")
        audit["source_offers"] += 1
        if offer["accepted"]:
            audit["accepted_excluded"] += 1
            continue
        audit["declined_offers"] += 1
        missing = not m["hover_target_complete"]; censored = not m["dwell_observed"]
        audit["declined_missing_hover_target"] += missing
        audit["declined_censored_duration"] += censored
        if missing or censored:
            audit["excluded_unknown_union"] += 1
            continue
        rows.append(dict(writer=offer["writer"], session=offer["session"], key=offer["key"],
            position=pos, outside=int(offer["outside"]), dwell_seconds=float(m["dwell_seconds"]),
            hovered=m["hovered"][pos], targeted=m["targeted"][pos],
            default_all=m["default_all"][pos], default_argumentative=m["default_argumentative"][pos]))
    audit["eligible_declined_offers"] = len(rows)
    audit["source_menus"] = len(menus)
    return rows, dict(audit)


def indicators(row):
    short = row["dwell_seconds"] <= CONFIG["short_seconds"]
    return dict(primary=not row["default_all"] and short,
        hovered=row["hovered"], targeted=row["targeted"],
        hover_only_short=not row["hovered"] and short,
        explicit_targets_short=not row["targeted"] and short,
        default_argumentative_short=not row["default_argumentative"] and short,
        short_1s=not row["default_all"] and row["dwell_seconds"] <= 1.,
        short_5s=not row["default_all"] and row["dwell_seconds"] <= 5.)


def statistics(rows, shuffled=False):
    ordered = sorted(rows, key=lambda r: (r["writer"], r["session"], r["key"], r["position"]))
    grouped = defaultdict(list)
    for row in ordered: grouped[row["writer"]].append(row)
    rng = np.random.default_rng(CONFIG["permutation_seed"])
    values, counts, eligible_counts, omitted = [], [], [], []
    keys = list(ARMS)
    for writer in sorted(grouped):
        group = grouped[writer]
        labels = np.array([r["outside"] for r in group])
        if shuffled: labels = rng.permutation(labels)
        if set(labels) != {0, 1}:
            omitted.append(writer)
            continue
        matrix = np.array([[indicators(r)[k] for k in keys] for r in group], float)
        values.append(np.array([matrix[labels == side].mean(0) for side in (0, 1)]))
        counts.append([int((labels == side).sum()) for side in (0, 1)])
        eligible_counts.append([matrix[labels == side].sum(0).tolist() for side in (0, 1)])
    if len(values) < 3:
        raise ValueError("fewer than three paired writers")
    means = np.asarray(values); delta = means[:, 1] - means[:, 0]
    indices = np.random.default_rng(CONFIG["seed"]).integers(len(values), size=(CONFIG["bootstrap"], len(values)))
    draws = delta[indices].mean(1)
    results = {}
    for j, key in enumerate(keys):
        effect = float(delta[:, j].mean()); low, high = np.quantile(draws[:, j], [.025, .975]).tolist()
        se = float(np.std(draws[:, j], ddof=1)); z = effect / se if se > 0 else None
        results[key] = dict(effect=effect, ci95=[low, high], state=contrast_state(effect, low, high, ARMS[key]),
            expected_direction=ARMS[key], inside_share=float(means[:, 0, j].mean()),
            outside_share=float(means[:, 1, j].mean()), standard_error=se, z=z,
            p_approx=math.erfc(abs(z)/math.sqrt(2)) if z is not None else None,
            p_method="two-sided normal-reference Wald approximation; descriptive, not permutation p",
            inside_events=int(np.asarray(eligible_counts)[:, 0, j].sum()),
            outside_events=int(np.asarray(eligible_counts)[:, 1, j].sum()))
    return dict(contrasts=results, paired_writers=len(values),
        declined_inside=int(np.asarray(counts)[:, 0].sum()), declined_outside=int(np.asarray(counts)[:, 1].sum()),
        excluded_unpaired_writers=len(omitted), excluded_unpaired_offers=sum(len(grouped[w]) for w in omitted),
        bootstrap_draws=CONFIG["bootstrap"], weighting="equal paired writer weight; within-writer offer fractions")


def summary(rows, audit):
    actual = statistics(rows)
    control = statistics(rows, shuffled=True)
    return dict(card=CONFIG["card"], question="Do declined outside-repertoire offers more often have no target marker during short menu displays?",
        primary=actual["contrasts"].pop("primary"), specifications=actual.pop("contrasts"),
        support=actual, extraction_audit=audit,
        control=control["contrasts"]["primary"],
        uncertainty="Conditions on frozen repertoire and interface reconstruction; no cluster refit",
        descriptive=True, scientific_admission=False,
        interpretation="No target marker is not no examination; default-first is hypothetical; duration is menu-level, not option gaze; no pruning/dislike/taste/habit identification")


def execute(output, inputs, config):
    output = Path(output); started = time.monotonic()
    offers, menus, pins = source(inputs, config)
    freeze_or_equal(output / "INPUTS.json", dict(paths=inputs, config=config, pins=pins))
    if (output / "SUMMARY.json").exists():
        return verify(output, inputs, config)["summary"]
    # Joining is linear and short. Validate in the same deterministic chunks used
    # on resume; never overwrite a completed extraction checkpoint.
    chunks = [offers[i:i+max(1, math.ceil(len(offers)/10))] for i in range(0, len(offers), max(1, math.ceil(len(offers)/10)))]
    for i, chunk in enumerate(chunks):
        path = output / f"parts/{i:02d}.json"
        rows, audit = join(chunk, menus)
        freeze_or_equal(path, dict(rows=rows, audit=audit))
        if i == 0 and not (output / "FIRST_TENTH.json").exists():
            elapsed = time.monotonic() - started
            write(output / "FIRST_TENTH.json", dict(projected_seconds=max(1., elapsed * 24),
                elapsed_seconds=elapsed, forecast_cpu_seconds=600, completed_chunks=1, total_chunks=len(chunks)))
        if (output / "YIELD_REQUEST.json").exists():
            return dict(status="yielded", chunks_saved=i+1, total_chunks=len(chunks))
    rows, audit = join(offers, menus)  # global duplicate detection across chunks
    freeze_or_equal(output / "ROWS.json", rows)
    result = summary(rows, audit)
    freeze_or_equal(output / "SUMMARY.json", result)
    freeze_or_equal(output / "OUTPUT_HASHES.json", {p.relative_to(output).as_posix(): filehash(p)
        for p in output.rglob("*.json") if p.name not in {"OUTPUT_HASHES.json", "YIELD_REQUEST.json"}})
    return result


def verify(output, inputs, config):
    output = Path(output)
    offers, menus, pins = source(inputs, config)
    if read(output / "INPUTS.json") != dict(paths=inputs, config=config, pins=pins):
        raise ValueError("source bindings changed")
    for name, expected in read(output / "OUTPUT_HASHES.json").items():
        if filehash(output / name) != expected: raise ValueError("saved output changed")
    rows, audit = join(offers, menus)
    if rows != read(output / "ROWS.json"): raise ValueError("source reconstruction changed")
    result = summary(rows, audit)
    if result != read(output / "SUMMARY.json"): raise ValueError("replayed statistics differ")
    return dict(verified=True, summary=result)
