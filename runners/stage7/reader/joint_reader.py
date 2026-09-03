"""The Sounding joint reader SL-J (§8) and the locally named external mechanisms (§5)
inside the capsule. STDLIB ONLY.

SL-J: for every WITHHELD factor the model PROPOSES candidate values as content (never as
tags: a goal is an ordering of pulls, a belief is a set of flags, a law is a skill shape
or, with demonstrations, a fitted parameter table, an action space is a subset of the
live options, a maker context is perceived tools and deadline, a residue is a habit or a
held intention); proposals are parsed into executable candidates; the solver computes
the exact prefix likelihood of every candidate combination with the supplied factors;
the posterior weighs the candidates' executions into one prediction; the equivalence
class is the set of candidates within a band of the top; abstention fires when the class
is not a singleton. Candidate generation and candidate selection are logged separately
(R01-R05 read the proposal lists; R06-R13 read the posteriors and prospective scores).

The external mechanisms carry their LOCAL names by default (the packet uses no published
name without a passed conformance fixture, §5):
  weighted_language_hypotheses   the model proposes hypotheses AND a likelihood rule per
                                 hypothesis (a type-weight table); the posterior is computed
                                 externally from the rule, never by the model
  sequential_hypothesis_particles particles over factor candidates propagated across
                                 prefix checkpoints, weighted by the solver's step
                                 likelihoods, ESS-resampled, rejuvenated by re-proposal
                                 when text diversity collapses
  adaptive_factor_expansion      start from the goal alone; add belief, residue, then law
                                 only when held-out prefix likelihood improves past a
                                 threshold; extend the evidence window only when the
                                 current window leaves the top candidates tied
  synthesized_agent_model        the model synthesizes a law table as data, validated for
                                 syntax and semantics, executed by the solver
  known_law_inverse_planning     the exact grid posterior (a known-law reference)
  epistemic_translation          belief sentences parsed into the belief structure;
                                 belief-sensitive posterior

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §3 (candidate generation scored apart from selection: selection
  cannot be credited when the true candidate was never generated; short hypothesis
  given long evidence; a distinctness gate sized by identifiability, so the equivalence
  band is derived from the prefix length), §4 (instruct readers only; a model
  adjudicator is a ruler: proposals are parsed by a strict grammar and unparsed output
  counts as no proposal, never as a guess).
gates: none here; the engines own the bands. bands: none.
"""

from __future__ import annotations

import itertools
import math
import re

from . import law as LAW
from .client import Client
from .supplied_state import TYPE_WORDS, evidence_text

TYPES = list(LAW.ACTION_TYPES)
TOOLS = list(LAW.TOOLS)
MAX_COMBOS = 96
OWNER_OF = {"write": "produce", "probe": "produce", "revise": "tighten", "restructure": "tighten",
            "check": "audit", "consult": "audit", "fix": "audit", "cite": "attribute"}


# ── proposal grammars (parsed strictly; unparsed = no proposal) ───────────────────────

LAST_RAW: dict = {}


def _lines(text: str) -> list[str]:
    return [ln.strip(" -*\t") for ln in text.splitlines() if ln.strip(" -*\t")]


def propose_goal(client: Client, body: str, seed: int, n: int = 3) -> list[dict]:
    """Candidate goals as pull orderings: 'pull: TYPE > TYPE' lines; each maps to the
    utility table whose top two match (the executable candidate)."""
    prompt = (body + "\n\nWhat is the maker after right now? Give up to three guesses, each on its own line, as "
              "'pull: FIRST > SECOND' where FIRST and SECOND are two of: " + ", ".join(TYPES) + ". Nothing else.")
    g = client.generate(prompt, seed=seed, max_new=48, greedy=True)
    LAST_RAW["proximal_goal"] = g.get("text", "")
    out, seen = [], set()
    keys = []
    for ln in _lines(g["text"]):
        m = re.match(r"pull:\s*([a-z]+)\s*>\s*([a-z]+)", ln.lower())
        if not m or m.group(1) not in TYPES or m.group(2) not in TYPES:
            continue
        keys.append(((m.group(1), m.group(2)), ln))
    if not keys:
        # a prose answer naming action types in order ('working on revising sec1 and checking
        # sec2') is decoded as the pull ordering of the first two distinct types named
        named = []
        for w in re.findall(r"[a-z]+", g.get("text", "").lower()):
            t = _TYPE_WORD.get(w)
            if t and t not in named:
                named.append(t)
        if len(named) == 1:
            # one type named: the goal that owns it, the second slot from its standard table
            order = [t for t, _ in sorted(LAW.GOAL_UTILITY[OWNER_OF[named[0]]].items(), key=lambda kv: -kv[1]) if t != named[0]]
            named.append(order[0])
        if len(named) >= 2:
            keys.append(((named[0], named[1]), "prose: " + " > ".join(named[:2]) + " | " + g.get("text", "").strip()[:120]))
    for key, ln in keys:
        if key in seen:
            continue
        seen.add(key)
        # the executable content: the standard table of the goal that owns the top type
        owner = OWNER_OF[key[0]]
        out.append({"ref": f"g{len(out)}", "content": {"utility": dict(LAW.GOAL_UTILITY[owner]), "owner": owner}, "text": ln, "signature": key})
    return out[:n]


_TYPE_WORD = {}
for _t in ("write", "revise", "check", "consult", "cite", "restructure", "probe", "fix"):
    for _form in (_t, _t + "s", _t + "d", _t + "ed", _t + "ing", _t.rstrip("e") + "ing", _t + "es"):
        _TYPE_WORD[_form] = _t
