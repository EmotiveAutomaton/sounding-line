"""D6: logged menu examination by display position.

DESIGN CHECK: LESSONS 3-5. NULL: exchangeable slot labels yield zero slot-one
minus slot-five hover probability; planted position differences are recovered.
The primary uses paired five-item menus and equal writer weight. Fewer than
two writers or malformed pointer mappings are invalid, never a negative result.
Hover is a logged target event, not proof of reading. Keyboard/default source
semantics are authenticated separately; absent hover never becomes nonexposure.
Bootstrap intervals are descriptive, and the shared states own fixed bands.
"""
from __future__ import annotations

import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

from .events_p5 import read, write, freeze_or_equal, filehash
from . import states_v2 as states


def pointer(value, indices):
    """Resolve logged option identity to displayed array position, preserving null."""
    if value in (None, "", -1):
        return None
    if isinstance(value, bool):
        raise ValueError("boolean suggestion pointer")
    if isinstance(value, str):
        if not value.isdecimal():
            raise ValueError("malformed suggestion pointer")
        value = int(value)
    if type(value) is not int or value not in indices:
        raise ValueError("suggestion pointer outside displayed menu")
    return indices.index(value)


def extract_session(events, session, p2, domain):
    """Audit source state before computing any contrast; no inferred key events."""
    if not events or events[0].get("eventName") != "system-initialize":
        raise ValueError("missing initialization")
    times = [float(e["eventTimestamp"]) for e in events]
    if not all(math.isfinite(x) for x in times) or times != sorted(times):
        raise ValueError("invalid source chronology")
    decisions = {r["key"]: r for r in p2["decisions"]}
    if len(decisions) != len(p2["decisions"]) or set(decisions) != {r["key"] for r in session["rows"]}:
        raise ValueError("P2/prepared decision join differs")
    rows = []
    audit = Counter({"sessions": 1, "source_events": len(events)})
    event_names = Counter(e["eventName"] for e in events)
    target_changes = Counter()
    for source_row in session["rows"]:
        start, end = source_row["ordinal"], source_row["end_ordinal"]
        if not (0 <= start < end <= len(events)):
            raise ValueError("invalid prepared menu bounds")
        opening = events[start]
        decision = decisions[source_row["key"]]
        if opening["eventName"] != "suggestion-open" or decision["ordinal"] != start:
            raise ValueError("prepared opening differs")
        options = opening["currentSuggestions"]
        if isinstance(options, str):
            options = json.loads(options)
        if not isinstance(options, list) or not options:
            raise ValueError("empty menu")
        if [o["original"] for o in options] != source_row["menu"] or len(options) != decision["menu_size"]:
            raise ValueError("displayed menu differs")
        indices = [o["index"] for o in options]
        if any(type(i) is not int for i in indices) or len(set(indices)) != len(indices):
            raise ValueError("invalid displayed option identities")
        # Hover snapshots outside hover events are stale in the released code.
        # A close/reopen pair retains this offered menu; collect only its visible
        # episodes, ending at selection or the prepared next-menu boundary.
        opened_hover = opening.get("currentHoverIndex")
        opened_selection = opening.get("currentSuggestionIndex")
        hovered = [False] * len(options)
        hover_target_complete = True
        navigated = [False] * len(options)
        sequence = []
        keyboard_sequence = []
        state_changes = []
        explicit_keys = []
        previous_hover = opened_hover
        previous_selection = opened_selection
        selected = None
        visible = True
        episode_start = start
        episodes = []
        last_terminal = None
        for ordinal in range(start + 1, end):
            event = events[ordinal]
            hover = event.get("currentHoverIndex")
            selection = event.get("currentSuggestionIndex")
            name = event["eventName"]
            if name == "suggestion-reopen":
                if visible:
                    raise ValueError("reopen while menu is already visible")
                visible = True
                episode_start = ordinal
                audit["reopened_menus"] += 1
            if name == "suggestion-hover" and visible:
                audit["hover_events_before_boundary"] += 1
                position = pointer(hover, indices)
                if position is None:
                    audit["hover_events_without_target"] += 1
                    hover_target_complete = False
                else:
                    hovered[position] = True
                    sequence.append(dict(ordinal=ordinal, position=position,
                                         seconds=(times[ordinal] - times[start]) / 1000))
            elif name in ("suggestion-up", "suggestion-down") and visible:
                # Navigation records a DOM position; hover/click records an
                # option identity. Sorting/filtering may make these differ.
                position = pointer(selection, list(range(len(options))))
                if position is None:
                    raise ValueError("keyboard navigation without target")
                navigated[position] = True
                keyboard_sequence.append(dict(ordinal=ordinal, event=name, position=position,
                                              seconds=(times[ordinal] - times[start]) / 1000))
                audit["keyboard_navigation_events"] += 1
            elif name in ("suggestion-hover", "suggestion-up", "suggestion-down"):
                audit["target_events_outside_visible_episodes"] += 1
            if hover != previous_hover or selection != previous_selection:
                target_changes[name] += 1
                state_changes.append(dict(ordinal=ordinal, event=name, hover=hover, selected=selection))
            for field in ("key", "code", "keyCode", "which"):
                if event.get(field) not in (None, ""):
                    # Only key metadata, never textDelta/currentDoc.
                    explicit_keys.append(dict(ordinal=ordinal, event=name, field=field, value=event[field]))
            if name == "suggestion-select":
                selected = pointer(selection, indices)
                if selected is None or not visible:
                    raise ValueError("selection event without selected target")
            if name in ("suggestion-select", "suggestion-close") and visible:
                episodes.append(dict(start=episode_start, end=ordinal, observed_end=True,
                                     seconds=(times[ordinal] - times[episode_start]) / 1000))
                visible = False
                last_terminal = ordinal
            previous_hover, previous_selection = hover, selection
            if selected is not None:
                break
        if visible:
            episodes.append(dict(start=episode_start, end=end - 1, observed_end=False,
                                 seconds=(times[end - 1] - times[episode_start]) / 1000))
        if source_row["handling"] in ("accept", "edit"):
            if selected is None or options[selected]["original"] != source_row["inserted"]:
                raise ValueError("selected source/prepared text differs")
        elif selected is not None:
            raise ValueError("selected source has nonaccepting handling")
        scores = []
        for option in options:
            score = option.get("probability")
            if score is None or isinstance(score, bool):
                scores.append(None)
            else:
                score = float(score)
                if not math.isfinite(score):
                    raise ValueError("nonfinite logged producer score")
                scores.append(score)
        ranks = (rankdata(scores, method="average").tolist()
                 if all(x is not None for x in scores) else None)
        if ranks is not None:
            ranks = [x - 1 for x in ranks]
        audit["menus"] += 1
        audit["five_item_menus" if len(options) == 5 else "nonfive_item_menus"] += 1
        audit["menus_with_explicit_key_metadata"] += bool(explicit_keys)
        audit["menus_with_nonempty_stale_open_hover"] += opened_hover not in (None, "", -1)
        audit["menus_without_hover"] += not any(hovered)
        audit["menus_without_hover_with_keyboard"] += not any(hovered) and any(navigated)
        audit["dismissals_without_hover"] += source_row["handling"] == "dismiss" and not any(hovered)
        audit["menus_with_censored_visible_episode"] += any(not e["observed_end"] for e in episodes)
        targeted = [h or k or i == selected for i, (h, k) in enumerate(zip(hovered, navigated))]
        default_all = [v or i == 0 for i, v in enumerate(targeted)]
        default_argumentative = [v or (i == 0 and domain == "argumentative") for i, v in enumerate(targeted)]
        rows.append(dict(key=source_row["key"], writer=session["writer"], session=session["session"],
            domain=domain, handling=source_row["handling"], menu_size=len(options), hovered=hovered,
            hover_target_complete=hover_target_complete,
            navigated=navigated, targeted=targeted, default_all=default_all,
            default_argumentative=default_argumentative, hover_sequence=sequence,
            keyboard_sequence=keyboard_sequence, open_hover=opened_hover, open_selection=opened_selection,
            selected=selected, target_changes=state_changes, explicit_keys=explicit_keys,
            terminal=events[last_terminal]["eventName"] if last_terminal is not None else None,
            visible_episodes=episodes, dwell_seconds=sum(e["seconds"] for e in episodes),
            dwell_observed=all(e["observed_end"] for e in episodes), source_score_ranks=ranks,
            logged_score_outside_probability_range=sum(x is not None and not 0 <= x <= 1 for x in scores)))
    return dict(rows=rows, audit=dict(audit), event_names=dict(event_names),
                target_change_event_names=dict(target_changes))


