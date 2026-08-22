"""G172 reading matrix — nine readers score every corpus artifact against its lexically
matched candidate set with the conditional-likelihood reader; relation contrasts land the
verdict band.

Card: prereg/g172.py (frozen). Per-reader instrument gates run BEFORE that reader's matrix
row (known-answer echo, exact-equivalence tie, shuffle floor); a reader that fails is
recorded INSTRUMENT-FAIL and its row is excluded from contrasts rather than repaired.

Output: per-reader chunks results/g172/read_{reader}.json (resume-safe), then
results/g172/verdict.json with contrasts, permutation p-values, and the band.
GPU; lock once per invocation; readers run smallest-first so the ollama residency can drain.
"""

from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

import torch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from prereg.g172 import (ALPHA, BANDS, KNOWN_ANSWER_FLOOR, MAKERS,               # noqa: E402
                         N_PERMUTATIONS, READERS, SEED0, SHUFFLE_BAND, TIE_TOL,
                         TOPICS, candidate, relation, short)
from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock              # noqa: E402
from soundingline.probe.conditional_reader import (artifact_logprob,             # noqa: E402
                                                   candidate_scores, free_readers,
                                                   load_reader)

CORPUS = REPO / "corpora" / "g172"
OUT = REPO / "results" / "g172"
MANIFEST = OUT / "corpus_manifest.json"
VERDICT = OUT / "verdict.json"


def load_corpus() -> list[dict]:
    rows = []
    for mdir in sorted(CORPUS.iterdir()):
        for p in sorted(mdir.glob("art_*.json")):
            rows.append(json.loads(p.read_text(encoding="utf-8")))
    return rows


def first_sentence(text: str) -> str:
    for sep in (". ", "! ", "? "):
        if sep in text:
            return text.split(sep)[0] + sep.strip()
    return text[:120]


def reader_gates(model, tok, arts: list[dict], rng: random.Random) -> dict:
    """Known-answer echo, exact-equivalence, shuffle floor. Returns gate record."""
    probe = rng.sample(arts, min(16, len(arts)))
    ka_hits = 0
    for a in probe:
        own = first_sentence(a["text"])
        others = rng.sample([x for x in arts if x is not a], 3)
        cands = [own] + [first_sentence(o["text"]) for o in others]
        res = candidate_scores(model, tok, cands, a["text"])
        ka_hits += res["order"][0] == 0
    ka = ka_hits / len(probe)

    ties = []
    for a in probe[:8]:
        c = candidate(a["topic_i"], a["goal_i"])
        s1, _, _ = artifact_logprob(model, tok, c, a["text"])
        s2, _, _ = artifact_logprob(model, tok, str(c), a["text"])
        ties.append(abs(s1 - s2))
    tie_ok = max(ties) < TIE_TOL

    sh_hits, sh_n = 0, 0
    for a in rng.sample(arts, min(24, len(arts))):
        cands = [candidate(a["topic_i"], g) for g in range(4)]
        res = candidate_scores(model, tok, cands, a["text"])
        fake_truth = rng.randrange(4)
        sh_hits += res["order"][0] == fake_truth
        sh_n += 1
    sh = sh_hits / sh_n
    return {"known_answer": ka, "tie_max": max(ties), "shuffle_top1": sh,
            "pass": (ka >= KNOWN_ANSWER_FLOOR and tie_ok
                     and SHUFFLE_BAND[0] <= sh <= SHUFFLE_BAND[1])}


