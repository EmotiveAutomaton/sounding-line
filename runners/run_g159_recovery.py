"""G159 recovery battery — the realized-choice study under prereg/g159.py (frozen card).

DESIGN CHECK: lives on the card (prereg/g159.py), derived before this runner was written;
this file implements it and adds nothing. Arms and gates per the card:

    --build-manifest   deterministic events on disk: P+ (assigned problem instructions on
                       R+ texts, echo-matched decoys), P- (counterfactual sets on the R-
                       twins, same decoy rule), S+ (exact-grade realized surface truths
                       with mechanically-unsatisfied decoys), fabrication sets (P- plus
                       the none option). Echo-matching at construction: the three
                       unassigned pool instructions whose content-word overlap with THIS
                       text sits closest to the truth's.
    --arm X            p_plus | p_minus | blind | fabrication | surface | delta   (GPU)
    --verdict          echo bars (CPU), gates one-sided in their guarded directions,
                       the execution effect banded per the card, everything on disk.

Output: results/g159/  (manifest, per-arm partials + summaries, verdict.json)
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
CORPUS = REPO / "corpora" / "g159_rebuild"
OUT = REPO / "results" / "g159"
MANIFEST = OUT / "manifest.json"
OLLAMA = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen3.5:9b"
DECODING = {"temperature": 0.0, "num_predict": 200}
SEED = 15950
K = 4
NONE_OPT = "none of these instructions was given"

sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runners"))
from run_g131_gen import PROBLEM                                       # noqa: E402
from run_g158_adjudicate import mechanical_check, BUILD_SUFFIX         # noqa: E402

STOP = set("the a an and or but if of to in on for with as by at from is are was were be "
           "been being it its this that these those not no than then so such your you "
           "one two exactly least".split())


def content_words(s: str) -> set:
    return {w.lower() for w in re.findall(r"[a-zA-Z']+", s)} - STOP


def echo_score(instruction: str, text_words: set) -> float:
    cw = content_words(instruction)
    return len(cw & text_words) / max(len(cw), 1)


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


PICK = """This essay was rewritten following exactly one of the numbered revision \
instructions below. Read the essay and decide which instruction was applied.

ESSAY:
{text}

INSTRUCTIONS:
{cands}

Answer with the number only."""

PICK_NONE = """This essay may have been rewritten following one of the numbered revision \
instructions below, or following none of them. Read it and decide.

ESSAY:
{text}

OPTIONS:
{cands}

Answer with the number only."""

BLIND = """One of the numbered revision instructions below was applied to an essay you \
cannot see. Which do you think it was?

INSTRUCTIONS:
{cands}

Answer with a number only."""

DELTA = """An essay was rewritten following exactly one of the numbered revision \
instructions below. Here is the ORIGINAL and the REWRITE. Decide which instruction was \
applied.

ORIGINAL:
{base}

REWRITE:
{text}

INSTRUCTIONS:
{cands}

Answer with the number only."""


def load_arts():
    arts = {}
    for fam_dir in sorted(CORPUS.iterdir()):
        if not fam_dir.is_dir():
            continue
        for p in sorted(fam_dir.glob("*.json")):
            if p.name != "manifest.json":
                r = json.loads(p.read_text(encoding="utf-8"))
                arts[(r["family"], r["artifact_id"])] = r
    return arts


def load_bases():
    src = REPO / "corpora" / "g131_factorial"
    bases = {}
    for fam in ("qwen", "llama"):
        for ti in range(10):
            p = src / fam / f"none_0_none_{ti:02d}.json"
            bases[(fam, ti)] = json.loads(p.read_text(encoding="utf-8"))["text"]
    return bases


def echo_matched_decoys(truth: str, assigned: list[str], text: str) -> list[str]:
    """The K-1 unassigned pool instructions whose echo scores on THIS text sit closest to
    the truth's — deterministic (sorted by |difference|, then alphabetically)."""
    tw = content_words(text)
    t_echo = echo_score(truth, tw)
    pool = [i for i in PROBLEM if i not in assigned and i != truth]
    ranked = sorted(pool, key=lambda i: (abs(echo_score(i, tw) - t_echo), i))
    return ranked[:K - 1]


