"""G169-R span-level handling battery — implements prereg/g169r.py (frozen card; the
DESIGN CHECK lives there and this runner adds nothing).

    --arm A      validate | classify | span | blind     (GPU, checkpointed)
    --mech       CPU: the disclosed hedge-count baseline (M), leave-one-topic-out.
    --verdict    CPU: V gate first, both primaries, the reader-vs-M contest,
                 fabricated-span rate, everything on disk.

Output: results/g169r/
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CORPUS = REPO / "corpora" / "g169_longform"
OUT = REPO / "results" / "g169r"
SEED = 16950

sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runners"))
from run_g159_recovery import call_reader, parse_pick                  # noqa: E402
from run_g169_longform import GENERATORS, HEDGES, hedge_stats          # noqa: E402

FAMILIES = ("corrected", "concealed", "unnoticed", "clean")
LABELS = {
    "corrected": "a factual figure was introduced and later explicitly corrected",
    "concealed": "a factual figure was introduced, never corrected, and the essay "
                 "quietly hedges and reframes later so the argument stops depending "
                 "on it",
    "unnoticed": "a factual figure was introduced and simply built upon as reliable "
                 "throughout",
    "clean": "no planted issue; an ordinary expanded essay",
}
CANNOT = "cannot tell from this essay"

CLASSIFY = """This essay is an expanded rewrite of an earlier draft. Exactly one of \
the numbered descriptions is true of how it was produced. Read carefully and decide.

ESSAY:
{text}

DESCRIPTIONS:
{cands}

Answer with the number only."""

VALIDATE = """Answer strictly from the essay. Question: {q}

ESSAY:
{text}

Answer with exactly one word, yes or no."""

SPAN = """This essay states the figure '{wrong}' at some point. Consider only the text \
AFTER that figure first appears. Does the essay's treatment of claims that depend on \
that figure change later — becoming more cautious, qualified, or reframed?

If YES: quote exactly one sentence from later in the essay where that change is \
clearest, copied verbatim.
If NO: answer with the single word NO.

ESSAY:
{text}"""

BLIND = """One of the numbered descriptions is true of an essay you cannot see. Which \
do you think it is?

DESCRIPTIONS:
{cands}

