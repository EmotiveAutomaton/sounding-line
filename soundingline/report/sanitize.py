"""Strip identity cues from an artifact before a human reads it.

── WHY THIS EXISTS, AND WHAT IT COSTS ────────────────────────────────────────────────────────

The curator, on the second artifact of the first blind reading session:

    I can tell this is that same guy you had me reading yesterday... And I can tell **before I
    even read the words**, because it's just the format of it. The fact that the text hits the
    next line and makes it a sort of paragraph makes it shaped the same.

Recognition arrived through LINE SHAPE, ahead of content. A hard-wrapped essay at a fixed column
is a fingerprint, and so are HTML comment residue, a bare title-and-date header, and a trailing
list of translation links. None of that is the artifact; all of it identifies the maker.

**This breaks C-21's "same bytes", deliberately, and the direction matters.** The probe reads the
store's raw extraction, cruft and all. After this, the human reads something cleaner. Any
human/probe disagreement therefore has that gap inside it, and it is logged rather than glossed.

The trade is made this way round because recognition is the worse contaminant. A curator who has
identified the author is no longer reading the artifact — they are reading their prior about a
person, which is exactly the surface-cue channel the plain-text export was built to close. Losing
byte-identity costs a comparison; losing blindness costs the reading itself.

**What this does NOT do:** it cannot remove voice, subject matter, or the thousand things that
make writing recognisable to someone who knows the writer. It removes the cues that fire *before*
reading. A curator who recognises an artifact after reading it should flag it and say so — that
is a different and much less damaging kind of contamination.
"""

from __future__ import annotations

import re

_URL_ONLY = re.compile(r"^\s*(https?://|www\.)\S+\s*$", re.I)
_HTML_RESIDUE = re.compile(r"<!--|-->|<[a-z/][^>]*>", re.I)
_DATE_LINE = re.compile(
    r"^\s*((january|february|march|april|may|june|july|august|september|october|november|"
    r"december)\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}\s+\w+\s+\d{4})\s*$", re.I)
_TRANSLATION = re.compile(
    r"^\s*(russian|japanese|romanian|spanish|german|chinese|hungarian|catalan|danish|arabic|"
    r"french|italian|korean|portuguese|polish|dutch|turkish|hebrew|czech|greek|ukrainian|"
    r"serbian|persian|farsi|vietnamese|thai|indonesian|swedish|norwegian|finnish)\s+"
    r"translation\s*$", re.I)
# The same list rendered inline rather than one-per-line: "Translations: Chinese French ...".
_TRANSLATION_INLINE = re.compile(r"^\s*translations?\s*:.{0,200}$", re.I)
_NAV_NOISE = re.compile(
    r"^\s*(home|menu|search|share|tweet|subscribe|newsletter|sign in|log in|sign up|"
    r"skip to (main )?content|back to top|next|previous|prev|read more|comments?|reply|"
    r"tags?|categor(y|ies)|archives?|rss|follow|contact|about|privacy|terms|cookie[s]?"
    r"( policy| settings)?|accept( all)?|copyright.*|all rights reserved.*)\s*[:|]?\s*$", re.I)


_ENTITY = re.compile(r"&#?\w{2,8};")

# ── DATE CENSORING ────────────────────────────────────────────────────────────────────────────
#
# The curator, overruling an earlier decision of mine to keep dates on the grounds that they were
# symmetric across the halves:
#
#     I strongly disagree with the decision to keep date in... It is just too strong of a signal
#     that overrides everything else, and the AI 100% will catch that. If you're doing any kind of
#     probe, it will hyper focus on that and there's just no reason for it not to, **because it's
#     what I did and it will be even better about doing that.**
#
# He is right and the symmetry test was the wrong test. A cue does not need to be lopsided to do
# damage; it needs to DOMINATE what follows it. He demonstrated that on himself twice in one
# session — "in the first sentence I see the smell of AI-isms linked right next to the number 2026,
# so I'm immediately suspicious and withdrawing", and then "I wasn't able to stop myself from
# scanning for a date."
#
# THE FACT THAT A DATE WAS GIVEN IS KEPT; THE VALUE IS REMOVED. A maker choosing to date their
# work is a decision and the probe should see it. The specific year is what licenses the shortcut,
# so it becomes `[year]` and the decision survives without the cue.
_MONTHS = (r"january|february|march|april|may|june|july|august|september|october|november|"
           r"december|jan|feb|mar|apr|jun|jul|aug|sept?|oct|nov|dec")
_DATE_PATTERNS: tuple[tuple[re.Pattern, str], ...] = (
    (re.compile(rf"\b(?:{_MONTHS})\.?\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+(?:19|20)\d{{2}}\b", re.I),
     "[date]"),
    (re.compile(rf"\b\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{_MONTHS})\.?,?\s+(?:19|20)\d{{2}}\b", re.I),
     "[date]"),
    (re.compile(rf"\b(?:{_MONTHS})\.?\s+(?:19|20)\d{{2}}\b", re.I), "[date]"),
    (re.compile(r"\b(?:19|20)\d{2}[-/]\d{1,2}[-/]\d{1,2}\b"), "[date]"),
    (re.compile(r"\b\d{1,2}[-/]\d{1,2}[-/](?:19|20)?\d{2}\b"), "[date]"),
    # Bare years last, so the fuller forms above claim their digits first.
    (re.compile(r"\b(?:19|20)\d{2}s\b"), "[decade]"),
    (re.compile(r"\b(?:19|20)\d{2}\b"), "[year]"),
)


