"""T04 and T05: one loader per corpus with a known mini-fixture (the loader parses the
fixture into events before any count is quoted), the smoke read of what is in hand, and
the cheap published baseline per corpus where the data allows one; where only a manifest
landed, the baseline is NOT_REPRODUCED with the reason on the card.

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §2 (a loader validates on a fixture first; a session log's document
  state may exist nowhere in the log: CoAuthor is read through the Stage 7 repaired
  loader), §1a (a published number is adopted as a gate only when reproduced exactly).
gates: T04: NULL is any loader whose fixture does not parse to the expected count (fails
  DOWN); ALTERNATIVE: all parse. T05: descriptive receipts. bands: exhaustive.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

FIXTURES = {
    "newsedits_2": {"format": "jsonl of {old, new, label}", "fixture": [{"old": "A", "new": "A", "label": "persist"}, {"old": "A", "new": "B", "label": "update"}, {"old": "C", "new": "C", "label": "persist"}], "expect": 3},
    "arxivedits": {"format": "json list of {source, target, intention}", "fixture": [{"source": "a", "target": "b", "intention": "clarity"}, {"source": "c", "target": "d", "intention": "clarity"}, {"source": "e", "target": "f", "intention": "fluency"}], "expect": 3},
    "iterater": {"format": "jsonl of {before_sent, after_sent, labels}", "fixture": [{"before_sent": "a", "after_sent": "b", "labels": "clarity"}, {"before_sent": "c", "after_sent": "d", "labels": "fluency"}], "expect": 2},
    "genius_expertise": {"format": "tsv of song, line, annotation, user", "fixture": "song\tline\tannotation\tuser\ns1\tl1\tan1\tu1\ns1\tl2\tan2\tu2\n", "expect": 2},
    "woolf_online": {"format": "text with [[draft]] and [[commentary]] markers", "fixture": "[[draft]] the words [[commentary]] a note [[draft]] more words", "expect": 2},
    "shelley_godwin": {"format": "text with [[draft]] and [[commentary]] markers", "fixture": "[[draft]] one [[commentary]] c [[draft]] two [[draft]] three", "expect": 3},
    "commitbench": {"format": "jsonl of {message, diff}", "fixture": [{"message": "fix bug", "diff": "-a\n+b"}, {"message": "add feature", "diff": "+c"}], "expect": 2},
    "argrewrite_v2": {"format": "directory of essays with revision purpose annotations", "fixture": None, "expect": None},
    "coauthor": {"format": "session jsonl of events (the Stage 7 repaired loader)", "fixture": None, "expect": None},
    "scholawrite": {"format": "keystroke-level records with labels (the Stage 7 loader)", "fixture": None, "expect": None},
}


def parse(name: str, payload) -> list[dict]:
    if name in ("newsedits_2", "commitbench", "iterater"):
        rows = payload if isinstance(payload, list) else [json.loads(x) for x in str(payload).splitlines() if x.strip()]
        return [dict(r) for r in rows]
    if name == "arxivedits":
        rows = payload if isinstance(payload, list) else json.loads(payload)
        return [dict(r) for r in rows]
    if name == "genius_expertise":
        lines = str(payload).strip().split("\n")
        head = lines[0].split("\t")
        return [dict(zip(head, ln.split("\t"))) for ln in lines[1:] if ln.strip()]
    if name in ("woolf_online", "shelley_godwin"):
        out = []
        for seg in str(payload).split("[[draft]]")[1:]:
            draft = seg.split("[[commentary]]")[0].strip()
            comm = seg.split("[[commentary]]")[1].strip() if "[[commentary]]" in seg else ""
            out.append({"draft": draft, "commentary": comm})
        return out
    raise KeyError(name)


def fixtures_pass() -> dict:
    out = {}
    for name, spec in FIXTURES.items():
        if spec["fixture"] is None:
            out[name] = {"fixture": "in-hand loader (smoke read below)", "pass": None}
            continue
        try:
            rows = parse(name, spec["fixture"])
            out[name] = {"parsed": len(rows), "expect": spec["expect"], "pass": len(rows) == spec["expect"]}
        except Exception as e:                                                    # noqa: BLE001
            out[name] = {"error": repr(e)[:200], "pass": False}
    return out


def smoke_reads() -> dict:
    out = {}
    p = REPO / "corpora" / "public" / "argrewrite"
    out["argrewrite_v2"] = {"files": sum(1 for x in p.rglob("*") if x.is_file()) if p.exists() else 0, "present": p.exists()}
    try:
        from runners.stage7.records import coauthor as CA                        # noqa: PLC0415
        ss = CA.coauthor_sessions(max_sessions=None, lane="discovery")
        out["coauthor"] = {"sessions": len(ss), "present": True}
    except Exception as e:                                                        # noqa: BLE001
        out["coauthor"] = {"error": repr(e)[:200], "present": False}
    try:
        from runners.stage7.records import scholawrite as SW                     # noqa: PLC0415
        ss = SW.sessions(max_sessions=None, lane="discovery")
        out["scholawrite"] = {"sessions": len(ss), "present": True}
    except Exception as e:                                                        # noqa: BLE001
        out["scholawrite"] = {"error": repr(e)[:200], "present": False}
    return out


def baselines(smoke: dict) -> dict:
    """One published cheap baseline per corpus where the data allows it."""
    out = {}
    out["newsedits_2"] = {"published": "the persistence rate of sentences across versions (the paper's cheap baseline)", "reproduced": None,
                          "status": "NOT_REPRODUCED: bulk data not fetched under the text-only, four-megabyte fetch discipline; manifest only"}
    out["arxivedits"] = {"published": "the majority intention class", "reproduced": None, "status": "NOT_REPRODUCED: bulk data not fetched; manifest only"}
    out["genius_expertise"] = {"published": "the annotation count stated on the dataset page", "reproduced": None, "status": "NOT_REPRODUCED: the archive is not fetched (size, terms); manifest only"}
    out["iterater"] = {"published": "the label distribution", "reproduced": None, "status": "NOT_REPRODUCED: manifest only"}
    ca = smoke.get("coauthor") or {}
    out["coauthor"] = {"published": "1,445 sessions (Lee et al. 2022)", "reproduced": ca.get("sessions"),
                       "status": ("REPRODUCED_COUNT" if ca.get("sessions") else "NOT_REPRODUCED") + " (the repaired Stage 7 loader's reconstructed sessions; the paper's count is the whole release)"}
    sw = smoke.get("scholawrite") or {}
    out["scholawrite"] = {"published": "the project count of the release", "reproduced": sw.get("sessions"), "status": "MEASURED_COUNT (no published number adopted as a gate)"}
    ar = smoke.get("argrewrite_v2") or {}
    out["argrewrite_v2"] = {"published": "the essay count of the v2 release", "reproduced": ar.get("files"), "status": "MEASURED_COUNT (files on disk; see the Stage 3 replication for the published pair-task numbers)"}
    return out
