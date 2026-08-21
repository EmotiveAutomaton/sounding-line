"""G165 reader-ablation ruler — implements prereg/g165.py (frozen card; the DESIGN
CHECK lives there and this runner adds nothing).

    --gate       CPU: pipeline-purity (exact-equivalence) + anchor check. Runs FIRST;
                 every GPU arm needs its produce.
    --arm X      self_route | cand_disc | self_route_leak | cand_disc_leak   (GPU,
                 checkpointed, gpu lock once per invocation)
    --verdict    CPU: paired McNemar vs the recorded direct picks, bands, leak gate,
                 echo cells, everything on disk.

Output: results/g165/  (gate.json, per-arm partials + summaries, verdict.json)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
G159 = REPO / "results" / "g159"
OUT = REPO / "results" / "g165"
OLLAMA = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen3.5:9b"
DECODING = {"temperature": 0.0, "num_predict": 260}
SEED = 16500
LEAK_N = 50

sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runners"))
from run_g159_recovery import (                                        # noqa: E402
    call_reader, content_words, echo_score, load_arts, parse_pick)

ROUTE = """Read this essay. Describe, as exactly three numbered production decisions, \
how you yourself would have produced it: what to argue, how to structure it, what to \
emphasize. Do not quote the essay. Three short numbered lines only.

ESSAY:
{text}"""

PICK_SR = """This essay was rewritten following exactly one of the numbered revision \
instructions below. You previously reconstructed how you would have produced it:

YOUR ROUTE:
{route}

Now read the essay and decide which instruction was applied.

ESSAY:
{text}

INSTRUCTIONS:
{cands}

Answer with the number only."""

EVIDENCE = """If an essay were rewritten following the instruction below, name the \
single most specific visible feature the rewrite would show. One sentence only.

INSTRUCTION: {cand}"""

PICK_CD = """This essay was rewritten following exactly one of the numbered revision \
instructions below. Beside each instruction is a prediction of what the rewrite would \
show if that instruction had been applied. Read the essay and decide which instruction \
was applied.

ESSAY:
{text}

INSTRUCTIONS:
{cands}

