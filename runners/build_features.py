"""Extract and cache all 342 features for every corpus, whole-artifact and windowed.

Extraction costs ~1.35 s per 400-word window, so a full sweep is ~30 minutes. Every downstream
analysis reuses this cache rather than re-extracting, which is what makes the re-validation pass
cheap enough to run over everything we have ever claimed.

── WHY WINDOWED AS WELL AS WHOLE ─────────────────────────────────────────────────────────────

`docs/theory/CURATOR_GUESSES.md` B1 — his primary detector, and the largest unexploited item in
the project:

    When I've been talking about the veneer... it is the VARIATION. An opening reaching for
    professional register and then relaxing out of it. The performance is what costs something, so
    the performance is what slips, and the slip is where the maker shows.

**Not one measure in this project has ever kept a within-artifact spread.** Every one computes a
whole-document mean and throws the variation away. Caching per-window features makes the variance
of all 342 available as measures in their own right, at no extra cost.

Worth holding in view while this runs: Gate 3's N13 null failed on a within-artifact sd of **0.808**
against a between-half signal of **0.087**. We recorded that as instability in the measure. B1 says
it may have been the signal.

── WINDOWING ─────────────────────────────────────────────────────────────────────────────────

Fixed 400-word non-overlapping windows, capped per artifact so a long text cannot outvote a short
one, and **artifacts yielding fewer than 3 windows are marked** — a variance over two windows is not
a variance, and letting those through would put noise in the same column as signal.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUT = REPO / "results" / "features"
WINDOW = 400
MAX_WINDOWS = 8
MIN_WINDOWS = 3


def windows(text: str, n: int = WINDOW, cap: int = MAX_WINDOWS) -> list[str]:
    w = text.split()
    out = [" ".join(w[i:i + n]) for i in range(0, len(w) - n + 1, n)]
    if len(out) <= cap:
        return out
    step = len(out) / cap
    return [out[int(i * step)] for i in range(cap)]


def load_corpus(name: str) -> list[dict]:
    """Every corpus, normalised to {id, group, text}."""
    if name in ("ladder", "ladder2", "ladder3"):
        d = REPO / "corpora" / name
        man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
        return [{"id": it["id"], "group": it["rung"],
                 "text": (d / f"{it['id']}.txt").read_text(encoding="utf-8")}
                for it in man["items"] if (d / f"{it['id']}.txt").exists()]
    if name == "nomaker":
        d = REPO / "corpora" / "nomaker"
        man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
        return [{"id": it["id"], "group": it["kind"],
                 "text": (d / f"{it['id']}.txt").read_text(encoding="utf-8")}
                for it in man["items"] if (d / f"{it['id']}.txt").exists()]
    if name == "argrewrite":
        from runners.run_argrewrite import load as la                  # noqa: PLC0415
        return [{"id": f"{a}_d{d}", "group": d, "text": txt}
                for a, dr in la().items() for d, txt in dr.items()]
    if name == "gate3":
        from runners.run_gate3 import load_corpus as lc                # noqa: PLC0415
        out = []
        for i, (aid, half, text) in enumerate(lc()):
            out.append({"id": str(aid), "group": str(half), "text": text})
        return out
    raise ValueError(name)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpora", default="ladder,ladder2,nomaker,gate3")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    from soundingline.measures.features import extract                 # noqa: PLC0415

    OUT.mkdir(parents=True, exist_ok=True)
    for cname in args.corpora.split(","):
        dest = OUT / f"{cname}.json"
        if dest.exists() and not args.force:
            # A cache written by a broken environment holds empty feature dicts, and skipping it
            # froze a corrupt file for three days (audit L26). Validate before trusting.
            try:
                cached = json.loads(dest.read_text(encoding="utf-8"))["items"]
                ok = bool(cached) and bool(cached[0].get("whole")) and bool(cached[-1].get("whole"))
            except Exception:                                          # noqa: BLE001
                ok = False
            if ok:
                print(f"{cname}: cached, skipping")
                continue
            print(f"{cname}: cache invalid (empty or truncated) — rebuilding")
        try:
            rows = load_corpus(cname)
        except Exception as e:                                         # noqa: BLE001
            print(f"{cname}: SKIPPED — {type(e).__name__}: {e}")
            continue
        print(f"{cname}: {len(rows)} artifacts", flush=True)
        t0 = time.time()
        out = []
        buf = io.StringIO()
        for i, r in enumerate(rows):
            ws = windows(r["text"])
            with contextlib.redirect_stdout(buf):                      # biberplus is noisy
                whole = extract(r["text"])
                wfeat = [extract(w) for w in ws]
            if not whole:
                raise RuntimeError(f"{cname}/{r['id']}: extract() returned 0 features — "
                                   "environment broken, refusing to write a poisoned cache")
            out.append({"id": r["id"], "group": r["group"],
                        "n_words": len(r["text"].split()),
                        "n_windows": len(ws),
                        "enough_windows": len(ws) >= MIN_WINDOWS,
                        "whole": whole, "windows": wfeat})
            if (i + 1) % 10 == 0:
                el = time.time() - t0
                print(f"  {i + 1}/{len(rows)}  {el / (i + 1):.1f}s each, "
                      f"~{el / (i + 1) * (len(rows) - i - 1) / 60:.0f} min left", flush=True)
            # checkpoint under a temp name: a reader must never see a partial cache at the
            # final path (a concurrent audit recorded prefix statistics — audit L26)
            dest.with_suffix(".building").write_text(
                json.dumps({"corpus": cname, "window": WINDOW,
                            "min_windows": MIN_WINDOWS, "items": out}),
                encoding="utf-8", newline="\n")
        import os                                                      # noqa: PLC0415
        os.replace(dest.with_suffix(".building"), dest)
        short = sum(1 for o in out if not o["enough_windows"])
        print(f"  done in {(time.time() - t0) / 60:.1f} min. "
              f"{short} artifacts with <{MIN_WINDOWS} windows (excluded from variance analyses)",
              flush=True)


if __name__ == "__main__":
    main()