_TYPE_WORD.update({"writing": "write", "written": "write", "wrote": "write", "revising": "revise", "revision": "revise", "revisions": "revise",
                   "checking": "check", "checks": "check", "consulting": "consult", "consultation": "consult", "citing": "cite", "citation": "cite",
                   "citations": "cite", "restructuring": "restructure", "reordering": "restructure", "probing": "probe", "fixing": "fix",
                   "repairing": "fix", "repair": "fix", "drafting": "write", "draft": "write", "reworking": "revise",
                   "rework": "revise", "reworks": "revise", "reworked": "revise", "tightening": "revise", "tighten": "revise",
                   "verify": "check", "verifying": "check", "auditing": "check", "audit": "check", "sourcing": "consult"})


_FIELD = re.compile(r"([a-z_]+)\s*=\s*([a-z0-9|]+)")


def _field_proposals(lines: list[str], key: str, fields: tuple, allowed: dict, defaults: dict | None) -> list[tuple]:
    """Lines starting with `key` carry field=value pairs. A line with every field is one
    proposal; consecutive partial lines merge into one proposal, the missing fields filled
    from `defaults` (the visible brief) when given, else dropped. A value that still holds
    the template's alternatives ('yes|no') is no commitment and is dropped."""
    out, seen = [], set()
    partial: dict = {}

    def flush():
        nonlocal partial
        if partial:
            filled = dict(defaults or {})
            filled.update(partial)
            if all(f in filled for f in fields):
                key_ = tuple(filled[f] for f in fields)
                if key_ not in seen:
                    seen.add(key_)
                    out.append(key_)
            partial = {}

    for ln in lines:
        low = ln.lower()
        if not low.startswith(key):
            continue
        pairs = {k: v for k, v in _FIELD.findall(low[len(key):]) if k in allowed and v in allowed[k]}
        if not pairs:
            continue
        if all(f in pairs for f in fields):
            flush()
            key_ = tuple(pairs[f] for f in fields)
            if key_ not in seen:
                seen.add(key_)
                out.append(key_)
            continue
        if any(f in partial for f in pairs):        # a new partial proposal begins
            flush()
        partial.update(pairs)
    flush()
    return out


def propose_belief(client: Client, body: str, seed: int, n: int = 3, defaults: dict | None = None) -> list[dict]:
    prompt = (body + "\n\nWhat does the maker believe about the situation? Give up to three guesses, each on its own line, as "
              "'belief: library=yes|no source=yes|no deadline=tight|loose checked=SECTION|none'. Nothing else.")
    g = client.generate(prompt, seed=seed, max_new=64, greedy=True)
    LAST_RAW["belief_state"] = g.get("text", "")
    allowed = {"library": {"yes", "no"}, "source": {"yes", "no"}, "deadline": {"tight", "loose"},
               "checked": {"none"} | {f"sec{i}" for i in range(1, 9)}}
    out = []
    for key in _field_proposals(_lines(g["text"]), "belief:", ("library", "source", "deadline", "checked"), allowed, defaults):
        out.append({"ref": f"b{len(out)}", "text": "belief: " + " ".join(f"{f}={v}" for f, v in zip(("library", "source", "deadline", "checked"), key)),
                    "signature": key,
                    "content": {"believed_tools": {"library": key[0] == "yes", "source_access": key[1] == "yes"},
                                "believed_deadline": key[2], "believed_checked": [] if key[3] == "none" else [key[3]]}})
    return out[:n]


def propose_law(client: Client, body: str, seed: int, n: int = 3) -> list[dict]:
    """Candidate laws as skill shapes: 'skill: STRONG,STRONG weak: WEAK,WEAK pace: steady|erratic'."""
    prompt = (body + "\n\nHow does this maker work? Give up to three guesses, each on its own line, as "
              "'skill: A,B weak: C,D pace: steady|erratic' with A-D from: " + ", ".join(TYPES) + ". Nothing else.")
    g = client.generate(prompt, seed=seed, max_new=64, greedy=True)
    LAST_RAW["expertise_law"] = g.get("text", "")
    out, seen = [], set()
    keys = []
    # a proposal may sit on one line ('skill: a,b weak: c,d pace: steady') or across
    # consecutive lines ('skill: ...' / 'weak: ...' / 'pace: ...'); records are merged
    records: list[dict] = []
    for ln in _lines(g["text"]):
        low = re.sub(r"^\d+[.)]\s*", "", ln.lower())
        low = re.sub(r"\b(?:skills|strengths?|strong)\s*:", "skill:", low)      # the readers' synonyms
        low = re.sub(r"\b(?:weaknesses|weakness|weaks)\s*:", "weak:", low)
        parts = re.split(r"(?=\b(?:skill|weak|pace)\s*:)", low)
        fields = {}
        for part in parts:
            mm = re.match(r"(skill|weak|pace)\s*:\s*(.*)", part.strip())
            if mm:
                fields[mm.group(1)] = mm.group(2)
        if not fields:
            continue
        if "skill" in fields or not records or any(k in records[-1] for k in fields):
            records.append(dict(fields))
        else:
            records[-1].update(fields)
    for rec in records:
        strong = [x for x in re.findall(r"[a-z]+", rec.get("skill", "")) if x in TYPES]
        weak = [x for x in re.findall(r"[a-z]+", rec.get("weak", "")) if x in TYPES]
        if len(weak) == 0 and re.search(r"\b(?:none|no)\b", rec.get("weak", "")):
            weak = ["none", "none"]                       # 'weak: none': two strong types, no weak ones
        if len(strong) < 2 or len(weak) < 2 or set(strong[:2]) & set(weak[:2]):
            continue                                      # incomplete, or every type in every slot: no proposal
        pm = re.search(r"(steady|erratic)", rec.get("pace", ""))
        paces = [pm.group(1)] if pm else ["steady", "erratic"]       # no pace given: both, weighed by the prefix
        for pace in paces:
            keys.append((strong[0], strong[1], weak[0], weak[1], pace))
    for key in keys:
        if key in seen:
            continue
        seen.add(key)
        ln = f"skill: {key[0]},{key[1]} weak: {key[2]},{key[3]} pace: {key[4]}"
        skill = {t: 0.5 for t in TYPES}
        skill[key[0]] = 0.9
        skill[key[1]] = 0.85
        cost = {t: 0.3 for t in TYPES}
        cost[key[0]] = 0.1
        cost[key[1]] = 0.1
        if key[2] != "none":                             # 'weak: none' leaves the other types at the default
            skill[key[2]] = 0.25
            skill[key[3]] = 0.3
            cost[key[2]] = 0.6
            cost[key[3]] = 0.5
        out.append({"ref": f"k{len(out)}", "text": ln, "signature": key,
                    "content": {"skill": skill, "feasible_min_skill": {"restructure": 0.6, "probe": 0.4, "fix": 0.3},
                                "cost": cost, "chain": {}, "fluency": 0.9 if key[4] == "steady" else 1.6,
                                "expected_len": 12.0, "confidence": 0.7 if key[4] == "steady" else 0.4}})
    return out[:n]


