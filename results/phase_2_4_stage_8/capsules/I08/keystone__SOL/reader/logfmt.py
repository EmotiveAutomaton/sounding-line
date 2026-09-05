"""The ONE log grammar (brief §5): the population corpus is rendered in it, the adapters are
trained on it, and the forward-model readout scores option lines in it. STDLIB ONLY, NO
REPOSITORY IMPORTS: this file is copied into every capsule and imported by the constructor.

    task: <topic>
    audience: <editor|peer|self>
    tools: library=<yes|no> source=<yes|no>
    deadline: <tight|loose>
    sections: sec1(2) sec2(3) ...
    goal: <name>              (present on the conditioned half of the corpus; the supplied purpose)
    log:
    00 write sec1 s1.1 done
    01 check sec1 s1.1 done
    ...
    07 stop

Earlier artifacts by the same maker (the accumulation arm) precede the current header under
`earlier work by the same maker:` with each log rendered whole, then `now:`.

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §3 (a filename or format two code paths share is built by ONE helper:
  the constructor's renderer and the capsule's readout call these functions and the guard
  suite asserts a round trip), §5 (no gate here).
gates: none (a grammar). bands: none.
"""

from __future__ import annotations

EARLIER = "earlier work by the same maker:"
NOW = "now:"
LOG = "log:"


def header(topic: str, audience: str, tools: dict, deadline: str, sections: list[dict],
           goal: str | None = None) -> str:
    lines = [f"task: {topic}", f"audience: {audience}",
             f"tools: library={'yes' if tools.get('library') else 'no'} source={'yes' if tools.get('source_access') else 'no'}",
             f"deadline: {deadline}",
             "sections: " + " ".join(f"{s['name']}({len(s['slots'])})" for s in sections)]
    if goal:
        lines.append(f"goal: {goal}")
    lines.append(LOG)
    return "\n".join(lines)


def event_line(i: int, type_: str, section: str, slot: str, outcome: str | None = None) -> str:
    s = f"{i:02d} {type_} {section} {slot}"
    return s + (f" {outcome}" if outcome else "")


def stop_line(i: int) -> str:
    return f"{i:02d} stop"


def render_log(head: str, events: list[dict], stopped: bool) -> str:
    lines = [head] + [event_line(e["step"] if "step" in e else e["i"], e["type"], e["section"], e["slot"], e.get("outcome")) for e in events]
    if stopped:
        lines.append(stop_line(len(events)))
    return "\n".join(lines)


def compose(earlier_logs: list[str], head: str, prefix_lines: list[str]) -> str:
    """The scoring prefix: earlier logs (if any), the current header, the visible prefix
    lines, and a trailing newline so the next line is scored as a fresh line."""
    parts = []
    if earlier_logs:
        parts.append(EARLIER)
        parts.extend(earlier_logs)
        parts.append(NOW)
    parts.append(head)
    parts.extend(prefix_lines)
    return "\n".join(parts) + "\n"


def header_from_evidence(ev: dict, goal: str | None = None, context_override: dict | None = None) -> str:
    """The header the capsule builds from a VisibleEvidenceV1 (brief, artifact state);
    `context_override` applies a changed-context counterfactual to tools, deadline, or
    audience before rendering."""
    b = dict(ev.get("brief") or {})
    st = ev["artifact_state"]
    tools = dict(b.get("tools_available") or {})
    deadline = b.get("deadline", "loose")
    audience = b.get("audience", "peer")
    if context_override:
        if "tools" in context_override:
            tools.update(context_override["tools"])
        deadline = context_override.get("deadline", deadline)
        audience = context_override.get("audience", audience)
    return header(st.get("topic", "the document"), audience, tools, deadline, st["sections"], goal)


def apply_change_to_header_context(b: dict, kind: str) -> dict:
    """The changed-context counterfactual in header terms (the same five kinds as the law)."""
    tools = dict(b.get("tools_available") or {})
    out = {"tools": tools, "deadline": b.get("deadline", "loose"), "audience": b.get("audience", "peer")}
    if kind == "library_arrives":
        tools["library"] = True
    elif kind == "library_withdrawn":
        tools["library"] = False
    elif kind == "deadline_lifted":
        out["deadline"] = "loose"
    elif kind == "deadline_imposed":
        out["deadline"] = "tight"
    elif kind == "audience_changes":
        out["audience"] = "editor" if out["audience"] != "editor" else "self"
    return out


def prefix_lines(process_prefix: list[dict]) -> list[str]:
    return [event_line(e["step"], e["type"], e["section"], e["slot"], e.get("outcome")) for e in process_prefix]


def parse_line(line: str) -> dict | None:
    """One log line back to an event; None for anything that is not one."""
    parts = line.strip().split()
    if len(parts) == 2 and parts[1] == "stop" and parts[0].isdigit():
        return {"i": int(parts[0]), "stop": True}
    if len(parts) in (4, 5) and parts[0].isdigit():
        out = {"i": int(parts[0]), "type": parts[1], "section": parts[2], "slot": parts[3], "stop": False}
        if len(parts) == 5:
            out["outcome"] = parts[4]
        return out
    return None