def build_manifest() -> None:
    import numpy as np
    rng = np.random.default_rng(SEED)
    arts = load_arts()
    p_plus, p_minus, surface = [], [], []
    for (fam, aid), art in sorted(arts.items()):
        if art["target"] == "problem":
            dest = p_plus if art["realization_arm"] == "plus" else p_minus
            for truth in [BUILD_SUFFIX.sub("", i) for i in art["instructions"]]:
                decoys = echo_matched_decoys(truth, art["instructions"], art["text"])
                cands = decoys + [truth]
                cands = [cands[j] for j in rng.permutation(len(cands))]
                dest.append({"family": fam, "artifact_id": aid, "amount": art["amount"],
                             "topic_i": int(aid.split("_")[-1]), "truth": truth,
                             "cands": cands, "truth_idx": cands.index(truth)})
        elif art["target"] == "surface" and art["realization_arm"] == "plus":
            for truth in [BUILD_SUFFIX.sub("", i) for i in art["instructions"]]:
                chk = mechanical_check(truth, art["text"])
                if not (chk and chk[0] == "exact" and chk[1]):
                    continue                       # exact-grade REALIZED truths only
                unsat = [i for i in _surface_probe()
                         if i != truth and (c := mechanical_check(i, art["text"]))
                         and not c[1]]
                if len(unsat) < K - 1:
                    continue
                cands = unsat[:K - 1] + [truth]
                cands = [cands[j] for j in rng.permutation(len(cands))]
                surface.append({"family": fam, "artifact_id": aid,
                                "amount": art["amount"],
                                "topic_i": int(aid.split("_")[-1]), "truth": truth,
                                "cands": cands, "truth_idx": cands.index(truth)})
    man = {"seed": SEED, "k": K, "model": MODEL, "prereg": "prereg/g159.py",
           "p_plus": p_plus, "p_minus": p_minus, "surface": surface,
           "n": {"p_plus": len(p_plus), "p_minus": len(p_minus),
                 "surface": len(surface)}}
    OUT.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(man), encoding="utf-8", newline="\n")
    print(f"manifest: P+ {len(p_plus)}, P- {len(p_minus)}, S+ {len(surface)}")


def _surface_probe():
    from run_g158_adjudicate import _all_checkable_surface             # noqa: PLC0415
    return _all_checkable_surface()


def run_arm(arm: str) -> None:
    from soundingline.gpulock import acquire_gpu_lock                  # noqa: PLC0415
    acquire_gpu_lock(f"g159_{arm}")                    # once per invocation (LESSONS §5)
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    arts = load_arts()
    bases = load_bases()
    events = {"p_plus": man["p_plus"], "p_minus": man["p_minus"],
              "blind": man["p_plus"], "fabrication": man["p_minus"],
              "surface": man["surface"], "delta": man["p_plus"]}[arm]

    def prompt_for(e):
        art = arts[(e["family"], e["artifact_id"])]
        cands = e["cands"] + ([NONE_OPT] if arm == "fabrication" else [])
        cs = "\n".join(f"{j + 1}. {c}" for j, c in enumerate(cands))
        if arm == "blind":
            return BLIND.format(cands=cs), len(cands)
        if arm == "fabrication":
            return PICK_NONE.format(text=art["text"], cands=cs), len(cands)
        if arm == "delta":
            return DELTA.format(base=bases[(e["family"], e["topic_i"])],
                                text=art["text"], cands=cs), len(cands)
        return PICK.format(text=art["text"], cands=cs), len(cands)

    part = OUT / f"{arm}_partial.jsonl"
    done = {}
    if part.exists():
        done = {json.loads(x)["i"]: json.loads(x)
                for x in part.read_text(encoding="utf-8").splitlines()}
    with part.open("a", encoding="utf-8", newline="\n") as fh:
        for i, e in enumerate(events):
            if i in done:
                continue
            p, n = prompt_for(e)
            pick = parse_pick(call_reader(p), n)
            row = {"i": i, **{k: e[k] for k in e if k != "cands"},
                   "n_cands": n, "pick": pick}
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            done[i] = row
    if len(done) < len(events):
        print(f"INCOMPLETE {arm}: {len(done)}/{len(events)}")
        sys.exit(1)
    rows = [done[i] for i in sorted(done)]
    ok = [r for r in rows if r["pick"] is not None]
    if arm == "fabrication":
        none_idx = K                                   # the appended option's index
        summary = {"arm": arm, "n": len(rows), "n_parsed": len(ok),
                   "over_attribution_rate": round(
                       sum(1 for r in ok if r["pick"] != none_idx) / max(len(ok), 1), 4)}
    else:
        hit = sum(1 for r in ok if r["pick"] == r["truth_idx"])
        summary = {"arm": arm, "n": len(rows), "n_parsed": len(ok),
                   "accuracy": round(hit / max(len(ok), 1), 4)}
    (OUT / f"{arm}.json").write_text(json.dumps(summary, indent=1),
                                     encoding="utf-8", newline="\n")
    print(json.dumps(summary, indent=1))