def propose_action_space(client: Client, body: str, options: list[str], seed: int, n: int = 3) -> list[dict]:
    prompt = (body + "\n\nWhich of these moves does the maker see as open right now? Give up to three guesses, each on its "
              "own line, as 'open: id, id, id' using ids from: " + ", ".join(sorted(options)) + ". Nothing else.")
    g = client.generate(prompt, seed=seed, max_new=96, greedy=True)
    LAST_RAW["subjective_action_space"] = g.get("text", "")
    out, seen = [], set()
    for ln in _lines(g["text"]):
        m = re.match(r"open:\s*(.+)", ln.lower())
        if not m:
            continue
        ids = tuple(sorted({x.strip() for x in m.group(1).split(",") if x.strip() in options}))
        if not ids or ids in seen:
            continue
        seen.add(ids)
        out.append({"ref": f"a{len(out)}", "text": ln, "signature": ids, "content": list(ids)})
    return out[:n]


def propose_context(client: Client, body: str, seed: int, n: int = 3, defaults: dict | None = None) -> list[dict]:
    prompt = (body + "\n\nHow does the maker see the situation (which may differ from the brief)? Up to three guesses, each on "
              "its own line, as 'sees: library=usable|not deadline=tight|loose audience=high|low|none'. Nothing else.")
    g = client.generate(prompt, seed=seed, max_new=64, greedy=True)
    LAST_RAW["maker_context"] = g.get("text", "")
    allowed = {"library": {"usable", "not"}, "deadline": {"tight", "loose"}, "audience": {"high", "low", "none"}}
    out = []
    for key in _field_proposals(_lines(g["text"]), "sees:", ("library", "deadline", "audience"), allowed, defaults):
        ln = f"sees: library={key[0]} deadline={key[1]} audience={key[2]}"
        out.append({"ref": f"c{len(out)}", "text": ln, "signature": key,
                    "content": {"perceived_tools": {"library": key[0] == "usable", "source_access": True},
                                "perceived_deadline": key[1], "audience_weight": {"high": 0.8, "low": 0.3, "none": 0.0}[key[2]]}})
    return out[:n]


def propose_residue(client: Client, body: str, options: list[str], seed: int, n: int = 3) -> list[dict]:
    prompt = (body + "\n\nWhat carried habit or held intention shapes this maker's moves? Up to three guesses, each on its own "
              "line, as 'habit: TYPE intention: ID', where TYPE is one of " + ", ".join(TYPES) + " or none, and ID is one of the "
              "option ids or none. Nothing else.")
    g = client.generate(prompt, seed=seed, max_new=64, greedy=True)
    LAST_RAW["history_residue"] = g.get("text", "")
    out, seen = [], set()
    for ln in _lines(g["text"]):
        low = re.sub(r"^\d+[.)]\s*", "", ln.lower())
        # the readers copy notation: 'habit: write|none intention: none', 'habit: revise|intention: improve'
        m = re.match(r"habit:\s*([a-z]+)(?:\s*(?:\||/|,|;|\bor\b)\s*(?!intention)[a-z]*)*\s*[,;|]?\s*intention:\s*([a-z0-9:._-]+)", low)
        if not m:
            continue
        hab, intent = m.group(1), m.group(2)
        if hab == "no":
            hab = "none"
        if hab != "none" and hab not in TYPES:
            continue
        if intent not in options:
            intent = "none"                                # an intention that is not an option id: no held intention
        key = (hab, intent)
        if key in seen:
            continue
        seen.add(key)
        maint = None if intent == "none" else {"cue_step": 10 ** 6, "option": intent}
        out.append({"ref": f"h{len(out)}", "text": ln, "signature": key,
                    "content": {"habit": {} if hab == "none" else {hab: 0.9}, "maintained": maint}})
    if not out:
        # nothing parsed: the null residue (no carried habit, no held intention) keeps the
        # proposal set solvable; flagged default so the notes record the raw text as unparsed
        out.append({"ref": "h0", "text": "default: no carried habit, no held intention", "signature": ("none", "none"),
                    "content": {"habit": {}, "maintained": None}, "default": True})
    return out[:n]


PROPOSERS = {"proximal_goal": propose_goal, "belief_state": propose_belief, "expertise_law": propose_law,
             "subjective_action_space": propose_action_space, "maker_context": propose_context,
             "history_residue": propose_residue}


# ── the joint posterior through the solver ───────────────────────────────────────────

def _band(n_prefix: int) -> float:
    """The equivalence band in nats, sized by the observation count: two candidates
    within one over the prefix length of each other in log likelihood are treated as
    unresolved (LESSONS §3's identifiability rule)."""
    return 1.0 / max(1, n_prefix)