Answer with the number only."""


def load_manifest():
    return json.loads((G159 / "manifest.json").read_text(encoding="utf-8"))


def leak_subsample(events):
    import numpy as np
    rng = np.random.default_rng(SEED)
    idx = sorted(rng.choice(len(events), size=LEAK_N, replace=False).tolist())
    return [events[i] | {"src_i": i} for i in idx]


def events_for(arm):
    man = load_manifest()
    if arm in ("self_route", "cand_disc"):
        return man["p_plus"]
    return leak_subsample(man["p_minus"])


def sr_prompts(e, art, route=None):
    cs = "\n".join(f"{j + 1}. {c}" for j, c in enumerate(e["cands"]))
    if route is None:
        return ROUTE.format(text=art["text"])
    return PICK_SR.format(route=route, text=art["text"], cands=cs)


def cd_pick_prompt(e, art, ev_by_cand):
    cs = "\n".join(f"{j + 1}. {c}\n   predicted: {ev_by_cand[c]}"
                   for j, c in enumerate(e["cands"]))
    return PICK_CD.format(text=art["text"], cands=cs)


def gate():
    """Pipeline purity: prompts are byte-pure functions of (text, candidates). Permute
    every hidden manifest field and assert the prompt hashes do not move. Plus the
    anchor check. CPU only, runs before any GPU arm."""
    arts = load_arts()
    man = load_manifest()
    defects = []
    h = lambda s: hashlib.sha256(s.encode()).hexdigest()               # noqa: E731
    for e in man["p_plus"][:20] + man["p_minus"][:20]:
        art = arts[(e["family"], e["artifact_id"])]
        hidden_permuted = {**e, "family": "xx", "amount": 99,
                           "artifact_id": "zz_00", "truth_idx": -1, "topic_i": -1}
        for build in (lambda ev: sr_prompts(ev, art),
                      lambda ev: sr_prompts(ev, art, route="R"),
                      lambda ev: cd_pick_prompt(ev, art,
                                                {c: "E" for c in ev["cands"]})):
            if h(build(e)) != h(build(hidden_permuted)):
                defects.append(e["artifact_id"])
                break
    anchor = json.loads((G159 / "p_plus.json").read_text(encoding="utf-8"))
    anchor_ok = anchor["accuracy"] >= 0.80 and anchor["n_parsed"] >= 90
    out = {"prereg": "prereg/g165.py",
           "pipeline_purity": {"events_checked": 40, "defects": defects,
                               "pass": not defects},
           "anchor": {"recorded_direct_accuracy": anchor["accuracy"],
                      "n_parsed": anchor["n_parsed"], "pass": bool(anchor_ok)}}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "gate.json").write_text(json.dumps(out, indent=1), encoding="utf-8",
                                   newline="\n")
    print(json.dumps(out, indent=1))
    if defects or not anchor_ok:
        sys.exit(1)


def run_arm(arm):
    from soundingline.gpulock import acquire_gpu_lock                  # noqa: PLC0415
    acquire_gpu_lock(f"g165_{arm}")                    # once per invocation (LESSONS §5)
    arts = load_arts()
    events = events_for(arm)
    mode = "self_route" if arm.startswith("self_route") else "cand_disc"
    OUT.mkdir(parents=True, exist_ok=True)
    part = OUT / f"{arm}_partial.jsonl"
    done = {}
    if part.exists():
        done = {json.loads(x)["i"]: json.loads(x)
                for x in part.read_text(encoding="utf-8").splitlines()}

    # candidate-evidence cache (temperature 0: one call per unique instruction string)
    ev_cache_path = OUT / "evidence_cache.json"
    ev_cache = (json.loads(ev_cache_path.read_text(encoding="utf-8"))
                if ev_cache_path.exists() else {})

    def evidence_for(cand):
        if cand not in ev_cache:
            ev_cache[cand] = (call_reader(EVIDENCE.format(cand=cand)) or "").strip() \
                or "(no prediction)"
            ev_cache_path.write_text(json.dumps(ev_cache, indent=1), encoding="utf-8",
                                     newline="\n")
        return ev_cache[cand]

    with part.open("a", encoding="utf-8", newline="\n") as fh:
        for i, e in enumerate(events):
            if i in done:
                continue
            art = arts[(e["family"], e["artifact_id"])]
            if mode == "self_route":
                route = (call_reader(sr_prompts(e, art)) or "").strip()
                pick = parse_pick(call_reader(sr_prompts(e, art, route=route)),
                                  len(e["cands"]))
                gen_text = route
            else:
                ev_by_cand = {c: evidence_for(c) for c in e["cands"]}
                pick = parse_pick(call_reader(cd_pick_prompt(e, art, ev_by_cand)),
                                  len(e["cands"]))
                gen_text = " ".join(ev_by_cand[c] for c in e["cands"])
            row = {"i": i, **{k: e[k] for k in e if k != "cands"},
                   "n_cands": len(e["cands"]), "pick": pick, "gen_text": gen_text}
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


def verdict():
    from scipy.stats import binomtest
    man = load_manifest()
    arts = load_arts()
    direct = {json.loads(x)["i"]: json.loads(x) for x in
              (G159 / "p_plus_partial.jsonl").read_text(encoding="utf-8").splitlines()}
    rows_of = lambda a: [json.loads(x) for x in                        # noqa: E731
                         (OUT / f"{a}_partial.jsonl").read_text(encoding="utf-8")
                         .splitlines()]
    out = {"prereg": "prereg/g165.py", "gates": {}, "verdict": {},
           "recorded_baselines": {"direct": 0.86, "context_only_floor": 0.32}}

    # leak gate first (guarded direction UP)
    for arm in ("self_route_leak", "cand_disc_leak"):
        rows = [r for r in rows_of(arm) if r["pick"] is not None]
        acc = sum(1 for r in rows if r["pick"] == r["truth_idx"]) / max(len(rows), 1)
        bt = binomtest(sum(1 for r in rows if r["pick"] == r["truth_idx"]),
                       len(rows), 0.25, alternative="greater")
        out["gates"][arm] = {"accuracy": round(acc, 4), "n": len(rows),
                             "expectations": "null=0.25 (nothing executed); "
                                             "alternative=UP (leak)",
                             "p_above_floor": round(bt.pvalue, 5),
                             "void_if": "one-sided p < 0.05",
                             "void": bool(bt.pvalue < 0.05)}
    leak_void = any(out["gates"][a]["void"]
                    for a in ("self_route_leak", "cand_disc_leak"))

    # primary: paired McNemar vs recorded direct picks, and echo cells (L148 standing)
    for arm in ("self_route", "cand_disc"):
        rows = {r["i"]: r for r in rows_of(arm)}
        b = c = both = neither = n_pair = 0
        echo_cells = {"gen_echo_right": [], "gen_echo_wrong": []}
        for i, e in enumerate(man["p_plus"]):
            r, d = rows.get(i), direct.get(i)
            if not r or not d or r["pick"] is None or d["pick"] is None:
                continue
            n_pair += 1
            new_hit = r["pick"] == e["truth_idx"]
            dir_hit = d["pick"] == e["truth_idx"]
            b += (new_hit and not dir_hit)
            c += (dir_hit and not new_hit)
            both += (new_hit and dir_hit)
            neither += (not new_hit and not dir_hit)
            gw = content_words(r.get("gen_text", ""))
            scores = [echo_score(cand, gw) for cand in e["cands"]]
            cell = ("gen_echo_right" if scores.index(max(scores)) == e["truth_idx"]
                    else "gen_echo_wrong")
            echo_cells[cell].append(new_hit)
        acc = (b + both) / max(n_pair, 1)
        delta = acc - (c + both) / max(n_pair, 1)
        mc = binomtest(b, b + c, 0.5) if (b + c) else None
        p = round(mc.pvalue, 5) if mc else 1.0
        band = ("HELPS" if delta >= 0.05 and p < 0.05 else
                "HURTS" if delta <= -0.05 and p < 0.05 else "NO-GAIN")
        out["verdict"][arm] = {
            "n_paired": n_pair, "accuracy": round(acc, 4),
            "delta_vs_direct": round(delta, 4),
            "discordant": {"new_only_right": b, "direct_only_right": c},
            "mcnemar_p": p, "band": band, "interpreted": (not leak_void),
            "below_context_floor": bool(acc < 0.32),
            "echo_cells": {k: {"n": len(v),
                               "accuracy": round(sum(v) / max(len(v), 1), 4)}
                           for k, v in echo_cells.items()},
            "power_note": "0.80-power detectable delta ~0.10 at n=100 (card)"}
    out["gates"]["leak_voids_positives"] = bool(leak_void)
    _ = arts
    (OUT / "verdict.json").write_text(json.dumps(out, indent=1), encoding="utf-8",
                                     newline="\n")
    print(json.dumps(out, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--arm", choices=["self_route", "cand_disc", "self_route_leak",
                                      "cand_disc_leak"])
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
    _ = time                                            # retained: backoff lives in caller


if __name__ == "__main__":
    main()
