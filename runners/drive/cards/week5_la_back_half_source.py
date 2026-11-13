"""LA3/LA4 metadata and lemma extension over immutable, qualified LA0 rows.

DESIGN CHECK: LESSONS3--5. Preserve actual source identities, annotation/text
separation and source chronology gaps. No inferred ICSI chronology, invented
speaker role, raw identity export, reader model, or changed laugh label.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import hashlib
import hmac
import json
import re
import time
import xml.etree.ElementTree as ET
import zipfile

from . import week5_la_source as old
from .timing_p6 import gzread, gzip_equal


class SourceYield(Exception):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf8")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    data = canonical(value)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError("LA extension immutable receipt changed")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(data)
        temporary.replace(path)


def requested(output):
    return any((p / "YIELD_REQUEST.json").exists() or (p / "STOP_REQUEST.json").exists()
               for p in (output, output.parent, output.parent.parent))


def identity(salt, corpus, kind, value):
    return hmac.new(salt, (corpus + "|" + kind + "|" + value).encode(), hashlib.sha256).hexdigest()[:24]


def parse_date(value):
    for fmt in ("%d-%m-%Y", "%d-%m-%y"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc).timestamp()
        except ValueError:
            pass
    raise ValueError("unsupported AMI date syntax")


def metadata_extension(archives, salt, original, ordering=None, check=None):
    """Metadata only. Any optional date map must itself be reviewed and pinned."""
    extended = {m: {**row, "speakers": {s: dict(v) for s, v in row["speakers"].items()}}
                for m, row in original.items()}
    with zipfile.ZipFile(archives / "AMI.zip") as z:
        for node in ET.fromstring(z.read("corpusResources/meetings.xml")):
            if check:
                check()
            raw = node.get("observation")
            meeting = identity(salt, "AMI", "meeting", raw)
            if meeting not in extended:
                continue
            scenario = node.get("type") == "scenario"
            if scenario and not re.fullmatch(r"[A-Za-z]{2}\d{4}[a-d]", raw):
                raise ValueError("unrecognized AMI scenario-series identifier")
            series = raw[:-1] if scenario else raw
            rank = ord(raw[-1]) - ord("a") if scenario else 0
            date = parse_date(node.get("dateOnly", ""))
            clock = node.get("startTime", "")
            start_seconds = None
            if clock:
                if not re.fullmatch(r"\d{2}:\d{2}", clock):
                    raise ValueError("unsupported AMI start-time syntax")
                hour, minute = map(int, clock.split(":"))
                if hour > 23 or minute > 59:
                    raise ValueError("invalid AMI start clock")
                start_seconds = date + hour * 3600 + minute * 60
            extended[meeting].update(group=identity(salt, "AMI", "group", series),
                                     series_rank=rank, order_qualified=True,
                                     ordering_basis="AMI scenario phases a-d; nonscenario singleton",
                                     source_local_calendar_seconds=start_seconds, source_local_day_seconds=date,
                                     source_timezone="unspecified",
                                     start_utc_seconds=None, scenario=scenario)
            for speaker in node:
                if old.tag(speaker) != "speaker":
                    continue
                key = identity(salt, "AMI", "speaker", raw + "|" + speaker.get("nxt_agent", ""))
                if key not in extended[meeting]["speakers"]:
                    continue
                person = speaker.get("global_name")
                extended[meeting]["speakers"][key].update(
                    person=identity(salt, "AMI", "person", person) if person else None,
                    role=old.normalized(speaker.get("role")))
    with zipfile.ZipFile(archives / "ICSI-core.zip") as z:
        by_stream = defaultdict(set)
        for name in sorted(n for n in z.namelist() if n.startswith("ICSI/DialogueActs/") and n.endswith(".xml")):
            if check:
                check()
            for node in ET.fromstring(z.read(name)):
                person = node.get("participant")
                for child in node:
                    if old.tag(child) == "child":
                        word = PurePosixPath(child.get("href", "").split("#")[0].replace("\\", "/")).name
                        pieces = word.split(".")
                        if len(pieces) >= 3 and person:
                            by_stream[(pieces[0], pieces[1])].add(person)
        for (raw, agent), people in by_stream.items():
            meeting = identity(salt, "ICSI", "meeting", raw)
            speaker = identity(salt, "ICSI", "speaker", raw + "|" + agent)
            if meeting not in extended or speaker not in extended[meeting]["speakers"]:
                continue
            if len(people) != 1:
                raise ValueError("ICSI stream maps to multiple participants")
            match = re.fullmatch(r"([A-Za-z]+)(\d+)", raw)
            if not match:
                raise ValueError("unrecognized ICSI series identifier")
            # Numeric suffix is retained as a source label, not asserted to be a date.
            extended[meeting].update(group=identity(salt, "ICSI", "group", match.group(1)),
                                     series_rank=None, source_series_number=int(match.group(2)),
                                     order_qualified=False, ordering_basis="no packaged chronology",
                                     start_utc_seconds=None, scenario=False)
            extended[meeting]["speakers"][speaker].update(
                person=identity(salt, "ICSI", "person", next(iter(people))), role=None)
    if ordering is not None:
        if not ordering.get("source_document_sha256") or not ordering.get("source_description") or not ordering.get("source_document"):
            raise ValueError("chronology requires documented source provenance")
        if digest(ordering["source_document"]) != ordering["source_document_sha256"]:
            raise ValueError("chronology source document changed")
        values = ordering["meeting_start_utc_seconds"]
        for meeting, seconds in values.items():
            if meeting not in extended or extended[meeting]["corpus"] != "ICSI" or not isinstance(seconds, (int, float)):
                raise ValueError("unrecognized chronology row")
            extended[meeting].update(start_utc_seconds=float(seconds), order_qualified=True,
                                     series_rank=float(seconds), ordering_basis="pinned supplementary source chronology")
    for meeting, meta in extended.items():
        if "group" not in meta:
            raise ValueError("source meeting missing group metadata")
        for row in meta["speakers"].values():
            row.setdefault("person", None)
            row.setdefault("role", None)
    return extended


def speech_track(archives, salt, metadata, check=None):
    """All timed lexical words, including speech outside supported act spans.

    Text and raw stream identifiers are inspected locally but never emitted.
    ICSI-plus is a duplicate layer and is not concatenated.
    """
    rows, counts = [], Counter()
    for archive, corpus, prefix in (("AMI", "AMI", "words/"), ("ICSI-core", "ICSI", "ICSI/Words/")):
        with zipfile.ZipFile(archives / (archive + ".zip")) as z:
            for name in sorted(n for n in z.namelist() if n.startswith(prefix) and n.endswith(".xml")):
                if check:
                    check()
                parts = PurePosixPath(name).name.split(".")
                if len(parts) < 3:
                    raise ValueError("unrecognized lexical stream filename")
                meeting = identity(salt, corpus, "meeting", parts[0])
                speaker = identity(salt, corpus, "speaker", parts[0] + "|" + parts[1])
                if meeting not in metadata or speaker not in metadata[meeting]["speakers"]:
                    raise ValueError("timed lexical stream absent from qualified roster")
                for ordinal, node in enumerate(ET.fromstring(z.read(name))):
                    if check and ordinal % 256 == 0:
                        check()
                    if old.tag(node) != "w" or not "".join(node.itertext()).strip():
                        continue
                    start, end = old.number(node.get("starttime")), old.number(node.get("endtime"))
                    if start is None or end is None or end < start:
                        counts[corpus + "_unsupported_word_timing"] += 1
                        continue
                    rows.append({"meeting": meeting, "speaker": speaker, "start": start, "end": end})
                    counts[corpus + "_timed_words"] += 1
    rows.sort(key=lambda r: (r["meeting"], r["start"], r["end"], r["speaker"]))
    return rows, dict(counts)


def load_lemmatizer(manifest_path):
    manifest = json.loads(Path(manifest_path).read_text("utf8"))
    root = Path(manifest["model_root"])
    if manifest.get("name") != "en_core_web_sm" or manifest.get("version") != "3.8.0":
        raise ValueError("unapproved linguistic lemmatizer")
    actual_files = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    if actual_files != set(manifest["files"]):
        raise ValueError("incomplete linguistic resource manifest")
    for name, value in manifest["files"].items():
        if digest(root / name) != value:
            raise ValueError("linguistic resource pin changed")
    import spacy
    from spacy.tokens import Doc
    nlp = spacy.load(root, disable=["parser", "ner"])
    def lemmatize(words):
        doc = nlp(Doc(nlp.vocab, words=words))
        if len(doc) != len(words):
            raise ValueError("linguistic pipeline changed source word boundaries")
        return [t.lemma_.casefold() for t in doc]
    if lemmatize(["children", "were", "running"]) != ["child", "be", "run"]:
        raise ValueError("pinned linguistic resource fails its constructed lemma check")
    return lemmatize


def prepare_lemmas(acts, output, binding, lemmatize, max_blocks=None):
    values = []
    count = 0
    ordered = sorted(acts, key=lambda a: (a["meeting"], a["start"], a["end"], a["speaker"], a["id"]))
    for start in range(0, len(ordered), 64):
        if requested(output):
            return None
        end = min(len(ordered), start + 64)
        path = output / "lemma-blocks" / f"{start:07d}-{end:07d}.json"
        if path.exists():
            block = json.loads(path.read_text("utf8"))
            seal = json.loads(path.with_suffix(".seal.json").read_text("utf8"))
            if digest(path) != seal["sha256"] or block["binding"] != binding or block["range"] != [start, end]:
                raise ValueError("LA lemma checkpoint changed")
        else:
            if max_blocks is not None and count >= max_blocks:
                return None
            begun = time.process_time()
            rows = []
            for act in ordered[start:end]:
                words = [w["text"] for w in act["words"] if w.get("kind") == "word" and not w.get("laugh", False)]
                lemmas = lemmatize(words)
                if len(lemmas) != len(words):
                    raise ValueError("lemma alignment changed")
                rows.append({"id": act["id"], "lemmas": [s for s in lemmas if s.isalpha()]})
            block = {"binding": binding, "range": [start, end], "rows": rows}
            write(path, block)
            write(path.with_suffix(".seal.json"), {"sha256": digest(path)})
            if not (output / "COST_PROBE.json").exists():
                write(output / "COST_PROBE.json", {"binding": binding, "phase": "first-64-acts",
                      "measured_cpu_seconds": time.process_time() - begun, "forecast_cpu_seconds": None})
            count += 1
        values.extend(block["rows"])
    by_id = {row["id"]: row["lemmas"] for row in values}
    frequencies = defaultdict(Counter)
    for act in ordered:
        frequencies[act["corpus"]].update(by_id[act["id"]])
    stop = {corpus: [word for word, _ in sorted(freq.items(), key=lambda t: (-t[1], t[0]))[:200]]
            for corpus, freq in frequencies.items()}
    excluded = {k: set(v) for k, v in stop.items()}
    corpus_by_id = {a["id"]: a["corpus"] for a in ordered}
    for row in values:
        corpus = corpus_by_id[row["id"]]
        row["content_lemmas"] = [s for s in row["lemmas"] if s not in excluded[corpus]]
    return values, stop


def produce(output, inputs, config, verifying=False, constructed_lemmatizer=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    def check():
        if requested(output):
            raise SourceYield()
    if requested(output):
        return {"status": "yielded", "complete_card": False}
    source = Path(inputs["source"])
    if not config.get("constructed_fixture"):
        if "fixture_archive_pins" in config:
            raise ValueError("human source cannot use fixture archive pins")
        if not {"ACTS.json.gz", "LAUGHS.json.gz", "METADATA.json.gz"}.issubset(config["source_pins"]):
            raise ValueError("qualified LA0 pins incomplete")
        for name, value in config["source_pins"].items():
            if digest(source / name) != value:
                raise ValueError("qualified LA0 input changed")
    acts, laughs, original = [gzread(source / n) for n in ("ACTS.json.gz", "LAUGHS.json.gz", "METADATA.json.gz")]
    salt = Path(inputs["identity_salt"]).read_bytes()
    if len(salt) != 32:
        raise ValueError("identity salt length")
    archives = Path(inputs["archive_root"])
    pins = {k: digest(archives / (k + ".zip")) for k in old.PINS}
    expected = config.get("fixture_archive_pins", old.PINS)
    if pins != expected:
        raise ValueError("LA metadata archive pin changed")
    if config.get("constructed_fixture") and not all(a["id"].startswith("constructed-") for a in acts):
        raise ValueError("fixture cannot read human acts")
    ordering = json.loads(Path(inputs["ordering"]).read_text("utf8")) if inputs.get("ordering") else None
    try:
        meta = metadata_extension(archives, salt, original, ordering, check)
        speech, speech_counts = speech_track(archives, salt, meta, check)
    except SourceYield:
        return {"status": "yielded", "complete_card": False}
    binding = hashlib.sha256(canonical({"source": {n: digest(source / n) for n in ("ACTS.json.gz", "LAUGHS.json.gz", "METADATA.json.gz")},
                       "archives": pins, "salt": hashlib.sha256(salt).hexdigest(), "module": digest(Path(__file__)),
                       "lemma_manifest": digest(inputs["lemma_manifest"]) if inputs.get("lemma_manifest") else "constructed",
                       "ordering": ordering, "mode": config.get("mode", "all")})).hexdigest()
    if config.get("mode", "all") == "metadata":
        lemmas, stop = [], {}
    else:
        if requested(output):
            return {"status": "yielded", "complete_card": False}
        lemmatize = constructed_lemmatizer or load_lemmatizer(inputs["lemma_manifest"])
        prepared = prepare_lemmas(acts, output, binding, lemmatize, config.get("max_new_blocks"))
        if prepared is None:
            return {"status": "yielded", "complete_card": False}
        lemmas, stop = prepared
    values = {"METADATA_EXT.json.gz": meta, "LEMMA_ACTS.json.gz": lemmas, "SPEECH.json.gz": speech}
    for name, value in values.items():
        if verifying:
            if gzread(output / name) != value:
                raise ValueError("LA preparation complete replay differs")
        else:
            gzip_equal(output / name, value)
    summary = {"binding": binding, "meetings": len(meta), "acts": len(acts), "lemma_acts": len(lemmas),
               "top200_by_corpus": stop, "speech_counts": speech_counts,
               "chronology_held_meetings": sum(not m["order_qualified"] for m in meta.values()),
               "cross_series_history_qualified": all(m.get("start_utc_seconds") is not None for m in meta.values() if m["corpus"] == "ICSI"),
               "record_kind": "run", "theory_tags": [], "by_construction": False}
    if verifying:
        if json.loads((output / "SUMMARY.json").read_text("utf8")) != summary:
            raise ValueError("LA preparation summary differs")
        return {"verified": True, "complete_source_replay": True}
    write(output / "SUMMARY.json", summary)
    return summary


def execute(output, inputs, config):
    return produce(output, inputs, config)


def verify(output, inputs, config):
    # Independent lemma blocks; compare all final products after reconstruction.
    replay = Path(output) / "independent-replay"
    result = produce(replay, inputs, {k: v for k, v in config.items() if k != "max_new_blocks"})
    if result.get("status") == "yielded":
        return {**result, "verified": False}
    for name in ("METADATA_EXT.json.gz", "LEMMA_ACTS.json.gz", "SPEECH.json.gz"):
        if gzread(replay / name) != gzread(Path(output) / name):
            raise ValueError("LA independent source reconstruction differs")
    if result != json.loads((Path(output) / "SUMMARY.json").read_text("utf8")):
        raise ValueError("LA independent source summary differs")
    return {"verified": True, "complete_source_and_lemma_replay": True}
