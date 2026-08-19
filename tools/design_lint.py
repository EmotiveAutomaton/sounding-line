"""PostToolUse design linter for prereg/*.py and gate-bearing runners (his ruling 2026-08-18).

The rushed-design failure class kept recurring THROUGH the prose re-read rule: the L73 verdict
bands left a silent gap, and the L132 shuffle gate fired on the alternative hypothesis's own
signature because its direction and its expectation under success were never derived. Both
defects were made at design time, both were mechanically preventable, and the record's own
observation is that code-side rules hold where prose rules drift. So the rule gets teeth.

Any NEW OR EDITED file in prereg/, or runner that declares verdict machinery (the words VOID,
verdict band, or threshold in its text), must carry a DESIGN CHECK block:

    DESIGN CHECK (yyyy-mm-dd)
    lessons read: <the LESSONS sections read for THIS design, by number>
    gates: for EVERY gate or band -- its expectation under the NULL, its expectation under
           the ALTERNATIVE, and the failure DIRECTION it guards
    bands: exhaustive (no silent interval), stated

Violations exit 2 with the rule text on stderr for same-turn correction. Advisory with teeth,
same contract as theory_lint. The judgment half (whether the derivations are RIGHT) cannot be
linted and still binds by being read; this only guarantees the derivations exist.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

GATE_WORDS = re.compile(r"\bVOID\b|verdict band|VERDICT_BANDS|threshold_null|\"verdicts\"",
                        re.IGNORECASE)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:                                                 # noqa: BLE001
        sys.exit(0)
    fp = (payload.get("tool_input") or {}).get("file_path", "") or ""
    fp_norm = fp.replace("\\", "/").lower()
    if not fp_norm.endswith(".py"):
        sys.exit(0)
    in_prereg = "/prereg/" in fp_norm
    in_runners = "/runners/" in fp_norm
    if not (in_prereg or in_runners):
        sys.exit(0)
    try:
        text = Path(fp).read_text(encoding="utf-8", errors="replace")
    except OSError:
        sys.exit(0)
    gatey = bool(GATE_WORDS.search(text))
    if not (in_prereg or gatey):
        sys.exit(0)
    if "DESIGN CHECK" in text:
        sys.exit(0)
    kind = "preregistration card" if in_prereg else "gate-bearing runner"
    print(
        f"design_lint: {Path(fp).name} is a {kind} without a DESIGN CHECK block.\n"
        "Before this design lands, add to its header:\n"
        "  DESIGN CHECK (date)\n"
        "  lessons read: <LESSONS sections read for THIS design>\n"
        "  gates: every gate's expectation under the NULL and under the ALTERNATIVE, and\n"
        "         the failure DIRECTION it guards (the L132 shuffle gate died to this)\n"
        "  bands: exhaustive, no silent interval (the L73 bands died to this)\n"
        "This is his ruling (2026-08-18): the derivations exist in writing before the run.",
        file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
