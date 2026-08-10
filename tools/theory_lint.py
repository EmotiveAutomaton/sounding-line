"""PostToolUse format linter for docs/theory/*.md (the subagent's step-1 recommendation).

Reads the hook JSON on stdin, filters to theory files IN THE SCRIPT (the hook `if:` glob
semantics changed across Claude Code versions, so path filtering lives here), and checks the
mechanically decidable subset of docs/theory/README.md's format spec:

    1. every hypothesis table is followed (within a few lines) by a bold afterword paragraph
    2. that afterword carries a Confidence line using the fixed vocabulary
    3. no em or en dashes in prose (quote blocks and code blocks excepted; his style ruling)

Violations exit 2 with the specific rule text on stderr, which Claude Code shows to the model
for same-turn self-correction. PostToolUse cannot block; this is a corrective nudge with teeth.
Judgment-shaped rules (blockquotes are the curator's only, load-bearing order) stay in
.claude/rules/theory-format.md and the README itself.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CONFIDENCE_TERMS = ("untested", "one bad test away", "replicated and controlled",
                    "instrument-dead")
AFTERWORD_MARKS = ("**What the table says.**", "**What the ledger says.**",
                   "**State of the section's claim.**", "**What the dashboard says.**",
                   "**What these add up to.**")


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    fp = (payload.get("tool_input") or {}).get("file_path", "") or ""
    fp_norm = fp.replace("\\", "/").lower()
    if "docs/theory/" not in fp_norm or not fp_norm.endswith(".md") \
            or fp_norm.endswith("readme.md") or "/essays/" in fp_norm:
        sys.exit(0)
    p = Path(fp)
    if not p.exists():
        sys.exit(0)
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()

    problems: list[str] = []

    # ── tables need afterwords with a fixed-vocabulary confidence line
    i = 0
    while i < len(lines):
        if re.match(r"\|\s*#\s*\|", lines[i]):          # a hypothesis table header
            j = i
            while j < len(lines) and lines[j].startswith("|"):
                j += 1
            window = "\n".join(lines[j:j + 6])
            if not any(m in window for m in AFTERWORD_MARKS):
                problems.append(
                    f"line {j}: hypothesis table has no afterword paragraph beneath it "
                    f"(README: 'Under every hypothesis table, a short paragraph... revisited "
                    f"in the same edit')")
            else:
                k = j
                while k < len(lines) and "Confidence:" not in lines[k] \
                        and not lines[k].startswith("## "):
                    k += 1
                if k >= len(lines) or "Confidence:" not in lines[k]:
                    problems.append(
                        f"line {j}: afterword lacks a 'Confidence:' line "
                        f"(README: fixed vocabulary, every paragraph)")
                else:
                    tail = " ".join(lines[k:k + 3]).lower()
                    if not any(t in tail for t in CONFIDENCE_TERMS):
                        problems.append(
                            f"line {k + 1}: Confidence line does not use the fixed vocabulary "
                            f"({' / '.join(CONFIDENCE_TERMS)})")
            i = j
        else:
            i += 1

    # ── dash discipline: no em/en dashes in prose; quotes and code excepted
    for n, ln in enumerate(lines, 1):
        if ln.startswith(">") or ln.startswith("    ") or ln.startswith("#"):
            continue
        if "—" in ln:
            problems.append(f"line {n}: em dash in prose (his ruling: restructure the "
                            f"sentence; en dashes live only inside quote blocks)")
        elif "–" in ln:
            problems.append(f"line {n}: en dash outside a quote block (his ruling: en dashes "
                            f"exist only as em-dash replacements inside quotes)")

    if problems:
        sys.stderr.write(
            f"theory format check, {p.name}: {len(problems)} issue(s)\n" +
            "\n".join("  - " + x for x in problems[:10]) +
            ("\n  (more suppressed)" if len(problems) > 10 else "") +
            "\nFix in this turn; the spec is docs/theory/README.md.\n")
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