def joint_posterior(ev: dict, supplied: dict, proposals: dict, client: Client) -> dict | None:
    """Every combination of proposals for the withheld factors (capped), each completed
    with the supplied factors, scored by exact prefix likelihood; returns the posterior,
    the mixed prediction, and the equivalence class."""
    names = list(proposals)
    lists = [proposals[n] for n in names]
    if any(not L for L in lists):
        return None
    combos = list(itertools.product(*lists))[:MAX_COMBOS]
    lls, execs, keys = {}, {}, {}
    for combo in combos:
        st = dict(supplied)
        key = "|".join(c["ref"] for c in combo)
        for n, c in zip(names, combo):
            st[n] = c["content"]
        st.pop("maker_context", None) if "maker_context" not in proposals else None
        if "subjective_action_space" not in proposals:
            st.pop("subjective_action_space", None)
        try:
            lls[key] = LAW.prefix_log_likelihood(st, ev)
            execs[key] = LAW.execute(st, ev)
            kind = ev["query"].get("context_change")
            execs[key]["changed_context"] = LAW.execute_changed(st, ev, kind)["next_action"] if kind else None
        except LAW.LawError:
            continue
        keys[key] = {n: c["ref"] for n, c in zip(names, combo)}
        client.solver(3)
    if not lls:
        return None
    mx = max(lls.values())
    post = {k: math.exp(v - mx) for k, v in lls.items()}
    z = sum(post.values())
    post = {k: v / z for k, v in post.items()}
    band = _band(len(ev.get("process_prefix", [])))
    eq = sorted(k for k, v in lls.items() if v >= mx - band)
    na: dict = {}
    cc: dict = {}
    inv: dict = {}
    p_stop = 0.0
    for k, w in post.items():
        for a, p in execs[k]["next_action"].items():
            na[a] = na.get(a, 0.0) + w * p
        for a, p in (execs[k].get("changed_context") or {}).items():
            cc[a] = cc.get(a, 0.0) + w * p
        for a, p in (execs[k].get("invalidation") or {}).items():
            inv[a] = inv.get(a, 0.0) + w * p
        p_stop += w * execs[k]["p_stop"]
    opts = LAW.options_at_cut(ev)
    td = {t: 0.0 for t in TYPES}
    sd = {s: 0.0 for s in ev["query"]["sections"]}
    for a in opts:
        td[a["type"]] += na.get(LAW.action_id(a), 0.0)
        sd[a["section"]] = sd.get(a["section"], 0.0) + na.get(LAW.action_id(a), 0.0)
    # per-factor marginals (the factor posterior, scored apart from the prospective gain)
    marg = {n: {} for n in names}
    for k, w in post.items():
        for n in names:
            r = keys[k][n]
            marg[n][r] = marg[n].get(r, 0.0) + w
    cand_preds = {k: dict(sorted(execs[k]["next_action"].items(), key=lambda kv: -kv[1])[:4]) for k in post}
    return {"next_action": na, "next_type": td, "next_section": sd, "p_stop": p_stop, "posterior": post,
            "changed_context": cc or None, "invalidation": inv or None,
            "factor_marginals": marg, "equivalence_class": eq, "abstain": len(eq) > 1,
            "confidence": max(post.values()), "band": band, "n_combos": len(lls), "candidate_preds": cand_preds}


def context_from_brief(ev: dict) -> dict | None:
    """The external context is never proposed: it is visible in the brief."""
    b = ev.get("brief")
    if not b:
        return None
    return {"brief_sections": list(b.get("required_sections", [])), "audience": b.get("audience", "peer"),
            "tools": {t: bool(v) for t, v in (b.get("tools_available") or {}).items()}, "deadline": b.get("deadline", "loose")}


def proposable(withheld: list[str]) -> list[str]:
    """Which withheld factors the reader proposes: never the external context (visible);
    the maker context and the subjective action space only when belief and law are
    supplied (otherwise they derive from the proposed belief and law)."""
    out = [f for f in withheld if f in PROPOSERS]
    if "belief_state" in withheld or "expertise_law" in withheld:
        out = [f for f in out if f not in ("maker_context", "subjective_action_space")]
    return out


def sounding_joint(ev: dict, client: Client, evidence_sha: str, withheld: list[str], seed: int,
                   propose: list[str] | None = None) -> dict:
    """SL-J proper: propose for every withheld factor, then the joint posterior. When the
    task names `propose`, only those withheld factors are proposed; a withheld factor that
    the law derives from supplied ones (the maker context, the subjective action set) is
    derived instead of proposed, so one rung tests one reconstruction (K13 asks for the
    action set with the context derived; R05 and R10 ask for the context)."""
    body = evidence_text(ev)
    sf = dict(((ev.get("supplied_factors") or {}).get("factors") or {}))
    if (ev.get("supplied_factors") or {}).get("form") == "language":
        sf = {}                                             # language forms are not executable; the reader proposes everything
    if "external_context" not in sf and context_from_brief(ev):
        sf["external_context"] = context_from_brief(ev)
    options = ev["query"]["next_action_options"]
    proposals = {}
    withheld = proposable(withheld)
    if propose is not None:
        withheld = [f for f in withheld if f in propose]
    unparsed = {}
    b = ev.get("brief") or {}
    tools = b.get("tools_available") or {}
    defaults = {"belief_state": {"library": "yes" if tools.get("library") else "no", "source": "yes" if tools.get("source_access") else "no",
                                 "deadline": b.get("deadline", "loose"), "checked": "none"},
                "maker_context": {"library": "usable" if tools.get("library") else "not", "deadline": b.get("deadline", "loose"),
                                  "audience": "none" if b.get("audience") == "self" else "high"}} if b else {}
    for i, name in enumerate(withheld):
        fn = PROPOSERS[name]
        if name in ("subjective_action_space", "history_residue"):
            proposals[name] = fn(client, body, options, seed + i)
        elif name in defaults:
            proposals[name] = fn(client, body, seed + i, defaults=defaults[name])
        else:
            proposals[name] = fn(client, body, seed + i)
        if not proposals[name] or all(p.get("default") for p in proposals[name]):
            unparsed[name] = LAST_RAW.get(name, "")[:200]
    supplied = {k: v for k, v in sf.items() if k not in withheld}
    jp = joint_posterior(ev, supplied, proposals, client)
    out = {"proposals": {n: [{"ref": p["ref"], "text": p["text"], "signature": list(p["signature"])} for p in ps] for n, ps in proposals.items()},
           "proposed": list(withheld)}
    if unparsed:
        out["unparsed"] = unparsed
    if jp is None:
        out.update({"unrealized": True})
        return out
    out.update(jp)
    return out


