"""Stage-2 Tree-S scout E24-S6 (discovery lane): the tokenizer control. Does tokenizer
similarity between reader and maker explain the crossed matrix better than family?

The route this closes (Stage-2 brief, S1/S6): token familiarity impersonating process
familiarity. Metric: for each reader-maker pair, tokenize every artifact with both
tokenizers and take the Jaccard overlap of the token-string multisets, averaged over
artifacts — a direct measure of how similarly the two models segment the same text. Then
the same double-centered rank machinery as the geometry linkage: does tokenizer overlap
predict the margin cells after reader and maker effects are removed, and does it survive
alongside the family relation?

DESIGN CHECK (2026-08-24, discovery lane). Lessons read: section 3 (double-center both
sides so reader quality and maker difficulty vanish, the L166 matrix-beside-contrast rule;
report cells; permutation null within reader). Failure directions: overlap predicting the
matrix as strongly as family favors the tokenizer rival (RIVAL-FAVORED); overlap at or
near zero relation leaves the family account standing (QUIET for this rival). CPU only.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUT = REPO / "results" / "scouts"
SEED0 = 19200
N_PERMS = 20000

MAKER_SHORT = {"Qwen/Qwen2.5-0.5B": "qwen25_05b", "Qwen/Qwen2.5-1.5B": "qwen25_15b",
               "HuggingFaceTB/SmolLM2-1.7B-Instruct": "smollm2_17b_instruct",
               "HuggingFaceTB/SmolLM2-360M-Instruct": "smollm2_360m_instruct"}


def arm_run() -> int:
    from transformers import AutoTokenizer                                       # noqa: PLC0415
    from prereg.g172 import READERS, short                                       # noqa: PLC0415
    from runners.scout_stage2_s import READERS2                                  # noqa: PLC0415

    arts = []
    for variant in ("g172", "g172_family2"):
        for p in sorted((REPO / "corpora" / variant).rglob("art_*.json")):
            a = json.loads(p.read_text(encoding="utf-8"))
            if a["maker"] in MAKER_SHORT:
                arts.append(a)
    texts = [a["text"] for a in arts][:120]

    models = sorted(set(READERS + READERS2 + list(MAKER_SHORT)))
    toks = {m: AutoTokenizer.from_pretrained(m) for m in models}
    token_lists = {m: [tuple(toks[m].tokenize(t)) for t in texts] for m in models}

    def overlap(a: str, b: str) -> float:
        vals = []
        for ta, tb in zip(token_lists[a], token_lists[b]):
            ca, cb = Counter(ta), Counter(tb)
            inter = sum((ca & cb).values())
            union = sum((ca | cb).values())
            vals.append(inter / union if union else 0.0)
        return float(np.mean(vals))

    # margins per (reader, maker) from the landed matrix chunks
    cells: dict[tuple, list] = {}
    for variant in ("orig", "fam2"):
        for ch in OUT.glob(f"mx_{variant}_*.json"):
            if ch.name.endswith("_done.json"):
                continue
            rec = json.loads(ch.read_text(encoding="utf-8"))
            if "cases" not in rec:
                continue
            rname = short(rec["reader"])
            for c in rec["cases"]:
                mk = MAKER_SHORT.get(c["maker"])
                if mk:
                    cells.setdefault((rname, mk), []).append(c["margin"])
    margin = {k: sum(v) / len(v) for k, v in cells.items()}
    readers = sorted({r for r, _ in margin})
    makers = sorted({m for _, m in margin})

    name_of = {short(m): m for m in models}
    name_of.update({v: k for k, v in MAKER_SHORT.items()})
    M = np.array([[margin[(r, m)] for m in makers] for r in readers])
    T = np.array([[overlap(name_of[r], name_of[m]) for m in makers] for r in readers])
    F = np.array([[1.0 if (("qwen" in r) == ("qwen" in m)) else 0.0
                   for m in makers] for r in readers])

    def dc(A):
        return A - A.mean(1, keepdims=True) - A.mean(0, keepdims=True) + A.mean()

    def spearman(x, y):
        rx = np.argsort(np.argsort(x))
        ry = np.argsort(np.argsort(y))
        return float(np.corrcoef(rx, ry)[0, 1])

    Md, Td, Fd = dc(M), dc(T), dc(F)

    def perm_p(obs, X):
        rng = random.Random(SEED0 + 3)
        ge = 0
        for _ in range(N_PERMS):
            P = Md.copy()
            for i in range(P.shape[0]):
                row = list(P[i])
                rng.shuffle(row)
                P[i] = row
            ge += abs(spearman(dc(P).ravel(), X.ravel())) >= abs(obs)
        return (ge + 1) / (N_PERMS + 1)

    tok_r = spearman(Md.ravel(), Td.ravel())
    fam_r = spearman(Md.ravel(), Fd.ravel())
    tok_p = perm_p(tok_r, Td)
    fam_p = perm_p(fam_r, Fd)
    # family-vs-tokenizer: correlation of margins with family AFTER rank-regressing out
    # tokenizer overlap (residual rank relation)
    rT = np.argsort(np.argsort(Td.ravel())).astype(float)
    rM = np.argsort(np.argsort(Md.ravel())).astype(float)
    beta = np.polyfit(rT, rM, 1)
    resid = rM - np.polyval(beta, rT)
    fam_resid_r = spearman(resid, Fd.ravel())
    status = ("RIVAL-FAVORED" if (tok_p < 0.05 and abs(tok_r) >= abs(fam_r)
                                  and abs(fam_resid_r) < 0.2)
              else "QUIET")
    (OUT / "s6_tokenizer.json").write_text(json.dumps(
        {"scout": "E24-S6", "status": status,
         "tokenizer_overlap_rank_r": tok_r, "tokenizer_p": tok_p,
         "family_rank_r": fam_r, "family_p": fam_p,
         "family_after_tokenizer_residual_r": fam_resid_r,
         "overlap_matrix": {f"{r}->{m}": round(float(T[i, j]), 4)
                            for i, r in enumerate(readers)
                            for j, m in enumerate(makers)},
         "note": "QUIET means the tokenizer rival does not displace the family account; "
                 "it never affirms family by itself"}, indent=1),
        encoding="utf-8", newline="\n")
    print(f"{status}: tokenizer r {tok_r:.3f} (p {tok_p:.5f}), family r {fam_r:.3f} "
          f"(p {fam_p:.5f}), family-after-tokenizer {fam_resid_r:.3f}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=["run"])
    ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rc = arm_run()
    print(f"s6 in {(time.time() - t0) / 60:.0f} min")
    return rc


if __name__ == "__main__":
    sys.exit(main())
