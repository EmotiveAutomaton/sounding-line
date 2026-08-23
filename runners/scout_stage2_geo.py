"""Stage-2 Tree-S scout E24-S07 (discovery lane): does representational alignment between a
reader and a maker predict how well that reader inverts that maker's artifacts?

The trigger (Stage-2 brief section 5, S7): a stable pairwise inversion matrix, which the
crossed reversal supplied twice. This is the DESCRIPTIVE half only; causal transfer (S8)
waits behind it.

Method. Every reader and every maker representation is captured on the SAME shared text set
(the mechanically normalized artifacts from both maker families: shared, process-matched,
already read by every model in the matrix; recorded as process-matched rather than neutral).
Linear CKA between each reader-maker pair at the aligned late stage (mean-pooled states from
the last quarter of each model's blocks). Then the linkage: does CKA(reader, maker) predict
margin(reader on maker's artifacts) BEYOND reader quality and maker difficulty? Both sides
are double-centered (reader means and maker means removed) so a strong reader or an easy
maker cannot manufacture the correlation, and the statistic is a rank correlation over the
double-centered cells with a within-reader permutation null.

DESIGN CHECK (2026-08-23, discovery lane). Lessons read at build time: section 3 (the L61
n-much-smaller-than-d rule: raw CKA magnitudes are uninterpretable at this sample size, so
the quotable object is the correspondence-null-tested match structure and the linkage rank
statistic, never a CKA value; the criterion can fail, since shuffled text correspondence
must destroy the alignment or the whole capture is noise), section 5 (produces guard,
gpulock once). Failure directions: correspondence null NOT separating from the true pairing
means capture is uninformative, INSTRUMENT-FAILED, and no linkage is computed; a linkage
permutation p above 0.05 is QUIET, never spun.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUT = REPO / "results" / "scouts"
SEED0 = 18500
N_CORRESPONDENCE_PERMS = 100
N_LINKAGE_PERMS = 20000

MAKER_SHORT = {"Qwen/Qwen2.5-0.5B": "qwen25_05b", "Qwen/Qwen2.5-1.5B": "qwen25_15b",
               "HuggingFaceTB/SmolLM2-1.7B-Instruct": "smollm2_17b_instruct",
               "HuggingFaceTB/SmolLM2-360M-Instruct": "smollm2_360m_instruct"}


def shared_texts(source: str = "process") -> list[str]:
    """process = the normalized matrix artifacts (process-matched); neutral = human
    student essays no matrix model produced, the replication set L168 owes."""
    if source == "neutral":
        src = REPO / "corpora" / "public" / "argrewrite" / "essays" / "Draft1"
        texts = [p.read_text(encoding="utf-8", errors="ignore")[:1500]
                 for p in sorted(src.glob("*.txt"))]
        texts = [t for t in texts if len(t.split()) > 60]
    else:
        src = REPO / "corpora" / "g172_norm"
        texts = [json.loads(p.read_text(encoding="utf-8"))["text"]
                 for p in sorted(src.rglob("art_*.json"))]
    rng = random.Random(SEED0)
    rng.shuffle(texts)
    return texts[:80]


def late_reps(model_name: str, texts: list[str]) -> np.ndarray:
    """(n_texts, d) mean-pooled hidden states averaged over the last quarter of blocks."""
    import torch                                                                 # noqa: PLC0415
    from soundingline.probe.conditional_reader import load_reader, free_readers  # noqa: PLC0415
    model, tok = load_reader(model_name, device="cuda", dtype="float16")
    n_blocks = model.config.num_hidden_layers
    take = list(range(max(0, n_blocks - max(1, n_blocks // 4)), n_blocks))
    rows = []
    for t in texts:
        enc = tok(t, return_tensors="pt", add_special_tokens=False,
                  truncation=True, max_length=384).to("cuda")
        with torch.no_grad():
            hs = model(**enc, output_hidden_states=True).hidden_states[1:]
        rows.append(np.mean([hs[b][0].mean(0).float().cpu().numpy() for b in take], axis=0))
    free_readers()
    return np.stack(rows)


def linear_cka(X: np.ndarray, Y: np.ndarray) -> float:
    Xc = X - X.mean(0)
    Yc = Y - Y.mean(0)
    num = np.linalg.norm(Xc.T @ Yc, "fro") ** 2
    den = np.linalg.norm(Xc.T @ Xc, "fro") * np.linalg.norm(Yc.T @ Yc, "fro")
    return float(num / den) if den else 0.0


def arm_capture(source: str = "process") -> int:
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock          # noqa: PLC0415
    from prereg.g172 import READERS                                              # noqa: PLC0415
    from runners.scout_stage2_s import READERS2                                  # noqa: PLC0415
    texts = shared_texts(source)
    models = sorted(set(READERS + READERS2 + list(MAKER_SHORT)))
    tag = "" if source == "process" else "_neutral"
    dest_dir = OUT / ("geo_reps" + tag)
    dest_dir.mkdir(parents=True, exist_ok=True)
    acquire_gpu_lock("scout_geo_capture")
    try:
        for m in models:
            dest = dest_dir / (MAKER_SHORT.get(m, m.split("/")[-1]).lower()
                               .replace(".", "").replace("-", "_") + ".npy")
            if dest.exists():
                continue
            print(f"capturing {m}")
            np.save(dest, late_reps(m, texts))
    finally:
        release_gpu_lock()
    (OUT / f"geo_capture{tag}_done.json").write_text(json.dumps(
        {"scout": "E24-S07", "n_texts": len(texts), "n_models": len(models),
         "text_source": source}, indent=1),
        encoding="utf-8", newline="\n")
    return 0


def arm_link(source: str = "process") -> int:
    from prereg.g172 import short                                                # noqa: PLC0415
    tag = "" if source == "process" else "_neutral"
    rng = random.Random(SEED0 + 1)
    reps = {p.stem: np.load(p) for p in (OUT / ("geo_reps" + tag)).glob("*.npy")}

    # correspondence null first (the instrument gate): true-pairing CKA must exceed the
    # 95th percentile of row-shuffled CKA for the median model pair, else capture is noise
    names = sorted(reps)
    gate_pairs = [(names[i], names[j]) for i in range(len(names))
                  for j in range(i + 1, len(names))][:12]
    passed = 0
    for a, b in gate_pairs:
        true = linear_cka(reps[a], reps[b])
        null = []
        idx = list(range(reps[a].shape[0]))
        for _ in range(N_CORRESPONDENCE_PERMS):
            rng.shuffle(idx)
            null.append(linear_cka(reps[a][idx], reps[b]))
        passed += true > np.quantile(null, 0.95)
    gate_frac = passed / len(gate_pairs)
    print(f"correspondence gate: {passed}/{len(gate_pairs)} pairs separate from the null")
    if gate_frac < 0.75:
        (OUT / f"geo_link{tag}.json").write_text(json.dumps(
            {"scout": "E24-S07", "status": "INSTRUMENT-FAILED",
             "correspondence_gate": gate_frac}, indent=1), encoding="utf-8", newline="\n")
        return 0

    # margins per (reader, maker) from the landed orig+fam2 matrix chunks
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
                if mk is None:
                    continue
                cells.setdefault((rname, mk), []).append(c["margin"])
    margin = {k: sum(v) / len(v) for k, v in cells.items()}

    readers = sorted({r for r, _ in margin})
    makers = sorted({m for _, m in margin})
    key = lambda s: s.lower().replace(".", "").replace("-", "_")   # noqa: E731
    M = np.array([[margin[(r, m)] for m in makers] for r in readers])
    C = np.array([[linear_cka(reps[key(r)], reps[key(m)]) for m in makers]
                  for r in readers])
    # double-center both so reader quality and maker difficulty vanish
    def dc(A):
        return A - A.mean(1, keepdims=True) - A.mean(0, keepdims=True) + A.mean()
    Md, Cd = dc(M), dc(C)

    def spearman(x, y):
        rx = np.argsort(np.argsort(x))
        ry = np.argsort(np.argsort(y))
        return float(np.corrcoef(rx, ry)[0, 1])

    obs = spearman(Md.ravel(), Cd.ravel())
    perm_rng = random.Random(SEED0 + 2)
    ge = 0
    for _ in range(N_LINKAGE_PERMS):
        P = Md.copy()
        for i in range(P.shape[0]):                 # shuffle maker labels within reader
            row = list(P[i])
            perm_rng.shuffle(row)
            P[i] = row
        ge += abs(spearman(dc(P).ravel(), Cd.ravel())) >= abs(obs)
    p = (ge + 1) / (N_LINKAGE_PERMS + 1)
    status = "PROMISING" if (obs > 0 and p < 0.05) else "QUIET"
    print(f"linkage: double-centered rank correlation {obs:.3f}, permutation p {p:.5f} "
          f"-> {status}")
    (OUT / f"geo_link{tag}.json").write_text(json.dumps(
        {"scout": "E24-S07", "status": status, "correspondence_gate": gate_frac,
         "text_source": source,
         "n_readers": len(readers), "n_makers": len(makers),
         "double_centered_spearman": obs, "permutation_p": p,
         "note": "raw CKA magnitudes deliberately unreported (L61); only the null-tested "
                 "linkage statistic is quotable; shared texts are process-matched, not "
                 "neutral, a recorded scope limit"}, indent=1),
        encoding="utf-8", newline="\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=["capture", "link"])
    ap.add_argument("--source", default="process", choices=["process", "neutral"])
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rc = {"capture": arm_capture, "link": arm_link}[a.arm](a.source)
    print(f"{a.arm} in {(time.time() - t0) / 60:.0f} min")
    return rc


if __name__ == "__main__":
    sys.exit(main())
