"""Stage-2 Tree-S scout E24-S08 (discovery lane): causal direction transfer. The geometry
leg is twice-measured and descriptive; this asks whether mapped geometry is USED.

Method. In the MAKER's representation space, fit goal directions (difference of means per
goal over the maker's own artifacts, last-quarter pooled states). Fit a linear map from
maker space to reader space on the eighty neutral shared texts (ridge), and push each goal
direction through it. Then, while the reader scores a maker artifact's candidate set,
amplify or ablate the mapped direction of that artifact's TRUE goal at the reader's
three-quarter-depth block, artifact tokens only, and watch the true-candidate margin.

If aligned geometry is causally used, amplification should raise the true margin and
ablation lower it, selectively against matched controls. If geometry is merely
descriptive, nothing selective moves.

DESIGN CHECK (2026-08-23, discovery lane). Lessons read at build time: section 3 (known
answer before signal: the mapped direction must decode the goal in READER space on held-out
artifacts above chance, or the map failed and the causal test is uninterpretable; the
criterion can fail by construction since a bad map produces noise directions; controls are
norm-matched, and the control gate carries its own null-effect failure condition per the
L162 corollary), section 5 (produces guard, gpulock once). Failure directions: decode gate
DOWN means INSTRUMENT-FAILED, no causal claim either way; sign pair without control
separation is generic steering, never transfer; capability shift beyond 5 percent voids the
dose. Statuses are scout words only.
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
SEED0 = 18800
MAKERS = {"Qwen/Qwen2.5-1.5B": "g172",
          "HuggingFaceTB/SmolLM2-1.7B-Instruct": "g172_family2"}
READERS = ["Qwen/Qwen2.5-1.5B", "HuggingFaceTB/SmolLM2-1.7B-Instruct"]
ALPHAS = (4.0, 8.0)
CAPABILITY_TOL = 0.05
N_PERMS = 20000


def maker_artifacts(maker: str) -> list[dict]:
    from prereg.g172 import short                                                # noqa: PLC0415
    src = REPO / "corpora" / MAKERS[maker] / short(maker)
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(src.glob("art_*.json"))]


def pooled_last_quarter(model, tok, texts: list[str]) -> np.ndarray:
    import torch                                                                 # noqa: PLC0415
    n_blocks = model.config.num_hidden_layers
    take = list(range(max(0, n_blocks - max(1, n_blocks // 4)), n_blocks))
    rows = []
    for t in texts:
        enc = tok(t, return_tensors="pt", add_special_tokens=False,
                  truncation=True, max_length=384).to("cuda")
        with torch.no_grad():
            hs = model(**enc, output_hidden_states=True).hidden_states[1:]
        rows.append(np.mean([hs[b][0].mean(0).float().cpu().numpy() for b in take], axis=0))
    return np.stack(rows)


def key_of(name: str) -> str:
    from runners.scout_stage2_geo import MAKER_SHORT                             # noqa: PLC0415
    return (MAKER_SHORT.get(name, name.split("/")[-1]).lower()
            .replace(".", "").replace("-", "_"))


def arm_run() -> int:
    import torch                                                                 # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock          # noqa: PLC0415
    from soundingline.probe.conditional_reader import (artifact_logprob,         # noqa: PLC0415
                                                       candidate_scores,
                                                       free_readers, load_reader)
    from soundingline.probe.interventions import SubspaceIntervention, get_blocks  # noqa: PLC0415
    from prereg.g174 import NEUTRAL_PASSAGES                                     # noqa: PLC0415
    from prereg.g172 import candidate                                            # noqa: PLC0415

    neutral_reps = {p.stem: np.load(p)
                    for p in (OUT / "geo_reps_neutral").glob("*.npy")}
    rng = random.Random(SEED0)
    results = {}
    acquire_gpu_lock("scout_s8")
    try:
        for maker in MAKERS:
            arts = maker_artifacts(maker)
            m_model, m_tok = load_reader(maker, device="cuda", dtype="float16")
            m_reps = pooled_last_quarter(m_model, m_tok, [a["text"] for a in arts])
            free_readers()
            goals = sorted({a["goal_i"] for a in arts})
            mu = m_reps.mean(0)
            m_dirs = {}
            for g in goals:
                sel = np.array([a["goal_i"] == g for a in arts])
                d = m_reps[sel].mean(0) - mu
                m_dirs[g] = d / (np.linalg.norm(d) + 1e-9)

            for reader in READERS:
                if reader == maker:
                    continue
                cell = f"{key_of(maker)}->{key_of(reader)}"
                print(f"== {cell} ==")
                X = neutral_reps[key_of(maker)]
                Y = neutral_reps[key_of(reader)]
                lam = 1.0
                W = np.linalg.solve(X.T @ X + lam * np.eye(X.shape[1]), X.T @ Y)
                mapped = {g: (d @ W) / (np.linalg.norm(d @ W) + 1e-9)
                          for g, d in m_dirs.items()}

                r_model, r_tok = load_reader(reader, device="cuda", dtype="float16")
                r_reps = pooled_last_quarter(r_model, r_tok, [a["text"] for a in arts])
                # KNOWN-ANSWER: mapped directions must decode the maker's goal in reader
                # space, held-out by topic parity
                test = [i for i, a in enumerate(arts) if a["topic_i"] % 2 == 1]
                mu_r = r_reps.mean(0)
                hits = 0
                for i in test:
                    scores = {g: float((r_reps[i] - mu_r) @ mapped[g]) for g in goals}
                    hits += max(scores, key=scores.get) == arts[i]["goal_i"]
                ka = hits / len(test)
                print(f"  decode gate {ka:.3f} vs chance {1 / len(goals):.2f}")
                if ka < 0.45:
                    results[cell] = {"status": "INSTRUMENT-FAILED", "decode_gate": ka}
                    free_readers()
                    continue

                n_blocks = len(get_blocks(r_model))
                blk = int(n_blocks * 0.75)
                d_model = r_reps.shape[1]
                sample = rng.sample(arts, min(40, len(arts)))
                g_ctrl = torch.Generator().manual_seed(SEED0 + 3)
                rand_dir = torch.randn(d_model, 1, generator=g_ctrl)
                shuf = {g: mapped[goals[(gi + 1) % len(goals)]]
                        for gi, g in enumerate(goals)}

                def margins(mode, alpha, dirs) -> list[float]:
                    out = []
                    for a in sample:
                        iv = None
                        if mode:
                            u = torch.tensor(dirs[a["goal_i"]],
                                             dtype=torch.float32).reshape(d_model, 1) \
                                if isinstance(dirs, dict) else dirs
                            iv = SubspaceIntervention(
                                {blk: u}, {blk: torch.zeros(d_model)}, alpha, mode)
                        cands = [candidate(a["topic_i"], g) for g in range(4)]
                        res = candidate_scores(r_model, r_tok, cands, a["text"],
                                               intervention=iv)
                        t = a["goal_i"]
                        out.append(res["scores"][t]
                                   - (sum(res["scores"]) - res["scores"][t]) / 3)
                    return out

                base = margins(None, 0, None)
                arms = {}
                for al in ALPHAS:
                    arms[f"amp_{al}"] = margins("amplify", al, mapped)
                arms["ablate"] = margins("ablate", 1.0, mapped)
                arms["rand_amp"] = margins("amplify", ALPHAS[0], rand_dir)
                arms["shuf_amp"] = margins("amplify", ALPHAS[0], shuf)

                def perm_p(diffs):
                    r2 = random.Random(SEED0 + 7)
                    obs = sum(diffs) / len(diffs)
                    ge = sum(1 for _ in range(N_PERMS)
                             if abs(sum(x * r2.choice((1, -1)) for x in diffs)
                                    / len(diffs)) >= abs(obs))
                    return obs, (ge + 1) / (N_PERMS + 1)

                deltas = {k: perm_p([a - b for a, b in zip(v, base)])
                          for k, v in arms.items()}
                best_amp = max((deltas[f"amp_{al}"][0] for al in ALPHAS))
                abl = deltas["ablate"][0]
                ctrl = max(abs(deltas["rand_amp"][0]), abs(deltas["shuf_amp"][0]))
                cap_b = [artifact_logprob(r_model, r_tok, "Text follows.", p)[0]
                         for p in NEUTRAL_PASSAGES[:4]]
                iv_c = SubspaceIntervention(
                    {blk: torch.tensor(mapped[goals[0]],
                                       dtype=torch.float32).reshape(d_model, 1)},
                    {blk: torch.zeros(d_model)}, ALPHAS[0], "amplify")
                cap_a = [artifact_logprob(r_model, r_tok, "Text follows.", p,
                                          intervention=iv_c)[0]
                         for p in NEUTRAL_PASSAGES[:4]]
                cap = abs(sum(cap_a) / 4 - sum(cap_b) / 4) / abs(sum(cap_b) / 4)
                sign_pair = best_amp > 0 and abl < 0
                selective = ctrl < 0.5 * max(abs(best_amp), 1e-9)
                status = ("INSTRUMENT-FAILED" if cap > CAPABILITY_TOL else
                          "PROMISING" if (sign_pair and selective
                                          and min(deltas[f"amp_{al}"][1]
                                                  for al in ALPHAS) < 0.05) else
                          "RIVAL-FAVORED" if (sign_pair and not selective) else "QUIET")
                results[cell] = {"status": status, "decode_gate": ka, "block": blk,
                                 "n_sample": len(sample),
                                 "deltas": {k: {"mean": v[0], "p": v[1]}
                                            for k, v in deltas.items()},
                                 "capability_change": cap}
                print(f"  {status}: amp {best_amp:+.4f}, abl {abl:+.4f}, "
                      f"ctrl {ctrl:.4f}, cap {cap:.4f}")
                free_readers()
    finally:
        release_gpu_lock()
    overall = ("PROMISING" if any(v["status"] == "PROMISING" for v in results.values())
               else "QUIET" if any(v["status"] == "QUIET" for v in results.values())
               else "INSTRUMENT-FAILED")
    (OUT / "s8_transfer.json").write_text(json.dumps(
        {"scout": "E24-S08", "status": overall, "cells": results,
         "note": "discovery lane; a PROMISING here opens nothing by itself and routes to "
                 "the promotion conjunction"}, indent=1), encoding="utf-8", newline="\n")
    print(f"overall {overall}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=["run"])
    ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rc = arm_run()
    print(f"s8 in {(time.time() - t0) / 60:.0f} min")
    return rc


if __name__ == "__main__":
    sys.exit(main())
