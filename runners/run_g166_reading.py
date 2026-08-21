"""G166-R equifinality reading battery — implements prereg/g166.py (frozen card; the
DESIGN CHECK lives there and this runner adds nothing).

    --gate       CPU: exact-equivalence purity (X). Runs first; arms gate on it.
    --arm A      process | classify | blind          (GPU, checkpointed)
    --surface    CPU: the mechanical nearest-centroid baseline (S).
    --verdict    CPU: P ceiling first, per-route confusion, the C-vs-S contest,
                 bands, everything on disk.

Output: results/g166/
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CORPUS = REPO / "corpora" / "g166_routes"
OUT = REPO / "results" / "g166"
SEED = 16650

sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runners"))
from run_g159_recovery import call_reader, parse_pick                  # noqa: E402
from run_g166_routes import GENERATORS, ROUTES                         # noqa: E402

DESCRIPTIONS = {
    "direct": "written in one pass directly from the topic brief",
    "outline": "planned as a five-point outline first, then written following it",
    "rewrite": "produced by fully rewriting an earlier draft essay on the topic",
    "select": "written committed to one thesis chosen from three proposed candidates",
    "revise": "drafted, then explicitly critiqued for two weaknesses and rewritten",
}
CANNOT = "cannot tell from this essay"

CLASSIFY = """This essay was produced by exactly one of the numbered production \
routes below. Read it carefully and decide which.

ESSAY:
{text}

ROUTES:
{cands}

Answer with the number only."""

PROCESS = """This essay was produced by exactly one of the numbered production routes \
below. You are also shown the working materials recorded during its production. Decide \
which route produced it.

ESSAY:
{text}

RECORDED WORKING MATERIALS:
{record}

ROUTES:
{cands}

Answer with the number only."""

BLIND = """One of the numbered production routes below produced an essay you cannot \
see. Which do you think it was?

ROUTES:
{cands}