def run_reader(reader: str, arts: list[dict]) -> dict:
    dest = OUT / f"read_{short(reader)}.json"
    if dest.exists():
        return json.loads(dest.read_text(encoding="utf-8"))
    print(f"== reader {short(reader)} ==")
    model, tok = load_reader(reader, device="cuda", dtype="float16")
    rng = random.Random(SEED0 + 7 + READERS.index(reader))
    gates = reader_gates(model, tok, arts, rng)
    print(f"  gates: {gates}")
    cases = []
    if gates["pass"]:
        for a in arts:
            cands = [candidate(a["topic_i"], g) for g in range(4)]
            res = candidate_scores(model, tok, cands, a["text"])
            truth = a["goal_i"]
            margin = res["scores"][truth] - (sum(res["scores"]) - res["scores"][truth]) / 3
            cases.append({"maker": a["maker"], "topic_i": a["topic_i"], "goal_i": truth,
                          "trial": a["trial"], "relation": relation(a["maker"], reader),
                          "margin": margin, "top1": res["order"][0] == truth,
                          "rank": res["order"].index(truth) + 1})
    rec = {"reader": reader, "gates": gates, "cases": cases}
    dest.write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8", newline="\n")
    free_readers()
    return rec


def contrasts(records: list[dict]) -> dict:
    """Pooled per-artifact C1 (exact - mean cross) and C2 (mean sibling - mean cross)."""
    by_art: dict[tuple, dict[str, list[float]]] = {}
    for rec in records:
        if not rec["gates"]["pass"]:
            continue
        for c in rec["cases"]:
            key = (c["maker"], c["topic_i"], c["goal_i"], c["trial"])
            by_art.setdefault(key, {"exact": [], "sibling": [], "cross": []})
            by_art[key][c["relation"]].append(c["margin"])
    c1, c2 = [], []
    for cell in by_art.values():
        if cell["exact"] and cell["cross"]:
            c1.append(cell["exact"][0] - sum(cell["cross"]) / len(cell["cross"]))
        if cell["sibling"] and cell["cross"]:
            c2.append(sum(cell["sibling"]) / len(cell["sibling"])
                      - sum(cell["cross"]) / len(cell["cross"]))

    def perm_p(diffs: list[float]) -> tuple[float, float]:
        rng = random.Random(SEED0 + 9)
        obs = sum(diffs) / len(diffs)
        ge = sum(1 for _ in range(N_PERMUTATIONS)
                 if abs(sum(d * rng.choice((1, -1)) for d in diffs) / len(diffs)) >= abs(obs))
        return obs, (ge + 1) / (N_PERMUTATIONS + 1)

    m1, p1 = perm_p(c1)
    m2, p2 = perm_p(c2)
    if m1 > 0 and p1 < ALPHA and m2 > 0 and p2 < ALPHA:
        band = "SIMILARITY-GRADED"
    elif m1 > 0 and p1 < ALPHA:
        band = "EXACT-ONLY"
    elif m1 < 0 and p1 < ALPHA:
        band = "REVERSED"
    else:
        band = "FLAT"
    assert band in BANDS
    return {"c1_mean": m1, "c1_p": p1, "c1_n": len(c1),
            "c2_mean": m2, "c2_p": p2, "c2_n": len(c2), "band": band}


def main() -> int:
    if not MANIFEST.exists():
        print("no corpus manifest; run run_g172_corpus.py first")
        return 1
    arts = load_corpus()
    print(f"{len(arts)} artifacts, {len(READERS)} readers")
    t0 = time.time()
    acquire_gpu_lock("g172_matrix")
    try:
        order = sorted(READERS, key=lambda r: ("3b" in r.lower() or "2.8b" in r, r))
        records = [run_reader(r, arts) for r in order]
    finally:
        release_gpu_lock()
    result = contrasts(records)
    per_reader = {short(r["reader"]): {
        "gates_pass": r["gates"]["pass"],
        "top1": (sum(c["top1"] for c in r["cases"]) / len(r["cases"])) if r["cases"] else None,
        "mean_margin": (sum(c["margin"] for c in r["cases"]) / len(r["cases"]))
                       if r["cases"] else None,
    } for r in records}
    import transformers                                                          # noqa: PLC0415
    VERDICT.write_text(json.dumps({
        "prereg": "prereg/g172.py", "contrasts": result, "per_reader": per_reader,
        "n_artifacts": len(arts), "minutes": round((time.time() - t0) / 60, 1),
        "versions": {"torch": torch.__version__, "transformers": transformers.__version__},
    }, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