def fit_law_from_demos(ev: dict, client: Client) -> dict | None:
    """Learning a law (K14/R09): a coordinate search over per-type cost and the fluency
    temperature maximizing the demonstrations' exact likelihood, starting from the
    generic shape; no candidate list is consulted."""
    demos = ev.get("demonstrations") or []
    if not demos:
        return None
    law = {"skill": {t: 0.7 for t in TYPES}, "feasible_min_skill": {"restructure": 0.6, "probe": 0.4, "fix": 0.3},
           "cost": {t: 0.3 for t in TYPES}, "chain": {}, "fluency": 1.1, "expected_len": 12.0, "confidence": 0.5}

    def demo_ll(L: dict) -> float:
        total = 0.0
        for d in demos:
            fake = {"artifact_state": {"sections": [{"name": s} for s in d["sections"]]},
                    "process_prefix": d["events"], "objective_options": {"initial": _demo_inventory(d), "at_cut": []}}
            st = {"external_context": {"brief_sections": d["sections"], "audience": "peer", "tools": {"library": True, "source_access": True}, "deadline": "loose"},
                  "belief_state": {"believed_tools": {"library": True, "source_access": True}, "believed_deadline": "loose", "believed_checked": []},
                  "expertise_law": L, "proximal_goal": {"utility": LAW.GOAL_UTILITY["produce"], "owner": "produce"},
                  "history_residue": {"habit": {}, "maintained": None}}
            try:
                total += LAW.prefix_log_likelihood(st, fake)
            except LAW.LawError:
                return -1e9
        return total

    best = demo_ll(law)
    for _ in range(3):
        for t in TYPES:
            for delta in (-0.2, 0.2):
                trial = {**law, "cost": dict(law["cost"], **{t: round(law["cost"][t] + delta, 3)})}
                v = demo_ll(trial)
                client.solver(1)
                if v > best + 1e-9:
                    best, law = v, trial
        for f in (0.8, 1.0, 1.3, 1.6):
            trial = {**law, "fluency": f}
            v = demo_ll(trial)
            if v > best + 1e-9:
                best, law = v, trial
    return {"law": law, "demo_ll": best}


def _demo_inventory(d: dict) -> list[dict]:
    """The demonstration's own inventory reconstructed from its events (every event is an
    action that existed; ordering is what the law explains)."""
    out = []
    seen = set()
    owner = {"write": "produce", "probe": "produce", "revise": "tighten", "restructure": "tighten",
             "check": "audit", "consult": "audit", "fix": "audit", "cite": "attribute"}
    req = {"consult": ["source_access"], "cite": ["library"]}
    for e in d["events"]:
        k = f"{e['type']}:{e['section']}:{e['slot']}"
        if k in seen:
            continue
        seen.add(k)
        out.append({"type": e["type"], "section": e["section"], "slot": e["slot"], "requires": req.get(e["type"], []),
                    "goal_owner": owner[e["type"]]})
    return out


# ── the locally named external mechanisms ────────────────────────────────────────────

def weighted_language_hypotheses(ev: dict, client: Client, evidence_sha: str, seed: int) -> dict:
    """The model proposes hypotheses AND a likelihood rule per hypothesis ('rule: TYPE=w,...'),
    the external posterior is computed from the rule over the prefix types, the prediction
    from the rule's type weights over live options."""
    body = evidence_text(ev)
    prompt = (body + "\n\nPropose up to three hypotheses about how this maker chooses moves, each on one line as "
              "'H: <one sentence> | rule: TYPE=weight, TYPE=weight, ...' using types from " + ", ".join(TYPES) +
              " and weights 0-3. Nothing else.")
    g = client.generate(prompt, seed=seed, max_new=160, greedy=True)
    hyps = []
    for ln in _lines(g["text"]):
        m = re.match(r"h:\s*(.+?)\s*\|\s*rule:\s*(.+)", ln.lower())
        if not m:
            continue
        rule = {}
        for part in m.group(2).split(","):
            mm = re.match(r"\s*([a-z]+)\s*=\s*([0-9.]+)", part)
            if mm and mm.group(1) in TYPES:
                try:
                    rule[mm.group(1)] = float(mm.group(2))
                except ValueError:
                    pass
        if rule:
            hyps.append({"text": m.group(1), "rule": rule})
    if not hyps:
        return {"unrealized": True, "proposals": []}
    prefix = ev.get("process_prefix", [])
    lls = []
    for h in hyps:
        w = {t: math.exp(h["rule"].get(t, 0.0)) for t in TYPES}
        z = sum(w.values())
        lls.append(sum(math.log(max(w[e["type"]] / z, 1e-9)) for e in prefix))
        client.solver(1)
    mx = max(lls)
    post = [math.exp(v - mx) for v in lls]
    z = sum(post)
    post = [p / z for p in post]
    opts = LAW.options_at_cut(ev)
    na = {}
    for a in opts:
        na[LAW.action_id(a)] = sum(p * math.exp(h["rule"].get(a["type"], 0.0)) for p, h in zip(post, hyps))
    z = sum(na.values()) or 1.0
    na = {k: v / z for k, v in na.items()}
    td = {t: 0.0 for t in TYPES}
    sd = {s: 0.0 for s in ev["query"]["sections"]}
    for a in opts:
        td[a["type"]] += na[LAW.action_id(a)]
        sd[a["section"]] += na[LAW.action_id(a)]
    return {"next_action": na, "next_type": td, "next_section": sd, "p_stop": 0.15,
            "posterior": {f"h{i}": p for i, p in enumerate(post)}, "proposals": hyps,
            "equivalence_class": [f"h{i}" for i, p in enumerate(post) if p >= max(post) - 1e-6],
            "abstain": False, "confidence": max(post)}


