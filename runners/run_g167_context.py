"""G167 context-conditioning battery — implements prereg/g167.py (frozen card; the
DESIGN CHECK lives there and this runner adds nothing).

    --gate       CPU: card-leak audit + pipeline purity. Runs first.
    --arm X      true_card | false_card | irrelevant_card     (GPU, checkpointed)
    --verdict    CPU: movement analysis vs the recorded no-card arm, bands,
                 abstention shifts, everything on disk.

Output: results/g167/
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results" / "g167"
G166R = REPO / "results" / "g166"
SEED = 16700

sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runners"))
from run_g159_recovery import call_reader, parse_pick                  # noqa: E402
from run_g166_reading import (                                         # noqa: E402
    CANNOT, DESCRIPTIONS, ROUTES, build_events, load_arts)

DRAFT_ROUTES = {"rewrite", "revise"}          # makers who had a complete prior version

CARD_DRAFT = ("The maker began with a complete previous version of this text in hand.")
CARD_NODRAFT = ("The maker began with only the assigned question and no previous "
                "version of this text.")
CARD_IRRELEVANT = ("The work took place on a weekday morning.")

CLASSIFY_CTX = """This essay was produced by exactly one of the numbered production \
routes below. One fact about the production context is known and reliable:

KNOWN CONTEXT: {card}

Read the essay and decide which route produced it.

ESSAY:
{text}

ROUTES:
{cands}

