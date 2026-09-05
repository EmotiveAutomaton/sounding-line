"""Record readers inside the capsule (brief §7.4, P13, P14). STDLIB ONLY.
CoAuthor (decision after a shown suggestion): CU uniform over the four decisions, CPOS the
position baseline (a decision marginal by document-length bucket, supplied by the task
from the discovery fit), CPRIOR the prior-decision persistence, CDIR the model reading the
document tail and the suggestion. ScholaWrite (the next event's category and whether it
switches): SU uniform, SPERS persistence at the task-supplied rate, SDIR the model reading
the event window.

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §3 (blind floors follow the truth marginal: the position and
  persistence baselines are FITTED on discovery and supplied, never assumed), §4.
gates: none here. bands: none.
"""

from __future__ import annotations

from .client import Client

DECISIONS = ("accept", "edit", "dismiss", "ignore")
CATEGORIES = ("Planning", "Implementation", "Revision")


def _bucket(n: int) -> str:
    return "short" if n < 800 else ("mid" if n < 2000 else "long")


def coauthor(ev: dict, arm: str, client: Client, evidence_sha: str, task: dict) -> dict:
    h = ev["history"]
    if arm == "CU":
        return {"decision": {d: 0.25 for d in DECISIONS}}
    if arm == "CPOS":
        table = task.get("position_table") or {}
        d = table.get(_bucket(int(h.get("doc_len", 0)))) or table.get("all") or {x: 0.25 for x in DECISIONS}
        return {"decision": {x: float(d.get(x, 0.0)) + 1e-3 for x in DECISIONS}}
    if arm == "CPRIOR":
        prior = h.get("prior_decisions") or []
        if not prior:
            return {"decision": {d: 0.25 for d in DECISIONS}}
        last = prior[-1]
        return {"decision": {d: (0.6 if d == last else 0.4 / 3) for d in DECISIONS}}
    if arm == "CDIR":
        body = ("A writer is drafting with an assistant that offers suggestions. The document so far ends with:\n"
                f"...{h.get('doc_tail', '')[-600:]}\n\nThe assistant now shows this suggestion:\n{str(h.get('suggestion', ''))[:400]}\n\n"
                f"Earlier in this session the writer's decisions were: {', '.join(prior for prior in (h.get('prior_decisions') or [])[-6:]) or 'none yet'}.")
        r = client.likelihood(body + "\n\nWhat does the writer do with this suggestion?",
                              {"accept": "takes it as offered", "edit": "takes it and then changes its wording",
                               "dismiss": "closes it and writes on alone", "ignore": "leaves it open and writes on"}, evidence_sha, "decision")
        return {"decision": r["probs"] if r.get("valid") else {d: 0.25 for d in DECISIONS}}
    raise ValueError(arm)


def scholawrite(ev: dict, arm: str, client: Client, evidence_sha: str, task: dict) -> dict:
    h = ev["history"]
    cur = h.get("current_category")
    if arm == "SU":
        return {"next_category": {c: 1 / 3 for c in CATEGORIES}}
    if arm == "SPERS":
        rate = float(task.get("persistence_rate", 0.8))
        return {"next_category": {c: (rate if c == cur else (1 - rate) / 2) for c in CATEGORIES}}
    if arm == "SDIR":
        lines = []
        for e in h.get("window", []):
            lines.append(f"[{e.get('category', '?')}] before: {e['before'][-160:]!r} after: {e['after'][-160:]!r} (length change {e['len_delta']:+d})")
        body = ("A writer is revising a scholarly draft. Recent revision events, oldest first, each tagged with its kind of work "
                "(Planning, Implementation, Revision):\n" + "\n".join(lines))
        r = client.likelihood(body + "\n\nWhat kind of work is the writer's NEXT revision?",
                              {"Planning": "planning: outlining, noting ideas", "Implementation": "implementation: writing new content",
                               "Revision": "revision: reworking existing content"}, evidence_sha, "next_category")
        return {"next_category": r["probs"] if r.get("valid") else {c: 1 / 3 for c in CATEGORIES}}
    raise ValueError(arm)