def verdict() -> None:
    from scipy.stats import binomtest
    import numpy as np
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    arts = load_arts()
    get = lambda a: json.loads((OUT / f"{a}.json").read_text(encoding="utf-8"))  # noqa: E731
    rows_of = lambda a: [json.loads(x) for x in                        # noqa: E731
                         (OUT / f"{a}_partial.jsonl").read_text(encoding="utf-8").splitlines()]

    out = {"prereg": "prereg/g159.py", "gates": {}, "verdict": {}}

    # gates, one-sided in the guarded direction (card: null AND alternative stated there)
    for gate, expect_note in (("blind", "null=alt=0.25"), ("p_minus", "null=alt=0.25; "
                              "the leak gate: nothing executed, nothing echoes on twins")):
        g = get(gate)
        bt = binomtest(round(g["accuracy"] * g["n_parsed"]), g["n_parsed"], 1 / K,
                       alternative="greater")
        out["gates"][gate] = {"accuracy": g["accuracy"], "n": g["n_parsed"],
                              "expectations": expect_note,
                              "guarded_direction": "UP (leak)",
                              "p_above_floor": round(bt.pvalue, 5),
                              "VOID_if": "one-sided p < 0.05",
                              "void": bool(bt.pvalue < 0.05)}

    # echo bars (CPU) on identical sets — the matching-validation disclosure rule
    def echo_bar(events):
        hits = 0
        for e in events:
            tw = content_words(arts[(e["family"], e["artifact_id"])]["text"])
            scores = [echo_score(c, tw) for c in e["cands"]]
            hits += scores.index(max(scores)) == e["truth_idx"]
        return round(hits / max(len(events), 1), 4)

    eb_plus = echo_bar(man["p_plus"])
    eb_minus = echo_bar(man["p_minus"])
    bt_echo = binomtest(round(eb_plus * len(man["p_plus"])), len(man["p_plus"]), 1 / K,
                        alternative="greater")
    echo_ok = bt_echo.pvalue >= 0.05
    out["gates"]["echo_bar"] = {"p_plus_echo": eb_plus, "p_minus_echo": eb_minus,
                                "matching_holds": bool(echo_ok),
                                "rule": "if echo fails upward, the P+ margin reads "
                                        "against max(echo, 0.25), disclosed"}

    # surface oracle wiring
    oracle_bad = 0
    for e in man["surface"]:
        text = arts[(e["family"], e["artifact_id"])]["text"]
        passing = [j for j, c in enumerate(e["cands"])
                   if (chk := mechanical_check(c, text)) and chk[1]]
        if passing != [e["truth_idx"]]:
            oracle_bad += 1
    out["gates"]["surface_oracle_wiring_defects"] = oracle_bad

    # the primary quantity: the execution effect
    pp, pm = get("p_plus"), get("p_minus")
    floor = max(eb_plus, 0.25) if not echo_ok else 0.25
    effect = pp["accuracy"] - pm["accuracy"]
    n1, n2 = pp["n_parsed"], pm["n_parsed"]
    p_pool = (pp["accuracy"] * n1 + pm["accuracy"] * n2) / (n1 + n2)
    se = (p_pool * (1 - p_pool) * (1 / n1 + 1 / n2)) ** 0.5
    z = effect / se if se > 0 else 0.0
    from scipy.stats import norm
    p_two = float(2 * (1 - norm.cdf(abs(z))))
    out["verdict"]["execution_effect"] = {
        "p_plus_accuracy": pp["accuracy"], "p_minus_accuracy": pm["accuracy"],
        "effect": round(effect, 4), "z": round(z, 3), "p": round(p_two, 5),
        "floor_used_for_margin_reading": floor,
        "band": ("SUPPORTED" if effect >= 0.15 else
                 "PARTIAL" if effect >= 0.08 else "NOT-DETECTED"),
        "power_note": "detectable-at-0.80-power effect ~0.18 at these n (card)"}

    # secondary arms, reported never banded
    out["secondary"] = {
        "fabrication": get("fabrication"),
        "surface": get("surface"),
        "delta_interface_I2": get("delta"),
        "interface_rule": "I2 reported separately, never pooled with I1 (contract 3b)"}

    # per-cell tables
    def cells(arm):
        rows = [r for r in rows_of(arm) if r["pick"] is not None]
        t = {}
        for key in ("family", "amount"):
            t[key] = {}
            for r in rows:
                t[key].setdefault(str(r[key]), []).append(r["pick"] == r["truth_idx"])
            t[key] = {c: {"n": len(v), "accuracy": round(float(np.mean(v)), 4)}
                      for c, v in sorted(t[key].items())}
        return t
    out["cells"] = {"p_plus": cells("p_plus"), "p_minus": cells("p_minus"),
                    "delta": cells("delta")}

    (OUT / "verdict.json").write_text(json.dumps(out, indent=1),
                                      encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-manifest", action="store_true")
    ap.add_argument("--arm", choices=["p_plus", "p_minus", "blind", "fabrication",
                                      "surface", "delta"])
    ap.add_argument("--verdict", action="store_true")
    args = ap.parse_args()
    if args.build_manifest:
        build_manifest()
    elif args.arm:
        run_arm(args.arm)
    elif args.verdict:
        verdict()
    else:
        ap.error("pick a mode")


if __name__ == "__main__":
    main()
