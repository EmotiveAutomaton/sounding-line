"""Re-export the reading set after the first session was contaminated by recognition.

── WHAT WENT WRONG AND WHAT THIS FIXES ───────────────────────────────────────────────────────

The first export drew ten artifacts at random from the store. Three problems, all found by the
curator inside twenty minutes:

  1. Two artifacts were by the SAME well-known author, and both were recognised from LINE SHAPE
     before a word was read.
  2. Two more were from the Gate 2 calibration set the curator had already read.
  3. Extraction cruft — HTML comment residue, a trailing list of translation links — carried the
     source's identity plainly.

So: keep slot 01, which has already been read and whose reading stands. Replace 02-10 under three
constraints that the first export had none of.

  ONE ARTIFACT PER HOST.       Two essays by one author is one author, and the second one is a
                               recognition hazard rather than an observation.
  NOTHING ALREADY READ.        Anything in the Gate 2 calibration set is excluded by URL.
  SANITISED.                   `report.sanitize` strips pre-reading identity cues and reflows the
                               line shape.

── THE COST, STATED ──────────────────────────────────────────────────────────────────────────

Sanitising breaks C-21's "the human reads the same bytes the probe reads". The probe read the raw
extraction; the curator now reads something cleaner. The trade is deliberate and the reasoning is
in `sanitize.py`: recognition destroys the reading, while extraction noise only degrades a
comparison. Slot 01 was read UNSANITISED and is left that way rather than quietly reissued, so the
set is not uniform and the record says which is which.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from urllib.parse import urlparse

import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from soundingline.report.sanitize import sanitize            # noqa: E402

STORE = REPO / "corpora" / "store"
OUT = REPO / "to_be_read"
KEY = REPO / "results" / "reading_key.json"


def host_of(url: str) -> str:
    h = urlparse(url).hostname or "?"
    if h == "web.archive.org":
        return "archived:" + (url.split("/http", 1)[-1].split("/")[0] if "/http" in url else url)
    return h.removeprefix("www.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--keep", type=int, default=1, help="how many leading slots to leave alone")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--max-chars", type=int, default=9000)
    args = ap.parse_args()

    old = json.loads(KEY.read_text(encoding="utf-8"))["key"]
    keep_labels = [f"artifact_{i:02d}" for i in range(1, args.keep + 1)]
    kept = {lb: old[lb] for lb in keep_labels if lb in old}

    # Everything already seen: the kept slots, the discarded slots, and Gate 2's calibration set.
    seen_urls = {v["url"] for v in old.values()}
    seen_hosts = {host_of(v["url"]) for v in kept.values()}
    g2 = REPO / "corpora" / "manifests" / "gate2.json"
    if g2.exists():
        for it in json.loads(g2.read_text(encoding="utf-8")).get("items", []):
            seen_urls.add(it.get("final_url", it.get("url", "")))

    recs = []
    for m in sorted(STORE.glob("*.meta.json")):
        d = json.loads(m.read_text(encoding="utf-8"))
        txt = STORE / f"{m.name.replace('.meta.json', '')}.txt"
        if txt.exists() and d["final_url"] not in seen_urls:
            recs.append((d, txt))

    random.Random(args.seed).shuffle(recs)

    picked, used_hosts = [], set(seen_hosts)
    for d, txt in recs:
        h = host_of(d["final_url"])
        if h in used_hosts:
            continue
        body = sanitize(txt.read_text(encoding="utf-8"))[: args.max_chars]
        if len(body) < 500:          # a stub after sanitising is not a reading
            continue
        used_hosts.add(h)
        picked.append((d, body))
        if len(picked) >= args.n - len(kept):
            break

    for p in OUT.glob("artifact_*.txt"):
        if p.stem not in keep_labels:
            p.unlink()

    key = dict(kept)
    for i, (d, body) in enumerate(picked, len(kept) + 1):
        label = f"artifact_{i:02d}"
        (OUT / f"{label}.txt").write_text(body, encoding="utf-8")
        key[label] = {"url": d["final_url"], "sha256": d["sha256"],
                      "n_chars_full": d["n_chars"], "exported_chars": len(body),
                      "sanitised": True}
    for lb in kept:
        key[lb]["sanitised"] = False

    KEY.write_text(json.dumps({"seed": args.seed, "sanitised": True,
                               "note": ("slots 1..%d predate sanitisation and were read raw"
                                        % len(kept)),
                               "key": key}, indent=2), encoding="utf-8")

    print(f"kept {len(kept)}, re-exported {len(picked)} -> {OUT.relative_to(REPO)}/")
    for lb in sorted(key):
        print(f"  {lb}.txt  {key[lb]['exported_chars']:>6} chars  "
              f"{'raw' if not key[lb]['sanitised'] else 'sanitised'}")


if __name__ == "__main__":
    main()
