"""G168-R role-recovery battery — implements prereg/g168r.py (frozen card; the DESIGN
CHECK lives there and this runner adds nothing).

    --gate       CPU: pipeline purity + balanced-marginal assertion. Arms gate on it.
    --arm A      process | classify | blind          (GPU, checkpointed)
    --verdict    CPU: P gate per question, per-question bands, everything on disk.

Output: results/g168r/
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CORPUS = REPO / "corpora" / "g168_roles"
OUT = REPO / "results" / "g168r"
SEED = 16850

sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runners"))
from run_g159_recovery import call_reader                              # noqa: E402

PROTOCOL = ("This essay was produced by two participants under a logged protocol: "
            "one PROPOSED a thesis (sometimes several candidates), the other chose "
            "or accepted it and WROTE the essay; sometimes the writer first vetoed "
            "the plan and forced a revision; afterwards one of the two rewrote a "
            "single paragraph.")

QUESTIONS = {
    "selection": {
        "q": "Did the writer choose the thesis from among several proposed "
             "alternatives, or accept the only proposal made?",
        "options": ["chose among several alternatives", "accepted the only proposal"],
        "truth": lambda c: 0 if c["condition"]["selection"] == "from3" else 1},
    "veto": {
        "q": "Before writing, did the writer reject the proposed plan once and "
             "force a revision?",
        "options": ["yes, a veto and revision happened", "no veto happened"],
        "truth": lambda c: 0 if c["condition"]["veto"] else 1},
    "repair": {
        "q": "After writing, the rewritten paragraph was rewritten by which "
             "participant?",
        "options": ["the one who proposed the thesis", "the one who wrote the essay"],
        "truth": lambda c: 0 if c["condition"]["repair_actor"] == "proposer" else 1},
}

ASK = """{protocol}

{body}QUESTION: {q}
1. {o1}
2. {o2}

