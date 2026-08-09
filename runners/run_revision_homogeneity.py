"""G81 — self-revision is homogeneous; imposed change is lumpy. First measurement.

The connoisseurship import: a maker's own revisions are "of like kind" throughout, while imposed
changes show "distinct steps." Operationalised distributionally: per author, the paragraph-level
change magnitude between drafts; homogeneity = low dispersion of those magnitudes. The control is
synthetic imposition: splice paragraphs from another author into draft 1 at the same total change
volume and ask whether the statistic separates real self-revision from the splice.

    SEPARATES   real-vs-spliced AUC > 0.7 on the dispersion statistic
    BLIND       it cannot tell them apart — the import needs a sharper statistic
"""

from __future__ import annotations

import difflib
import json
import random
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "revision_homogeneity"
ESSAYS = REPO / "corpora" / "public" / "argrewrite" / "essays"


def paras(text: str) -> list[str]:
    return [p.strip() for p in text.split("\n") if len(p.split()) > 15]


def change_profile(a: list[str], b: list[str]) -> list[float]:
    out = []
    for i, pa in enumerate(a):
        best = max((difflib.SequenceMatcher(None, pa, pb).ratio() for pb in b), default=0.0)
        out.append(1.0 - best)
    return out


def dispersion(profile: list[float]) -> float:
    import numpy as np                                                # noqa: PLC0415
    p = np.array(profile)
    return float(p.std() / (p.mean() + 1e-9))


def main() -> None:
    import numpy as np                                                # noqa: PLC0415

    # draft folders disagree on stems: Draft1 holds draft1_2018argrewrite_N, Draft3 holds
    # 2018argrewrite_N — normalise by stripping any draftN_ prefix before pairing
    def norm(stem: str) -> str:
        return re.sub(r"^draft\d+_", "", stem)

    d1 = {norm(p.stem): p.read_text(encoding="utf-8", errors="ignore")
          for p in (ESSAYS / "Draft1").glob("*.txt")}
    d3 = {norm(p.stem): p.read_text(encoding="utf-8", errors="ignore")
          for p in (ESSAYS / "Draft3").glob("*.txt")}
    ids = sorted(set(d1) & set(d3))
    print(f"{len(ids)} authors with draft 1 and draft 3")
    rng = random.Random(9)

    real, spliced = [], []
    for aid in ids:
        pa, pb = paras(d1[aid]), paras(d3[aid])
        if len(pa) < 4 or len(pb) < 3:
            continue
        prof = change_profile(pa, pb)
        real.append(dispersion(prof))
        # synthetic imposition: replace ~30% of draft-1 paragraphs with another author's
        other = d1[rng.choice([x for x in ids if x != aid])]
        po = paras(other)
        k = max(1, len(pa) * 3 // 10)
        idxs = rng.sample(range(len(pa)), k)
        forged = list(pa)
        for i in idxs:
            forged[i] = rng.choice(po) if po else forged[i]
        spliced.append(dispersion(change_profile(pa, forged)))

    labels = [0] * len(real) + [1] * len(spliced)
    scores = real + spliced
    order = np.argsort(scores)
    ranks = np.empty(len(scores))
    ranks[order] = np.arange(1, len(scores) + 1)
    n1 = sum(labels)
    n0 = len(labels) - n1
    auc = (float(sum(r for r, l in zip(ranks, labels) if l)) - n1 * (n1 + 1) / 2) / (n0 * n1)
    print(f"real dispersion median {np.median(real):.3f}  spliced {np.median(spliced):.3f}  "
          f"AUC {auc:.3f}")
    verdict = "SEPARATES" if auc > 0.7 else "BLIND"
    print(f"  >>> {verdict}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.json").write_text(json.dumps(
        {"n_authors": len(real), "real_median": float(np.median(real)),
         "spliced_median": float(np.median(spliced)), "auc": float(auc),
         "verdict": verdict}, indent=2), encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / 'summary.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
