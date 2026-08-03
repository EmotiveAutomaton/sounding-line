"""Export artifacts as plain text, exactly as the instrument sees them.

── WHY THIS EXISTS ───────────────────────────────────────────────────────────────────────────

The curator, unprompted:

    I'm realizing now that I'm drawing too much information from surface level indicators on the
    text... The website surface level is going to inform my reading more than I want it to
    consistently. The addition of links, for example. This is something that I note and informs
    my decision in a hard to quantify way.

**Every calibration reading so far has been of a WEB PAGE. The instrument reads EXTRACTED PLAIN
TEXT.** Layout, typography, link density, how expensive the site looks — all of it reached the
curator and none of it reached the probe. So the human standard and the instrument have never been
scored on the same object, and every agreement or disagreement between them has that gap inside
it.

This is a confound in the calibration data, not in the instrument, and it is the curator's
observation rather than mine. It also cuts both ways: a well-built site inflates the human reading
of a hollow artifact, and a plain one deflates the reading of a careful artifact — which is
precisely the E40 surface-cue problem the curator already reported losing to vibe coding.

The fix is theirs too: read the same bytes the probe reads. This writes them out.

**Retro-fit note:** it does not repair the existing calibration passes. Those were readings of web
pages and are marked as such. Recorded as C-21.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STORE = REPO / "corpora" / "store"
OUT = REPO / "to_be_read"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10, help="how many to export")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max-chars", type=int, default=9000)
    args = ap.parse_args()

    metas = sorted(STORE.glob("*.meta.json"))
    recs = []
    for m in metas:
        d = json.loads(m.read_text(encoding="utf-8"))
        txt = STORE / f"{m.name.replace('.meta.json', '')}.txt"
        if txt.exists():
            recs.append((d, txt))

    random.Random(args.seed).shuffle(recs)
    picked = recs[: args.n]

    OUT.mkdir(parents=True, exist_ok=True)
    for p in OUT.glob("*.txt"):
        p.unlink()

    key = {}
    for i, (d, txt) in enumerate(picked, 1):
        # Blind label. The filename carries no domain, no date, no category — the curator has
        # already shown that a visible date alone can decide a reading (calibration 01 §0).
        label = f"artifact_{i:02d}"
        body = txt.read_text(encoding="utf-8")[: args.max_chars]
        (OUT / f"{label}.txt").write_text(body, encoding="utf-8")
        key[label] = {"url": d["final_url"], "sha256": d["sha256"],
                      "n_chars_full": d["n_chars"], "exported_chars": len(body)}

    # The key is written OUTSIDE the reading folder so it cannot be opened by accident.
    (REPO / "results" / "reading_key.json").write_text(
        json.dumps({"seed": args.seed, "key": key}, indent=2), encoding="utf-8")

    print(f"exported {len(picked)} artifacts to {OUT.relative_to(REPO)}/")
    print(f"key (do not open before reading): results/reading_key.json")
    for label in key:
        print(f"  {label}.txt  {key[label]['exported_chars']:>6} chars")


if __name__ == "__main__":
    main()
