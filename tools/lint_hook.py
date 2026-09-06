"""One portable entry point for both linters (H5, 2026-08-28).

THE PROBLEM. `.claude/settings.json` names two absolute Windows paths per hook -- the venv
interpreter and the script:

    "command": "e:\\EmotiveAutomaton\\...\\.venv\\Scripts\\python.exe",
    "args":    ["e:\\EmotiveAutomaton\\...\\tools\\theory_lint.py"]

That is one machine. A fresh clone anywhere else -- a different drive letter, another user, a
Linux box, a worktree -- silently runs NOTHING: a hook whose interpreter does not exist cannot
report that it did not run, so both rules would look enforced while being absent. The `args`
field is NOT itself the defect (the documented hook schema supports it); the hardcoded
locations are.

THE ADAPTER. This file resolves the repo from its OWN location (`__file__`), so it is correct
from any working directory, on any machine, under any drive letter. It needs only the standard
library, so the system `python` works and the venv is not required.

It accepts every shape:
    python tools/lint_hook.py                  # hook payload on stdin, dispatches by path
    python tools/lint_hook.py <file> [file..]  # command line
    python tools/lint_hook.py --changed        # CI: designs new or modified against HEAD
    python tools/lint_hook.py --all            # CI: every theory file

Exit codes are lintio's: 0 pass, 2 violation, 3 unusable invocation. A hook that fails is
ADVISORY -- it cannot block the tool call. That is why the same checks must also be reachable
from a runner or CI invocation, which is what `--changed` / `--all` are for. Advisory hook
failure is not a substitute for a failed invariant.
"""

from __future__ import annotations

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

from lintio import EXIT_OK, paths_from_invocation, rel_posix  # noqa: E402


def _dispatch(paths: list[Path]) -> int:
    import design_lint                                                # noqa: PLC0415
    import theory_lint                                                # noqa: PLC0415
    rc = EXIT_OK
    for p in paths:
        if not p.exists():
            continue
        norm = rel_posix(p)
        problems: list[str] = []
        if "docs/theory/" in norm:
            problems = theory_lint.check_file(p)
            if problems:
                sys.stderr.write(
                    f"theory format check, {p.name}: {len(problems)} issue(s)\n"
                    + "\n".join("  - " + x for x in problems[:10])
                    + ("\n  (more suppressed)" if len(problems) > 10 else "")
                    + "\nFix in this turn; the spec is docs/theory/README.md.\n")
        elif norm.endswith(".py"):
            problems = design_lint.check_file(p)
            if problems:
                sys.stderr.write("design_lint: this design is not checkable as written.\n"
                                 + "\n".join("  - " + x for x in problems)
                                 + "\n\nBefore this design lands, its header needs:\n"
                                 + design_lint.RULE_TEXT + "\n")
        if problems:
            rc = 2
    return rc


def main() -> int:
    argv = sys.argv[1:]
    if "--changed" in argv:
        import design_lint                                            # noqa: PLC0415
        try:
            return _dispatch(design_lint._changed_paths())
        except RuntimeError as e:
            print(str(e), file=sys.stderr)
            return 3
    if "--all" in argv:
        root = TOOLS.parent
        return _dispatch(sorted((root / "docs" / "theory").rglob("*.md")))
    paths, early = paths_from_invocation([a for a in argv if not a.startswith("--")])
    if early is not None:
        return early
    return _dispatch(paths)


if __name__ == "__main__":
    sys.exit(main())