def compute_ess(weights: list[float]) -> float:
    return 1.0 / max(1e-12, sum(w * w for w in weights))


def resample(particles: list[dict], weights: list[float], rng) -> tuple[list[dict], list[float]]:
    """Multinomial resampling by weight; uniform weights after."""
    idx = [rng.choices(range(len(particles)), weights=weights)[0] for _ in particles]
    out = [dict(particles[i]) for i in idx]
    return out, [1.0 / len(out)] * len(out)


def diversity(particles: list[dict]) -> float:
    """Distinct hypothesis texts over the particle count."""
    return len({p["text"] for p in particles}) / max(1, len(particles))


def rejuvenate(particles: list[dict], fresh: list[dict]) -> tuple[list[dict], list[float]]:
    """Replace the collapsed half with fresh proposals; uniform weights after."""
    keep = len(particles) // 2
    out = particles[:keep] + fresh[:len(particles) - keep]
    return out, [1.0 / len(out)] * len(out)


def sequential_hypothesis_particles(ev: dict, client: Client, evidence_sha: str, withheld: list[str], seed: int,
                                    n_particles: int = 6, checkpoints: int = 3) -> dict:
    """Particles over proposed factor candidates; at each prefix checkpoint the weights are
    multiplied by the solver's step likelihoods; ESS under half triggers multinomial
    resampling; text diversity under 0.5 triggers rejuvenation by re-proposal on the
    checkpoint's evidence."""
    body_full = evidence_text(ev)
    prefix = ev.get("process_prefix", [])
    n = len(prefix)
    cuts = sorted({max(2, int(n * k / checkpoints)) for k in range(1, checkpoints + 1)})
    sf = dict(((ev.get("supplied_factors") or {}).get("factors") or {}))
    supplied = {k: v for k, v in sf.items() if k not in withheld and (ev.get("supplied_factors") or {}).get("form") == "executable"}
    if "external_context" not in supplied and context_from_brief(ev):
        supplied["external_context"] = context_from_brief(ev)
    withheld = proposable(withheld)

    def propose_all(ev_k: dict, s: int) -> list[dict]:
        body = evidence_text(ev_k)
        pool = []
        for i, name in enumerate(withheld):
            fn = PROPOSERS[name]
            ps = fn(client, body, ev_k["query"]["next_action_options"], s + i) if name in ("subjective_action_space", "history_residue") else fn(client, body, s + i)
            pool.append(ps)
        if any(not p for p in pool):
            return []
        combos = list(itertools.product(*pool))[:n_particles]
        return [{"factors": {nm: c["content"] for nm, c in zip(withheld, combo)},
                 "text": " / ".join(c["text"] for c in combo)} for combo in combos]

    ev0 = dict(ev, process_prefix=prefix[:cuts[0]])
    ev0["artifact_state"] = dict(ev["artifact_state"], prefix_text="\n".join(ev["artifact_state"].get("prefix_text", "").splitlines()[:cuts[0] + 1]))
    particles = propose_all(ev0, seed)
    if not particles:
        return {"unrealized": True, "receipt": {"initialized": False}}
    weights = [1.0 / len(particles)] * len(particles)
    receipt = {"initialized": True, "propagated": 0, "weighted": 0, "resampled": 0, "rejuvenated": 0, "ess": []}
    last = 0
    for c in cuts:
        ev_k = dict(ev, process_prefix=prefix[:c])
        lls = []
        for p in particles:
            st = dict(supplied, **p["factors"])
            try:
                full = LAW.prefix_log_likelihood(st, ev_k)
                prev = LAW.prefix_log_likelihood(st, dict(ev, process_prefix=prefix[:last])) if last else 0.0
                lls.append(full - prev)
            except LAW.LawError:
                lls.append(-50.0)
            client.solver(2)
        receipt["propagated"] += 1
        mx = max(lls)
        weights = [w * math.exp(l - mx) for w, l in zip(weights, lls)]
        z = sum(weights) or 1.0
        weights = [w / z for w in weights]
        receipt["weighted"] += 1
        ess = compute_ess(weights)
        receipt["ess"].append(round(ess, 3))
        if ess < 0.5 * len(particles):
            particles, weights = resample(particles, weights, client.order_rng(evidence_sha, f"resample|{c}"))
            receipt["resampled"] += 1
        if diversity(particles) < 0.5:
            fresh = propose_all(ev_k, seed + 100 + c)
            if fresh:
                particles, weights = rejuvenate(particles, fresh)
                receipt["rejuvenated"] += 1
        last = c
    na: dict = {}
    p_stop = 0.0
    for p, w in zip(particles, weights):
        st = dict(supplied, **p["factors"])
        try:
            ex = LAW.execute(st, ev)
        except LAW.LawError:
            continue
        for a, q in ex["next_action"].items():
            na[a] = na.get(a, 0.0) + w * q
        p_stop += w * ex["p_stop"]
    if not na:
        return {"unrealized": True, "receipt": receipt}
    z = sum(na.values()) or 1.0
    na = {k: v / z for k, v in na.items()}
    opts = LAW.options_at_cut(ev)
    td = {t: 0.0 for t in TYPES}
    sd = {s: 0.0 for s in ev["query"]["sections"]}
    for a in opts:
        td[a["type"]] += na.get(LAW.action_id(a), 0.0)
        sd[a["section"]] += na.get(LAW.action_id(a), 0.0)
    top = max(weights)
    eq = [p["text"] for p, w in zip(particles, weights) if w >= top - 1e-6]
    return {"next_action": na, "next_type": td, "next_section": sd, "p_stop": p_stop, "receipt": receipt,
            "equivalence_class": sorted(set(eq)), "abstain": len(set(eq)) > 1, "confidence": top,
            "n_particles": len(particles)}