Answer with the number only."""


def load_cases():
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(CORPUS.glob("case_*.json"))]


def log_summary(c):
    lines = []
    for e in c["events"]:
        pl = e.get("payload") or {}
        bits = [f"{e['actor_id']} {e['operation']} {e['target']}"]
        if "candidates" in pl:
            bits.append(f"candidates: {len(pl['candidates'])}")
        if "objection" in pl:
            bits.append("objection recorded")
        lines.append(" — ".join(bits))
    return "\n".join(lines)


def build_prompt(arm, c, qkey):
    spec = QUESTIONS[qkey]
    if arm == "blind":
        body = ""
    elif arm == "process":
        body = (f"ESSAY:\n{c['artifact_final']}\n\nRECORDED EVENT LOG:\n"
                f"{log_summary(c)}\n\n")
    else:
        body = f"ESSAY:\n{c['artifact_final']}\n\n"
    return ASK.format(protocol=PROTOCOL, body=body, q=spec["q"],
                      o1=spec["options"][0], o2=spec["options"][1])


def gate():
    cases = load_cases()
    # balanced marginals, asserted (the card's analytic-floor condition)
    bad = []
    for qkey, spec in QUESTIONS.items():
        n0 = sum(1 for c in cases if spec["truth"](c) == 0)
        if not (15 <= n0 <= 25):
            bad.append((qkey, n0))
    h = lambda s: hashlib.sha256(s.encode()).hexdigest()               # noqa: E731
    defects = []
    for c in cases[:10]:
        stripped = {**c, "condition": {"selection": "xx", "veto": "xx",
                                       "repair_actor": "xx", "proposer": "xx",
                                       "realizer": "xx"},
                    "events": [], "thesis": "xx"}
        for qkey in QUESTIONS:
            if h(build_prompt("classify", c, qkey)) != \
                    h(build_prompt("classify", stripped, qkey)):
                defects.append(c["case_id"])
                break
    out = {"prereg": "prereg/g168r.py",
           "balanced_marginals": {"violations": bad, "pass": not bad},
           "pipeline_purity": {"cases_checked": 10, "defects": defects,
                               "pass": not defects}}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "gate.json").write_text(json.dumps(out, indent=1), encoding="utf-8",
                                   newline="\n")
    print(json.dumps(out, indent=1))
    if bad or defects:
        sys.exit(1)


def run_arm(arm):
    import re
    from soundingline.gpulock import acquire_gpu_lock                  # noqa: PLC0415
    acquire_gpu_lock(f"g168r_{arm}")                   # once per invocation (LESSONS §5)
    cases = load_cases()
    items = []
    if arm == "blind":
        for qkey in QUESTIONS:
            items.append(("blind", qkey))
    else:
        for c in cases:
            for qkey in QUESTIONS:
                items.append((c["case_id"], qkey))
    by_id = {c["case_id"]: c for c in cases}
    OUT.mkdir(parents=True, exist_ok=True)
    part = OUT / f"{arm}_partial.jsonl"
    done = {}
    if part.exists():
        done = {json.loads(x)["i"]: json.loads(x)
                for x in part.read_text(encoding="utf-8").splitlines()}
    with part.open("a", encoding="utf-8", newline="\n") as fh:
        for i, (cid, qkey) in enumerate(items):
            if i in done:
                continue
            c = by_id.get(cid) or cases[0]
            p = build_prompt(arm, c, qkey)
            resp = call_reader(p) or ""
            m = re.search(r"\b([12])\b", resp)
            pick = int(m.group(1)) - 1 if m else None
            truth = QUESTIONS[qkey]["truth"](c) if cid != "blind" else None
            fh.write(json.dumps({"i": i, "case_id": cid, "question": qkey,
                                 "pick": pick, "truth": truth}) + "\n")
            fh.flush()
            done[i] = True
    if len(done) < len(items):
        print(f"INCOMPLETE {arm}: {len(done)}/{len(items)}")
        sys.exit(1)
    (OUT / f"{arm}_done.json").write_text(json.dumps({"n": len(done)}),
                                          encoding="utf-8", newline="\n")
    print(f"{arm}: {len(done)} rows")


def verdict():
    from scipy.stats import binomtest
    rows_of = lambda a: [json.loads(x) for x in                        # noqa: E731
                         (OUT / f"{a}_partial.jsonl").read_text(encoding="utf-8")
                         .splitlines()]
    out = {"prereg": "prereg/g168r.py", "gates": {}, "verdict": {}}
    p_rows = rows_of("process")
    c_rows = rows_of("classify")
    for qkey in QUESTIONS:
        pq = [r for r in p_rows if r["question"] == qkey and r["pick"] is not None]
        p_acc = sum(1 for r in pq if r["pick"] == r["truth"]) / max(len(pq), 1)
        p_pass = p_acc >= 0.85
        cq = [r for r in c_rows if r["question"] == qkey and r["pick"] is not None]
        acc = sum(1 for r in cq if r["pick"] == r["truth"]) / max(len(cq), 1)
        bt = binomtest(sum(1 for r in cq if r["pick"] == r["truth"]), len(cq), 0.5,
                       alternative="greater")
        band = ("READS" if acc >= 0.70 else
                "PARTIAL" if acc > 0.60 and bt.pvalue < 0.05 else "BLIND")
        out["gates"][f"P_{qkey}"] = {"accuracy": round(p_acc, 4),
                                     "pass": bool(p_pass)}
        out["verdict"][qkey] = {"artifact_only": round(acc, 4), "n": len(cq),
                                "p_vs_0.5": round(bt.pvalue, 5), "band": band,
                                "interpreted": bool(p_pass),
                                "power_note": "~0.72 detectable at n=40 (card)"}
    (OUT / "verdict.json").write_text(json.dumps(out, indent=1), encoding="utf-8",
                                     newline="\n")
    print(json.dumps(out, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--arm", choices=["process", "classify", "blind"])
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
