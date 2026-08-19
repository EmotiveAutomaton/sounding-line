"""G158 — Phase 2.1.3 stage (c): artifact-only recovery of realized choices, exploratory.

The construct probe the factorial corpus can still honestly support after L138/L139:
ground truth is the MECHANICAL EXACT-GRADE realized subset only (102 events, 61
artifacts, 4 instructions); the reader sees ONLY the final essay (interface I1 of the
evaluation contract §3b -- no delta exists here, no prompt is shown); candidates are
same-pool instructions MECHANICALLY VERIFIED UNSATISFIED in that artifact, so a decoy can
never be the better reading of the text. The measured trivial-feature bar (L138) runs on
the identical candidate sets.

Arms:
  R1 recovery      essay + 4 candidates, pick the instruction that was given
  R2 blind         candidates only, no essay -- the floor arm
  R3 echo          CPU: pick the candidate with max content-word overlap with the essay
                   (the L138 bar ported to the exact task)
  R4 oracle        CPU: pick the candidate whose mechanical check passes on the essay --
                   the construction ceiling, 1.0 by design, a wiring check
  R5 none          zero-instruction control essays, 4 unsatisfied candidates + an
                   explicit "none of these instructions was given" option -- fabrication
  R6 problem       EXPLORATORY-ATTENUATED: problem-pool assignments (no realization
                   labels exist, L139), scored against ASSIGNMENT; positive results only
                   are interpretable -- a null here is attenuation-confounded and is
                   preregistered as UNINTERPRETABLE, stated in the output file itself
  R7 problem_echo  CPU: the echo bar on R6's identical candidate sets

DESIGN CHECK (2026-08-19, at design time). Lessons read: LESSONS §3 to §5 including
L137/L139's entries; CONTROLS 6 and 7. Expectations, both ways, with directions:
  R2 blind: null AND alternative = analytic 1/k = 0.25 once truth-balanced (the truth
    marginal is skewed 37/31/22/12, so the BANDED read uses the balanced subsample, 12
    per instruction; raw reported beside it -- CONTROLS entry 6). Guarded failure:
    construction leak, direction UP.
  R3 echo: null (no instruction wording echoes into text) = 0.25; alternative = above,
    unbounded -- it is the bar, not a gate. R1 minus R3 on identical events is the
    quantity of interest; R1 alone is NOT a finding (L138's means).
  R4 oracle: 1.0 by construction; anything else is a wiring defect and the run aborts
    its own interpretation (printed, not banded).
  R5 none: correct behavior = the none option; fabrication direction UP; the L139
    acquiescence result predicts failure here -- measured, not banded, and a high rate
    further quarantines reader-asserted realization.
  R6: expectation under alternative = above the R7 echo bar by more than the ~0.59
    attenuation factor explains; under null = at R7. Only the above-bar outcome is
    actionable (exploratory foraging, the L137 plan).
No verdict bands anywhere: exploratory by declaration, nothing here can VOID, and no
claim language attaches to any number in this file (contract §7 does not apply until a
constructed corpus with verified realization exists -- that is 2.1.5's job).

Output: results/g158/recovery_summary.json (+ per-arm partial jsonl, checkpointed).
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
OUT = REPO / "results" / "g158"
OLLAMA = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen3.5:9b"
DECODING = {"temperature": 0.0, "num_predict": 200}
SEED = 15830
K = 4
NONE_OPT = "none of these instructions was given"

sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runners"))
from run_g158_adjudicate import (mechanical_check, load_corpus,        # noqa: E402
                                 _all_checkable_surface, BUILD_SUFFIX)

STOP = set("the a an and or but if of to in on for with as by at from is are was were be "
           "been being it its this that these those not no than then so such your you "
           "one two exactly least".split())


def content_words(s: str) -> set:
    return {w.lower() for w in re.findall(r"[a-zA-Z']+", s)} - STOP


def call_reader(prompt: str) -> str | None:
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


def parse_pick(resp: str | None, n: int) -> int | None:
    if not resp:
        return None
    m = re.search(r"\b([1-9])\b", resp)
    if m and 1 <= int(m.group(1)) <= n:
        return int(m.group(1)) - 1
    return None


PICK_PROMPT = """This essay was written following exactly one of the numbered writing \
instructions below. Read the essay and decide which instruction it follows.

ESSAY:
{text}

INSTRUCTIONS:
{cands}

Answer with the number of the instruction that was given, and nothing else."""

BLIND_PROMPT = """One of the numbered writing instructions below was given for an essay \
you cannot see. Which do you think it was?

INSTRUCTIONS:
{cands}

Answer with a number only."""

NONE_PROMPT = """This essay may have been written following one of the numbered writing \
instructions below, or none of them. Read the essay and decide.

ESSAY:
{text}

OPTIONS:
{cands}

