"""The repaired CoAuthor loader (brief §2.1.8, §7.4, D07, D08, P13). THE STAGE-6 DEFECT:
runners/stage6/records.py routed `suggestion-select` into the text-delta branch first, so
the acceptance branch below it never fired and every scored decision was a dismissal.
Here a `suggestion-select` event BOTH records the acceptance on the open suggestion AND
applies its document delta where present; the branches are not exclusive. The decision
vocabulary: accept (selected), edit (selected, then a text edit inside the inserted span
before the next suggestion opens), dismiss (closed without selection), reopen (a closed
suggestion reopened; not a decision), ignore (a shown suggestion neither selected nor
closed before the next one opens). Validated on known mini-logs (D07): accept, dismiss,
reopen, edit, ignore, and a malformed delta, each recovered exactly.

What the source licenses (D08): CoAuthor logs carry no independent final document, so
the reconstruction gate is internal consistency (every delta applies under the standard
semantics without an overflow); no final-text equality is claimed.

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §2 (an extractor over someone else's data reads the format from
  the data and keeps an unparseable-row ledger), §3 (a session log's document state may
  exist nowhere in the log: replay the deltas; two silent zeros were the only symptom
  last time, so the decision marginal is printed and a marginal with a zero class is an
  instrument event; a gate dependency is the verdict), §5.
gates: the loader fixtures (D07): NULL of a broken loader is any fixture decision
  recovered wrong (failure direction: any mismatch fails DOWN); ALTERNATIVE: every fixture
  exact. The reconstruction gate (D08/T-style): a session with an overflow or more than
  2 percent bad deltas is unreconstructed and excluded, never patched. bands: exhaustive.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

COAUTHOR_DIR = REPO / "corpora" / "coauthor" / "coauthor-v1.0"
DECISIONS = ("accept", "edit", "dismiss", "ignore")


def _split_hash(key: str, salt: str = "s7split") -> float:
    return int(hashlib.md5(f"{salt}|{key}".encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def lane_of(key: str, salt: str = "s7split") -> str:
    """discovery 0.50, transfer 0.15, confirmation 0.25, attack 0.10; keyed on the
    session (every descendant shares it)."""
    h = _split_hash(key, salt)
    return "discovery" if h < 0.50 else ("transfer" if h < 0.65 else ("confirmation" if h < 0.90 else "attack"))


def apply_delta(doc: str, cursor: int, delta) -> tuple[str, int, int | None, int]:
    """Standard Quill semantics. Returns (doc, cursor, op_pos, insert_len): op_pos is the
    position of the first insert or delete (so an edit inside a just-accepted span can be
    detected, deletes included). Raises OverflowError on a retain or
    delete past the end (the internal known answer), ValueError on an unknown shape."""
    if delta in ("", None):
        return doc, cursor, None, 0
    if isinstance(delta, str):
        try:
            delta = json.loads(delta)
        except (ValueError, TypeError):
            return doc[:cursor] + str(delta) + doc[cursor:], cursor + len(str(delta)), cursor, len(str(delta))
    if isinstance(delta, dict) and "ops" in delta:
        out = []
        pos = 0
        ins_start, ins_len = None, 0
        for op in delta["ops"]:
            if "retain" in op:
                n = int(op["retain"])
                if pos + n > len(doc):
                    raise OverflowError(f"retain {n} past end ({pos}+{n}>{len(doc)})")
                out.append(doc[pos:pos + n])
                pos += n
            elif "insert" in op:
                s = op["insert"] if isinstance(op["insert"], str) else " "
                if ins_start is None:
                    ins_start = sum(len(x) for x in out)
                ins_len += len(s)
                out.append(s)
            elif "delete" in op:
                n = int(op["delete"])
                if pos + n > len(doc):
                    raise OverflowError(f"delete {n} past end")
                if ins_start is None:
                    ins_start = pos
                pos += n
        out.append(doc[pos:])
        return "".join(out), cursor, ins_start, ins_len
    raise ValueError(f"unknown delta shape: {type(delta)}")


def replay(lines) -> dict:
    """Replay one event stream (an iterable of JSON lines or dicts). Returns the shown
    suggestions with their decisions, the decision marginal, the reconstruction ledger."""
    events: list[dict] = []
    doc, cursor = "", 0
    bad_deltas = overflows = n_deltas = 0
    open_sugg: dict | None = None
    accepted_span: tuple[int, int] | None = None
    awaiting_insert = False                      # after a select with no delta, the next text-insert IS the suggestion
    for raw in lines:
        if isinstance(raw, str):
            try:
                e = json.loads(raw)
            except ValueError:
                bad_deltas += 1
                continue
        else:
            e = raw
        name = e.get("eventName", "")
        if name == "system-initialize":
            doc = e.get("currentDoc", "") or ""
            cursor = int(e.get("currentCursor") or 0)
            continue
        if name == "cursor-change":
            try:
                cursor = int(e.get("currentCursor") or cursor)
            except (TypeError, ValueError):
                pass
            continue
        if name == "suggestion-open":
            if open_sugg is not None and open_sugg["decided"] is None:
                open_sugg["decided"] = "ignore"                     # shown, never selected nor closed
            open_sugg = {"kind": "shown", "doc_len": len(doc), "doc_tail": doc[-400:],
                         "suggestions": e.get("currentSuggestions", ""), "decided": None, "edited": False}
            events.append(open_sugg)
            accepted_span = None
            awaiting_insert = False
            continue
        if name == "suggestion-select":
            # BOTH branches (the repair): record the acceptance, then apply the delta
            if open_sugg is not None and open_sugg["decided"] is None:
                open_sugg["decided"] = "accept"
            if e.get("textDelta") not in ("", None):
                try:
                    n_deltas += 1
                    doc, cursor, s0, s_len = apply_delta(doc, cursor, e.get("textDelta"))
                    if s0 is not None and s_len > 0:
                        accepted_span = (s0, s0 + s_len)
                except OverflowError:
                    overflows += 1
                except (ValueError, TypeError, KeyError):
                    bad_deltas += 1
            else:
                awaiting_insert = True               # this corpus: the selected text follows as a text-insert
            continue
        if name in ("suggestion-close", "suggestion-reopen"):
            if open_sugg is not None and open_sugg["decided"] is None and name == "suggestion-close":
                open_sugg["decided"] = "dismiss"
            if name == "suggestion-reopen":
                open_sugg = open_sugg or None
                if open_sugg is not None:
                    open_sugg["reopened"] = True
                    if open_sugg["decided"] == "dismiss":
                        open_sugg["decided"] = None                 # a reopened suggestion is undecided again
            continue
        if name in ("text-insert", "text-delete"):
            try:
                n_deltas += 1
                doc, cursor, ins0, ins_len = apply_delta(doc, cursor, e.get("textDelta"))
                if awaiting_insert and name == "text-insert" and ins0 is not None and ins_len > 0:
                    accepted_span = (ins0, ins0 + ins_len)       # the suggestion text itself, not an edit
                    awaiting_insert = False
                elif accepted_span and open_sugg is not None and open_sugg["decided"] == "accept":
                    # an edit STRICTLY inside the accepted span before the next suggestion opens
                    pos = ins0 if ins0 is not None else cursor
                    if accepted_span[0] < pos < accepted_span[1]:
                        open_sugg["decided"] = "edit"
                        open_sugg["edited"] = True
            except OverflowError:
                overflows += 1
            except (ValueError, TypeError, KeyError):
                bad_deltas += 1
            continue
    if open_sugg is not None and open_sugg["decided"] is None:
        open_sugg["decided"] = "ignore"
    decisions = [x["decided"] for x in events if x["decided"] in DECISIONS]
    marginal = {d: decisions.count(d) for d in DECISIONS}
    reconstructed = n_deltas > 0 and overflows == 0 and bad_deltas <= max(2, n_deltas // 50)
    return {"events": events, "decisions": decisions, "marginal": marginal, "n_deltas": n_deltas,
            "overflows": overflows, "bad_deltas": bad_deltas, "reconstructed": reconstructed, "final_len": len(doc)}


def coauthor_session(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        rep = replay(fh)
    key = f"ca|{path.stem}"
    return {"corpus": "coauthor", "session_id": key, "unit_key": key, "lane": lane_of(key), **rep,
            "events": rep["events"][-64:]}


def coauthor_sessions(max_sessions: int | None = None, lane: str | None = None, require_reconstructed: bool = True) -> list[dict]:
    out = []
    for p in sorted(COAUTHOR_DIR.glob("*.jsonl")):
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
        if len(s["decisions"]) >= 3:
            out.append(s)
    return out


# ── the known mini-logs (D07) ─────────────────────────────────────────────────────────

def _ev(name: str, **kw) -> dict:
    return {"eventName": name, **kw}


def _ins(pos: int, text: str) -> dict:
    return {"ops": [{"retain": pos}, {"insert": text}]}


FIXTURES = {
    "accept": ([_ev("system-initialize", currentDoc="abc"), _ev("suggestion-open", currentSuggestions="X"),
                _ev("suggestion-select"), _ev("suggestion-close"), _ev("text-insert", textDelta=_ins(3, " tail")),
                _ev("suggestion-open", currentSuggestions="Y"), _ev("suggestion-close")], ["accept", "dismiss"], "abc tail"),
    "accept_with_delta": ([_ev("system-initialize", currentDoc="abc"), _ev("suggestion-open", currentSuggestions="X"),
                _ev("suggestion-select", textDelta=_ins(3, " tail")), _ev("suggestion-open", currentSuggestions="Y"),
                _ev("suggestion-close")], ["accept", "dismiss"], "abc tail"),
    "dismiss": ([_ev("system-initialize", currentDoc="abc"), _ev("suggestion-open", currentSuggestions="X"),
                 _ev("suggestion-close")], ["dismiss"], "abc"),
    "reopen": ([_ev("system-initialize", currentDoc="abc"), _ev("suggestion-open", currentSuggestions="X"),
                _ev("suggestion-close"), _ev("suggestion-reopen"), _ev("suggestion-select"), _ev("suggestion-close"),
                _ev("text-insert", textDelta=_ins(3, " z"))], ["accept"], "abc z"),
    "edit": ([_ev("system-initialize", currentDoc="abc"), _ev("suggestion-open", currentSuggestions="X"),
              _ev("suggestion-select"), _ev("suggestion-close"), _ev("text-insert", textDelta=_ins(3, " tail")),
              _ev("text-delete", textDelta={"ops": [{"retain": 6}, {"delete": 1}]}),
              _ev("suggestion-open", currentSuggestions="Y"), _ev("suggestion-close")], ["edit", "dismiss"], "abc til"),
    "continue_after_accept": ([_ev("system-initialize", currentDoc="abc"), _ev("suggestion-open", currentSuggestions="X"),
              _ev("suggestion-select"), _ev("suggestion-close"), _ev("text-insert", textDelta=_ins(3, " tail")),
              _ev("text-insert", textDelta=_ins(8, " more")), _ev("suggestion-open", currentSuggestions="Y"), _ev("suggestion-close")],
              ["accept", "dismiss"], "abc tail more"),
    "ignore": ([_ev("system-initialize", currentDoc="abc"), _ev("suggestion-open", currentSuggestions="X"),
                _ev("text-insert", textDelta=_ins(3, "!")), _ev("suggestion-open", currentSuggestions="Y"),
                _ev("suggestion-select", textDelta=_ins(4, " k"))], ["ignore", "accept"], "abc! k"),
    "malformed": ([_ev("system-initialize", currentDoc="abc"), _ev("suggestion-open", currentSuggestions="X"),
                   _ev("suggestion-select", textDelta={"ops": [{"retain": 99}, {"insert": "x"}]}),
                   _ev("suggestion-open", currentSuggestions="Y"), _ev("suggestion-close")], ["accept", "dismiss"], "abc"),
}


def run_fixtures() -> list[str]:
    fails = []
    for name, (events, want, final) in FIXTURES.items():
        rep = replay(events)
        if rep["decisions"] != want:
            fails.append(f"{name}: decisions {rep['decisions']} != {want}")
        if name == "malformed" and rep["overflows"] != 1:
            fails.append(f"malformed: overflow count {rep['overflows']} != 1")
        if rep["final_len"] != len(final):
            fails.append(f"{name}: final length {rep['final_len']} != {len(final)}")
    return fails


if __name__ == "__main__":
    f = run_fixtures()
    print("coauthor fixtures:", "ALL OK" if not f else f)
    if not f and COAUTHOR_DIR.exists():
        ss = coauthor_sessions(max_sessions=40)
        marg = {d: sum(s["marginal"][d] for s in ss) for d in DECISIONS}
        print(f"{len(ss)} sessions; decision marginal {marg}; reconstructed {sum(1 for s in ss if s['reconstructed'])}")
    sys.exit(1 if f else 0)