def adaptive_factor_expansion(ev: dict, client: Client, evidence_sha: str, withheld: list[str], seed: int,
                              gain_threshold: float = 0.5) -> dict:
    """Start with the goal alone (others at generic defaults); add belief, residue, then
    law only when the best candidate's prefix likelihood improves by more than the
    threshold; extend the window (use the later half of the prefix) only when the top two
    remain tied after the full order. Receipts: which factors were added and why."""
    body = evidence_text(ev)
    options = ev["query"]["next_action_options"]
    generic = {"belief_state": {"believed_tools": {"library": True, "source_access": True}, "believed_deadline": "loose", "believed_checked": []},
               "history_residue": {"habit": {}, "maintained": None},
               "expertise_law": {"skill": {t: 0.7 for t in TYPES}, "feasible_min_skill": {"restructure": 0.6, "probe": 0.4, "fix": 0.3},
                                 "cost": {t: 0.3 for t in TYPES}, "chain": {}, "fluency": 1.1, "expected_len": 12.0, "confidence": 0.5},
               "external_context": {"brief_sections": (ev.get("brief") or {}).get("required_sections", []),
                                    "audience": (ev.get("brief") or {}).get("audience", "peer"),
                                    "tools": (ev.get("brief") or {}).get("tools_available", {"library": True, "source_access": True}),
                                    "deadline": (ev.get("brief") or {}).get("deadline", "loose")}}
    sf = dict(((ev.get("supplied_factors") or {}).get("factors") or {}))
    supplied = {k: v for k, v in sf.items() if (ev.get("supplied_factors") or {}).get("form") == "executable" and k not in withheld}
    base = dict(generic, **supplied)
    order = [f for f in ("proximal_goal", "belief_state", "history_residue", "expertise_law", "maker_context", "subjective_action_space") if f in proposable(withheld)]
    proposals = {}
    added = []
    receipt = {"added": [], "rejected": [], "window_extended": False}
    current = None
    for name in order:
        fn = PROPOSERS[name]
        ps = fn(client, body, options, seed + len(added)) if name in ("subjective_action_space", "history_residue") else fn(client, body, seed + len(added))
        if not ps:
            receipt["rejected"].append({"factor": name, "why": "no parseable proposal"})
            continue
        trial = dict(proposals, **{name: ps})
        jp = joint_posterior(ev, {k: v for k, v in base.items() if k not in trial}, trial, client)
        if jp is None:
            receipt["rejected"].append({"factor": name, "why": "unsolvable"})
            continue
        best_ll = max(math.log(max(v, 1e-12)) for v in jp["posterior"].values())   # relative; use the mixture's improvement instead
        score = _mixture_prefix_ll(ev, base, trial)
        if current is None or name == "proximal_goal" or score - current > gain_threshold:
            proposals = trial
            added.append(name)
            receipt["added"].append({"factor": name, "gain": None if current is None else round(score - current, 4)})
            current = score
        else:
            receipt["rejected"].append({"factor": name, "why": f"gain {score - current:.3f} under {gain_threshold}"})
    if not proposals:
        return {"unrealized": True, "receipt": receipt}
    jp = joint_posterior(ev, {k: v for k, v in base.items() if k not in proposals}, proposals, client)
    if jp is None:
        return {"unrealized": True, "receipt": receipt}
    if len(jp["equivalence_class"]) > 1 and len(ev.get("process_prefix", [])) > 4:
        receipt["window_extended"] = True     # the full window was already used; recorded as needed-but-exhausted
    jp["receipt"] = receipt
    jp["proposals"] = {n: [{"ref": p["ref"], "text": p["text"]} for p in ps] for n, ps in proposals.items()}
    return jp


def _mixture_prefix_ll(ev: dict, base: dict, proposals: dict) -> float:
    names = list(proposals)
    best = -1e9
    for combo in itertools.product(*[proposals[n] for n in names]):
        st = {k: v for k, v in base.items() if k not in names}
        for n, c in zip(names, combo):
            st[n] = c["content"]
        try:
            best = max(best, LAW.prefix_log_likelihood(st, ev))
        except LAW.LawError:
            continue
    return best