def contrast(rows, bootstrap, seed, field="hovered"):
    grouped = defaultdict(list)
    for row in rows:
        if row["menu_size"] == 5 and row.get("hover_target_complete", True):
            values = row[field]
            grouped[row["writer"]].append(float(values[0]) - float(values[4]))
    if len(grouped) < 2:
        return dict(effect=None, ci95=None, state="invalid", writers=len(grouped),
                    reason="fewer than two writers with paired five-item menus")
    values = np.array([np.mean(grouped[w]) for w in sorted(grouped)])
    effect = float(values.mean())
    rng = np.random.default_rng(seed)
    draws = values[rng.integers(len(values), size=(bootstrap, len(values)))].mean(1)
    low, high = np.quantile(draws, [.025, .975]).tolist()
    se = float(np.std(draws, ddof=1))
    z = effect / se if se > 0 else None
    return dict(effect=effect, ci95=[low, high], standard_error=se, z=z,
        p_approx=math.erfc(abs(z) / math.sqrt(2)) if z is not None else None,
        p_method="two-sided normal-reference Wald approximation; descriptive, not permutation p",
        state=states.contrast_state(effect, low, high, expected_direction=1), writers=len(values),
        menus=sum(len(v) for v in grouped.values()))


def statistics(rows, config):
    eligible = [r for r in rows if r["menu_size"] == 5 and r.get("hover_target_complete", True)]
    rng = np.random.default_rng(config["seed"] + 1)
    permuted = [dict(r, hovered=rng.permutation(r["hovered"]).tolist()) for r in eligible]
    domains = {}
    for domain in sorted({r["domain"] for r in rows}):
        subset = [r for r in eligible if r["domain"] == domain]
        selected = [r["selected"] for r in subset if r["selected"] is not None]
        counts = [selected.count(i) for i in range(5)]
        domains[domain] = dict(menus=len(subset), primary=contrast(subset, config["bootstrap"], config["seed"]),
            selected_slot_counts=counts, selected_slot_shares=[n / len(selected) for n in counts] if selected else None,
            open_hover_counts=dict(Counter(str(r["open_hover"]) for r in subset)),
            open_selection_counts=dict(Counter(str(r["open_selection"]) for r in subset)))
    ranks = [r["source_score_ranks"] for r in eligible if r["source_score_ranks"] is not None]
    # This sensitivity treats any unlogged option as potentially examined. It
    # never substitutes a point estimate for unobserved exposure.
    lower = [dict(r, bounds=[float(r["hovered"][0]), 0, 0, 0, 1.]) for r in eligible]
    upper = [dict(r, bounds=[1., 0, 0, 0, float(r["hovered"][4])]) for r in eligible]
    return dict(card="D6", question="Is a logged hover more likely at the first menu slot than the fifth?",
        primary=contrast(eligible, config["bootstrap"], config["seed"]),
        controls=dict(within_menu_position_shuffle=contrast(permuted, config["bootstrap"], config["seed"])),
        specifications=domains,
        exposure_sensitivity={name: contrast(eligible, config["bootstrap"], config["seed"], name)
                              for name in ("targeted", "default_all", "default_argumentative")},
        exposure_sensitivity_convention="Targeted combines hover, arrow target and selected slot; default_all adds slot one to every menu; default_argumentative adds it only under hypothetical argumentative=nonstory mapping",
        assignment_audit=dict(score_rank_menus=len(ranks), mean_ascending_score_rank_by_position=np.mean(ranks, axis=0).tolist() if ranks else None,
            source_score_outside_probability_range=sum(r["logged_score_outside_probability_range"] for r in rows),
            caution="Logged score ranks are descriptive; balance alone does not establish random assignment or causal examination"),
        latent_exposure_bounds=dict(lower=contrast(lower, config["bootstrap"], config["seed"], "bounds"),
            upper=contrast(upper, config["bootstrap"], config["seed"], "bounds"),
            convention="Conditional on recorded hover indicating examination; unhovered slots may all be examined or unexamined"),
        source_menus=len(rows), excluded_nonfive_menus=sum(r["menu_size"] != 5 for r in rows),
        excluded_five_item_missing_hover_target=sum(r["menu_size"] == 5 and not r.get("hover_target_complete", True) for r in rows),
        weighting="Within-writer menu means, then equal writer weight; 2000 writer bootstrap draws",
        descriptive=True, scientific_admission=False, extension_run=False,
        extension="Content-coefficient shrinkage under a separately frozen examination model, positive direction",
        interpretation="Logged target activity is evidence of examination, not proof of reading; no hover is not no exposure")


