"""Shared hook/CLI plumbing for the linters (H5, 2026-08-28).

Both linters were hook-only: they did `json.load(sys.stdin)` and nothing else. Three
consequences, all of them observed rather than theorised:

  1. NO COMMAND ENTRY POINT. Run `python tools/theory_lint.py docs/theory/DECISION_TRACES.md`
     and argv is ignored while the script blocks forever on a stdin that never reaches EOF.
     Two such processes were found alive on 2026-08-28 having hung since 2026-08-24 16:19.
     They are why this file exists.
  2. THE RULE ONLY EXISTED IF A HOOK FIRED. A file written by `sed`, a heredoc, or a runner
     is never an Edit/Write tool call, so nothing checked it. An advisory hook cannot be the
     only enforcement of an invariant.
  3. MALFORMED HOOK INPUT WAS SILENT. `except: sys.exit(0)` treated an unreadable payload the
     same as a clean pass.

`paths_from_invocation()` accepts both shapes and NEVER blocks: stdin is read only when it is
not a TTY, and only after argv has been tried.

Exit codes, same contract for both linters and for CI:
    0  nothing to check, or everything passed
    2  a violation (PostToolUse shows stderr to the model for same-turn correction)
    3  the invocation itself was unusable (malformed payload); distinct from "passed"
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

EXIT_OK, EXIT_VIOLATION, EXIT_BAD_INPUT = 0, 2, 3


def paths_from_invocation(argv: list[str] | None = None) -> tuple[list[Path], int | None]:
    """Returns (paths, early_exit_code). A non-None code means exit immediately with it.

    Order matters: argv first, so a human running this at a shell is never left hanging on
    stdin. Hook mode is entered only when argv carries no paths AND stdin is a real pipe.
    """
    argv = list(sys.argv[1:] if argv is None else argv)
    args = [a for a in argv if not a.startswith("-")]
    if args:
        return [Path(a) for a in args], None
    if sys.stdin is None or sys.stdin.isatty():
        # interactive with no arguments: say what to do instead of blocking on stdin
        print(f"usage: {Path(sys.argv[0]).name} <file> [file ...]   "
              f"(or pipe a PostToolUse hook payload on stdin)", file=sys.stderr)
        return [], EXIT_OK
    raw = sys.stdin.read()
    if not raw.strip():
        return [], EXIT_OK                      # empty payload: nothing was edited
    try:
        payload = json.loads(raw)
    except ValueError as e:
        print(f"{Path(sys.argv[0]).name}: hook payload is not valid JSON ({e}). "
              f"Nothing was checked.", file=sys.stderr)
        return [], EXIT_BAD_INPUT
    fp = (payload.get("tool_input") or {}).get("file_path") or ""
    return ([Path(fp)] if fp else []), None


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def rel_posix(p: Path) -> str:
    """Path as the checkers want to match it: forward slashes, lowercase, repo-relative
    where possible. Portable: no machine-specific absolute prefixes are baked in."""
    try:
        s = str(p.resolve().relative_to(repo_root()))
    except (ValueError, OSError):
        s = str(p)
    return s.replace(os.sep, "/").replace("\\", "/").lower()