Answer with the number only."""


def true_card(route):
    return CARD_DRAFT if route in DRAFT_ROUTES else CARD_NODRAFT


def false_card(route):
    return CARD_NODRAFT if route in DRAFT_ROUTES else CARD_DRAFT


def card_for(arm, route):
    return {"true_card": true_card(route), "false_card": false_card(route),
            "irrelevant_card": CARD_IRRELEVANT}[arm]


def content_words(s):
    stop = set("the a an and or of to in on for with by at from is was be it this "
               "that then their no one".split())
    return {w.lower() for w in re.findall(r"[A-Za-z']+", s)} - stop


def gate():
    import numpy as np
    # 1. card-leak audit: no card shares a content word with any route description
    desc_words = set()
    for d in DESCRIPTIONS.values():
        desc_words |= content_words(d)
    desc_words |= content_words(CANNOT)
    leaks = {}
    for name, card in (("draft", CARD_DRAFT), ("nodraft", CARD_NODRAFT),
                       ("irrelevant", CARD_IRRELEVANT)):
        overlap = sorted(content_words(card) & desc_words)
        if overlap:
            leaks[name] = overlap
    # 2. pipeline purity: prompt pure in (essay, card, candidates)
    events, arts = build_events(np)
    h = lambda s: hashlib.sha256(s.encode()).hexdigest()               # noqa: E731
    defects = []
    for e in events[:20]:
        a = arts[e["case_id"]]
        cs = "\n".join(f"{j + 1}. {c}" for j, c in enumerate(e["cands"]))
        stripped = {**a, "route_family": "xx", "events": [], "lineage_id": "xx"}
        build = lambda art: CLASSIFY_CTX.format(card=CARD_IRRELEVANT,               # noqa: E731
                                                text=art["artifact_final"], cands=cs)
        if h(build(a)) != h(build(stripped)):
            defects.append(e["case_id"])
    out = {"prereg": "prereg/g167.py",
           "card_leak_audit": {"overlaps": leaks, "pass": not leaks},
           "pipeline_purity": {"events_checked": 20, "defects": defects,
                               "pass": not defects}}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "gate.json").write_text(json.dumps(out, indent=1), encoding="utf-8",
                                   newline="\n")
    print(json.dumps(out, indent=1))
    if leaks or defects:
        sys.exit(1)


def run_arm(arm):
    import numpy as np
    from soundingline.gpulock import acquire_gpu_lock                  # noqa: PLC0415
    acquire_gpu_lock(f"g167_{arm}")                    # once per invocation (LESSONS §5)
    events, arts = build_events(np)
    OUT.mkdir(parents=True, exist_ok=True)
    part = OUT / f"{arm}_partial.jsonl"
    done = {}
    if part.exists():
        done = {json.loads(x)["i"]: json.loads(x)
                for x in part.read_text(encoding="utf-8").splitlines()}
    with part.open("a", encoding="utf-8", newline="\n") as fh:
        for i, e in enumerate(events):
            if i in done:
                continue
            a = arts[e["case_id"]]
            cs = "\n".join(f"{j + 1}. {c}" for j, c in enumerate(e["cands"]))
            p = CLASSIFY_CTX.format(card=card_for(arm, e["route"]),
                                    text=a["artifact_final"], cands=cs)
            pick = parse_pick(call_reader(p), len(e["cands"]))
            row = {"i": i, **{k: e[k] for k in e if k != "cands"}, "pick": pick}
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            done[i] = row
    if len(done) < len(events):
        print(f"INCOMPLETE {arm}: {len(done)}/{len(events)}")
        sys.exit(1)
    rows = [done[i] for i in sorted(done)]
    ok = [r for r in rows if r["pick"] is not None]
    hit = sum(1 for r in ok if r["pick"] == r["truth_idx"])
    summary = {"arm": arm, "n": len(rows), "n_parsed": len(ok),
               "accuracy": round(hit / max(len(ok), 1), 4)}
    (OUT / f"{arm}.json").write_text(json.dumps(summary, indent=1), encoding="utf-8",
                                     newline="\n")
    print(json.dumps(summary, indent=1))


def _mass(rows, events, subset_of):
    """Committed mass on the card-compatible subset, and abstention rate."""
    compat = comm = 0
    for r in rows:
        if r["pick"] is None:
            continue
        e = events[r["i"]]
        if r["pick"] == e["cannot_idx"]:
            continue
        comm += 1
        picked = None
        for route, d in DESCRIPTIONS.items():
            if e["cands"][r["pick"]] == d:
                picked = route
        if picked in subset_of(e["route"]):
            compat += 1
    n = len(rows)
    return compat / max(n, 1), comm / max(n, 1)


def verdict():
    import numpy as np
    events, arts = build_events(np)
    rows_of = lambda p: [json.loads(x) for x in                        # noqa: E731
                         p.read_text(encoding="utf-8").splitlines()]
    base_rows = rows_of(G166R / "classify_partial.jsonl")
    out = {"prereg": "prereg/g167.py", "gates": {}, "verdict": {}}

    true_subset = lambda route: (DRAFT_ROUTES if route in DRAFT_ROUTES              # noqa: E731
                                 else set(ROUTES) - DRAFT_ROUTES)
    wrong_subset = lambda route: (set(ROUTES) - DRAFT_ROUTES                        # noqa: E731
                                  if route in DRAFT_ROUTES else DRAFT_ROUTES)

    base_true_mass, base_comm = _mass(base_rows, events, true_subset)
    base_wrong_mass, _ = _mass(base_rows, events, wrong_subset)

    irr_rows = rows_of(OUT / "irrelevant_card_partial.jsonl")
    irr_true_mass, irr_comm = _mass(irr_rows, events, true_subset)
    stable = abs(irr_comm - base_comm) <= 0.10
    out["gates"]["irrelevant_card_stability"] = {
        "recorded_no_card_committed": round(base_comm, 4),
        "irrelevant_card_committed": round(irr_comm, 4),
        "stable_within_0.10": bool(stable),
        "rule": "if unstable, movements read against the irrelevant arm, disclosed"}
    ref_true_mass = base_true_mass if stable else irr_true_mass
    ref_wrong_mass = base_wrong_mass if stable else _mass(irr_rows, events,
                                                          wrong_subset)[0]

    t_rows = rows_of(OUT / "true_card_partial.jsonl")
    f_rows = rows_of(OUT / "false_card_partial.jsonl")
    t_mass, t_comm = _mass(t_rows, events, true_subset)
    f_mass, f_comm = _mass(f_rows, events, wrong_subset)
    true_move = t_mass - ref_true_mass
    false_move = f_mass - ref_wrong_mass
    band = ("INERT" if true_move < 0.15 else
            "PROJECTION" if false_move >= 0.5 * true_move else "CONDITIONS")
    t_acc = json.loads((OUT / "true_card.json").read_text(encoding="utf-8"))
    out["verdict"]["context_movement"] = {
        "baseline_compatible_mass": round(ref_true_mass, 4),
        "true_card_compatible_mass": round(t_mass, 4),
        "true_movement": round(true_move, 4),
        "false_card_wrongsubset_mass": round(f_mass, 4),
        "false_movement": round(false_move, 4),
        "band": band,
        "committed_rates": {"no_card": round(base_comm, 4),
                            "true": round(t_comm, 4), "false": round(f_comm, 4),
                            "irrelevant": round(irr_comm, 4)},
        "true_card_accuracy_on_all": t_acc["accuracy"],
        "note": "movement floor 0.15 per card; subsets are draft {rewrite, revise} "
                "vs no-draft {direct, outline, select}"}
    _ = arts
    (OUT / "verdict.json").write_text(json.dumps(out, indent=1), encoding="utf-8",
                                     newline="\n")
    print(json.dumps(out, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--arm", choices=["true_card", "false_card", "irrelevant_card"])
    ap.add_argument("--verdict", action="store_true")
    args = ap.parse_args()
    if args.gate:
        gate()
    elif args.arm:
        run_arm(args.arm)
    elif args.verdict:
        verdict()
    else:
        ap.error("pick a mode")


if __name__ == "__main__":
    main()
