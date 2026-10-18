"""Authenticate raw revision events against frozen P2/P6 identities.

This is a source adapter, not an executable analysis or burst classifier.
Primary source populations must agree exactly; the broader upstream roster
may cover additional sessions, which are disclosed rather than used or guessed
invalid. No selected-option index or prepared inserted text is consulted.
"""
from __future__ import annotations

import json
from pathlib import Path

from .timing_census import read, filehash
from .timing_pmap_source import completed, indexed, bound_record
from .timing_revision_events import replay_revision_events

INPUTS = frozenset(("repo_root", "foundation_complete", "foundation_plan", "session_index",
                   "prepared_sessions", "raw_roster", "source_pins", "p6_index", "p6_completion"))
SCORE_FIELDS = frozenset(("population_probability", "population_surprisal", "population_log_frequency"))


class Sources:
    def __init__(self, inputs):
        if set(inputs) != INPUTS:
            raise ValueError("exact revision source inputs required")
        self.inputs = inputs
        self.root = Path(inputs["repo_root"]).resolve()
        plan, complete = read(inputs["foundation_plan"]), read(inputs["foundation_complete"])
        if complete.get("status") != "COMPLETE" or complete.get("plan_sha256") != filehash(inputs["foundation_plan"]):
            raise ValueError("foundation plan unauthenticated")
        for name in ("prepared_sessions", "raw_roster", "source_pins"):
            path = Path(inputs[name]).resolve()
            if plan["pins"].get(path.relative_to(self.root).as_posix()) != filehash(path):
                raise ValueError("foundation source metadata changed")
        completed(inputs["foundation_complete"], inputs["session_index"], fresh=False)
        completed(inputs["p6_completion"], inputs["p6_index"])
        p6_binding_path = Path(inputs["p6_index"]).parent / "P6_BINDINGS.json"
        completed(inputs["p6_completion"], p6_binding_path)
        p6_binding = read(p6_binding_path)
        expected = dict(config={}, repo_root=str(self.root), index_sha256=filehash(inputs["p6_index"]),
            inputs={name: filehash(inputs[name]) for name in ("foundation_complete", "prepared_sessions", "raw_roster", "session_index")})
        if p6_binding != expected:
            raise ValueError("P6 was extracted from different source metadata")
        self.p2, self.p6, self.meta, self.raw = (indexed(inputs[k]) for k in
            ("session_index", "p6_index", "prepared_sessions", "raw_roster"))
        if not (self.p2.keys() == self.p6.keys() == self.meta.keys()):
            raise ValueError("primary revision source populations differ")
        if not self.p2.keys() <= self.raw.keys():
            raise ValueError("raw roster lacks primary sessions")
        self.population = dict(primary_session_ids=sorted(self.p2), primary_sessions=len(self.p2),
            upstream_only_session_ids=sorted(self.raw.keys() - self.p2.keys()), raw_roster_sessions=len(self.raw))
        self.pins = {Path(k).as_posix(): v for k, v in read(inputs["source_pins"]).items()}

    def session(self, sid):
        row, raw, meta = self.p2[sid], self.raw[sid], self.meta[sid]
        timeline = bound_record(self.inputs["session_index"], row)
        p6 = bound_record(self.inputs["p6_index"], self.p6[sid])
        identity = (sid, row["writer"], timeline["prompt"])
        for value in (timeline, meta, p6):
            if (value["session"], value["writer"], value["prompt"]) != identity:
                raise ValueError("revision session identity differs")
        if (p6["timestamp"], p6["end_at"]) != (meta["timestamp"], meta["end_at"]):
            raise ValueError("P6 chronology differs from source metadata")
        path = (self.root / raw["path"]).resolve()
        path.relative_to(self.root)
        actual_sha = filehash(path)
        if (actual_sha != raw["source_sha256"] or actual_sha != timeline["source_sha256"]
                or self.pins.get(path.relative_to(self.root).as_posix()) != actual_sha):
            raise ValueError("raw revision source differs from frozen metadata")
        with path.open(encoding="utf8") as stream:
            events = [json.loads(line) for line in stream]
        result = replay_revision_events(events)
        if result["replay"]["final_document"] != timeline["final_document"]:
            raise ValueError("revision raw replay differs from P2 final document")
        expected_words = []
        for word in p6["words"]:
            if not SCORE_FIELDS <= word.keys():
                raise ValueError("P6 occurrence lacks frozen score fields")
            expected_words.append({k: v for k, v in word.items() if k not in SCORE_FIELDS})
        if result["replay"]["words"] != expected_words:
            raise ValueError("revision raw replay differs from exact P6 occurrences")
        return dict(session=sid, writer=row["writer"], prompt=timeline["prompt"],
            timestamp=meta["timestamp"], end_at=meta["end_at"],
            source_hashes=dict(raw=actual_sha, p2=row["sha256"], p6=self.p6[sid]["sha256"]),
            occurrence_count=len(expected_words), revision_events=result["revision_events"],
            delta_clock=result["delta_clock"], classification=result["classification"])
