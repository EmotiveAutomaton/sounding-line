"""The canonical lock verifier. Run from anywhere; exits 1 on any missing or altered
locked file. Replaces the ad-hoc inline snippets used before 2026-08-21.

`soundingline/locks.py` is itself hash-locked and never edited, so when a locked file
MOVES, the lock keeps its original path as the key and the move is recorded twice: in
`docs/method/DEVIATIONS.md` (the human record) and in PATH_MAP below (the executable
record). The two must agree; a mapping here without its deviation entry is a defect.

    python tools/verify_locks.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from soundingline.hashlock import hash_file                            # noqa: E402
from soundingline.locks import LOCKS                                   # noqa: E402

# lock key (original path) -> current path, per docs/method/DEVIATIONS.md
PATH_MAP = {
    # 2026-08-08: five gate-era files moved in the documentation reorganisation
    # (docs/gateN/... -> docs/gates/gateN/...), handled by prefix below.
    # 2026-08-21: the founding spec moved off the repo top level at the curator's
    # instruction.
    "SOUNDING_LINE_SPEC.md": "docs/SOUNDING_LINE_SPEC.md",
}


def current_path(lock_key: str) -> Path:
    if lock_key in PATH_MAP:
        return REPO / PATH_MAP[lock_key]
    p = REPO / lock_key
    if not p.exists() and lock_key.startswith("docs/gate"):
        return REPO / lock_key.replace("docs/gate", "docs/gates/gate", 1)
    return p


def main() -> int:
    bad = []
    for key, expected in LOCKS.items():
        p = current_path(key)
        if not p.exists():
            bad.append((key, "MISSING", str(p)))
            continue
        actual = hash_file(p)
        if actual != expected:
            bad.append((key, "HASH MISMATCH", str(p)))
    if bad:
        for key, kind, path in bad:
            print(f"LOCK FAIL {kind}: {key} (checked {path})")
        return 1
    print(f"ALL {len(LOCKS)} LOCKS OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
