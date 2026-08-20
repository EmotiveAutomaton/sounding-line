"""G162-R reading battery — implements prereg/g162.py (frozen card; DESIGN CHECK lives
there and this runner adds nothing).

    --arm X     validate | classify | classify_delta | blind      (GPU, checkpointed)
    --verdict   scores everything: V gate first, per-class confusion, echo bar and
                echo-split cells, mechanical oracle, the primary pair band.

Output: results/g162/  (per-arm partials + summaries, verdict.json)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CORPUS = REPO / "corpora" / "g162_anomaly"
OUT = REPO / "results" / "g162"
OLLAMA = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen3.5:9b"
DECODING = {"temperature": 0.0, "num_predict": 250}
SEED = 16250

sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runners"))
from run_g162_gen import FAMILIES, REFRAIN, load_base                  # noqa: E402

LABELS = {
    "corrected": "an error was introduced and later explicitly corrected",
    "concealed": "an error was introduced and never corrected, but the essay quietly "
                 "reframes so it no longer depends on it",
    "unnoticed": "an error was introduced and simply built upon as if true",
    "repeated": "the same error was introduced several times",
    "deliberate": "an unusual construction is used deliberately as a rhetorical device",
    "clean": "no planted issue; an ordinary rewrite",
}
CANNOT = "cannot tell from this essay"


def call_reader(prompt):
    req = urllib.request.Request(OLLAMA, data=json.dumps(
        {"model": MODEL, "prompt": prompt, "stream": False, "think": False,
         "options": DECODING}).encode(), headers={"Content-Type": "application/json"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                resp = json.loads(r.read()).get("response", "")
            return re.sub(r"<think>.*?</think>", "", resp, flags=re.DOTALL).strip()
        except Exception as e:                                        # noqa: BLE001
            print(f"  call failed (attempt {attempt + 1}): {e}")
            time.sleep(20 * (attempt + 1))
    return None


def parse_pick(resp, n):
    if not resp:
        return None
    m = re.search(r"\b([1-9])\b", resp)
    if m and 1 <= int(m.group(1)) <= n:
        return int(m.group(1)) - 1
    return None


CLASSIFY = """This essay is a rewrite of an earlier draft. Exactly one of the numbered \
descriptions is true of how it was produced. Read carefully and decide.

ESSAY:
{text}

DESCRIPTIONS:
{cands}

Answer with the number only."""

CLASSIFY_D = """This is an ORIGINAL essay and its REWRITE. Exactly one of the numbered \
descriptions is true of how the rewrite was produced. Compare them and decide.

ORIGINAL:
{base}

REWRITE:
{text}

DESCRIPTIONS:
{cands}

Answer with the number only."""

BLIND = """One of the numbered descriptions is true of an essay you cannot see. Which \
do you think it is?

DESCRIPTIONS:
{cands}

Answer with the number only."""

VALIDATE = """Answer strictly from the essay. Question: {q}

ESSAY:
{text}