Answer with the number only."""


def load_arts():
    arts = []
    for gen in GENERATORS:
        for p in sorted((CORPUS / gen).glob("*.json")):
            arts.append(json.loads(p.read_text(encoding="utf-8")))
    return arts


def record_text(a):
    """The recorded intermediates, for the process-aware arm ONLY (I3)."""
    parts = []
    for e in a["events"]:
        pl = e.get("payload") or {}
        if "outline" in pl:
            parts.append(f"an outline written first:\n{pl['outline'][:400]}")
        if "candidates" in pl:
            parts.append("three thesis candidates proposed: "
                         + " | ".join(pl["candidates"]))
        if "selected" in pl:
            parts.append(f"the selected thesis: {pl['selected']}")
        if "weaknesses" in pl:
            parts.append("a self-critique naming two weaknesses: "
                         + " | ".join(pl["weaknesses"]))
        if "base_ref" in pl:
            parts.append("an earlier draft essay that was rewritten (reference: "
                         + pl["base_ref"] + ")")
    if a["artifact_versions"] and not parts:
        parts.append("a prior version of the text exists in the record")
    return "\n".join(parts) or "(no intermediate materials were recorded)"


def build_events(np):
    rng = np.random.default_rng(SEED)
    arts = load_arts()
    order = list(ROUTES)
    events = []
    for a in arts:
        cands = [DESCRIPTIONS[r] for r in order] + [CANNOT]
        perm = list(rng.permutation(len(order))) + [len(order)]
        shuffled = [cands[j] for j in perm]
        truth_idx = perm.index(order.index(a["route_family"]))
        events.append({"case_id": a["case_id"], "route": a["route_family"],
                       "generator": a["generator"],
                       "topic": a["brief_id"], "cands": shuffled,
                       "truth_idx": truth_idx, "cannot_idx": len(order)})
    return events, {a["case_id"]: a for a in arts}


def gate():
    import numpy as np
    events, arts = build_events(np)
    h = lambda s: hashlib.sha256(s.encode()).hexdigest()               # noqa: E731
    defects = []
    for e in events[:20]:
        a = arts[e["case_id"]]
        cs = "\n".join(f"{j + 1}. {c}" for j, c in enumerate(e["cands"]))
        stripped = {**a, "route_family": "xx", "events": [], "lineage_id": "xx",
                    "construction_seed": -1, "artifact_versions": []}
        build = lambda art: CLASSIFY.format(text=art["artifact_final"], cands=cs)  # noqa: E731
        if h(build(a)) != h(build(stripped)):
            defects.append(e["case_id"])
    out = {"prereg": "prereg/g166.py",
           "exact_equivalence": {"events_checked": 20, "defects": defects,
                                 "pass": not defects}}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "gate.json").write_text(json.dumps(out, indent=1), encoding="utf-8",
                                   newline="\n")
    print(json.dumps(out, indent=1))
    if defects:
        sys.exit(1)


def run_arm(arm):
    import numpy as np
    from soundingline.gpulock import acquire_gpu_lock                  # noqa: PLC0415
    acquire_gpu_lock(f"g166r_{arm}")                   # once per invocation (LESSONS §5)
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
            if arm == "process":
                p = PROCESS.format(text=a["artifact_final"],
                                   record=record_text(a), cands=cs)
            elif arm == "classify":
                p = CLASSIFY.format(text=a["artifact_final"], cands=cs)
            else:
                p = BLIND.format(cands=cs)
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


def surface_features(text):
    words = re.findall(r"[A-Za-z']+", text)
    sents = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    paras = [p for p in text.split("\n\n") if p.strip()]
    n = max(len(words), 1)
    return [len(words),
            len(words) / max(len(sents), 1),
            len(set(w.lower() for w in words)) / n,
            len(paras),
            sum(1 for w in words if w.lower() in ("i", "we", "my", "our")) / n]


def surface():
    """Nearest-centroid on cheap features, leave-one-topic-out within family (S)."""
    import numpy as np
    arts = load_arts()
    rows = []
    for gen in GENERATORS:
        fam = [a for a in arts if a["generator"] == gen]
        topics = sorted({a["brief_id"] for a in fam})
        X = {a["case_id"]: np.array(surface_features(a["artifact_final"]))
             for a in fam}
        mu = np.mean([X[a["case_id"]] for a in fam], axis=0)
        sd = np.std([X[a["case_id"]] for a in fam], axis=0) + 1e-9
        for t in topics:
            train = [a for a in fam if a["brief_id"] != t]
            test = [a for a in fam if a["brief_id"] == t]
            cents = {r: np.mean([(X[a["case_id"]] - mu) / sd for a in train
                                 if a["route_family"] == r], axis=0)
                     for r in ROUTES}
            for a in test:
                z = (X[a["case_id"]] - mu) / sd
                pick = min(cents, key=lambda r: float(np.linalg.norm(z - cents[r])))
                rows.append({"case_id": a["case_id"], "truth": a["route_family"],
                             "pick": pick, "generator": gen})
    acc = sum(1 for r in rows if r["pick"] == r["truth"]) / max(len(rows), 1)
    out = {"arm": "surface", "n": len(rows), "accuracy": round(acc, 4),
           "features": "words, sent-length, type-token, paragraphs, first-person",
           "cv": "leave-one-topic-out within family"}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "surface.json").write_text(json.dumps({"summary": out, "rows": rows},
                                                 indent=1), encoding="utf-8",
                                      newline="\n")
    print(json.dumps(out, indent=1))


def verdict():
    from scipy.stats import binomtest
    import numpy as np
    events, arts = build_events(np)
    rows_of = lambda a: [json.loads(x) for x in                        # noqa: E731
                         (OUT / f"{a}_partial.jsonl").read_text(encoding="utf-8")
                         .splitlines()]
    out = {"prereg": "prereg/g166.py", "gates": {}, "verdict": {}}

    # P ceiling FIRST
    p_sum = json.loads((OUT / "process.json").read_text(encoding="utf-8"))
    p_pass = p_sum["accuracy"] >= 0.75
    out["gates"]["P_process_ceiling"] = {
        **p_sum, "pass": bool(p_pass),
        "rule": "arms below are UNINTERPRETED if this fails"}

    b_sum = json.loads((OUT / "blind.json").read_text(encoding="utf-8"))
    out["gates"]["B_context_floor"] = {**b_sum,
                                       "floor_used": max(b_sum["accuracy"], 0.2)}
    s_sum = json.loads((OUT / "surface.json").read_text(encoding="utf-8"))["summary"]
    out["gates"]["S_surface_baseline"] = s_sum

    def confusion(arm):
        rr = [r for r in rows_of(arm) if r["pick"] is not None]
        conf = {}
        for route in ROUTES:
            sel = [r for r in rr if r["route"] == route]
            row = {}
            for j, g in enumerate(ROUTES):
                row[g] = round(sum(1 for r in sel
                                   if events[r["i"]]["cands"][r["pick"]] ==
                                   DESCRIPTIONS[g]) / max(len(sel), 1), 4)
            row["cannot_tell"] = round(sum(1 for r in sel
                                           if r["pick"] == r["cannot_idx"])
                                       / max(len(sel), 1), 4)
            conf[route] = row
        return conf

    c_sum = json.loads((OUT / "classify.json").read_text(encoding="utf-8"))
    c, s = c_sum["accuracy"], s_sum["accuracy"]
    bt = binomtest(round(c * c_sum["n_parsed"]), c_sum["n_parsed"], 0.2,
                   alternative="greater")
    band = ("SEPARATES" if c >= 0.40 and (c - s) >= 0.10 else
            "PARTIAL" if (0.28 <= c < 0.40 and bt.pvalue < 0.05) or
                         (c >= 0.40 and (c - s) < 0.10) else "BLIND")
    out["verdict"]["route_recovery"] = {
        "artifact_only": c, "n": c_sum["n_parsed"],
        "p_vs_0.2": round(bt.pvalue, 5), "surface_baseline": s,
        "margin_over_surface": round(c - s, 4), "band": band,
        "interpreted": bool(p_pass),
        "power_note": "0.80-power detectable ~0.32 vs 0.2 at n=100 (card)"}
    out["confusion"] = {"classify": confusion("classify"),
                        "process": confusion("process")}
    _ = arts
    (OUT / "verdict.json").write_text(json.dumps(out, indent=1), encoding="utf-8",
                                     newline="\n")
    print(json.dumps({k: out[k] for k in ("gates", "verdict")}, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--arm", choices=["process", "classify", "blind"])
    ap.add_argument("--surface", action="store_true")
    ap.add_argument("--verdict", action="store_true")
    args = ap.parse_args()
    if args.gate:
        gate()
    elif args.arm:
        run_arm(args.arm)
    elif args.surface:
        surface()
    elif args.verdict:
        verdict()
    else:
        ap.error("pick a mode")


if __name__ == "__main__":
    main()