def interface_review(path):
    review = read(path)
    required = {"display_order", "hover_event", "keyboard_navigation", "default_highlight", "domain_mapping"}
    if (review.get("status") != "reviewed" or not review.get("source_files")
            or set(review.get("findings", {})) != required
            or any(not review["findings"][key] for key in required)):
        raise ValueError("complete reviewed interface audit required before execution")
    pins = {}
    for item in review["source_files"]:
        source = Path(item["path"])
        if not source.is_absolute() or filehash(source) != item["sha256"]:
            raise ValueError("reviewed interface source changed")
        pins[str(source)] = item["sha256"]
    return review, pins


def execute(output: Path, inputs: dict, config: dict) -> dict:
    if set(inputs) != {"p2_index", "source_roster", "source_root", "sessions", "interface_audit"}:
        raise ValueError("explicit D6 inputs differ")
    if config != {"bootstrap": 2000, "seed": 20261017}:
        raise ValueError("frozen D6 config differs")
    started = time.monotonic()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    review, source_pins = interface_review(inputs["interface_audit"])
    file_pins = {str(Path(v)): filehash(v) for k, v in inputs.items() if k != "source_root"}
    binding = dict(paths=inputs, config=config, pins=file_pins)
    if (output / "INPUTS.json").exists():
        if read(output / "INPUTS.json") != binding:
            raise ValueError("resume inputs/config differ")
        if (output / "SUMMARY.json").exists():
            raise ValueError("completed output is verified, never rerun")
    elif any(output.iterdir()):
        raise ValueError("unbound existing output")
    else:
        write(output / "INPUTS.json", binding)
    source_pins.update(file_pins)
    freeze_or_equal(output / "INTERFACE_AUDIT.json", review)
    index = read(inputs["p2_index"])
    sessions = read(inputs["sessions"])
    roster_rows = read(inputs["source_roster"])
    meta = {r["session"]: r for r in roster_rows}
    prepared = {s["session"]: s for s in sessions}
    if (len(meta) != len(roster_rows) or len(prepared) != len(sessions)
            or len({r["session"] for r in index}) != len(index)
            or set(prepared) != {r["session"] for r in index} or not set(prepared) <= set(meta)):
        raise ValueError("source cohort differs")
    rows = []
    audit = Counter()
    event_names = Counter()
    target_changes = Counter()
    receipts = []
    elapsed = 0.
    source_root = Path(inputs["source_root"]).resolve()
    p2_root = Path(inputs["p2_index"]).resolve().parent
    for item in sorted(index, key=lambda r: r["session"]):
        unit_started = time.monotonic()
        session = prepared[item["session"]]
        source_meta = meta[item["session"]]
        if session["writer"] != item["writer"] or session["writer"] != source_meta["writer"]:
            raise ValueError("writer source join differs")
        source_path = (source_root / source_meta["path"]).resolve()
        p2_path = (p2_root / item["file"]).resolve()
        if not source_path.is_relative_to(source_root) or not p2_path.is_relative_to(p2_root):
            raise ValueError("source path outside explicit root")
        for path, expected in ((source_path, source_meta["source_sha256"]), (p2_path, item["sha256"])):
            if filehash(path) != expected:
                raise ValueError("source changed")
            source_pins[str(path)] = expected
        relative = f"sessions/{item['session']}.json"
        path = output / relative
        receipt_path = path.with_suffix(".receipt.json")
        if receipt_path.exists():
            receipt = read(receipt_path)
            if (receipt["source_sha256"] != source_meta["source_sha256"]
                    or receipt["p2_sha256"] != item["sha256"] or receipt["file"] != relative
                    or filehash(path) != receipt["sha256"]):
                raise ValueError("checkpoint binding/content changed")
            saved = read(path)
        else:
            with source_path.open(encoding="utf8") as f:
                events = [json.loads(line) for line in f]
            saved = extract_session(events, session, read(p2_path), source_meta["domain"])
            if path.exists():
                retained = path.with_name(path.name + ".incomplete")
                if retained.exists():
                    raise ValueError("second incomplete checkpoint is not retried")
                path.rename(retained)
            write(path, saved)
            receipt = dict(file=relative, sha256=filehash(path), source_sha256=source_meta["source_sha256"],
                           p2_sha256=item["sha256"], elapsed_seconds=time.monotonic() - unit_started)
            write(receipt_path, receipt)
        rows.extend(saved["rows"])
        audit.update(saved["audit"])
        event_names.update(saved["event_names"])
        target_changes.update(saved["target_change_event_names"])
        receipts.append(receipt)
        elapsed += receipt["elapsed_seconds"]
        if len(receipts) == max(1, math.ceil(.1 * len(index))) and not (output / "FIRST_TENTH.json").exists():
            write(output / "FIRST_TENTH.json", dict(sessions=len(receipts), elapsed_seconds=elapsed,
                projected_seconds=elapsed * len(index) / len(receipts), forecast_cpu_seconds=3600))
        if (output / "YIELD_REQUEST.json").exists():
            return dict(status="yielded", sessions_saved=len(receipts), sessions_total=len(index))
    freeze_or_equal(output / "SOURCE_PINS.json", source_pins)
    freeze_or_equal(output / "SESSION_INDEX.json", receipts)
    freeze_or_equal(output / "ROWS.json", rows)
    extraction_audit = dict(counts=dict(audit), event_names=dict(event_names),
                            target_change_event_names=dict(target_changes))
    freeze_or_equal(output / "EXTRACTION_AUDIT.json", extraction_audit)
    result = statistics(rows, config)
    result.update(extraction_audit=extraction_audit, interface_findings=review["findings"],
                  elapsed_seconds_this_invocation=time.monotonic() - started,
                  source_checkpoint_elapsed_seconds=elapsed)
    write(output / "SUMMARY.json", result)
    write(output / "OUTPUT_HASHES.json", {p.relative_to(output).as_posix(): filehash(p)
        for p in output.rglob("*") if p.is_file() and p.name not in ("OUTPUT_HASHES.json", "YIELD_REQUEST.json")})
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output)
    binding = read(output / "INPUTS.json")
    if binding["paths"] != inputs or binding["config"] != config:
        raise ValueError("verification binding differs")
    for path, expected in read(output / "SOURCE_PINS.json").items():
        if filehash(path) != expected:
            raise ValueError("source changed")
    for relative, expected in read(output / "OUTPUT_HASHES.json").items():
        if filehash(output / relative) != expected:
            raise ValueError("output changed")
    saved = read(output / "SUMMARY.json")
    rebuilt = statistics(read(output / "ROWS.json"), config)
    if any(saved[key] != value for key, value in rebuilt.items()):
        raise ValueError("saved primary/control/audit statistics differ")
    return dict(verified=True, primary=rebuilt["primary"])
