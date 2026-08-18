"""G149 text port — does the motivation-shift sampler find KNOWN specification shifts in text?

The gridworld ruler passed (L127: planted goal switches detected at 89.5% with priced false
alarms). This is the same instrument concept ported to text, where the known shift is a splice
between two ladder artifacts on the SAME TOPIC at DIFFERENT specification doses (the ladder
holds topic constant across rungs by construction, so a rung-crossed same-topic splice isolates
the specification change from topic).

    SAMPLER     per 40-word window: the 9 static surface features + the 40-word function-word
                profile (the pan25 channel builders, reused); shift score at each interior
                boundary = cosine distance between adjacent window feature vectors, z-scored
                within item; detected shift = argmax
    ARMS        planted (rung-0 first half + rung-60 second half, same topic, known boundary),
                null (unspliced full texts, threshold = 95th percentile of max score),
                topic-splice comparison (same rung, different topics -- the confound bound:
                the sampler is EXPECTED to fire here too, and the number says how much of any
                detection could be topic rather than specification)
    GATES       planted rung-crossed shifts detected above the null threshold and localized
                within +/- 1 window boundary; unspliced items quiet at 5% by construction

CPU only, no model calls. Output: results/g149/text_port.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runners"))

RESULTS = REPO / "results" / "g149"
LADDER = REPO / "corpora" / "ladder3"
W = 40
LOC_TOL = 1
SEED = 53


def features(words: list[str], statics, fw_profile) -> list[float]:
    text = " ".join(words)
    return list(statics(text, None)) + list(fw_profile(text))


def windows(text: str) -> list[list[str]]:
    ws = text.split()
    return [ws[i:i + W] for i in range(0, len(ws) - W + 1, W)]


def shift_curve(text: str, np, statics, fw_profile):
    wins = windows(text)
    if len(wins) < 4:
        return None
    F = np.array([features(w, statics, fw_profile) for w in wins], float)
    F = (F - F.mean(0)) / (F.std(0) + 1e-9)
    d = []
    for i in range(len(F) - 1):
        a, b = F[i], F[i + 1]
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        d.append(1.0 - float(a @ b) / (na * nb + 1e-12))
    d = np.array(d)
    return (d - d.mean()) / (d.std() + 1e-9)


def main() -> None:
    import numpy as np                                                # noqa: PLC0415
    from build_pan25_channels import statics as _st                   # noqa: PLC0415
    from build_pan25_channels import fw_profile as _fw                # noqa: PLC0415

    def statics(text, _):
        return _st(text, {})                       # empty rank dict: rank features constant,
                                                   # harmless under per-item z-scoring

    rng = np.random.default_rng(SEED)
    metas = {}
    for f in sorted(LADDER.glob("r*.json")):
        m = json.loads(f.read_text(encoding="utf-8"))
        metas.setdefault(m["topic"], {})[m["rung"]] = f.with_suffix(".txt")
    rungs_all = sorted({r for v in metas.values() for r in v})
    lo, hi = rungs_all[0], rungs_all[-1]
    topics = [t for t, v in metas.items() if lo in v and hi in v]

    def txt(p):
        return p.read_text(encoding="utf-8", errors="replace").strip()

    # null arm: unspliced texts, all rungs
    null_max = []
    for t, v in metas.items():
        for r, p in v.items():
            c = shift_curve(txt(p), np, statics, _fw)
            if c is not None:
                null_max.append(float(c.max()))
    thr = float(np.quantile(null_max, 0.95))

    def splice_arm(pairs):
        det, over, errs, n = 0, 0, [], 0
        for ta, pa, tb, pb in pairs:
            wa, wb = txt(pa).split(), txt(pb).split()
            half = len(wa) // 2
            spliced = " ".join(wa[:half] + wb[half:])
            c = shift_curve(spliced, np, statics, _fw)
            if c is None:
                continue
            n += 1
            true_b = half // W - 1                # boundary index nearest the splice
            if float(c.max()) > thr:
                over += 1
                err = abs(int(np.argmax(c)) - true_b)
                errs.append(err)
                if err <= LOC_TOL:
                    det += 1
        return {"n": n, "detected_and_localized": det,
                "detection_rate": round(det / max(n, 1), 4),
                "over_threshold_rate": round(over / max(n, 1), 4),
                "localization_mae_windows": round(float(np.mean(errs)), 3) if errs else None}

    # planted arm: same topic, rung-crossed
    planted = [(t, metas[t][lo], t, metas[t][hi]) for t in topics]
    # confound bound: same rung, different topics
    cross = []
    for i, ta in enumerate(topics):
        tb = topics[(i + 1) % len(topics)]
        cross.append((ta, metas[ta][lo], tb, metas[tb][lo]))

    out = {"seed": SEED, "window_words": W, "loc_tol_windows": LOC_TOL,
           "rungs_spliced": [lo, hi], "n_null": len(null_max),
           "threshold_null_q95": round(thr, 3),
           "planted_same_topic_rung_crossed": splice_arm(planted),
           "confound_bound_same_rung_topic_crossed": splice_arm(cross)}
    RESULTS.mkdir(parents=True, exist_ok=True)
    dest = RESULTS / "text_port.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))
    print(f"wrote {dest.relative_to(REPO)}")


if __name__ == "__main__":
    main()