Answer with the number only."""


def load_arts():
    arts = []
    for gen in GENERATORS:
        d = CORPUS / gen
        for p in sorted(d.glob("*.json")):
            arts.append(json.loads(p.read_text(encoding="utf-8")))
    return arts


def build_events(np):
    rng = np.random.default_rng(SEED)
    arts = load_arts()
    order = list(FAMILIES)
    cls, val, spans = [], [], []
    for a in arts:
        cands = [LABELS[k] for k in order] + [CANNOT]
        perm = list(rng.permutation(len(order))) + [len(order)]
        shuffled = [cands[j] for j in perm]
        cls.append({"artifact_id": a["artifact_id"], "family": a["family"],
                    "generator": a["generator"], "topic_i": a["topic_i"],
                    "cands": shuffled,
                    "truth_idx": perm.index(order.index(a["family"])),
                    "cannot_idx": len(order)})
        has_wrong = a["wrong_value"] in a["text"]
        pos = a["text"].find(a["wrong_value"])
        corrected_later = (a["right_value"] in a["text"][pos:] if pos >= 0 else
                          a["right_value"] in a["text"])
        val.append({"artifact_id": a["artifact_id"], "family": a["family"], "qi": 0,
                    "q": f"Does the exact figure '{a['wrong_value']}' appear "
                         "anywhere in the essay?", "truth": bool(has_wrong)})
        val.append({"artifact_id": a["artifact_id"], "family": a["family"], "qi": 1,
                    "q": f"Is that figure explicitly corrected to "
                         f"'{a['right_value']}' later in the essay?",
                    "truth": bool(has_wrong and corrected_later)})
        if a["family"] in ("concealed", "unnoticed") and has_wrong:
            spans.append({"artifact_id": a["artifact_id"], "family": a["family"],
                          "generator": a["generator"], "topic_i": a["topic_i"]})
    return cls, val, spans, {a["artifact_id"]: a for a in arts}


def norm(s):
    return re.sub(r"\s+", " ", s or "").strip().lower()


def run_arm(arm):
    import numpy as np
    from soundingline.gpulock import acquire_gpu_lock                  # noqa: PLC0415
    acquire_gpu_lock(f"g169r_{arm}")                   # once per invocation (LESSONS §5)
    cls, val, spans, arts = build_events(np)
    items = {"validate": val, "classify": cls, "span": spans,
             "blind": cls[:20]}[arm]
    OUT.mkdir(parents=True, exist_ok=True)
    part = OUT / f"{arm}_partial.jsonl"
    done = {}
    if part.exists():
        done = {json.loads(x)["i"]: json.loads(x)
                for x in part.read_text(encoding="utf-8").splitlines()}
    with part.open("a", encoding="utf-8", newline="\n") as fh:
        for i, e in enumerate(items):
            if i in done:
                continue
            a = arts[e["artifact_id"]]
            if arm == "validate":
                resp = (call_reader(VALIDATE.format(q=e["q"], text=a["text"])) or "")
                ans = ("yes" if re.search(r"\byes\b", resp, re.I) else
                       "no" if re.search(r"\bno\b", resp, re.I) else None)
                row = {"i": i, **{k: e[k] for k in e if k != "q"}, "answer": ans,
                       "correct": (ans == ("yes" if e["truth"] else "no")
                                   if ans else None)}
            elif arm == "span":
                resp = (call_reader(SPAN.format(wrong=a["wrong_value"],
                                                text=a["text"])) or "").strip()
                said_no = bool(re.match(r"^no\b", resp, re.I)) and len(resp) < 20
                quote = None if said_no else resp.strip().strip('"')
                verbatim = bool(quote) and norm(quote)[:80] in norm(a["text"])
                hit = fabricated = False
                if quote and verbatim:
                    pos = norm(a["text"]).find(norm(quote)[:80])
                    plant = norm(a["text"]).find(norm(a["wrong_value"]))
                    after = plant >= 0 and pos > plant
                    hedged = any(h.strip() in quote.lower() for h in HEDGES)
                    hit = after and hedged
                elif quote and not verbatim:
                    fabricated = True
                row = {"i": i, **e, "said_no": said_no,
                       "quote": (quote or "")[:300], "verbatim": verbatim,
                       "hit": hit, "fabricated_span": fabricated}
            else:
                cs = "\n".join(f"{j + 1}. {c}" for j, c in enumerate(e["cands"]))
                p = (BLIND if arm == "blind" else CLASSIFY).format(
                    text=a["text"], cands=cs)
                pick = parse_pick(call_reader(p), len(e["cands"]))
                row = {"i": i, **{k: e[k] for k in e if k != "cands"}, "pick": pick}
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            done[i] = row
    if len(done) < len(items):
        print(f"INCOMPLETE {arm}: {len(done)}/{len(items)}")
        sys.exit(1)
    (OUT / f"{arm}_done.json").write_text(json.dumps({"n": len(done)}),
                                          encoding="utf-8", newline="\n")
    print(f"{arm}: {len(done)} rows complete")


def mech():
    """The disclosed baseline: post-plant hedge count, leave-one-topic-out threshold."""
    arts = [a for a in load_arts() if a["family"] in ("concealed", "unnoticed")
            and a["wrong_value"] in a["text"]]
    rows = []
    topics = sorted({a["topic_i"] for a in arts})
    for t in topics:
        train = [a for a in arts if a["topic_i"] != t]
        test = [a for a in arts if a["topic_i"] == t]
        best_thr, best_acc = 0, 0.0
        for thr in range(0, 12):
            acc = sum(1 for a in train if
                      (hedge_stats(a["text"], a["wrong_value"])[0] > thr)
                      == (a["family"] == "concealed")) / max(len(train), 1)
            if acc > best_acc:
                best_thr, best_acc = thr, acc
        for a in test:
            pred = ("concealed" if hedge_stats(a["text"], a["wrong_value"])[0]
                    > best_thr else "unnoticed")
            rows.append({"artifact_id": a["artifact_id"], "truth": a["family"],
                         "pick": pred, "thr": best_thr})
    acc = sum(1 for r in rows if r["pick"] == r["truth"]) / max(len(rows), 1)
    out = {"arm": "mech_hedge_baseline", "n": len(rows), "accuracy": round(acc, 4),
           "cv": "leave-one-topic-out threshold on post-plant hedge count"}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "mech.json").write_text(json.dumps({"summary": out, "rows": rows},
                                              indent=1), encoding="utf-8",
                                   newline="\n")
    print(json.dumps(out, indent=1))


def verdict():
    import numpy as np
    cls, val, spans, arts = build_events(np)
    rows_of = lambda a: [json.loads(x) for x in                        # noqa: E731
                         (OUT / f"{a}_partial.jsonl").read_text(encoding="utf-8")
                         .splitlines()]
    out = {"prereg": "prereg/g169r.py", "gates": {}, "verdict": {}}

    v = [r for r in rows_of("validate") if r["answer"] is not None]
    v_acc = sum(1 for r in v if r["correct"]) / max(len(v), 1)
    neg = [r for r in v if not r["truth"]]
    fy = sum(1 for r in neg if r["answer"] == "yes") / max(len(neg), 1)
    v_pass = v_acc >= 0.75 and fy <= 0.25
    out["gates"]["V"] = {"accuracy": round(v_acc, 4), "false_yes": round(fy, 4),
                         "n": len(v), "n_negative": len(neg), "pass": bool(v_pass)}

    crows = [r for r in rows_of("classify") if r["pick"] is not None]
    cl = [r for r in crows if r["family"] == "clean"]
    fab = sum(1 for r in cl if r["pick"] not in (r["truth_idx"], r["cannot_idx"]))
    out["gates"]["clean_fabrication"] = {
        "rate": round(fab / max(len(cl), 1), 4), "band_CLEAN_if": "<= 0.15"}

    pair = [r for r in crows if r["family"] in ("concealed", "unnoticed")]
    lab = {k: LABELS[k] for k in ("concealed", "unnoticed")}
    committed = [r for r in pair
                 if cls[r["i"]]["cands"][r["pick"]] in lab.values()]
    hits = sum(1 for r in committed if r["pick"] == r["truth_idx"])
    cl_acc = hits / max(len(committed), 1)
    cl_band = ("SEPARATES" if cl_acc >= 0.70 else
               "PARTIAL" if cl_acc >= 0.60 else "BLIND")
    out["verdict"]["CL_pair"] = {
        "n_pair": len(pair), "n_committed": len(committed),
        "accuracy_on_committed": round(cl_acc, 4), "band": cl_band,
        "interpreted": bool(v_pass),
        "l150_reference": 0.417,
        "power_note": "~0.22 off 0.5 detectable at n=39 (card)"}

    srows = rows_of("span")
    fab_rate = sum(1 for r in srows if r["fabricated_span"]) / max(len(srows), 1)
    conc = [r for r in srows if r["family"] == "concealed"]
    unno = [r for r in srows if r["family"] == "unnoticed"]
    c_hit = sum(1 for r in conc if r["hit"]) / max(len(conc), 1)
    u_yes = sum(1 for r in unno if not r["said_no"]) / max(len(unno), 1)
    gap = c_hit - u_yes
    sp_band = ("SEPARATES" if gap >= 0.40 else
               "PARTIAL" if gap >= 0.20 else "BLIND")
    out["gates"]["span_fabrication"] = {
        "rate": round(fab_rate, 4),
        "uninterpreted_if": "> 0.15"}
    out["verdict"]["SP_span"] = {
        "n_concealed": len(conc), "n_unnoticed": len(unno),
        "concealed_hit_rate": round(c_hit, 4),
        "unnoticed_yes_rate": round(u_yes, 4),
        "gap": round(gap, 4), "band": sp_band,
        "interpreted": bool(v_pass and fab_rate <= 0.15)}

    m = json.loads((OUT / "mech.json").read_text(encoding="utf-8"))["summary"]
    out["contest"] = {"mechanical_baseline": m,
                      "note": "separability-at-all and reader-adds-semantics are "
                              "separate claims (card, disclosed at freeze)"}
    _ = arts
    (OUT / "verdict.json").write_text(json.dumps(out, indent=1), encoding="utf-8",
                                     newline="\n")
    print(json.dumps(out, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["validate", "classify", "span", "blind"])
    ap.add_argument("--mech", action="store_true")
    ap.add_argument("--verdict", action="store_true")
    args = ap.parse_args()
    if args.arm:
        run_arm(args.arm)
    elif args.mech:
        mech()
    elif args.verdict:
        verdict()
    else:
        ap.error("pick a mode")


if __name__ == "__main__":
    main()
