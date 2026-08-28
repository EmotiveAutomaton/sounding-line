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

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lintio import (EXIT_OK, EXIT_VIOLATION, paths_from_invocation,   # noqa: E402
                    rel_posix, repo_root)

CONFIDENCE_TERMS = ("untested", "one bad test away", "replicated and controlled",
                    "instrument-dead")
AFTERWORD_MARKS = ("**What the table says.**", "**What the ledger says.**",
                   "**State of the section's claim.**", "**What the dashboard says.**",
                   "**What these add up to.**")


def check_file(p: Path) -> list[str]:
    """The format checks for one theory file. Returns problems; empty means it passed."""
    fp_norm = rel_posix(p)
    if "docs/theory/" not in fp_norm or not fp_norm.endswith(".md") \
            or fp_norm.endswith("readme.md") or "/essays/" in fp_norm:
        return []
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()

    problems: list[str] = []

    # ── tables need afterwords with a fixed-vocabulary confidence line
    i = 0
    while i < len(lines):
        if re.match(r"\|\s*#\s*\|", lines[i]):          # a hypothesis table header
            j = i
            while j < len(lines) and lines[j].startswith("|"):
                j += 1
            # The window runs to the NEXT SECTION, not a fixed six lines (widened 2026-08-28).
            # The rule the README states is that a table has an afterword before its section
            # ends, and six lines could not express that: THE_TRIPLE_INFERENCE §5 puts a
            # definitional paragraph between its table and "State of the section's claim.",
            # and THREE_COGNITIVE_LAYERS §7 puts a curator quotation and a supersession note
            # there. Both were reported as having NO afterword when both have a correct one.
            # This is not a loosened rule: an afterword must still exist before the next `## `,
            # and test_theory_lint_still_catches_a_genuinely_missing_afterword pins that.
            end = j
            while end < len(lines) and not lines[end].startswith("## "):
                end += 1
            window = "\n".join(lines[j:end])
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

    return problems


def main() -> int:
    """Hook OR command line. Runs the SAME checks either way, so a `sed` edit or a runner
    write is checkable even though it fires no PostToolUse hook (H5).

    Why this is not `json.load(sys.stdin)` any more: with no piped payload that call blocks
    forever. Two of these were found alive on 2026-08-28 having hung since 2026-08-24 16:19,
    started by someone reasonably running `python tools/theory_lint.py <file>` -- argv was
    ignored and the process simply stopped. `paths_from_invocation` tries argv first and only
    reads stdin when it is a real pipe.
    """
    argv = sys.argv[1:]
    if "--all" in argv:
        paths = sorted((repo_root() / "docs" / "theory").rglob("*.md"))
        early = None
    else:
        paths, early = paths_from_invocation([a for a in argv if not a.startswith("--")])
    if early is not None:
        return early
    rc = EXIT_OK
    for p in paths:
        problems = check_file(p)
        if problems:
            rc = EXIT_VIOLATION
            sys.stderr.write(
                f"theory format check, {p.name}: {len(problems)} issue(s)\n" +
                "\n".join("  - " + x for x in problems[:10]) +
                ("\n  (more suppressed)" if len(problems) > 10 else "") +
                "\nFix in this turn; the spec is docs/theory/README.md.\n")
    return rc


if __name__ == "__main__":
    sys.exit(main())
