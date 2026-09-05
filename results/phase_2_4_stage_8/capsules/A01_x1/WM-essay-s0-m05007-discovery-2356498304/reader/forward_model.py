"""The forward-model reader inside the capsule (brief §4 FM, FM+P, FM+N; §6): the reader's
own generative distribution over the next log line, read out by scoring each live option's
serialization (and the stop line) under the model, normalized over the live set; the
changed-context choice by re-rendering the header under the change; earlier artifacts by
the same maker prepended as whole logs; a supplied or proposed purpose as the header's goal
line; the per-event mode (surprise localization) scores every boundary of a whole log on
its own prefix. The purpose proposal is a closed-set letter readout over the affordance
question (what could a reader use this document to do) with an explicit unknown option;
abstention and the equivalence class follow the Stage 7 band rule. STDLIB ONLY.

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §3 (a readout's candidate set is checked against the short-candidates
  rule: option lines share one grammar and differ only in the move; a per-token mean is not
  a ruler: the option score is the SUM over the option's tokens, all options being one
  short line; the known-answer probe of the readout is the guard suite's fake-server round
  trip and the pilot's oracle-versus-uniform check), §4 (instruct readers only; the adapter
  hash rides on every response).
gates: none here; the engines own the bands. bands: none.
"""

from __future__ import annotations

import math

from . import logfmt as LF
from .client8 import Client8

TYPES = ("write", "revise", "check", "consult", "cite", "restructure", "probe", "fix")
BAND = 0.15                                                     # the Stage 7 abstention band


def _softmax(vals: list[float]) -> list[float]:
    m = max(vals)
    ex = [math.exp(v - m) for v in vals]
    z = sum(ex)
    return [e / z for e in ex]


def _induced(next_action: dict, options: list[dict], sections: list[str]) -> tuple[dict, dict]:
    td = {t: 0.0 for t in TYPES}
    sd = {s: 0.0 for s in sections}
    for a in options:
        aid = f"{a['type']}:{a['section']}:{a['slot']}"
        p = next_action.get(aid, 0.0)
        td[a["type"]] += p
        sd[a["section"]] = sd.get(a["section"], 0.0) + p
    return td, sd


def _options_at(ev: dict) -> list[dict]:
    oo = ev.get("objective_options") or {}
    return list(oo.get("at_cut", [])) if isinstance(oo, dict) else list(oo or [])


def earlier_logs(ev: dict) -> list[str]:
    return [d["text"] for d in (ev.get("demonstrations") or []) if d.get("text")]


def score_boundary(client: Client8, prefix_text: str, i: int, option_ids: list[str], adapter: bool = True) -> dict:
    """One boundary: the live options' lines and the stop line scored in one call."""
    lines = []
    for aid in option_ids:
        t, s, sl = aid.split(":")
        lines.append(LF.event_line(i, t, s, sl))
    lines.append(LF.stop_line(i))
    r = client.sequence_logprobs(prefix_text, lines, adapter=adapter)
    lps = [float(x) for x in r["logprobs"]]
    opt_lps = lps[:-1]
    stop_lp = lps[-1]
    probs = _softmax(opt_lps) if opt_lps else []
    na = {aid: p for aid, p in zip(option_ids, probs)}
    m = max(lps)
    z = sum(math.exp(v - m) for v in lps)
    p_stop = math.exp(stop_lp - m) / z
    return {"next_action": na, "p_stop": p_stop, "option_lps": dict(zip(option_ids, opt_lps)), "stop_lp": stop_lp,
            "revision": r.get("revision"), "adapter_sha": r.get("adapter_sha")}