def censor_dates(text: str) -> str:
    """Replace date VALUES with tags, keeping the fact that a date was given."""
    for pat, tag in _DATE_PATTERNS:
        text = pat.sub(tag, text)
    return text

# The archived half of the corpus carries the Wayback Machine's own chrome into the extraction.
# It names the origin host outright, which defeats blinding on its own, and it is also the largest
# block of non-artifact text in the store. NOTE FOR THE RECORD: the probe reads this too.
_WAYBACK = re.compile(
    r"^\s*(the wayback machine\s*-\s*http|\d+\s+captures?$|about this capture|collected by|"
    r"timestamps|collection:|save page now|screenshot|this capture|web\.archive\.org)", re.I)
_WAYBACK_WINDOW = 80
# A site name trailing the page title: "Some Title - PCGamesN", "Kill Your Dependencies | Mike
# Perham", "Contact Us ⋆ Locksmith For NYC". Applied to the first content line only.
_TITLE_SUFFIX = re.compile(r"\s*(?:[|\-–—⋆·•]|@)\s*[^|\-–—⋆·•@]{2,40}$")


def _is_noise(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if _ENTITY.fullmatch(s):
        return True
    return bool(_URL_ONLY.match(s) or _TRANSLATION.match(s) or _NAV_NOISE.match(s)
                or _DATE_LINE.match(s) or _TRANSLATION_INLINE.match(s))


def _strip_wayback(lines: list[str]) -> list[str]:
    """Drop the archive's own banner: everything up to the last banner marker near the top."""
    last = -1
    for i, ln in enumerate(lines[:_WAYBACK_WINDOW]):
        if _WAYBACK.match(ln):
            last = i
    if last < 0:
        return lines
    # The banner ends in a run of short fragments (month names, years, "success", "fail").
    j = last + 1
    while j < len(lines) and (not lines[j].strip() or len(lines[j].strip()) <= 12):
        j += 1
    return lines[j:]


def _drop_nav_runs(lines: list[str], *, run: int = 6, width: int = 32) -> list[str]:
    """Remove runs of consecutive very short lines — menus, footers, link columns.

    A single short line is a heading and stays. Six in a row is navigation. Prose almost never
    produces that shape once the artifact has been reflowed.
    """
    out, i = [], 0
    while i < len(lines):
        j = i
        while j < len(lines) and lines[j].strip() and len(lines[j].strip()) <= width:
            j += 1
        if j - i >= run:
            i = j
            continue
        out.append(lines[i])
        i += 1
    return out


def sanitize(text: str, *, reflow: bool = True, dates: bool = True) -> str:
    """Remove pre-reading identity cues and, by default, the line-shape fingerprint.

    ``reflow`` joins hard-wrapped lines back into single-line paragraphs. It is the part that
    actually did the work in the case that motivated this file, and it is separable because on an
    artifact whose line breaks are semantic — verse, code, a list — reflowing would destroy
    content rather than a fingerprint. Short lines are therefore treated as deliberate and left
    alone; only runs of long lines are joined.
    """
    if dates:
        text = censor_dates(text)
    lines = [_HTML_RESIDUE.sub("", ln).rstrip() for ln in text.splitlines()]
    lines = _strip_wayback(lines)
    lines = [ln for ln in lines if not _is_noise(ln)]
    lines = _drop_nav_runs(lines)

    # Trim leading and trailing blank runs left behind by the removals.
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    # The first content line is usually the page title, which carries the site name after a
    # separator. The title itself is content; the masthead attached to it is not.
    if lines:
        head = _TITLE_SUFFIX.sub("", lines[0].strip())
        if len(head) >= 8:
            lines[0] = head

    if not reflow:
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() + "\n"

    # Reflow: join consecutive lines into a paragraph, but only where the line ABOVE was long
    # enough to look like a wrap rather than a deliberate break. 55 is below any common wrap
    # column (64/72/80) and above most list items and headings.
    out: list[str] = []
    buf: list[str] = []

    def flush() -> None:
        if buf:
            out.append(" ".join(x.strip() for x in buf))
            buf.clear()

    for ln in lines:
        s = ln.strip()
        if not s:
            flush()
            out.append("")
            continue
        if buf and len(buf[-1].strip()) >= 55:
            buf.append(s)
        else:
            flush()
            buf.append(s)
    flush()

    body = "\n".join(out)
    body = re.sub(r"[ \t]{2,}", " ", body)
    return re.sub(r"\n{3,}", "\n\n", body).strip() + "\n"