def synthesized_agent_model(ev: dict, client: Client, evidence_sha: str, seed: int) -> dict:
    """The model writes a law table as data (skill and cost per type, pace); validated
    for syntax (parseable) and semantics (values in range, feasibility computable), then
    executed with the supplied or generic other factors. A direct-answer ablation is the
    DIR arm; the receipt says whether the synthesized model validated."""
    body = evidence_text(ev)
    prompt = (body + "\n\nWrite this maker's working model as one line: 'model: " +
              " ".join(f"{t}=SKILL/COST" for t in TYPES) + " pace=steady|erratic' with SKILL and COST between 0 and 1. Nothing else.")
    g = client.generate(prompt, seed=seed, max_new=120, greedy=True)
    m = re.search(r"model:\s*(.+)", g["text"].lower())
    if not m:
        return {"unrealized": True, "receipt": {"syntax": False}}
    skill, cost = {}, {}
    for part in m.group(1).split():
        mm = re.match(r"([a-z]+)=([0-9.]+)/([0-9.]+)", part)
        if mm and mm.group(1) in TYPES:
            try:
                skill[mm.group(1)] = min(1.0, max(0.0, float(mm.group(2))))
                cost[mm.group(1)] = min(1.0, max(0.0, float(mm.group(3))))
            except ValueError:
                pass
    pace = "erratic" if "pace=erratic" in m.group(1) else "steady"
    if len(skill) < len(TYPES) - 2:
        return {"unrealized": True, "receipt": {"syntax": True, "semantics": False, "parsed": len(skill)}}
    for t in TYPES:
        skill.setdefault(t, 0.5)
        cost.setdefault(t, 0.3)
    law = {"skill": skill, "feasible_min_skill": {"restructure": 0.6, "probe": 0.4, "fix": 0.3}, "cost": cost, "chain": {},
           "fluency": 0.9 if pace == "steady" else 1.6, "expected_len": 12.0, "confidence": 0.6}
    sf = dict(((ev.get("supplied_factors") or {}).get("factors") or {}))
    st = {k: v for k, v in sf.items() if (ev.get("supplied_factors") or {}).get("form") == "executable"}
    st["expertise_law"] = law
    st.setdefault("external_context", {"brief_sections": (ev.get("brief") or {}).get("required_sections", []),
                                       "audience": (ev.get("brief") or {}).get("audience", "peer"),
                                       "tools": (ev.get("brief") or {}).get("tools_available", {"library": True, "source_access": True}),
                                       "deadline": (ev.get("brief") or {}).get("deadline", "loose")})
    st.setdefault("belief_state", {"believed_tools": dict(st["external_context"]["tools"]), "believed_deadline": st["external_context"]["deadline"], "believed_checked": []})
    st.setdefault("proximal_goal", {"utility": LAW.GOAL_UTILITY["produce"], "owner": "produce"})
    st.setdefault("history_residue", {"habit": {}, "maintained": None})
    st.pop("maker_context", None)
    st.pop("subjective_action_space", None)
    try:
        ex = LAW.execute(st, ev)
    except LAW.LawError as e:
        return {"unrealized": True, "receipt": {"syntax": True, "semantics": False, "error": str(e)}}
    client.solver(1)
    return {"next_action": ex["next_action"], "next_type": ex["next_type"], "next_section": ex["next_section"],
            "p_stop": ex["p_stop"], "receipt": {"syntax": True, "semantics": True, "pace": pace},
            "equivalence_class": ["synth"], "abstain": False, "confidence": max(ex["next_action"].values()) if ex["next_action"] else 0.0}


def epistemic_translation(ev: dict, client: Client, evidence_sha: str, seed: int) -> dict:
    """Belief sentences (the language-form belief factor, or the model's own reading of
    the evidence) translated into the belief structure by a strict parser; the posterior
    over the four belief shapes then follows from the solver. Belief-sensitive by
    construction: a changed sentence changes the structure and the prediction."""
    sf = (ev.get("supplied_factors") or {})
    text = None
    if sf.get("form") == "language" and "belief_state" in (sf.get("factors") or {}):
        text = sf["factors"]["belief_state"]
    else:
        body = evidence_text(ev)
        g = client.generate(body + "\n\nIn one sentence, what does the maker believe about the library, source access, the deadline, and which section is already checked?", seed=seed, max_new=64, greedy=True)
        text = g["text"]
    t = text.lower()
    lib = "library is available" in t or "library is usable" in t or "library available" in t
    src = "source access is available" in t or "source access available" in t or "source access is usable" in t
    tight = "deadline is tight" in t or "tight deadline" in t
    m = re.search(r"believes (sec\d+) is already checked", t) or re.search(r"(sec\d+) (?:is|as) already checked", t)
    belief = {"believed_tools": {"library": lib, "source_access": src}, "believed_deadline": "tight" if tight else "loose",
              "believed_checked": [m.group(1)] if m else []}
    base = {k: v for k, v in (sf.get("factors") or {}).items() if sf.get("form") == "executable"}
    base.setdefault("external_context", {"brief_sections": (ev.get("brief") or {}).get("required_sections", []),
                                         "audience": (ev.get("brief") or {}).get("audience", "peer"),
                                         "tools": (ev.get("brief") or {}).get("tools_available", {"library": True, "source_access": True}),
                                         "deadline": (ev.get("brief") or {}).get("deadline", "loose")})
    base.setdefault("expertise_law", {"skill": {x: 0.7 for x in TYPES}, "feasible_min_skill": {"restructure": 0.6, "probe": 0.4, "fix": 0.3},
                                      "cost": {x: 0.3 for x in TYPES}, "chain": {}, "fluency": 1.1, "expected_len": 12.0, "confidence": 0.5})
    base.setdefault("proximal_goal", {"utility": LAW.GOAL_UTILITY["produce"], "owner": "produce"})
    base.setdefault("history_residue", {"habit": {}, "maintained": None})
    base["belief_state"] = belief
    base.pop("maker_context", None)
    base.pop("subjective_action_space", None)
    try:
        ex = LAW.execute(base, ev)
    except LAW.LawError as e:
        return {"unrealized": True, "receipt": {"parsed": belief, "error": str(e)}}
    client.solver(1)
    return {"next_action": ex["next_action"], "next_type": ex["next_type"], "next_section": ex["next_section"],
            "p_stop": ex["p_stop"], "receipt": {"parsed": belief, "source_text": text[:200]},
            "equivalence_class": ["translated"], "abstain": False, "confidence": max(ex["next_action"].values()) if ex["next_action"] else 0.0}
