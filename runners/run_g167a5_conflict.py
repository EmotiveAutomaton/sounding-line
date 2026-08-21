"""G167-A5 evidence-conflict battery — implements prereg/g167a5.py (frozen card; the
DESIGN CHECK lives there and this runner adds nothing).

    --gate       CPU: pipeline purity + anchor. Arms gate on it.
    --arm X      true_note | false_note | false_note_flag    (GPU, checkpointed)
    --verdict    CPU: bands vs the recorded 0.86, note-following and flag rates.

Output: results/g167a5/
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
G159 = REPO / "results" / "g159"
OUT = REPO / "results" / "g167a5"
SEED = 16750
FLAG_OPT = "the note does not match the essay"

sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runners"))
from run_g159_recovery import call_reader, load_arts, parse_pick       # noqa: E402

NOTE_PICK = """This essay was rewritten following exactly one of the numbered revision \
instructions below. An unverified production note claims the applied instruction was:
"{note}"
The note may be wrong. Read the essay and decide which instruction was actually applied.

ESSAY:
{text}

INSTRUCTIONS:
{cands}

Answer with the number only."""


def load_manifest():
    return json.loads((G159 / "manifest.json").read_text(encoding="utf-8"))


def decoy_for(e, rng):
    decoys = [c for j, c in enumerate(e["cands"]) if j != e["truth_idx"]]
    return decoys[int(rng.integers(len(decoys)))]


def note_for(arm, e, rng):
    if arm == "true_note":
        return e["cands"][e["truth_idx"]]
    return decoy_for(e, rng)


def build_prompt(arm, e, art, note):
    cands = list(e["cands"]) + ([FLAG_OPT] if arm == "false_note_flag" else [])
    cs = "\n".join(f"{j + 1}. {c}" for j, c in enumerate(cands))
    return NOTE_PICK.format(note=note, text=art["text"], cands=cs), len(cands)


def gate():
    import numpy as np
    man = load_manifest()
    arts = load_arts()
    h = lambda s: hashlib.sha256(s.encode()).hexdigest()               # noqa: E731
    defects = []
    for e in man["p_plus"][:20]:
        art = arts[(e["family"], e["artifact_id"])]
        perm = {**e, "family": "xx", "amount": 99, "artifact_id": "zz", "topic_i": -1}
        build = lambda ev: build_prompt("false_note", ev, art, "N")[0]  # noqa: E731
        if h(build(e)) != h(build(perm)):
            defects.append(e["artifact_id"])
    anchor = json.loads((G159 / "p_plus.json").read_text(encoding="utf-8"))
    anchor_ok = anchor["accuracy"] >= 0.80 and anchor["n_parsed"] >= 90
    out = {"prereg": "prereg/g167a5.py",
           "pipeline_purity": {"events_checked": 20, "defects": defects,
                               "pass": not defects},
           "anchor": {"recorded_direct": anchor["accuracy"], "pass": bool(anchor_ok)}}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "gate.json").write_text(json.dumps(out, indent=1), encoding="utf-8",
                                   newline="\n")
    print(json.dumps(out, indent=1))
    if defects or not anchor_ok:
        sys.exit(1)


def run_arm(arm):
    import numpy as np
    from soundingline.gpulock import acquire_gpu_lock                  # noqa: PLC0415
    acquire_gpu_lock(f"g167a5_{arm}")                  # once per invocation (LESSONS §5)
    man = load_manifest()
    arts = load_arts()
    events = man["p_plus"]
    OUT.mkdir(parents=True, exist_ok=True)
    part = OUT / f"{arm}_partial.jsonl"
    done = {}
    if part.exists():
        done = {json.loads(x)["i"]: json.loads(x)
                for x in part.read_text(encoding="utf-8").splitlines()}
    rng = np.random.default_rng(SEED)
    notes = [note_for(arm, e, rng) for e in events]     # one stream, order-stable
    with part.open("a", encoding="utf-8", newline="\n") as fh:
        for i, e in enumerate(events):
            if i in done:
                continue
            art = arts[(e["family"], e["artifact_id"])]
            p, n = build_prompt(arm, e, art, notes[i])
            pick = parse_pick(call_reader(p), n)
            note_idx = e["cands"].index(notes[i]) if notes[i] in e["cands"] else -1
            row = {"i": i, **{k: e[k] for k in e if k != "cands"},
                   "n_cands": n, "pick": pick, "note_idx": note_idx,
                   "flag_idx": (n - 1) if arm == "false_note_flag" else None}
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            done[i] = row
    if len(done) < len(events):
        print(f"INCOMPLETE {arm}: {len(done)}/{len(events)}")
        sys.exit(1)
    rows = [done[i] for i in sorted(done)]
    ok = [r for r in rows if r["pick"] is not None]
    hit = sum(1 for r in ok if r["pick"] == r["truth_idx"])
    followed = sum(1 for r in ok if r["pick"] == r["note_idx"])
    flagged = sum(1 for r in ok if r.get("flag_idx") is not None
                  and r["pick"] == r["flag_idx"])
    summary = {"arm": arm, "n": len(rows), "n_parsed": len(ok),
               "accuracy_on_truth": round(hit / max(len(ok), 1), 4),
               "note_following_rate": round(followed / max(len(ok), 1), 4),
               "conflict_flag_rate": round(flagged / max(len(ok), 1), 4)}
    (OUT / f"{arm}.json").write_text(json.dumps(summary, indent=1), encoding="utf-8",
                                     newline="\n")
    print(json.dumps(summary, indent=1))


def verdict():
    get = lambda a: json.loads((OUT / f"{a}.json").read_text(encoding="utf-8"))  # noqa: E731
    tn, fn, ff = get("true_note"), get("false_note"), get("false_note_flag")
    tn_ok = tn["accuracy_on_truth"] >= 0.80
    ref = 0.86 if tn_ok else tn["accuracy_on_truth"]
    acc = fn["accuracy_on_truth"]
    band = ("EVIDENCE-HOLDS" if acc >= 0.70 else
            "SUGGESTIBLE" if acc <= 0.40 else "MIXED")
    out = {"prereg": "prereg/g167a5.py",
           "gates": {"true_note_sanity": {"accuracy": tn["accuracy_on_truth"],
                                          "pass": bool(tn_ok),
                                          "reference_used": ref}},
           "verdict": {"false_note_accuracy_on_truth": acc,
                       "vs_recorded_direct": round(acc - 0.86, 4),
                       "note_following_rate": fn["note_following_rate"],
                       "band": band},
           "secondary": {"flag_arm": ff,
                         "note": "a reader that flags under false notes and not "
                                 "true ones discriminates conflict even if forced "
                                 "choice bends"},
           "response": "the wing PAUSES in every branch per the card"}
    (OUT / "verdict.json").write_text(json.dumps(out, indent=1), encoding="utf-8",
                                     newline="\n")
    print(json.dumps(out, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--arm", choices=["true_note", "false_note", "false_note_flag"])
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
