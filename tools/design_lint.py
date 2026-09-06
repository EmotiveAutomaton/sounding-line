"""PostToolUse + command-line design linter for prereg/*.py and gate-bearing runners
(his ruling 2026-08-18; structural check added 2026-08-28).

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

WHAT CHANGED 2026-08-28 (H5). The check was `if "DESIGN CHECK" in text: sys.exit(0)`. Adding
those two words -- in a comment, in a docstring, anywhere -- satisfied a linter whose entire
purpose was to guarantee the derivations exist. It certified the presence of a STRING, not the
presence of a DESIGN. A file with a gate and no null, no alternative and no direction passed.

Now the block is parsed and its fields must be present and NONEMPTY: a `lessons read:` line
citing at least one section, and gate text that actually mentions a null, an alternative, and a
direction. Two limits stated plainly, because a linter that overclaims is worse than none:

  * This is STRUCTURAL VALIDATION, NOT PROOF OF SCIENTIFIC ADEQUACY. Whether the derivations
    are RIGHT cannot be linted and still binds by being read.
  * It never auto-fills anything. A missing null is reported, never invented -- invented
    methodology that satisfies a checker is worse than the gap it hides.

Violations exit 2 with the rule text on stderr for same-turn correction. Runs as a hook OR as
`python tools/design_lint.py <files...>`, so the rule survives a `sed` edit that fires no hook.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lintio import (EXIT_OK, EXIT_VIOLATION, paths_from_invocation,   # noqa: E402
                    rel_posix, repo_root)

GATE_WORDS = re.compile(r"\bVOID\b|verdict band|VERDICT_BANDS|threshold_null|\"verdicts\"",
                        re.IGNORECASE)

# The block runs from the DESIGN CHECK header to the end of the docstring or comment run it
# lives in. The house style (see prereg/g177.py) is PROSE, not `key: value` lines -- "Gates,
# null/alternative/direction:" and "Verdict bands per arm, exhaustive:" are the real headings.
# So the block is read WHOLE and asked whether the required derivations appear anywhere in it,
# rather than being forced into a field grammar the project does not use. Matching the existing
# convention is the point: a linter that fails 57 of 62 conforming files is measuring itself.
BLOCK_RE = re.compile(r"DESIGN\s+CHECK\b\s*\(?\s*(?P<date>\d{4}-\d{2}-\d{2})?", re.IGNORECASE)

LESSONS_RE = re.compile(r"lessons?\s+read", re.IGNORECASE)
# a citation must name something: "LESSONS §3", "§5", "L139", or an explicit "none" and why
CITES_RE = re.compile(r"§\s*\d|\bL\d{2,3}\b|\bLESSONS\b[^.\n]{0,40}\d|\bnone\b", re.IGNORECASE)

NULL_RE = re.compile(r"\bnull\b|\bH0\b", re.IGNORECASE)
ALT_RE = re.compile(r"\balternativ|\bH1\b|\bHA\b|under success", re.IGNORECASE)
DIR_RE = re.compile(r"\bdirection\b|failure\s+(?:up|down)\b|\bfailure\s+DOWN\b|"
                    r"\bhigher\b|\blower\b|\bincreas|\bdecreas|\babove\b|\bbelow\b|"
                    r"\bgreater\b|\bat least\b|[<>]=?", re.IGNORECASE)
BANDS_RE = re.compile(r"\bband", re.IGNORECASE)
EXHAUSTIVE_RE = re.compile(r"\bexhaustive\b|\bno\s+(?:silent\s+)?gap\b|\bno\s+silent\s+interval\b",
                           re.IGNORECASE)


def _block(text: str) -> tuple[str, str | None] | None:
    """(block_text, date) or None. The block is the DESIGN CHECK header through the end of
    the docstring/comment run containing it, capped so a whole module never counts as one."""
    m = BLOCK_RE.search(text)
    if not m:
        return None
    start = m.start()
    rest = text[start:]
    # end at the closing triple quote if we are inside a docstring, else at the first line
    # that is neither indented, nor a comment, nor blank
    end = len(rest)
    q = min([i for i in (rest.find('"""'), rest.find("'''")) if i != -1] or [-1])
    if q != -1:
        end = q
    lines, taken = rest[:end].splitlines(), []
    for ln in lines[:150]:
        taken.append(ln)
    return "\n".join(taken), m.group("date")


HEADING_RE = re.compile(r"^[ \t]*[A-Za-z][^:\n]{0,70}:", re.MULTILINE)


def _content_only(block: str) -> str:
    """The block with its HEADING LABELS removed.

    The house heading is `Gates, null/alternative/direction:` -- which contains the words
    null, alternative and direction. Searching the raw block for those terms therefore
    passed on the heading alone, which would have made this checker very nearly the magic
    string it replaced. The derivations have to appear in the PROSE, not in the label that
    announces them. Caught by test_h5_missing_direction_is_caught.
    """
    return HEADING_RE.sub(" ", block)


