"""The direct model reader DIR (§8) and the known-law selector KL inside the capsule.
DIR reads the visible evidence (prefix, brief, any supplied factors in their given form,
the live options) and answers every target through the letter-likelihood readout, option
order fixed per unit from the evidence hash. KL scores each supplied executable law's
prefix likelihood with the other supplied factors and mixes the laws' executions by the
posterior: system identification among supplied laws, never learning. STDLIB ONLY.

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §3 (score the SHORT hypothesis text given the LONG evidence; the
  letter readout with fixed order per unit across arms; a readout's candidate set is
  checked against the short-candidates rule: option descriptions are short and
  surface-matched by construction), §4 (instruct readers only).
gates: none here; the engines own the bands. bands: none.
"""

from __future__ import annotations

import math

from . import law as LAW
from .client import Client

TYPES = list(LAW.ACTION_TYPES)
TYPE_WORDS = {"write": "draft a slot", "revise": "rework a slot", "check": "check a section",
              "consult": "consult a source", "cite": "add a reference", "restructure": "reorder a section",
              "probe": "try a technique", "fix": "repair a slot"}


def evidence_text(ev: dict) -> str:
    """The evidence as the reader sees it: brief, artifact state, prefix, supplied factors
    (executable rendered as compact JSON-like lines, language verbatim), demonstrations,
    candidate laws, regime note."""
    parts = []
    b = ev.get("brief")
    if b:
        parts.append(f"Brief: required sections {', '.join(b['required_sections'])}; audience {b['audience']}; "
                     f"library {'available' if b['tools_available'].get('library') else 'unavailable'}, "
                     f"source access {'available' if b['tools_available'].get('source_access') else 'unavailable'}; deadline {b['deadline']}.")
    st = ev["artifact_state"]
    parts.append("Document: " + "; ".join(f"{s['name']} [{', '.join(s['filled']) or 'empty'}]" for s in st["sections"]))
    parts.append("The work so far:\n" + st.get("prefix_text", ""))
    sf = ev.get("supplied_factors")
    if sf:
        if sf.get("generic_law"):
            g = sf["generic_law"]
            parts.append("What is typical in this domain: strongest at " + ", ".join(k for k, _ in sorted(g["skill"].items(), key=lambda kv: -kv[1])[:3])
                         + f"; an episode usually runs about {int(g['expected_len'])} moves.")
        for name, val in (sf.get("factors") or {}).items():
            label = {"external_context": "Context", "belief_state": "What the maker believes", "expertise_law": "How this maker works",
                     "maker_context": "The situation as the maker sees it", "subjective_action_space": "Moves the maker sees as open",
                     "proximal_goal": "What the maker is after right now", "history_residue": "Carried habits and intentions"}[name]
            if isinstance(val, str):
                parts.append(f"{label}: {val}")
            else:
                parts.append(f"{label} (given as data): {_compact(val)}")
    demos = ev.get("demonstrations")
    if demos:
        for d in demos:
            parts.append(f"An earlier episode by the same maker ({d['topic']}):\n{d['text']}")
    laws = ev.get("candidate_laws")
    if laws:
        parts.append("Candidate ways this maker might work (exactly one is right):")
        for L in laws:
            parts.append(f"  {L['law_ref']}: {_compact(L['law'])}")
    return "\n\n".join(parts)


def _compact(v) -> str:
    if isinstance(v, dict):
        return "{" + ", ".join(f"{k}: {_compact(x)}" for k, x in v.items()) + "}"
    if isinstance(v, list):
        return "[" + ", ".join(_compact(x) for x in v) + "]"
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v)


def _option_words(opts: list[dict]) -> dict:
    return {LAW.action_id(a): f"{TYPE_WORDS[a['type']]}: {a['section']} {a['slot']}" for a in opts}


