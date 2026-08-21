"""G165-D discriminator — implements prereg/g165d.py (frozen card; DESIGN CHECK lives
there and this runner adds nothing). The same route-generation ablation as the G165
root, run where direct reading is weak: the frozen G129b delta events, paired to the
recorded recovery picks.

    --gate       CPU: pipeline purity + anchor. Runs first; arms gate on its produce.
    --arm X      sr_delta | cd_delta | sr_unchanged      (GPU, checkpointed)
    --verdict    CPU: paired McNemar vs recorded picks, bands, fabrication gate,
                 gap-closure vs the change block, everything on disk.

Output: results/g165d/
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
G129B = REPO / "results" / "g129b"
OUT = REPO / "results" / "g165d"
SEED = 16550

sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runners"))
import run_g129_confirm as g129                                        # noqa: E402

g129.set_card("b")
ask = g129.ask
delta_text = g129.delta_text
BRIEF = g129.BRIEF
NO_REV = g129.NO_REV

ROUTE_P = ("A student revised one sentence of an argumentative essay.\n"
           "THE ASSIGNMENT: {brief}\n{delta}\n"
           "In exactly two short numbered lines, describe how YOU would have made this "
           "revision and why. Do not name a category; describe the editing decisions.")

PICK_SR = ("A student revised one sentence of an argumentative essay.\n"
           "Your own reconstruction of the editing decisions:\n{route}\n{delta}\n"
           "Which revision purpose fits best? Answer with exactly one label "
           "from:\n{opts}\nLabel:")

EVIDENCE_P = ("If a student revised one sentence of an argumentative essay with the "
              "purpose '{label}', what is the single most specific visible change the "
              "revision would show? One short sentence.")

PICK_CD = ("A student revised one sentence of an argumentative essay.\n{delta}\n"
           "Candidate purposes, each with a prediction of what that purpose would "
           "look like:\n{opts_ev}\n"
           "Which revision purpose fits best? Answer with exactly one label "
           "from:\n{opts}\nLabel:")


def manifest():
    return json.loads((G129B / "manifest.json").read_text(encoding="utf-8"))


def recorded_picks(arm_file):
    return {json.loads(x)["i"]: json.loads(x) for x in
            (G129B / arm_file).read_text(encoding="utf-8").splitlines()}


def gate():
    man = manifest()
    h = lambda s: hashlib.sha256(s.encode()).hexdigest()               # noqa: E731
    defects = []
    for e, cands in list(zip(man["full"]["events"], man["full"]["cands"]))[:20]:
        opts = "\n".join(f"- {l}" for l in cands)
        perm = {**e, "author": "xx", "cycle": "99", "fine": "zz", "coarse": "zz"}
        for build in (lambda ev: ROUTE_P.format(brief=BRIEF, delta=delta_text(ev)),
                      lambda ev: PICK_SR.format(route="R", delta=delta_text(ev),
                                                opts=opts)):
            if h(build(e)) != h(build(perm)):
                defects.append(e.get("cycle", "?"))
                break
    rec = json.loads((G129B / "recovery.json").read_text(encoding="utf-8"))
    anchor_ok = abs(rec["accuracy"] - 0.4805) < 1e-6 and rec["n"] == 616
    out = {"prereg": "prereg/g165d.py",
           "pipeline_purity": {"events_checked": 20, "defects": defects,
                               "pass": not defects},
           "anchor": {"recorded_recovery": rec["accuracy"], "n": rec["n"],
                      "pass": bool(anchor_ok)}}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "gate.json").write_text(json.dumps(out, indent=1), encoding="utf-8",
                                   newline="\n")
    print(json.dumps(out, indent=1))
    if defects or not anchor_ok:
        sys.exit(1)


def run_arm(arm):
    import numpy as np
    from soundingline.gpulock import acquire_gpu_lock                  # noqa: PLC0415
    acquire_gpu_lock(f"g165d_{arm}")                   # once per invocation (LESSONS §5)
    man = manifest()
    rng = np.random.default_rng(SEED)
    if arm == "sr_unchanged":
        events = man["unchanged"]["events"]
        cands_all = man["unchanged"]["cands"]
    else:
        events = man["full"]["events"]
        cands_all = man["full"]["cands"]

    OUT.mkdir(parents=True, exist_ok=True)
    part = OUT / f"{arm}_partial.jsonl"
    done = set()
    if part.exists():
        done = {json.loads(x)["i"] for x in
                part.read_text(encoding="utf-8").splitlines()}

    ev_cache_path = OUT / "evidence_cache.json"
    ev_cache = (json.loads(ev_cache_path.read_text(encoding="utf-8"))
                if ev_cache_path.exists() else {})

    def evidence_for(label, seed):
        if label not in ev_cache:
            ev_cache[label] = (ask(EVIDENCE_P.format(label=label), seed) or
                               "(no prediction)")
            ev_cache_path.write_text(json.dumps(ev_cache, indent=1), encoding="utf-8",
                                     newline="\n")
        return ev_cache[label]

    with part.open("a", encoding="utf-8", newline="\n") as fh:
        for i, (e, cands) in enumerate(zip(events, cands_all)):
            if i in done:
                continue
            opts = "\n".join(f"- {l}" for l in cands)
            dtx = delta_text(e)
            gen_text = ""
            if arm.startswith("sr"):
                # route generation needs room; ask() caps num_predict at 30, which
                # would truncate the route and defeat the arm
                gen_text = _ask_long(ROUTE_P.format(brief=BRIEF, delta=dtx),
                                     seed=SEED + i)
                ans = ask(PICK_SR.format(route=gen_text, delta=dtx, opts=opts),
                          seed=SEED + 500000 + i).lower()
            else:
                ev_lines = "\n".join(
                    f"- {l}: {evidence_for(l, SEED + 900000 + j)}"
                    for j, l in enumerate(cands))
                ans = ask(PICK_CD.format(delta=dtx, opts_ev=ev_lines, opts=opts),
                          seed=SEED + 600000 + i).lower()
                gen_text = ev_lines
            got = [l for l in cands if l in ans]
            pick = got[0] if len(got) == 1 else str(rng.choice(got or cands))
            truth = e.get("fine") if arm != "sr_unchanged" else NO_REV
            fh.write(json.dumps({"i": i, "truth": truth, "pick": pick,
                                 "gen_len": len(gen_text.split())}) + "\n")
            fh.flush()
            done.add(i)
    if len(done) < len(events):
        print(f"INCOMPLETE {arm}: {len(done)}/{len(events)}")
        sys.exit(1)
    rows = [json.loads(x) for x in part.read_text(encoding="utf-8").splitlines()]
    if arm == "sr_unchanged":
        fab = sum(1 for r in rows if r["pick"] != NO_REV) / max(len(rows), 1)
        summary = {"arm": arm, "n": len(rows), "fabrication_rate": round(fab, 4)}
    else:
        acc = sum(1 for r in rows if r["pick"] == r["truth"]) / max(len(rows), 1)
        summary = {"arm": arm, "n": len(rows), "accuracy": round(acc, 4)}
    (OUT / f"{arm}.json").write_text(json.dumps(summary, indent=1), encoding="utf-8",
                                     newline="\n")
    print(json.dumps(summary, indent=1))


def _ask_long(prompt, seed):
    """ask() with a route-sized token budget; same retry contract."""
    import json as _json
    import re as _re
    import time as _time
    import urllib.request as _rq
    req = _rq.Request(g129.OLLAMA, data=_json.dumps(
        {"model": g129.MODEL, "prompt": prompt, "stream": False, "think": False,
         "options": {"temperature": 0.0, "seed": seed,
                     "num_predict": 140}}).encode(),
        headers={"Content-Type": "application/json"})
    for attempt in range(6):
        try:
            with _rq.urlopen(req, timeout=300) as r:
                resp = _json.loads(r.read()).get("response", "")
            return _re.sub(r"<think>.*?</think>", "", resp,
                           flags=_re.DOTALL).strip()
        except Exception:                                             # noqa: BLE001
            if attempt == 5:
                raise
            _time.sleep(20 * (attempt + 1))
    return ""


def verdict():
    from scipy.stats import binomtest
    man = manifest()
    direct = recorded_picks("recovery_partial.jsonl")
    out = {"prereg": "prereg/g165d.py", "gates": {}, "verdict": {},
           "references": {"direct": 0.4805, "change_block": 0.5471}}

    fabj = json.loads((OUT / "sr_unchanged.json").read_text(encoding="utf-8"))
    fab = fabj["fabrication_rate"]
    out["gates"]["sr_unchanged_fabrication"] = {
        "rate": fab, "n": fabj["n"],
        "expectations": "null ~0.00 (direct recorded twice); alternative UP",
        "band": ("CLEAN" if fab <= 0.05 else
                 "WARNING" if fab <= 0.15 else "SR-UNINTERPRETED")}

    for arm in ("sr_delta", "cd_delta"):
        rows = {json.loads(x)["i"]: json.loads(x) for x in
                (OUT / f"{arm}_partial.jsonl").read_text(encoding="utf-8")
                .splitlines()}
        b = c = n_pair = hits = dir_hits = 0
        for i, e in enumerate(man["full"]["events"]):
            r, d = rows.get(i), direct.get(i)
            if not r or not d:
                continue
            n_pair += 1
            new_hit = r["pick"] == r["truth"]
            dir_hit = d["pick"] == d["truth"]
            hits += new_hit
            dir_hits += dir_hit
            b += (new_hit and not dir_hit)
            c += (dir_hit and not new_hit)
        acc = hits / max(n_pair, 1)
        delta = acc - dir_hits / max(n_pair, 1)
        mc = binomtest(b, b + c, 0.5) if (b + c) else None
        p = round(mc.pvalue, 5) if mc else 1.0
        band = ("CONTRIBUTES" if delta >= 0.04 and p < 0.05 else
                "HURTS" if delta <= -0.04 and p < 0.05 else "NO-GAIN")
        if arm == "sr_delta" and fab > 0.15:
            band = "SR-UNINTERPRETED (fabrication gate)"
        out["verdict"][arm] = {
            "n_paired": n_pair, "accuracy": round(acc, 4),
            "delta_vs_direct": round(delta, 4),
            "discordant": {"new_only_right": b, "direct_only_right": c},
            "mcnemar_p": p, "band": band,
            "vs_change_block": round(acc - 0.5471, 4),
            "power_note": "0.80-power detectable delta ~0.05 at n=616 (card)"}
    (OUT / "verdict.json").write_text(json.dumps(out, indent=1), encoding="utf-8",
                                     newline="\n")
    print(json.dumps(out, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--arm", choices=["sr_delta", "cd_delta", "sr_unchanged"])
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
