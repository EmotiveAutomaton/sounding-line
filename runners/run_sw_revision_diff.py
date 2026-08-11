"""G141 — is the HF revision `anonymous_data` (pinned by the authors' training code)
byte-identical in membership to `main` (what we trained on)?

The subagent pin (2026-08-11) found both published training scripts load
revision="anonymous_data", which is gated to outsiders; we hold gated access. If the split
membership differs from main, no protocol match can reconcile the numbers, so this runs before
the faithful arms are interpreted.

Fingerprint per split: the sorted multiset of per-row sha256 over (before text, after text,
label), reduced to one digest. Same digest = same membership regardless of row order.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results" / "scholawrite"
OUT = RESULTS / "revision_diff.json"


def fingerprint(split) -> tuple[str, int]:
    cols = split.column_names
    bt = next((c for c in cols if "before" in c.lower()), cols[0])
    at = next((c for c in cols if "after" in c.lower()), None)
    lb = next((c for c in cols if "label" in c.lower() or "intention" in c.lower()), None)
    hashes = []
    for row in split:
        key = (str(row.get(bt, "")) + "\x1f" + str(row.get(at, "") if at else "")
               + "\x1f" + str(row.get(lb, "") if lb else ""))
        hashes.append(hashlib.sha256(key.encode("utf-8", "replace")).hexdigest())
    hashes.sort()
    whole = hashlib.sha256("".join(hashes).encode()).hexdigest()
    return whole, len(hashes)


def main() -> None:
    from datasets import load_dataset                                 # noqa: PLC0415
    report: dict = {"splits": {}}
    main_ds = load_dataset("minnesotanlp/scholawrite",
                           cache_dir=str(RESULTS / "hf_cache"))
    anon = load_dataset("minnesotanlp/scholawrite", revision="anonymous_data",
                        cache_dir=str(RESULTS / "hf_cache_anon"))
    identical = True
    for split in sorted(set(main_ds.keys()) | set(anon.keys())):
        m = fingerprint(main_ds[split]) if split in main_ds else ("ABSENT", 0)
        a = fingerprint(anon[split]) if split in anon else ("ABSENT", 0)
        same = m[0] == a[0]
        identical &= same
        report["splits"][split] = {"main_n": m[1], "anon_n": a[1], "same": same}
        print(f"{split}: main n={m[1]} anon n={a[1]} -> {'SAME' if same else 'DIFFERS'}")
    report["verdict"] = "IDENTICAL" if identical else "DIFFERS"
    print(f">>> {report['verdict']}")
    OUT.write_text(json.dumps(report, indent=1), encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
