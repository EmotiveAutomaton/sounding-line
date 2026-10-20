"""Bounded, review-gated SPGC fiction intake for the commissioned D31 card.

DESIGN CHECK: LESSONS sections 2–5 and CONTROLS read 2026-10-18.
NULL/ALTERNATIVE: acquisition and eligibility never inspect fear labels. Fiction
metadata is only a candidate frame, not proof of a novel or distinct protagonist.
Incomplete bibliographic review refuses a cohort; missing bytes or altered source
identity refuse reuse. These are input states, never scientific negatives.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import random
import re
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

SEED = 20261017
METADATA_URL = "https://zenodo.org/api/records/2422561/files/SPGC-metadata-2018-07-18.csv/content"
METADATA_SIZE = 10016560
METADATA_MD5 = "a2d5f325f13846cbec2fd21d982b4ef4"
FEAR_WORDS = tuple("afraid fear fears feared fearful frightened fright frighten frightening terror terrified terrifying horror horrified dread dreaded dreading panic panicked scared scare scary alarm alarmed apprehension anxious anxiety trembling trembled coward".split())
assert len(FEAR_WORDS) == len(set(FEAR_WORDS)) == 30
WORD = re.compile(r"\b\w+(?:['’]\w+)*\b", re.UNICODE)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf8")


def save_equal(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError("changed immutable intake output")
    else:
        with path.open("xb") as stream:
            stream.write(data)


class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlparse(newurl).scheme != "https" or urlparse(newurl).hostname not in {"zenodo.org", "www.gutenberg.org", "gutenberg.org"}:
            raise ValueError("intake redirect outside official hosts")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url, path, cap, expected_sha256=None):
    """One bounded GET, never automatic retry or whole-corpus retrieval."""
    if urlparse(url).scheme != "https" or urlparse(url).hostname not in {"zenodo.org", "www.gutenberg.org", "gutenberg.org"}:
        raise ValueError("unapproved intake host")
    path = Path(path)
    if path.exists():
        data = path.read_bytes()
        if expected_sha256 is None:
            raise ValueError("existing download needs its previously pinned hash")
    else:
        request = urllib.request.Request(url, headers={"User-Agent": "SoundingLine-Research-Intake/1.0"})
        with urllib.request.build_opener(OfficialRedirect()).open(request, timeout=60) as response:
            declared = response.headers.get("Content-Length")
            if declared is not None and int(declared) > cap:
                raise ValueError("declared download exceeds cap")
            data = response.read(cap + 1)
    if len(data) > cap or (expected_sha256 is not None and digest(data) != expected_sha256):
        raise ValueError("download size/hash refusal")
    save_equal(path, data)
    return {"url": url, "bytes": len(data), "sha256": digest(data)}


def metadata(data):
    if len(data) != METADATA_SIZE or hashlib.md5(data).hexdigest() != METADATA_MD5:
        raise ValueError("SPGC release metadata identity mismatch")
    return list(csv.DictReader(io.StringIO(data.decode("utf8"))))


def candidate_frame(rows):
    """Bibliographic candidates only; short fiction/translation/series need review."""
    authors = {}
    for row in rows:
        try:
            birth = int(row["authoryearofbirth"])
            languages = ast.literal_eval(row["language"])
            subjects = ast.literal_eval(row["subjects"])
        except (ValueError, SyntaxError):
            continue
        if not (1790 <= birth <= 1890 and languages == ["en"] and row["type"] == "Text"):
            continue
        if not any("fiction" in subject.casefold() for subject in subjects):
            continue
        if not re.fullmatch(r"PG\d+", row["id"]):
            raise ValueError("invalid Gutenberg identity")
        authors.setdefault(row["author"], []).append({"id": row["id"], "title": row["title"], "birth": birth, "subjects": sorted(subjects)})
    return {author: sorted(books, key=lambda book: int(book["id"][2:]))
            for author, books in sorted(authors.items()) if len(books) >= 3}


def author_order(frame):
    values = sorted(frame)
    random.Random(SEED).shuffle(values)
    return values


def reviewed_editions(candidates, reviews):
    """Return complete editions; a volume never stands in for its whole novel."""
    editions = {}
    for book in candidates:
        row = reviews[book['id']]
        if row['novel']:
            required = ('work_id', 'edition_id', 'part_number', 'part_count')
            if any(key not in row for key in required):
                raise ValueError('novel review lacks complete edition/part identity')
            if (not row['work_id'] or not row['edition_id'] or
                    type(row['part_number']) is not int or type(row['part_count']) is not int or
                    not 1 <= row['part_number'] <= row['part_count']):
                raise ValueError('invalid reviewed edition identity')
            key = (row['work_or_protagonist_group'], row['work_id'], row['edition_id'])
            editions.setdefault(key, []).append((row, book))
    groups = {}
    for (group, work, edition), parts in sorted(editions.items()):
        counts = {row['part_count'] for row, _ in parts}
        if len(counts) != 1:
            raise ValueError('inconsistent edition part counts')
        count = next(iter(counts))
        if sorted(row['part_number'] for row, _ in parts) != list(range(1, count + 1)):
            raise ValueError('incomplete or duplicated novel volume')
        ordered = [book for row, book in sorted(parts, key=lambda pair: pair[0]['part_number'])]
        groups.setdefault(group, {}).setdefault(work, []).append(
            {'work_id': work, 'edition_id': edition, 'parts': ordered,
             'subjects': sorted({s for book in ordered for s in book['subjects']})})
    return groups


def draw_cohort(frame, audit, count=40):
    """First eligible authors in frozen random order; all earlier reviews required.

    Each author's complete bibliographic audit declares English-language novelist
    eligibility and classifies every candidate book, with evidence and a stable
    work/protagonist-series group. Draw three groups, then one edition per group.
    Neither the audit nor the draw accepts outcome labels.
    """
    chosen, reviewed = [], []
    for author in author_order(frame):
        record = audit.get(author)
        if not record or record.get("complete") is not True or not record.get("evidence"):
            raise ValueError("missing complete bibliographic review: " + author)
        if type(record.get("english_language_novelist")) is not bool:
            raise ValueError("missing author-language eligibility")
        books = record.get("books", {})
        expected = {book["id"] for book in frame[author]}
        if set(books) != expected:
            raise ValueError("review does not cover all candidate editions")
        for book in frame[author]:
            review = books[book["id"]]
            if type(review.get("novel")) is not bool or not review.get("evidence"):
                raise ValueError("missing novel decision/evidence")
            if review["novel"]:
                if not review.get("work_or_protagonist_group"):
                    raise ValueError("missing edition/series grouping")
        groups = reviewed_editions(frame[author], books)
        reviewed.append(author)
        if not record["english_language_novelist"] or len(groups) < 3:
            continue
        rng = random.Random(str(SEED) + "|" + author)
        group_names = sorted(groups)
        rng.shuffle(group_names)
        selected = []
        for group in group_names[:3]:
            work = rng.choice(sorted(groups[group]))
            edition = rng.choice(sorted(groups[group][work], key=lambda row: row['edition_id']))
            selected.append(dict(edition, work_or_protagonist_group=group))
        chosen.append({"author": author, "books": selected})
        if len(chosen) == count:
            subjects = {subject for item in chosen for book in item["books"] for subject in book["subjects"]}
            if len(subjects) < 3:
                raise ValueError("insufficient subject-label coverage")
            return {"seed": SEED, "reviewed_authors": reviewed, "cohort": chosen,
                    "frame_sha256": digest(canonical(frame)), "audit_sha256": digest(canonical(audit))}
    raise ValueError("fewer than required eligible authors")


def book_body(text):
    start = re.search(r"^\*\*\* START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK[^\n]*\*\*\*\s*$", text, re.M | re.I)
    end = re.search(r"^\*\*\* END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK[^\n]*\*\*\*\s*$", text, re.M | re.I)
    if not start or not end or end.start() <= start.end():
        raise ValueError("unrecognized Gutenberg body delimiters")
    return text[start.end():end.start()]


def passages(body, book_id, maximum=100):
    tokens = list(WORD.finditer(body))
    hits = [i for i, token in enumerate(tokens) if token.group().casefold() in FEAR_WORDS]
    windows, previous_end = [], -1
    for hit in hits:
        left = max(0, min(hit - 150, len(tokens) - 300))
        right = min(len(tokens), left + 300)
        if left < previous_end:
            continue
        windows.append((left, right))
        previous_end = right
    rng = random.Random(str(SEED) + "|passages|" + book_id)
    if len(windows) > maximum:
        windows = sorted(rng.sample(windows, maximum))
    result = []
    for left, right in windows:
        start, end = tokens[left].start(), tokens[right - 1].end()
        value = body[start:end]
        result.append({"book": book_id, "word_start": left, "word_end": right,
                       "char_start": start, "char_end": end, "text": value, "sha256": digest(value.encode("utf8"))})
    return result