Answer with the number of your choice, and nothing else."""


def build_events(rng):
    """Scored events: exact-grade mechanically realized assignments; decoys are checkable
    instructions verified unsatisfied in the same artifact (exact-grade preferred)."""
    mech = json.loads((OUT / "realization_mechanical.json").read_text(encoding="utf-8"))
    arts = {(a["family"], a["artifact_id"]): a for a in load_corpus()}
    probe = _all_checkable_surface()
    events, skipped = [], 0
    for r in mech["rows"]:
        if not (r["checkable"] and r["grade"] == "exact" and r["realized"]):
            continue
        art = arts[(r["family"], r["artifact_id"])]
        truth = BUILD_SUFFIX.sub("", r["instruction"])
        unsat = []
        for ins in probe:
            if ins == truth:
                continue
            chk = mechanical_check(ins, art["text"])
            if chk and not chk[1]:
                unsat.append((0 if chk[0] == "exact" else 1, ins))
        unsat.sort(key=lambda t: (t[0], t[1]))
        exact_first = [i for _, i in unsat]
        if len(exact_first) < K - 1:
            skipped += 1
            continue
        decoys = exact_first[:K - 1]
        cands = decoys + [truth]
        order = rng.permutation(len(cands))
        cands = [cands[j] for j in order]
        events.append({"family": r["family"], "artifact_id": r["artifact_id"],
                       "amount": r["amount"], "coupling": r["coupling"],
                       "truth": truth, "cands": cands,
                       "truth_idx": cands.index(truth),
                       "decoy_grades": {i: ("exact" if g == 0 else "approx")
                                        for g, i in unsat[:K - 1]}})
    return events, skipped, arts


def build_problem_events(rng, arts):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "g131gen", REPO / "runners" / "run_g131_gen.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    events = []
    for (fam, aid), art in sorted(arts.items()):
        if art["target"] != "problem":
            continue
        assigned = [BUILD_SUFFIX.sub("", i) for i in art["instructions"]]
        unassigned = [i for i in mod.PROBLEM if i not in assigned]
        for truth in assigned:
            decoys = [unassigned[j] for j in
                      rng.choice(len(unassigned), size=K - 1, replace=False)]
            cands = decoys + [truth]
            cands = [cands[j] for j in rng.permutation(len(cands))]
            events.append({"family": fam, "artifact_id": aid, "amount": art["amount"],
                           "coupling": art["coupling"], "truth": truth, "cands": cands,
                           "truth_idx": cands.index(truth)})
    return events


def build_none_events(rng, arts):
    probe = _all_checkable_surface()
    events = []
    for (fam, aid), art in sorted(arts.items()):
        if art["amount"] != 0:
            continue
        unsat = [i for i in probe
                 if (c := mechanical_check(i, art["text"])) and not c[1]]
        if len(unsat) < K:
            continue
        cands = [unsat[j] for j in rng.choice(len(unsat), size=K, replace=False)]
        cands = cands + [NONE_OPT]
        events.append({"family": fam, "artifact_id": aid, "cands": cands})
    return events


def run_gpu_arm(name, events, prompt_fn):
    from soundingline.gpulock import acquire_gpu_lock                 # noqa: PLC0415
    acquire_gpu_lock(f"g158_{name}")
    part = OUT / f"recovery_{name}_partial.jsonl"
    done = {}
    if part.exists():
        done = {json.loads(x)["i"]: json.loads(x)
                for x in part.read_text(encoding="utf-8").splitlines()}
    with part.open("a", encoding="utf-8", newline="\n") as fh:
        for i, e in enumerate(events):
            if i in done:
                continue
            resp = call_reader(prompt_fn(e))
            pick = parse_pick(resp, len(e["cands"]))
            row = {"i": i, **{k: e[k] for k in e if k != "cands"},
                   "n_cands": len(e["cands"]), "pick": pick,
                   "picked": e["cands"][pick] if pick is not None else None}
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            done[i] = row
    return [done[i] for i in sorted(done)]


def score(rows, events, balanced_per=None, rng=None):
    ok = [r for r in rows if r["pick"] is not None]
    hit = [r for r in ok if "truth_idx" in r and r["pick"] == r["truth_idx"]]
    res = {"n": len(rows), "n_parsed": len(ok),
           "accuracy": round(len(hit) / max(len(ok), 1), 4)}
    if balanced_per and rng is not None:
        by = {}
        for r in ok:
            by.setdefault(r["truth"], []).append(r)
        per = min(balanced_per, min((len(v) for v in by.values()), default=0))
        bal = [v[j] for v in by.values()
               for j in rng.permutation(len(v))[:per]]
        res["balanced"] = {"per_instruction": per, "n": len(bal),
                           "accuracy": round(sum(1 for r in bal
                                                 if r["pick"] == r["truth_idx"])
                                             / max(len(bal), 1), 4)}
    for key in ("family", "amount", "coupling"):
        cells = {}
        for r in ok:
            if key in r:
                cells.setdefault(str(r[key]), []).append(r)
        res[f"by_{key}"] = {c: {"n": len(v), "accuracy":
                                round(sum(1 for r in v if r["pick"] == r["truth_idx"])
                                      / max(len(v), 1), 4)} for c, v in sorted(cells.items())}
    return res


def echo_pick(e, arts):
    text_w = content_words(arts[(e["family"], e["artifact_id"])]["text"])
    scores = [len(content_words(c) & text_w) / max(len(content_words(c)), 1)
              for c in e["cands"]]
    return scores.index(max(scores))


def main() -> None:
    import numpy as np
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["surface", "problem", "none", "summarize"],
                    required=True)
    args = ap.parse_args()
    rng = np.random.default_rng(SEED)
    events, skipped, arts = build_events(rng)
    prob_events = build_problem_events(np.random.default_rng(SEED + 1), arts)
    none_events = build_none_events(np.random.default_rng(SEED + 2), arts)

    fmt = lambda e, p: p.format(                                        # noqa: E731
        text=arts[(e["family"], e["artifact_id"])]["text"],
        cands="\n".join(f"{j + 1}. {c}" for j, c in enumerate(e["cands"])))

    # a partial jsonl exists from the first row on, so the produces-guard target is a
    # done-marker written only after every event is on disk (the produces lesson, §5)
    def mark_done(name, rows, n_expected):
        if len(rows) >= n_expected:
            (OUT / f"recovery_{name}_done.json").write_text(json.dumps(
                {"n": len(rows), "n_expected": n_expected}), encoding="utf-8",
                newline="\n")
        else:
            print(f"INCOMPLETE {name}: {len(rows)}/{n_expected}; stage retries")
            sys.exit(1)

    if args.arm == "surface":
        rows1 = run_gpu_arm("r1", events, lambda e: fmt(e, PICK_PROMPT))
        rows2 = run_gpu_arm("r2", events, lambda e: BLIND_PROMPT.format(
            cands="\n".join(f"{j + 1}. {c}" for j, c in enumerate(e["cands"]))))
        mark_done("r1", rows1, len(events))
        mark_done("r2", rows2, len(events))
    elif args.arm == "problem":
        mark_done("r6", run_gpu_arm("r6", prob_events, lambda e: fmt(e, PICK_PROMPT)),
                  len(prob_events))
    elif args.arm == "none":
        mark_done("r5", run_gpu_arm("r5", none_events, lambda e: fmt(e, NONE_PROMPT)),
                  len(none_events))
    elif args.arm == "summarize":
        srng = np.random.default_rng(SEED + 3)
        rows = lambda n: [json.loads(x) for x in                        # noqa: E731
                          (OUT / f"recovery_{n}_partial.jsonl")
                          .read_text(encoding="utf-8").splitlines()]
        r1, r2, r6, r5 = rows("r1"), rows("r2"), rows("r6"), rows("r5")
        # CPU arms on identical sets
        r3 = [{**{k: e[k] for k in e if k != "cands"}, "pick": echo_pick(e, arts)}
              for e in events]
        r4_bad = 0
        for e in events:
            text = arts[(e["family"], e["artifact_id"])]["text"]
            passing = [j for j, c in enumerate(e["cands"])
                       if (chk := mechanical_check(c, text)) and chk[1]]
            if passing != [e["truth_idx"]]:
                r4_bad += 1
        r7 = [{**{k: e[k] for k in e if k != "cands"}, "pick": echo_pick(e, arts)}
              for e in prob_events]
        n5 = [r for r in r5 if r["pick"] is not None]
        fab = sum(1 for r in n5 if r["pick"] != K)      # option K (0-based) is the none option
        summary = {
            "prereg": "runner docstring DESIGN CHECK (exploratory; no verdict bands)",
            "seed": SEED, "k": K, "model": MODEL, "decoding": DECODING,
            "events_surface": len(events), "events_skipped_thin_decoys": skipped,
            "R1_recovery": score(r1, events, balanced_per=12, rng=srng),
            "R2_blind": score(r2, events, balanced_per=12, rng=srng),
            "R3_echo_bar": score(r3, events, balanced_per=12, rng=srng),
            "R4_oracle_wiring_defects": r4_bad,
            "R5_none_control": {"n": len(r5), "n_parsed": len(n5),
                                "fabrication_rate": round(fab / max(len(n5), 1), 4),
                                "note": "share of zero-instruction essays where the "
                                        "reader asserted an unsatisfied instruction "
                                        "instead of the none option; L139 predicts UP"},
            "R6_problem_attenuated": {**score(r6, prob_events),
                                      "caveat": "scored against ASSIGNMENT; realization "
                                                "unverifiable (L139); attenuation ~0.59 "
                                                "if surface rates transfer; a NULL HERE "
                                                "IS UNINTERPRETABLE by prereg -- only "
                                                "above-bar positives are actionable"},
            "R7_problem_echo_bar": score(r7, prob_events),
        }
        (OUT / "recovery_summary.json").write_text(json.dumps(summary, indent=1),
                                                   encoding="utf-8", newline="\n")
        print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