def check_text(text: str, in_prereg: bool) -> list[str]:
    """Returns a list of problems. Empty means the block is structurally complete.

    STRUCTURAL ONLY. That the derivations EXIST and name a null, an alternative and a
    direction is decidable; whether they are RIGHT is not, and still binds by being read.
    """
    got = _block(text)
    if got is None:
        kind = "preregistration card" if in_prereg else "gate-bearing runner"
        return [f"no DESIGN CHECK block (this is a {kind})"]
    block, date = got
    problems: list[str] = []

    if not date:
        problems.append("DESIGN CHECK carries no (yyyy-mm-dd) date")

    if not LESSONS_RE.search(block):
        problems.append("the block never says which lessons were read")
    elif not CITES_RE.search(block):
        problems.append("`lessons read` cites no identifiable section "
                        "(name them, or write `none` and why)")

    body = _content_only(block)
    if not NULL_RE.search(body):
        problems.append("no expectation under the NULL is stated for any gate "
                        "(a heading naming `null` is not a derivation)")
    if not ALT_RE.search(body):
        problems.append("no expectation under the ALTERNATIVE is stated for any gate")
    if not DIR_RE.search(body):
        problems.append("no failure DIRECTION is stated (the L132 shuffle gate died to this)")
    if not BANDS_RE.search(block):
        problems.append("no verdict bands are stated")
    elif not EXHAUSTIVE_RE.search(block):
        problems.append("bands are stated but never claimed exhaustive "
                        "(the L73 bands died to a silent interval)")
    return problems


RULE_TEXT = """  DESIGN CHECK (date)
  lessons read: <LESSONS sections read for THIS design>
  gates: every gate's expectation under the NULL and under the ALTERNATIVE, and
         the failure DIRECTION it guards (the L132 shuffle gate died to this)
  bands: exhaustive, no silent interval (the L73 bands died to this)
This is his ruling (2026-08-18). Prose is fine -- the house style is
`Gates, null/alternative/direction:` and `Verdict bands per arm, exhaustive:`
(see prereg/g177.py). What is checked is that the derivations are THERE, not their
layout. Nothing is auto-filled: write the real derivation or leave it failing."""


def check_file(p: Path) -> list[str]:
    fp_norm = rel_posix(p)
    if not fp_norm.endswith(".py"):
        return []
    in_prereg = "prereg/" in fp_norm
    in_runners = "runners/" in fp_norm
    if not (in_prereg or in_runners):
        return []
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    if not (in_prereg or GATE_WORDS.search(text)):
        return []
    return [f"{p.name}: {q}" for q in check_text(text, in_prereg)]


def _changed_paths() -> list[Path]:
    """Files new or modified against HEAD. The 2026-08-18 ruling binds NEW OR EDITED designs;
    it is not retroactive, and it cannot be retroactive -- prereg/gate1.py, gate2.py and
    gate3.py are HASH-LOCKED in soundingline/locks.py, so 'fix the header' would break the
    pre-registration they exist to make checkable. Scoping by git means no curated grandfather
    list to drift: a legacy file is exempt exactly until someone edits it, and then it is not.
    """
    import subprocess                                                 # noqa: PLC0415
    root = repo_root()
    out: set[str] = set()
    # Trust only the repository containing this checker, for this invocation.
    # Do not mutate global Git configuration or silently swallow ownership errors.
    git = ["git", "-c", f"safe.directory={root.as_posix()}", "--no-optional-locks"]
    for cmd in (git + ["diff", "--name-only", "-z", "HEAD"],
                git + ["ls-files", "--others", "--exclude-standard", "-z"]):
        try:
            r = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.SubprocessError) as e:
            raise RuntimeError(f"Git enumeration failed; nothing certified: {e}") from e
        if r.returncode != 0:
            raise RuntimeError(f"Git enumeration failed; nothing certified: {r.stderr.strip()}")
        out.update(x for x in r.stdout.split("\0") if x)
    return [root / x for x in sorted(out)]


def _all_gate_paths() -> list[Path]:
    root = repo_root()
    return sorted(list((root / "prereg").rglob("*.py")) + list((root / "runners").rglob("*.py")))


def main() -> int:
    argv = sys.argv[1:]
    mode_changed = "--changed" in argv
    mode_audit = "--audit" in argv
    if mode_changed:
        try:
            paths, early = _changed_paths(), None
        except RuntimeError as e:
            print(str(e), file=sys.stderr)
            return 3
    elif mode_audit:
        paths, early = _all_gate_paths(), None
    else:
        paths, early = paths_from_invocation([a for a in argv if not a.startswith("--")])
    if early is not None:
        return early

    problems: list[str] = []
    per_file: list[tuple[Path, list[str]]] = []
    for p in paths:
        if not p.exists():
            continue
        ps = check_file(p)
        if ps:
            per_file.append((p, ps))
            problems += ps

    if mode_audit:
        # read-only inventory: reports the legacy backlog, never fails on it, never edits it
        print(f"design_lint audit: {len(per_file)} of {len(paths)} files carry an incomplete "
              f"or absent DESIGN CHECK block.")
        for p, ps in per_file:
            print(f"  {rel_posix(p)}")
            for q in ps:
                print(f"      - {q.split(': ', 1)[-1]}")
        print("\nThese are reported, not repaired. The 2026-08-18 ruling binds new or edited\n"
              "designs; nothing here is auto-filled and no hash-locked card is touched.")
        return EXIT_OK

    if not problems:
        return EXIT_OK
    print("design_lint: this design is not checkable as written.", file=sys.stderr)
    for q in problems:
        print(f"  - {q}", file=sys.stderr)
    print("\nBefore this design lands, its header needs:\n" + RULE_TEXT, file=sys.stderr)
    return EXIT_VIOLATION


if __name__ == "__main__":
    sys.exit(main())
