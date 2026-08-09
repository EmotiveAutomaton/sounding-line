"""PD-28 — is the revision effect polish or depth? The labels have been on disk all along.

The ArgRewrite annotations label each revision's purpose (surface vs content classes). The L5
effect — revision raises lexical sophistication — is either polish (if it lives in
surface-labelled revisions) or **the first depth signal on human text** (if it survives among
content-only revisions).

Schema-defensive: the workbook layout is undocumented here, so this runner first maps the schema
of three files; if it cannot find a purpose column it exits NEEDS-SCHEMA with the dump instead of
guessing. Sentence-level: revised sentences are attributed a purpose class; the sophistication
delta (mean word length, rare-word rate, stopword rate) is computed per class.

    POLISH      the sophistication shift concentrates in surface-labelled revisions
    DEPTH       it survives at full strength among content-labelled revisions — the first
                depth signal on human text
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "revision_purpose"
ANNOT = REPO / "corpora" / "public" / "argrewrite" / "annotations"

SURFACE = {"fluency", "spelling", "grammar", "word-usage", "wordusage", "clarity", "convention",
           "conventions", "organization", "surface"}
CONTENT = {"claim", "claims", "evidence", "reasoning", "rebuttal", "warrant", "idea",
           "development", "content", "precision"}


def soph(sent: str) -> tuple[float, float, float]:
    words = re.findall(r"[a-zA-Z']+", sent.lower())
    if not words:
        return (0.0, 0.0, 0.0)
    stop = {"the", "a", "an", "and", "or", "but", "of", "to", "in", "is", "was", "it", "that"}
    return (sum(map(len, words)) / len(words),
            sum(1 for w in words if len(w) > 8) / len(words),
            sum(1 for w in words if w in stop) / len(words))


def main() -> None:
    import numpy as np                                                # noqa: PLC0415
    from openpyxl import load_workbook                                # noqa: PLC0415

    files = sorted(ANNOT.rglob("*.xlsx"))
    print(f"{len(files)} annotation workbooks")

    # schema mapping on the first three
    schema_dump = []
    purpose_col = old_col = new_col = None
    for f in files[:3]:
        wb = load_workbook(f, read_only=True, data_only=True)
        ws = wb.active
        header = [str(c.value).strip().lower() if c.value else "" for c in next(ws.iter_rows())]
        schema_dump.append({"file": f.name, "header": header})
        for i, h in enumerate(header):
            if purpose_col is None and any(t in h for t in ("purpose", "label", "type", "category")):
                purpose_col = i
            if old_col is None and any(t in h for t in ("old", "before", "original", "draft1", "d1")):
                old_col = i
            if new_col is None and any(t in h for t in ("new", "after", "revised", "draft2", "d2")):
                new_col = i
        wb.close()
    print("schema:", json.dumps(schema_dump[:1], indent=1)[:400])
    if purpose_col is None or new_col is None:
        RESULTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / "summary.json").write_text(json.dumps(
            {"verdict": "NEEDS-SCHEMA", "schema_dump": schema_dump}, indent=2),
            encoding="utf-8", newline="\n")
        print(">>> NEEDS-SCHEMA — headers dumped, no purpose/new column recognised")
        return

    deltas = {"surface": [], "content": [], "other": []}
    for f in files:
        try:
            wb = load_workbook(f, read_only=True, data_only=True)
            ws = wb.active
            rows = ws.iter_rows()
            next(rows)
            for r in rows:
                vals = [c.value for c in r]
                if len(vals) <= max(purpose_col, new_col):
                    continue
                purpose = str(vals[purpose_col] or "").strip().lower()
                new_s = str(vals[new_col] or "")
                old_s = str(vals[old_col] or "") if old_col is not None else ""
                if not purpose or not new_s:
                    continue
                cls = ("surface" if any(t in purpose for t in SURFACE) else
                       "content" if any(t in purpose for t in CONTENT) else "other")
                sn, so = soph(new_s), soph(old_s)
                deltas[cls].append([sn[i] - so[i] for i in range(3)])
            wb.close()
        except Exception as e:                                        # noqa: BLE001
            print(f"  skip {f.name}: {type(e).__name__}")

    out = {"counts": {k: len(v) for k, v in deltas.items()}}
    print("revision counts:", out["counts"])
    for k in ("surface", "content"):
        if deltas[k]:
            arr = np.array(deltas[k])
            out[k] = {"d_wordlen": float(arr[:, 0].mean()), "d_rare": float(arr[:, 1].mean()),
                      "d_stop": float(arr[:, 2].mean())}
            print(f"{k}: wordlen {arr[:, 0].mean():+.4f}  rare {arr[:, 1].mean():+.4f}  "
                  f"stop {arr[:, 2].mean():+.4f}  (n={len(arr)})")
    if deltas["surface"] and deltas["content"]:
        s, c = out["surface"], out["content"]
        depth_carries = c["d_wordlen"] >= 0.5 * s["d_wordlen"] and c["d_rare"] >= 0.5 * s["d_rare"]
        out["verdict"] = "DEPTH-SIGNAL" if depth_carries else "POLISH"
    else:
        out["verdict"] = "NEEDS-SCHEMA"
    print(f"\n  >>> {out['verdict']}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.json").write_text(json.dumps(out, indent=2),
                                          encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / 'summary.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
