"""SC1. Sealed text marker and survey-column support counts for CANDOR.

DESIGN CHECK: LESSONS 2–5. Count each conversation once per turn model and
marker. Gate each cell using its actual distinct people, including separate
non-null survey denominators. Never emit a token, transcript, survey value,
identifier, source path or free-form exception. The six literal markers do
not label the acoustic event or establish a restart annotation.
"""
import csv
import hashlib
import os
import re
from pathlib import Path

for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[variable] = "2"

PINS = {
    "audiophile": ("transcripts/transcript_audiophile.parquet", 43399859, "037ec8d200f31d7f38980b19c3d1997a7eea4100d84e73b62f16d9d41fd5edb7"),
    "backbiter": ("transcripts/transcript_backbiter.parquet", 37426911, "4e1fb3aa1e7b4478bce306bab3ec1f666ce6b11947f76b0a34803d4e53d4540d"),
    "cliffhanger": ("transcripts/transcript_cliffhanger.parquet", 27136920, "07c40837f21e083a365d9cc5f2bbcfcd59b381fe0fbad0d744a7a4d4c749dfd4"),
    "natural_turn": ("transcripts/transcript_natural_turn.parquet", 77781591, "cd06ebd96e6c613a79cdc4b2c3ac2bf37eac9e1b3962bc3d1cf999b8fd5b661b"),
    "survey": ("surveys/survey.parquet", 1784918, "1002f2f06e2651180c38ed27c66145ca4f3a6fd8bb4833af351c76d2f6c45f39"),
}
MARKERS = {
    "bracketed_laughter": r"\[laughter\]", "laugh": r"\blaugh\b", "haha": r"\bhaha\b",
    "um": r"\bum\b", "uh": r"\buh\b", "mm_hmm": r"\bmm-hmm\b",
}
PATTERNS = {key: re.compile(value, re.IGNORECASE) for key, value in MARKERS.items()}
MIN_PEOPLE = 11


class Unavailable(Exception):
    pass


def source_layout(root, pins):
    layouts = [base for base in (root, root / "processed") if any(
        (base / name).is_file() for name, _, _ in pins.values())]
    if len(layouts) != 1:
        raise Unavailable(21)
    base = layouts[0]
    # One integrity pass and one descriptive projection, with room for Parquet footers.
    if sum(3 * size for _, size, _ in pins.values()) > 2_000_000_000:
        raise Unavailable(22)
    for name, size, digest in pins.values():
        p = base / name
        if not p.is_file():
            continue
        if p.stat().st_size != size:
            raise Unavailable(23)
        with p.open("rb") as src:
            if hashlib.file_digest(src, "sha256").hexdigest() != digest:
                raise Unavailable(23)
    return base


def text_cells(version, batches):
    speakers, conversations = set(), set()
    hits = {name: (set(), set()) for name in MARKERS}
    for batch in batches:
        for conversation, speaker, text in batch:
            if not conversation or not speaker or not isinstance(text, str) or not text.strip():
                continue
            speakers.add(speaker)
            conversations.add(conversation)
            for name, pattern in PATTERNS.items():
                if pattern.search(text):
                    hits[name][0].add(speaker)
                    hits[name][1].add(conversation)
    coverage = dict(version=version, n=len(speakers), conversations=len(conversations))
    rows = [dict(version=version, marker=name, n=len(persons), conversations=len(convos))
            for name, (persons, convos) in hits.items() if len(persons) >= MIN_PEOPLE]
    return coverage, rows


def survey_cells(table):
    import pyarrow.compute as pc
    people = table.column("user_id").to_pylist()
    if len(table.column_names) != len(set(table.column_names)):
        raise Unavailable(24)
    rows = []
    for key in table.column_names:
        valid = pc.is_valid(table.column(key)).to_pylist()
        observed = {person for person, ok in zip(people, valid) if ok and person}
        if len(observed) >= MIN_PEOPLE:
            rows.append(dict(column=key, n=len(observed)))
    return rows


def project(root, pins, batch_size):
    import pyarrow.parquet as pq
    base = source_layout(root, pins)
    sizes, markers, statuses = [], [], []
    result = {}
    for name, (path, _, _) in pins.items():
        file = base / path
        if not file.is_file():
            continue
        reader = pq.ParquetFile(file)
        present = set(reader.schema_arrow.names)
        required = ("user_id",) if name == "survey" else ("conversation_id","speaker","utterance")
        person_column = "user_id" if name == "survey" else "speaker"
        if person_column not in present:
            continue
        if not set(required).issubset(present):
            observed = set()
            for batch in reader.iter_batches(batch_size=batch_size,columns=[person_column],use_threads=False):
                observed.update(person for person in batch.column(0).to_pylist() if person)
            if len(observed)>=MIN_PEOPLE:
                statuses.append(dict(version=name,n=len(observed),required_fields=len(required),
                                     present_fields=len(set(required)&present)))
            continue
        if name == "survey":
            table = reader.read(use_threads=False)
            result["survey_columns"] = survey_cells(table)
            n = len({who for who in table.column("user_id").to_pylist() if who})
            if n>=MIN_PEOPLE:
                statuses.append(dict(version=name,n=n,required_fields=1,present_fields=1))
            continue
        def batches():
            for batch in reader.iter_batches(batch_size=batch_size, use_threads=False,
                                             columns=["conversation_id", "speaker", "utterance"]):
                yield zip(*(batch.column(j).to_pylist() for j in range(3)))
        size, rows = text_cells(name, batches())
        if size["n"] >= MIN_PEOPLE:
            sizes.append(size)
            statuses.append(dict(version=name,n=size["n"],required_fields=3,present_fields=3))
        markers.extend(rows)
    result.update(transcript_coverage=sizes, markers=markers, source_status=statuses)
    return result


def write_tables(output, tables):
    output.mkdir(exist_ok=True)
    total = 0
    ready = {}
    for name, rows in tables.items():
        if not rows:
            continue
        if len(rows) > 2000 or any(type(row["n"]) is not int or row["n"] < 0 for row in rows):
            raise Unavailable(25)
        rows = [row for row in rows if row["n"] >= MIN_PEOPLE]
        if not rows:
            continue
        from io import StringIO
        buf = StringIO(newline="")
        writer = csv.DictWriter(buf, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        data = buf.getvalue().encode("utf8")
        total += len(data)
        ready[name] = data
    if not ready or total > 256 * 1024:
        raise Unavailable(26)
    for name, data in ready.items():
        with (output / (name + ".csv")).open("xb") as dest:
            dest.write(data)


def run(root, output, pins=PINS):
    tables = project(root, pins, batch_size=16384)
    write_tables(output, tables)


if __name__ == "__main__":
    try:
        run(Path("/data"), Path("/out"))
    except Unavailable as exc:
        raise SystemExit(int(exc.args[0])) from None
    except Exception:
        raise SystemExit(28) from None