Answer with exactly one word, yes or no."""


def load_arts():
    arts = []
    for fam in FAMILIES:
        for p in sorted((CORPUS / fam).glob("*.json")):
            arts.append(json.loads(p.read_text(encoding="utf-8")))
    return arts


def build_events(np):
    rng = np.random.default_rng(SEED)
    arts = load_arts()
    order = list(LABELS)
    events, val = [], []
    for a in arts:
        cands = [LABELS[k] for k in order] + [CANNOT]
        perm = list(rng.permutation(len(order))) + [len(order)]
        shuffled = [cands[j] for j in perm]
        truth_idx = perm.index(order.index(a["family"]))
        ti = int(a["artifact_id"].split("_")[-1])
        events.append({"artifact_id": a["artifact_id"], "family": a["family"],
                       "generator": a["generator"], "topic_i": ti,
                       "cands": shuffled, "truth_idx": truth_idx,
                       "cannot_idx": len(order)})
        # validation questions, negative-class-heavy: one true-answer and one
        # false-answer question per artifact, mechanically decidable
        wrong, right = a["wrong_value"], a["right_value"]
        has_wrong = wrong in a["text"]
        has_right = right in a["text"]
        has_refrain = a["text"].count(REFRAIN) >= 3
        qs = [(f"Does the exact figure '{wrong}' appear anywhere in the essay?",
               has_wrong),
              (f"Does the exact figure '{right}' appear anywhere in the essay?",
               has_right),
              (f"Does the exact sentence '{REFRAIN}' appear three or more times?",
               has_refrain)]
        for qi, (q, truth) in enumerate(qs):
            val.append({"artifact_id": a["artifact_id"], "family": a["family"],
                        "qi": qi, "q": q, "truth": bool(truth)})
    return events, val, {a["artifact_id"]: a for a in arts}


def run_arm(arm):
    import numpy as np
    from soundingline.gpulock import acquire_gpu_lock                  # noqa: PLC0415
    acquire_gpu_lock(f"g162r_{arm}")                   # once per invocation (LESSONS §5)
    events, val, arts = build_events(np)
    OUT.mkdir(parents=True, exist_ok=True)
    part = OUT / f"{arm}_partial.jsonl"
    done = {}
    if part.exists():
        done = {json.loads(x)["i"]: json.loads(x)
                for x in part.read_text(encoding="utf-8").splitlines()}
    items = val if arm == "validate" else events
    with part.open("a", encoding="utf-8", newline="\n") as fh:
        for i, e in enumerate(items):
            if i in done:
                continue
            a = arts[e["artifact_id"]]
            if arm == "validate":
                resp = (call_reader(VALIDATE.format(q=e["q"], text=a["text"])) or "")
                ans = ("yes" if re.search(r"\byes\b", resp, re.I) else
                       "no" if re.search(r"\bno\b", resp, re.I) else None)
                row = {"i": i, **{k: e[k] for k in e if k != "q"},
                       "answer": ans, "correct": (ans == ("yes" if e["truth"] else "no")
                                                  if ans else None)}
            else:
                cs = "\n".join(f"{j + 1}. {c}" for j, c in enumerate(e["cands"]))
                if arm == "classify":
                    p = CLASSIFY.format(text=a["text"], cands=cs)
                elif arm == "classify_delta":
                    p = CLASSIFY_D.format(base=load_base(e["generator"],
                                                         e["topic_i"])["text"],
                                          text=a["text"], cands=cs)
                else:
                    p = BLIND.format(cands=cs)
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


def verdict():
    import numpy as np
    events, val, arts = build_events(np)
    rows = lambda a: [json.loads(x) for x in                            # noqa: E731
                      (OUT / f"{a}_partial.jsonl").read_text(encoding="utf-8").splitlines()]
    out = {"prereg": "prereg/g162.py", "gates": {}, "verdict": {}}

    # V gate FIRST
    v = [r for r in rows("validate") if r["answer"] is not None]
    v_acc = sum(1 for r in v if r["correct"]) / max(len(v), 1)
    neg = [r for r in v if not r["truth"]]
    false_yes = sum(1 for r in neg if r["answer"] == "yes") / max(len(neg), 1)
    v_pass = v_acc >= 0.75 and false_yes <= 0.25
    out["gates"]["V_validation_first"] = {
        "accuracy": round(v_acc, 4), "false_yes_rate": round(false_yes, 4),
        "n": len(v), "n_negative": len(neg),
        "pass": bool(v_pass),
        "rule": "semantic arms below are UNINTERPRETED if this fails"}

    # mechanical oracle wiring: string tests recover the four decidable families
    orc_bad = 0
    for e in events:
        a = arts[e["artifact_id"]]
        w, rt = a["wrong_value"] in a["text"], a["right_value"] in a["text"]
        rep = a["text"].count(a["wrong_value"]) >= 3
        refr = a["text"].count(REFRAIN) >= 3
        mech = ("deliberate" if refr else "repeated" if rep else
                "corrected" if (w and rt) else None if w else "clean")
        if a["family"] in ("corrected", "repeated", "deliberate", "clean") and \
                a["family"] != mech and (a["wrong_value"] in a["text"]
                                         or a["family"] in ("deliberate", "clean")):
            orc_bad += 1
    out["gates"]["mechanical_oracle_disagreements"] = orc_bad

    def table(arm):
        rr = [r for r in rows(arm) if r["pick"] is not None]
        conf = {}
        for f in FAMILIES:
            sel = [r for r in rr if r["family"] == f]
            row = {}
            for j, g in enumerate(FAMILIES):
                row[g] = round(sum(1 for r in sel
                                   if r["pick"] == _label_idx(r, g)) / max(len(sel), 1), 4)
            row["cannot_tell"] = round(sum(1 for r in sel
                                           if r["pick"] == r["cannot_idx"])
                                       / max(len(sel), 1), 4)
            conf[f] = row
        acc = sum(1 for r in rr if r["pick"] == r["truth_idx"]) / max(len(rr), 1)
        return conf, round(acc, 4), len(rr)

    def _label_idx(r, fam):
        e = events[r["i"]]
        from run_g162_reading import LABELS as L
        try:
            return e["cands"].index(L[fam])
        except ValueError:
            return -1

    for arm in ("classify", "classify_delta", "blind"):
        conf, acc, n = table(arm)
        out[arm] = {"n": n, "overall_accuracy": acc, "confusion": conf}

    # the PRIMARY: concealed vs unnoticed pair separation, artifact only
    rr = [r for r in rows("classify") if r["pick"] is not None
          and r["family"] in ("concealed", "unnoticed")]
    pair_scored = [r for r in rr
                   if events[r["i"]]["cands"][r["pick"]] in
                   (LABELS["concealed"], LABELS["unnoticed"])]
    pair_hit = sum(1 for r in pair_scored if r["pick"] == r["truth_idx"])
    pair_acc = pair_hit / max(len(pair_scored), 1)
    out["verdict"]["pair_separation"] = {
        "n_pair_events": len(rr), "n_committed_to_pair": len(pair_scored),
        "accuracy_on_committed": round(pair_acc, 4),
        "band": ("SEPARATES" if pair_acc >= 0.70 else
                 "PARTIAL" if pair_acc >= 0.60 else "BLIND"),
        "interpreted": bool(v_pass),
        "power_note": "detects ~0.17 off 0.5 at this n (card)"}

    # clean-family fabrication
    cl = [r for r in rows("classify") if r["pick"] is not None and r["family"] == "clean"]
    fab = sum(1 for r in cl if r["pick"] not in (r["truth_idx"], r["cannot_idx"]))
    out["gates"]["clean_fabrication"] = {
        "rate": round(fab / max(len(cl), 1), 4), "band_CLEAN_if": "<= 0.15",
        "l146_risk_note": "0.40 over-attribution on rewritten twins is the recorded risk"}

    (OUT / "verdict.json").write_text(json.dumps(out, indent=1),
                                      encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("gates", "verdict")}, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["validate", "classify", "classify_delta", "blind"])
    ap.add_argument("--verdict", action="store_true")
    args = ap.parse_args()
    if args.arm:
        run_arm(args.arm)
    elif args.verdict:
        verdict()
    else:
        ap.error("pick a mode")


if __name__ == "__main__":
    main()