def predict(ev: dict, client: Client8, task: dict) -> dict:
    """FM / FM+P / FM+N / the context and state variants, by task keys: goal_line (a purpose
    name or None), earlier (use the demonstrations as earlier logs), context_override (a
    header change), state_lines (extra header lines, E08), per_event (score every boundary),
    adapter (False for the untrained base through the same readout)."""
    q = ev["query"]
    adapter = bool(task.get("adapter", True))
    head = LF.header_from_evidence(ev, goal=task.get("goal_line"), context_override=task.get("context_override"))
    if task.get("state_lines"):
        head_lines = head.split("\n")
        head = "\n".join(head_lines[:-1] + list(task["state_lines"]) + head_lines[-1:])
    earlier = earlier_logs(ev) if task.get("earlier") else []
    prefix = ev.get("process_prefix", [])
    plines = LF.prefix_lines(prefix)
    opts = _options_at(ev)
    out: dict = {"notes": {"header": head, "n_earlier": len(earlier)}}
    if task.get("per_event"):
        per = []
        oo = ev.get("objective_options") or {}
        per_opts = oo.get("per_event") or []
        for i in range(len(prefix)):
            ids = per_opts[i] if i < len(per_opts) else q["next_action_options"]
            if not ids:
                per.append({"next_action": {}, "p_stop": None})
                continue
            r = score_boundary(client, LF.compose(earlier, head, plines[:i]), i, list(ids), adapter)
            per.append({"next_action": r["next_action"], "p_stop": r["p_stop"]})
        out["notes"]["per_event"] = per
        last = per[-1] if per else {"next_action": {}, "p_stop": 0.5}
        ids = q["next_action_options"]
        na = {k: last["next_action"].get(k, 0.0) for k in ids} if ids else {}
        z = sum(na.values())
        na = {k: v / z for k, v in na.items()} if z > 0 else {k: 1.0 / max(1, len(ids)) for k in ids}
        td, sd = _induced(na, opts, q["sections"])
        out.update({"next_action": na, "next_type": td, "next_section": sd, "p_stop": last["p_stop"] if last["p_stop"] is not None else 0.5})
        return out
    i = len(prefix)
    ids = list(q["next_action_options"])
    r = score_boundary(client, LF.compose(earlier, head, plines), i, ids, adapter)
    td, sd = _induced(r["next_action"], opts, q["sections"])
    out.update({"next_action": r["next_action"], "next_type": td, "next_section": sd, "p_stop": r["p_stop"]})
    out["notes"].update({"option_lps": r["option_lps"], "stop_lp": r["stop_lp"], "revision": r.get("revision"), "adapter_sha": r.get("adapter_sha")})
    change = q.get("context_change")
    if change and ids:
        b = ev.get("brief") or {}
        ctx = LF.apply_change_to_header_context(b, change)
        head2 = LF.header_from_evidence(ev, goal=task.get("goal_line"), context_override=ctx)
        if task.get("state_lines"):
            hl = head2.split("\n")
            head2 = "\n".join(hl[:-1] + list(task["state_lines"]) + hl[-1:])
        r2 = score_boundary(client, LF.compose(earlier, head2, plines), i, ids, adapter)
        out["changed_context"] = r2["next_action"]
    return out


def purpose_distribution(ev: dict, client: Client8, evidence_sha: str, candidates: dict, weights: str = "adapted") -> dict:
    """The affordance question over the closed purpose set plus unknown; the equivalence
    class is the set within BAND of the top; abstention when the class has two or more or
    unknown leads."""
    from .supplied_state import evidence_text                                   # the Stage 7 evidence rendering
    body = evidence_text(ev) + "\n\nWhat could a reader use this document to do?"
    opts = dict(candidates)
    opts["unknown"] = "it is not possible to tell from this"
    if weights == "base":
        r = client.likelihood_base(body, opts, evidence_sha, "purpose")
    else:
        r = client.likelihood(body, opts, evidence_sha, "purpose")
    if not r.get("valid"):
        probs = {k: 1.0 / len(opts) for k in opts}
    else:
        probs = dict(r["probs"])
    named = {k: v for k, v in probs.items() if k != "unknown"}
    z = sum(named.values()) or 1.0
    named = {k: v / z for k, v in named.items()}
    top = max(named.values()) if named else 0.0
    cls = sorted(k for k, v in named.items() if top - v <= BAND)
    unknown = probs.get("unknown", 0.0)
    abstain = len(cls) >= 2 or unknown >= max(named.values(), default=0.0)
    return {"purpose": named, "raw": probs, "equivalence_class": cls, "abstain": abstain,
            "confidence": top, "unknown": unknown, "weights": weights}


def recall_distribution(ev: dict, client: Client8, evidence_sha: str, question: str, candidates: dict, salt: str, weights: str = "adapted") -> dict:
    """A closed-set recall question (the pull ordering, the law, the residue) with the
    candidates the engine supplies, surface-matched by construction."""
    from .supplied_state import evidence_text
    body = evidence_text(ev) + "\n\n" + question
    if weights == "base":
        r = client.likelihood_base(body, candidates, evidence_sha, salt)
    else:
        r = client.likelihood_any(body, candidates, evidence_sha, salt) if len(candidates) > 6 else client.likelihood(body, candidates, evidence_sha, salt)
    probs = dict(r["probs"]) if r.get("valid") else {k: 1.0 / len(candidates) for k in candidates}
    return {"dist": probs, "confidence": max(probs.values()) if probs else 0.0}


def generate_log(ev: dict, client: Client8, task: dict) -> dict:
    """The generation gate: the reader writes a whole log from the header alone (no prefix,
    no earlier work), sampled from its own distribution; parsed events and the stop flag."""
    head = LF.header_from_evidence(ev, goal=task.get("goal_line"))
    prefix = LF.compose([], head, [])
    r = client.sample_log(prefix, int(task.get("seed", 0)), max_lines=int(task.get("max_lines", 40)),
                          temperature=float(task.get("temperature", 1.0)), adapter=bool(task.get("adapter", True)))
    events = []
    stopped = False
    for ln in (r.get("text") or "").split("\n"):
        e = LF.parse_line(ln)
        if e is None:
            if events:
                break
            continue
        if e.get("stop"):
            stopped = True
            break
        events.append({"type": e["type"], "section": e["section"], "slot": e["slot"], "outcome": e.get("outcome", "done")})
    return {"events": events, "stopped": stopped, "raw": (r.get("text") or "")[:4000], "n_new_tokens": r.get("n_new_tokens"),
            "revision": r.get("revision"), "adapter_sha": r.get("adapter_sha")}