def direct(ev: dict, client: Client, evidence_sha: str, targets: tuple[str, ...] | None = None) -> dict:
    """DIR: every target answered from the evidence text; next action over the live
    objective options (the reader must place mass away from subjectively unavailable
    ones on its own); stop as a two-way question; changed context, invalidation, and
    boundary type as their small option sets."""
    q = ev["query"]
    body = evidence_text(ev)
    opts = LAW.options_at_cut(ev)
    words = _option_words(opts)
    out = {}
    want = set(targets or ("next_action", "next_type", "next_section", "stop", "changed_context", "invalidation", "boundary_type"))
    if "next_action" in want:
        r = client.likelihood_any(body + "\n\nWhat does the maker do next?", words, evidence_sha, "next_action")
        out["next_action"] = r["probs"] if r.get("valid") else {k: 1.0 / len(words) for k in words}
    if "next_type" in want:
        r = client.likelihood_any(body + "\n\nWhat kind of move comes next?", {t: TYPE_WORDS[t] for t in TYPES}, evidence_sha, "next_type")
        out["next_type"] = r["probs"] if r.get("valid") else {t: 1.0 / len(TYPES) for t in TYPES}
    if "next_section" in want:
        secs = {s: f"the part called {s}" for s in q["sections"]}
        r = client.likelihood(body + "\n\nWhere does the maker work next?", secs, evidence_sha, "next_section")
        out["next_section"] = r["probs"] if r.get("valid") else {s: 1.0 / len(secs) for s in secs}
    if "stop" in want:
        r = client.likelihood(body + "\n\nAt the next natural pause, does the maker stop for good?",
                              {"stop": "stops here", "continue": "keeps going"}, evidence_sha, "stop")
        out["p_stop"] = r["probs"].get("stop", 0.5) if r.get("valid") else 0.5
    if "changed_context" in want:
        change = q.get("context_change", "")
        desc = {"library_arrives": "the library becomes available", "library_withdrawn": "the library is withdrawn",
                "deadline_lifted": "the deadline is lifted", "deadline_imposed": "a tight deadline is imposed",
                "audience_changes": "the audience changes"}.get(change, change)
        r = client.likelihood_any(body + f"\n\nSuppose {desc}. What does the maker do next?", words, evidence_sha, "changed_context")
        out["changed_context"] = r["probs"] if r.get("valid") else {k: 1.0 / len(words) for k in words}
    if "invalidation" in want:
        r = client.likelihood(body + "\n\nA source the maker used is later shown to be wrong. What does the maker do?",
                              {"correct": "corrects the passage that used it", "retain": "keeps the passage as it is",
                               "rewrite": "rewrites the whole part around it"}, evidence_sha, "invalidation")
        out["invalidation"] = r["probs"] if r.get("valid") else {k: 1 / 3 for k in ("correct", "retain", "rewrite")}
    if "boundary_type" in want:
        r = client.likelihood(body + "\n\nIf the maker stops at the next pause, why?",
                              {"satisfaction": "the current aim is met", "deadline": "time has run out",
                               "fatigue": "the maker is worn down", "equivalent": "no single reason stands out"}, evidence_sha, "boundary_type")
        out["boundary_type"] = r["probs"] if r.get("valid") else {k: 0.25 for k in q["boundary_types"]}
    return out


def known_law_select(ev: dict, client: Client | None = None) -> dict | None:
    """KL: posterior over the supplied candidate laws from the exact prefix likelihood,
    every other factor taken from the supplied set; predictions mixed by the posterior.
    None when the other factors are not supplied (the selector cannot run)."""
    laws = ev.get("candidate_laws")
    sf = (ev.get("supplied_factors") or {})
    if not laws or sf.get("form") != "executable":
        return None
    base = dict(sf.get("factors") or {})
    lls = {}
    execs = {}
    for L in laws:
        st = dict(base, expertise_law=L["law"])
        st.pop("maker_context", None)
        st.pop("subjective_action_space", None)
        try:
            lls[L["law_ref"]] = LAW.prefix_log_likelihood(st, ev)
            execs[L["law_ref"]] = LAW.execute(st, ev)
            kind = ev["query"].get("context_change")
            execs[L["law_ref"]]["changed_context"] = LAW.execute_changed(st, ev, kind)["next_action"] if kind else None
        except LAW.LawError:
            return None
        if client:
            client.solver(3)
    mx = max(lls.values())
    post = {k: math.exp(v - mx) for k, v in lls.items()}
    z = sum(post.values())
    post = {k: v / z for k, v in post.items()}
    na: dict = {}
    cc: dict = {}
    inv: dict = {}
    p_stop = 0.0
    for ref, w in post.items():
        for k, p in execs[ref]["next_action"].items():
            na[k] = na.get(k, 0.0) + w * p
        for k, p in (execs[ref].get("changed_context") or {}).items():
            cc[k] = cc.get(k, 0.0) + w * p
        for k, p in (execs[ref].get("invalidation") or {}).items():
            inv[k] = inv.get(k, 0.0) + w * p
        p_stop += w * execs[ref]["p_stop"]
    opts = LAW.options_at_cut(ev)
    td = {t: 0.0 for t in TYPES}
    sd = {s: 0.0 for s in ev["query"]["sections"]}
    for a in opts:
        td[a["type"]] += na.get(LAW.action_id(a), 0.0)
        sd[a["section"]] = sd.get(a["section"], 0.0) + na.get(LAW.action_id(a), 0.0)
    top = sorted(post.items(), key=lambda kv: -kv[1])
    eq = [k for k, v in top if v >= top[0][1] - 1e-6]
    return {"next_action": na, "next_type": td, "next_section": sd, "p_stop": p_stop, "posterior": post,
            "changed_context": cc or None, "invalidation": inv or None,
            "equivalence_class": eq, "abstain": len(eq) > 1, "confidence": top[0][1]}
