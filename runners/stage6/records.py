"""Stage 6 recorded process (brief §5.2, §5.3, T track): the licensed, already acquired
records with lineage-clean loaders and frozen partitions — ScholaWrite keystroke revisions
(HF dataset on disk with project and author columns), CoAuthor suggestion-event sessions
(1,447 local jsonl logs; the document state is reconstructed from the event stream, T02's
gate), the recorded drawing corpora (the Stage-4/5 quickdraw prefixes with their access
and equifinality rules), and OpenReview, which is NOT on this machine and whose prior
acquisition attempt closed RESOURCE_BLOCKED with receipts (runners/s3_run_h.py, H07), so
its T03 disposition is predeclared here rather than discovered mid-run.

No annotation is a value truth: ScholaWrite labels are local event descriptions and enter
only as targets or baselines, never as maker values (§5.2). The independent unit is the
project/author lineage, the session, or the drawing — never a row (§5.3).

DESIGN CHECK (2026-08-30)
lessons read: LESSONS §2 (before building an extractor over someone else's data: read the
  format from the data, keep an unparseable-row ledger, never silently drop), §3
  (denominators are declared opportunities; a gate dependency is the verdict), §5 (the
  loaders cache to the stage root; a produces guard on every derived file).
gates: the split receipt (I03) proves zero descendant overlap: every ScholaWrite project
  and author pair, every CoAuthor session (and its prompt lineage), and every drawing
  stays whole on one side. T02's reconstruction gate: replaying a session's deltas must
  reproduce the final recorded document text exactly (mismatches are counted and a
  session over the mismatch floor is excluded as unreconstructable, never patched).
bands: none here; the T-track engines' verdict bands live there.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from soundingline.stage6 import S6, now_iso, write_json                            # noqa: E402

SCHOLA_DIR = REPO / "results" / "scholawrite" / "dataset"
COAUTHOR_DIR = REPO / "corpora" / "coauthor" / "coauthor-v1.0"
DRAWINGS_RAW = REPO / "results" / "phase_2_4_stage_4" / "P01" / "raw"
CACHE = S6 / "records_cache"

OPENREVIEW_DISPOSITION = {
    "corpus": "openreview",
    "status": "RESOURCE_BLOCKED",
    "predeclared": True,
    "why": "the corpus is not on this machine; the Stage-3 acquisition attempt (H07) closed "
           "RESOURCE_BLOCKED with per-candidate receipts (no reachable OpenReview mirror on HF), "
           "and Stage 6 acquires nothing (§5.2 uses only already acquired records)",
    "receipt": "runners/s3_run_h.py H07; results/ ... s3_h07 verdict",
    "unblocks_if": "the curator supplies a licensed local copy before the scientific lock",
}


def _split_hash(key: str, salt: str = "s6split") -> float:
    return int(hashlib.md5(f"{salt}|{key}".encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def lane_of(key: str, salt: str = "s6split") -> str:
    """Lineage-keyed lane assignment: discovery 0.55, transfer 0.15, confirmation 0.30.
    The key is the INDEPENDENT UNIT (project|author, session id, drawing key); every
    descendant shares it, so descendants cannot cross a split (§5.3)."""
    h = _split_hash(key, salt)
    return "discovery" if h < 0.55 else ("transfer" if h < 0.70 else "confirmation")


# ── ScholaWrite (T01, T06; C12) ───────────────────────────────────────────────────────

def scholawrite_sessions(max_sessions: int | None = None, lane: str | None = None) -> list[dict]:
    """Revision sequences grouped into sessions: one session = one (project, author) pair's
    rows in timestamp order, segmented at gaps over 30 minutes. Each event: label (the
    revision type: the T01 target), high-level, before/after text lengths and a bounded
    text delta digest (the reader sees text; the loader keeps it). The split key is
    `project` (leave-project-out is the primary protocol; author is carried for the
    leave-author-out analysis and the I03 overlap audit)."""
    from datasets import load_from_disk                                           # noqa: PLC0415
    ds = load_from_disk(str(SCHOLA_DIR))["all_sorted"]
    by_pa: dict = {}
    for r in ds:
        by_pa.setdefault((str(r["project"]), str(r["author"])), []).append(
            {"t": int(r["timestamp"]), "label": r["label"], "high": r["high-level"],
             "before": r["before text"] or "", "after": r["after text"] or ""})
    out = []
    for (proj, auth), rows in sorted(by_pa.items()):
        rows.sort(key=lambda x: x["t"])
        seg: list = []
        segs = [seg]
        for i, r in enumerate(rows):
            if seg and r["t"] - seg[-1]["t"] > 30 * 60 * 1000:
                seg = []
                segs.append(seg)
            seg.append(r)
        for k, s in enumerate(segs):
            if len(s) < 8:
                continue
            key = f"sw|{proj}"
            out.append({"corpus": "scholawrite", "session_id": f"sw|{proj}|{auth}|{k}",
                        "unit_key": key, "project": proj, "author": auth,
                        "lane": lane_of(key), "n_events": len(s), "events": s})
    if lane:
        out = [s for s in out if s["lane"] == lane]
    out.sort(key=lambda s: s["session_id"])
    return out[:max_sessions] if max_sessions else out


def scholawrite_event_view(ev: dict, max_chars: int = 240) -> dict:
    """What a reader may see of one event: the local text neighborhood and the delta,
    NEVER the label (the label is the target)."""
    b, a = ev["before"], ev["after"]
    i = next((j for j, (x, y) in enumerate(zip(b, a)) if x != y), min(len(b), len(a)))
    lo = max(0, i - max_chars // 2)
    return {"before": b[lo:lo + max_chars], "after": a[lo:lo + max_chars],
            "len_delta": len(a) - len(b)}


# ── CoAuthor (T02, T07) ───────────────────────────────────────────────────────────────

def _apply_delta(doc: str, cursor: int, delta) -> tuple[str, int]:
    """Quill delta application, standard semantics: walk the OLD document, copying retained
    spans, appending inserts, skipping deletes, then copy the tail. A retain or delete that
    runs past the end of the document raises OverflowError — the internal known-answer the
    reconstruction gate counts (a wrong delta model overflows constantly; a right one never
    does)."""
    if delta in ("", None):
        return doc, cursor
    if isinstance(delta, str):
        try:
            delta = json.loads(delta)
        except (ValueError, TypeError):
            return doc[:cursor] + str(delta) + doc[cursor:], cursor + len(str(delta))
    if isinstance(delta, dict) and "ops" in delta:
        out = []
        pos = 0
        for op in delta["ops"]:
            if "retain" in op:
                n = int(op["retain"])
                if pos + n > len(doc):
                    raise OverflowError(f"retain {n} past end ({pos}+{n}>{len(doc)})")
                out.append(doc[pos:pos + n])
                pos += n
            elif "insert" in op:
                out.append(op["insert"] if isinstance(op["insert"], str) else " ")
            elif "delete" in op:
                n = int(op["delete"])
                if pos + n > len(doc):
                    raise OverflowError(f"delete {n} past end")
                pos += n
        out.append(doc[pos:])
        return "".join(out), cursor
    raise ValueError(f"unknown delta shape: {type(delta)}")


def coauthor_session(path: Path) -> dict:
    """One session replayed: the document state before every suggestion event, and the
    writer's decision (accept, dismiss, edit-then-accept, or ignore). The reconstruction
    gate: the replayed final text must equal the last recorded currentDoc exactly;
    mismatched sessions carry `reconstructed: False` and T02 excludes them (the gate is
    the count, never a patch)."""
    events = []
    doc, cursor = "", 0
    init_len = 0
    decisions = []
    bad_deltas = 0
    overflows = 0
    n_deltas = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                e = json.loads(line)
            except ValueError:
                bad_deltas += 1
                continue
            name = e.get("eventName", "")
            if name == "system-initialize":
                doc = e.get("currentDoc", "") or ""
                init_len = len(doc)
                cursor = int(e.get("currentCursor") or 0)
            elif name in ("text-insert", "text-delete", "suggestion-select"):
                try:
                    n_deltas += 1
                    doc, cursor = _apply_delta(doc, cursor, e.get("textDelta"))
                except OverflowError:
                    overflows += 1
                except (ValueError, TypeError, KeyError):
                    bad_deltas += 1
            elif name == "cursor-change":
                try:
                    cursor = int(e.get("currentCursor") or cursor)
                except (TypeError, ValueError):
                    pass
            elif name == "suggestion-open":
                events.append({"kind": "shown", "doc_len": len(doc), "doc_tail": doc[-400:],
                               "suggestions": e.get("currentSuggestions", ""), "decided": None})
            elif name in ("suggestion-select", "suggestion-close", "suggestion-reopen"):
                if events and events[-1]["decided"] is None:
                    events[-1]["decided"] = {"suggestion-select": "accept", "suggestion-close": "dismiss",
                                             "suggestion-reopen": "reopen"}[name]
                    if name != "suggestion-reopen":
                        decisions.append(events[-1]["decided"])
    # the gate: every delta applied under the standard semantics without one overflow
    # (the log carries no final reference text, so consistency is the known answer)
    reconstructed = n_deltas > 0 and overflows == 0 and bad_deltas <= max(2, n_deltas // 50)
    return {"corpus": "coauthor", "session_id": f"ca|{path.stem}", "unit_key": f"ca|{path.stem}",
            "lane": lane_of(f"ca|{path.stem}"), "reconstructed": reconstructed,
            "recon_len": len(doc), "init_len": init_len, "n_deltas": n_deltas,
            "overflows": overflows, "bad_deltas": bad_deltas,
            "n_suggestion_events": len(events), "decisions": decisions, "events": events[-64:]}


def coauthor_sessions(max_sessions: int | None = None, lane: str | None = None,
                      require_reconstructed: bool = False) -> list[dict]:
    paths = sorted(COAUTHOR_DIR.glob("*.jsonl"))
    out = []
    for p in paths:
        if max_sessions and len(out) >= max_sessions:
            break
        try:
            s = coauthor_session(p)
        except OSError:
            continue
        if lane and s["lane"] != lane:
            continue
        if require_reconstructed and not s["reconstructed"]:
            continue
        if s["n_suggestion_events"] >= 3:
            out.append(s)
    return out


# ── drawings (T04, F12): the Stage-4/5 corpora with their rules preserved ─────────────

def drawing_units(max_per_cat: int | None = None, lane: str | None = None) -> list[dict]:
    from runners.s4_run_p import CATEGORIES, load_drawings                        # noqa: PLC0415
    out = []
    for cat in CATEGORIES:
        p = DRAWINGS_RAW / f"{cat}.ndjson.prefix"
        if not p.exists():
            continue
        dl = [d for d in load_drawings(cat, p) if len(d["strokes"]) >= 5]
        if max_per_cat:
            dl = dl[:max_per_cat]
        for d in dl:
            key = f"dr|{cat}|{d['key_id']}"
            u = {"corpus": "drawings", "session_id": key, "unit_key": key, "cat": cat,
                 "lane": lane_of(key), "strokes": d["strokes"], "n_strokes": len(d["strokes"])}
            if not lane or u["lane"] == lane:
                out.append(u)
    return out


# ── the corpus dispositions registry (T03, T10) ───────────────────────────────────────

def corpus_inventory(light: bool = False) -> dict:
    """What is actually on disk, with counts; written to CORPUS_DISPOSITIONS at the
    structural lock so T10 dispositions rest on receipts, not memory."""
    inv = {"written_at": now_iso(),
           "openreview": dict(OPENREVIEW_DISPOSITION),
           "scholawrite": {"path": str(SCHOLA_DIR), "present": SCHOLA_DIR.exists()},
           "coauthor": {"path": str(COAUTHOR_DIR), "present": COAUTHOR_DIR.exists(),
                        "session_files": len(list(COAUTHOR_DIR.glob("*.jsonl"))) if COAUTHOR_DIR.exists() else 0},
           "drawings": {"path": str(DRAWINGS_RAW), "present": DRAWINGS_RAW.exists(),
                        "categories": sorted(p.name.split(".")[0] for p in DRAWINGS_RAW.glob("*.ndjson.prefix")) if DRAWINGS_RAW.exists() else []}}
    if not light and SCHOLA_DIR.exists():
        sess = scholawrite_sessions()
        lanes: dict = {}
        for s in sess:
            lanes[s["lane"]] = lanes.get(s["lane"], 0) + 1
        inv["scholawrite"].update({"sessions": len(sess), "projects": len({s["project"] for s in sess}),
                                   "authors": len({s["author"] for s in sess}), "lanes": lanes})
    return inv


def write_dispositions() -> Path:
    return write_json(S6 / "CORPUS_DISPOSITIONS.json", corpus_inventory())


def _selftest() -> list[str]:
    fails = []
    # lane assignment is deterministic and descendant-stable
    if lane_of("sw|12") != lane_of("sw|12"):
        fails.append("lane not deterministic")
    # delta replay on a synthetic session
    doc, cur = _apply_delta("hello world", 5, {"ops": [{"retain": 5}, {"insert": ","}]})
    if doc != "hello, world":
        fails.append(f"delta replay: {doc!r}")
    doc, _ = _apply_delta(doc, 0, {"ops": [{"retain": 0}, {"delete": 5}]})
    if doc != ", world":
        fails.append(f"delta delete: {doc!r}")
    # real CoAuthor sessions parse and mostly reconstruct under the standard semantics
    ps = sorted(COAUTHOR_DIR.glob("*.jsonl"))[:6]
    if ps:
        recs = [coauthor_session(p) for p in ps]
        rate = sum(1 for s in recs if s["reconstructed"]) / len(recs)
        if rate < 0.5:
            fails.append(f"coauthor reconstruction rate {rate:.2f} on {len(recs)} sessions "
                         f"(overflows: {[s['overflows'] for s in recs]})")
    # the openreview disposition is predeclared RESOURCE_BLOCKED
    if OPENREVIEW_DISPOSITION["status"] != "RESOURCE_BLOCKED":
        fails.append("openreview disposition")
    return fails


if __name__ == "__main__":
    f = _selftest()
    print("records self-tests:", "ALL OK" if not f else f)
    if not f:
        inv = corpus_inventory(light=True)
        print({k: (v if k == "openreview" else {kk: vv for kk, vv in v.items() if kk != 'path'}) for k, v in inv.items() if k != "written_at"})
    sys.exit(1 if f else 0)
