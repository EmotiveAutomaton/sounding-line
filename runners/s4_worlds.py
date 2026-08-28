"""Stage 4 world constructors (brief §6, §7): every construction the C, A, T, and H
cards score, built deterministically from a lineage id, with the constraint graph,
the maker's profile, the realized draws, and the mechanical realization checks that
the readers are scored against.

Two domains, both fictional: WORKSHOP (craft commissions) and CIVIC (a town's works).
Every world has unique surface text (seeded name banks) and its own utilities seed, so
no world is a relabeled copy of another (§6.2). The decision core reuses the Stage-3
utility construction (option i is argmax under axis i; softmax at TEMP), so the exact
reference likelihood exists for every record.

DESIGN CHECK (2026-08-27)
lessons read: LESSONS §3 (known-answer existence checked at construction, truth marginal
  variance inside every gate band, assigned is not realized, denominators declared,
  compliance pilot before a factorial), §4 (instruct makers only), CONTROLS §6
  (construction beats ablation; analytic floors by truth balance).
gates:
  - equal-information gate (C01): the coherent bundle and the fact list render the SAME
    fact ids and rule ids from one stored graph; NULL (a correct construction): the
    rendered id sets are identical for every world; ALTERNATIVE (a leaky bundle): the
    bundle carries an id the list lacks; failure direction guarded: a bundle advantage
    that is really extra information; band: any world with unequal id sets is rejected
    at construction (no partial credit).
  - truth-marginal gate: within each card's factorial cell the realized truth labels are
    not constant (a constant answer would let a constant reader pass, L229); NULL: at
    least two labels appear per cell; ALTERNATIVE: a degenerate cell; failure direction:
    a false pass; band: fewer than two labels in a cell marks the cell unusable.
  - probe-discrimination gate (C03): the exact expected improvement of the informative
    probe exceeds the redundant probe by the frozen margin (0.05 nats); NULL (a usable
    menu): margin met; ALTERNATIVE (a flat menu): margin not met, the world's C03 item
    is an instrument failure, never a failure of active reading; band: met / not met.
  - feasibility gate: a world whose feasibility mask leaves fewer than two options on a
    scored scenario is rejected (the choice would be forced, no evidence about the
    maker); band: at least two feasible options or the scenario is replaced.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners.s3_lib import AXES, PROFILE_W, choice_probs, hash_stable               # noqa: E402

DOMAINS4 = ("workshop", "civic")
STEPS = ("cast the parts", "carve the parts", "assemble from stock", "commission outside")
AFFECT_WORDS = ("noted", "reported", "flagged", "recorded")   # register-neutral verbs


# ── name banks (fictional, counterbalanced by seed) ───────────────────────────────────

_ADJ = ["Ashgrove", "Calder", "Marrow", "Fennick", "Holloway", "Brightwater", "Quill",
        "Sable", "Tarn", "Wexley", "Oriel", "Dunmore", "Larkspur", "Redfern", "Vale",
        "Kestrel", "Norbury", "Pellam", "Greyling", "Thistle"]
_SHOP = ["Bindery", "Foundry", "Loomworks", "Glassworks", "Joinery", "Press", "Pottery",
         "Smithy", "Atelier", "Tannery"]
_TOWN = ["Council", "Works Board", "Parish", "Harbor Authority", "Commons", "Assembly",
         "Ward", "Township"]
_PATRON = {"guild": "a guild that judges by its established pattern books",
           "court": "a court patron who rewards durability above all",
           "merchant": "a merchant house that counts every coin",
           "festival": "a festival committee working to a fixed opening day"}
_PATRON_LEAN = {"guild": "precedent", "court": "robust", "merchant": "cheap",
                "festival": "fast"}
_TOOLS = {"full": "a full kit including a kiln and a lathe",
          "no_kiln": "a kit with a lathe but no kiln",
          "no_lathe": "a kit with a kiln but no lathe"}
_TOOL_BLOCKS = {"full": set(), "no_kiln": {"cast the parts"}, "no_lathe": {"carve the parts"}}
_TRAINING = {"formal": "formally trained by a licensed master",
             "self": "self-taught from manuals",
             "apprentice": "trained as an apprentice in a family shop"}
_TRAIN_BLOCKS = {"formal": set(), "self": {"commission outside"}, "apprentice": set()}
_AUDIENCE = {"local": "work shown only to local buyers",
             "capital": "work shown to buyers in the capital",
             "export": "work sold abroad through an agent"}
_UNRELATED = ["prefers tea to coffee", "keeps a grey cat", "sings while working",
              "walks to work along the river"]

# scenario templates: (context template, {axis: option template}); slots {inst},{item}
_SCEN_WORKSHOP = [
    ("{inst} must decide how to produce the {item} for its patron.",
     {"robust": "the over-built version rated well past the brief",
      "cheap": "the pared-down version at half the material cost",
      "fast": "the version the crew can finish in a week",
      "precedent": "the version the pattern book prescribes"}),
    ("{inst} must choose a supplier for the {item}'s fittings.",
     {"robust": "the smith whose fittings never fail inspection",
      "cheap": "the yard selling salvaged fittings by the sack",
      "fast": "the stall that delivers by tomorrow",
      "precedent": "the smith every workshop in the street uses"}),
    ("{inst} must plan the finish for the {item}.",
     {"robust": "a triple-coat finish that outlasts the frame",
      "cheap": "a single wash of the cheapest varnish",
      "fast": "an oil rub done in an afternoon",
      "precedent": "the finish the old guild recipe names"}),
    ("{inst} must decide how to test the {item} before delivery.",
     {"robust": "a full load test with witnessed records",
      "cheap": "a glance-over by the apprentice",
      "fast": "a same-day check so the cart can leave",
      "precedent": "the inspection ritual the guild has always used"}),
    ("{inst} must choose packing for the {item}'s journey.",
     {"robust": "a braced crate with padded cradles",
      "cheap": "straw in a borrowed cart",
      "fast": "wrapped cloth loaded the same morning",
      "precedent": "the crate pattern the agent always requests"}),
    ("{inst} must staff the {item} commission.",
     {"robust": "two journeymen with a foreman checking each stage",
      "cheap": "one apprentice at the lowest wage",
      "fast": "every hand in the shop for three days",
      "precedent": "the pairing the master used on the last such piece"}),
    ("{inst} must source timber for the {item}.",
     {"robust": "seasoned heartwood with a decade of drying",
      "cheap": "green offcuts from the mill floor",
      "fast": "whatever the lumber cart carries this morning",
      "precedent": "the stand the guild has always bought from"}),
    ("{inst} must set the {item}'s delivery terms.",
     {"robust": "a guaranteed date with penalties the shop will honor",
      "cheap": "delivery when convenient at no extra charge",
      "fast": "the earliest date the shop can physically manage",
      "precedent": "the terms written in every prior contract"}),
    ("{inst} must handle a flaw found in the {item}.",
     {"robust": "rebuild the flawed section from scratch",
      "cheap": "fill and paint over the flaw",
      "fast": "trim the flaw and ship today",
      "precedent": "apply the repair the manuals describe"}),
    ("{inst} must record the {item} commission.",
     {"robust": "a full ledger with witnessed signatures",
      "cheap": "a note on the back of the receipt",
      "fast": "a tally scratched before the cart leaves",
      "precedent": "the entry format the guild register requires"}),
]
_SCEN_CIVIC = [
    ("{inst} must decide how to rebuild the {item}.",
     {"robust": "the reinforced design rated for a century storm",
      "cheap": "the relined structure at a third of the bid",
      "fast": "the prefabricated unit installed in ten days",
      "precedent": "the design every neighboring town adopted"}),
    ("{inst} must pick a contractor for the {item}.",
     {"robust": "the firm with the best inspection record in the county",
      "cheap": "the bid a fifth under every rival",
      "fast": "the crew that can start on Monday",
      "precedent": "the contractor the town has used for a decade"}),
    ("{inst} must schedule work on the {item}.",
     {"robust": "staggered phases with spare crews on standby",
      "cheap": "deferred phases stretched over three budgets",
      "fast": "a blitz with every crew for one week",
      "precedent": "the calendar the last such project followed"}),
    ("{inst} must choose materials for the {item}.",
     {"robust": "quarried stone warrantied for fifty years",
      "cheap": "reclaimed blocks from the demolished mill",
      "fast": "poured blocks curing by the weekend",
      "precedent": "the stone the county specification names"}),
    ("{inst} must inspect the finished {item}.",
     {"robust": "an independent survey with load trials",
      "cheap": "a walk-through by the clerk",
      "fast": "a sign-off the same afternoon",
      "precedent": "the inspection the county has always required"}),
    ("{inst} must notify residents about the {item}.",
     {"robust": "letters to every household with a hearing",
      "cheap": "a notice pinned at the hall",
      "fast": "a crier sent out this evening",
      "precedent": "the notice format used for every prior work"}),
    ("{inst} must fund the {item}.",
     {"robust": "a reserve-backed bond covering overruns",
      "cheap": "the smallest levy that clears the estimate",
      "fast": "an advance from the treasury released tomorrow",
      "precedent": "the levy formula used for the last three works"}),
    ("{inst} must set the {item}'s maintenance plan.",
     {"robust": "quarterly checks with logged repairs",
      "cheap": "repairs only when something fails",
      "fast": "a single fix-all visit before winter",
      "precedent": "the rota the county circulates"}),
    ("{inst} must respond to a defect in the {item}.",
     {"robust": "close it and rebuild the failing span",
      "cheap": "patch it and post a warning",
      "fast": "shore it up overnight and reopen",
      "precedent": "apply the remedy the county manual lists"}),
    ("{inst} must archive the {item} decision.",
     {"robust": "a bound minute book with witnessed seals",
      "cheap": "a line in the clerk's daybook",
      "fast": "a memo filed before the meeting ends",
      "precedent": "the register format every council keeps"}),
]
_ITEMS = {"workshop": ["altar screen", "harbor bell", "guild chest", "market clock",
                      "tithe barn doors", "choir stalls", "reading desk", "town seal"],
          "civic": ["footbridge", "mill race", "market hall roof", "harbor wall",
                    "north culvert", "well house", "school wing", "flood gate"]}
_SCENS = {"workshop": _SCEN_WORKSHOP, "civic": _SCEN_CIVIC}
N_SCEN = 10


def _rng(lid: str, salt: str = "") -> random.Random:
    return random.Random(hash_stable(lid + "|" + salt))


def institution_name(domain: str, rng: random.Random) -> str:
    if domain == "workshop":
        return f"the {rng.choice(_ADJ)} {rng.choice(_SHOP)}"
    return f"the {rng.choice(_ADJ)} {rng.choice(_TOWN)}"


def world_utilities(lid: str, scen_i: int) -> list[list[float]]:
    """4x4 utilities (option x axis) for one scenario of one world: option i leads on
    axis i by construction; off-axis values are seeded noise unique to the world."""
    rng = _rng(lid, f"u{scen_i}")
    U = [[rng.uniform(0.15, 0.55) for _ in AXES] for _ in AXES]
    for i in range(4):
        U[i][i] = rng.uniform(0.8, 1.0)
    return U


def draw_choice(U, w, rng: random.Random, feasible=None) -> str:
    """A REALIZED draw from softmax(w.u/TEMP) restricted to feasible options."""
    probs = choice_probs(U, w)
    keys = list(AXES)
    if feasible is not None:
        probs = [p if ax in feasible else 0.0 for p, ax in zip(probs, keys)]
        z = sum(probs)
        probs = [p / z for p in probs]
    r = rng.random()
    acc = 0.0
    for p, ax in zip(probs, keys):
        acc += p
        if r <= acc:
            return ax
    return keys[-1]


def profile_prior_from_context(patron: str) -> dict:
    """Context shifts the prior over profiles without determining it: the patron's lean
    holds 0.55 of the mass, the rest is spread evenly (the reliability the ruler uses)."""
    lean = _PATRON_LEAN[patron]
    return {ax: (0.55 if ax == lean else 0.15) for ax in AXES}


def scenario_text(domain: str, inst: str, item: str, scen_i: int) -> tuple[str, dict]:
    ctx_t, opts_t = _SCENS[domain][scen_i % N_SCEN]
    ctx = ctx_t.format(inst=inst.capitalize() if ctx_t.startswith("{inst}") else inst,
                       item=item)
    return ctx, {ax: opts_t[ax] for ax in AXES}


# ── the base world (C track) ──────────────────────────────────────────────────────────

def make_world(lid: str, domain: str) -> dict:
    """A commission world: institution facts, the constraint graph, the maker's profile
    drawn from the context-conditioned prior, ten scenarios with utilities and
    feasibility masks, realized draws for all ten, and the negative-control attribute."""
    rng = _rng(lid, "world")
    inst = institution_name(domain, rng)
    item = rng.choice(_ITEMS[domain])
    patron = rng.choice(list(_PATRON))
    tools = rng.choice(list(_TOOLS))
    training = rng.choice(list(_TRAINING))
    audience = rng.choice(list(_AUDIENCE))
    prior = profile_prior_from_context(patron)
    # the maker's profile is a draw from the prior (an exception with prob 0.45 total)
    r = rng.random()
    acc = 0.0
    profile = AXES[-1]
    for ax in AXES:
        acc += prior[ax]
        if r <= acc:
            profile = ax
            break
    w = PROFILE_W[profile]
    # constraint graph: facts -> blocked process steps; audience -> blocked option axis
    # on delivery-type scenarios (export agents refuse the fastest packing/delivery)
    blocked_steps = set(_TOOL_BLOCKS[tools]) | set(_TRAIN_BLOCKS[training])
    blocked_axis_scen = {}
    if audience == "export":
        blocked_axis_scen = {4: "fast", 7: "fast"}     # packing, delivery terms
    facts = [{"id": "F_patron", "text": f"Its patron is {_PATRON[patron]}."},
             {"id": "F_tools", "text": f"Its workshop holds {_TOOLS[tools]}."},
             {"id": "F_training", "text": f"Its master was {_TRAINING[training]}."},
             {"id": "F_audience", "text": f"Its work is {_AUDIENCE[audience]}."}]
    rules = [{"id": "R_patron", "text": f"A patron of that kind tends to reward the "
                                        f"{_PATRON_LEAN[patron]} choice, though not always."}]
    if blocked_steps:
        rules.append({"id": "R_steps", "text": "Without the tool or the training for it, a "
                                               "step cannot be taken: " +
                                               ", ".join(sorted(blocked_steps)) + " ruled out."})
    else:
        rules.append({"id": "R_steps", "text": "Every production step is available to it."})
    if blocked_axis_scen:
        rules.append({"id": "R_audience", "text": "An export agent refuses the fastest "
                                                  "packing and delivery terms."})
    else:
        rules.append({"id": "R_audience", "text": "Its buyers accept any packing and "
                                                  "delivery terms."})
    scen = []
    for si in range(N_SCEN):
        ctx, opts = scenario_text(domain, inst, item, si)
        feasible = [ax for ax in AXES if blocked_axis_scen.get(si) != ax]
        U = world_utilities(lid, si)
        draw = draw_choice(U, w, _rng(lid, f"draw{si}"), feasible)
        probs = choice_probs(U, w)
        z = sum(p for p, ax in zip(probs, AXES) if ax in feasible)
        dist = {ax: (p / z if ax in feasible else 0.0) for p, ax in zip(probs, AXES)}
        scen.append({"i": si, "context": ctx, "options": opts, "feasible": feasible,
                     "utilities": U, "draw": draw, "distribution": dist})
    feasible_steps = [s for s in STEPS if s not in blocked_steps]
    unrelated = rng.choice(_UNRELATED)
    return {"lineage_id": lid, "domain": domain, "institution": inst, "item": item,
            "context": {"patron": patron, "tools": tools, "training": training,
                        "audience": audience},
            "facts": facts, "rules": rules, "prior": prior, "profile": profile,
            "profile_matches_context": profile == _PATRON_LEAN[patron],
            "w": list(w), "blocked_steps": sorted(blocked_steps),
            "feasible_steps": feasible_steps, "unrelated_attribute": unrelated,
            "scenarios": scen}


def render_fact_list(world: dict) -> tuple[str, set]:
    ids = set()
    lines = [f"Facts about {world['institution']}:"]
    for f in world["facts"]:
        lines.append(f"- {f['text']}")
        ids.add(f["id"])
    lines.append("Rules that apply:")
    for r in world["rules"]:
        lines.append(f"- {r['text']}")
        ids.add(r["id"])
    return "\n".join(lines), ids


def render_bundle(world: dict) -> tuple[str, set]:
    """The coherent account: the same facts and rules organized into a maker model."""
    c = world["context"]
    ids = {"F_patron", "F_tools", "F_training", "F_audience", "R_patron", "R_steps",
           "R_audience"}
    steps_clause = ("so " + ", ".join(sorted(world["blocked_steps"])) +
                    " are ruled out for it" if world["blocked_steps"]
                    else "so every production step is available to it")
    aud_clause = ("and because its work is " + _AUDIENCE[c["audience"]] +
                  ", an export agent refuses the fastest packing and delivery terms"
                  if c["audience"] == "export"
                  else "and because its work is " + _AUDIENCE[c["audience"]] +
                  ", its buyers accept any packing and delivery terms")
    text = (f"Picture {world['institution']} as a maker shaped by its situation. Its patron "
            f"is {_PATRON[c['patron']]}, and a patron of that kind tends to reward the "
            f"{_PATRON_LEAN[c['patron']]} choice, though not always; that is the pull on "
            f"every decision it makes. Its workshop holds {_TOOLS[c['tools']]} and its "
            f"master was {_TRAINING[c['training']]}, {steps_clause}. Its work is "
            f"{_AUDIENCE[c['audience']]}, {aud_clause}. Read each choice below as that "
            f"maker's, with those pulls and limits in play.")
    return text, ids


def render_irrelevant(world: dict, rng: random.Random) -> str:
    """Accurate but irrelevant background, matched in length to the bundle."""
    pool = ["The river beside the town runs high in spring and low by late summer.",
            "The market square was repaved two generations ago with local granite.",
            "The bell in the old tower rings the hour from dawn to dusk.",
            "Wool from the eastern hills is carted through the town every autumn.",
            "The road to the coast follows the ridge and takes a full day on foot.",
            "The town keeps its weights and measures in a chest at the hall.",
            "A fair is held on the common in the week after the harvest.",
            "The chapel roof was retiled after the storm of the previous decade."]
    target = len(render_bundle(world)[0].split())
    out = []
    while sum(len(s.split()) for s in out) < target:
        out.append(rng.choice(pool))
    return f"Background on the town of {world['institution'].split()[1]}: " + " ".join(out)


def check_equal_information(world: dict) -> None:
    """The equal-information gate: identical fact and rule id sets."""
    _, a = render_fact_list(world)
    _, b = render_bundle(world)
    if a != b:
        raise ValueError(f"{world['lineage_id']}: bundle/list id sets differ {a ^ b}")


def context_conditions(world: dict, other_world: dict) -> dict:
    """The five C01 conditions as text blocks (empty for none)."""
    rng = _rng(world["lineage_id"], "irrelevant")
    fl, _ = render_fact_list(world)
    bd, _ = render_bundle(world)
    wrong, _ = render_bundle(other_world)
    wrong = wrong.replace(other_world["institution"], world["institution"])
    return {"none": "", "bundle": bd, "facts": fl, "incorrect_bundle": wrong,
            "irrelevant": render_irrelevant(world, rng)}


_IMPOSSIBLE_STEPS = ("spin the parts on a loom", "print the parts on a press",
                     "quarry the parts")


def step_question(world: dict, rng: random.Random) -> dict:
    """Feasible next process step, with exactly one correct option by construction in
    every case. One blocked step: which step is ruled out (the four real steps listed,
    one blocked). Two blocked steps (a kit without a kiln or lathe AND a self-taught
    master, two worlds in nine): that question would have two right answers, so it
    flips to which step the maker CAN take (one feasible step, the two blocked ones, one
    impossible distractor). None blocked: which listed step is available (one real step
    among three impossible ones)."""
    blocked = list(world["blocked_steps"])
    if len(blocked) == 1:
        return {"question": "Which of these production steps is ruled out for this maker?",
                "options": {s: s for s in STEPS}, "truth": blocked[0],
                "truth_provenance": "construction"}
    if len(blocked) >= 2:
        truth = rng.choice(world["feasible_steps"])
        opts = [truth] + blocked[:2] + [rng.choice(_IMPOSSIBLE_STEPS)]
        return {"question": "Which of these is a production step this maker can take?",
                "options": {s: s for s in opts}, "truth": truth,
                "truth_provenance": "construction"}
    truth = rng.choice(list(STEPS))
    return {"question": "Which of these is a production step this maker can take?",
            "options": {truth: truth, "x1": _IMPOSSIBLE_STEPS[0], "x2": _IMPOSSIBLE_STEPS[1],
                        "x3": _IMPOSSIBLE_STEPS[2]},
            "truth": truth, "truth_provenance": "construction"}


def unrelated_question(world: dict) -> dict:
    return {"question": "Which of these is true of this maker's habits?",
            "options": {u: u for u in _UNRELATED}, "truth": world["unrelated_attribute"],
            "truth_provenance": "construction"}


# ── records and the exact reference posterior (C02, C03) ──────────────────────────────

def record_lines(world: dict, scen_ids) -> str:
    lines = []
    for si in scen_ids:
        s = world["scenarios"][si]
        lines.append(f"- {s['context']} It chose: {s['options'][s['draw']]}.")
    return "\n".join(lines)


def reference_posterior(world: dict, scen_ids, prior: dict | None) -> dict:
    """Exact posterior over the four profiles from the context prior (with its stated
    reliability) and the realized records, via the world's own likelihood."""
    logp = {ax: math.log(prior[ax]) if prior else 0.0 for ax in AXES}
    for si in scen_ids:
        s = world["scenarios"][si]
        idx = AXES.index(s["draw"])
        for name in AXES:
            probs = choice_probs(s["utilities"], PROFILE_W[name])
            z = sum(p for p, ax in zip(probs, AXES) if ax in s["feasible"])
            p = probs[idx] / z if s["draw"] in s["feasible"] else 1e-12
            logp[name] += math.log(max(p, 1e-12))
    m = max(logp.values())
    exps = {k: math.exp(v - m) for k, v in logp.items()}
    z = sum(exps.values())
    return {k: v / z for k, v in exps.items()}


def predictive_from_posterior(world: dict, scen_i: int, post: dict) -> dict:
    s = world["scenarios"][scen_i]
    out = {ax: 0.0 for ax in AXES}
    for name, pw in post.items():
        probs = choice_probs(s["utilities"], PROFILE_W[name])
        z = sum(p for p, ax in zip(probs, AXES) if ax in s["feasible"])
        for p, ax in zip(probs, AXES):
            if ax in s["feasible"]:
                out[ax] += pw * p / z
    return out


def _entropy(p: dict) -> float:
    return -sum(v * math.log(v) for v in p.values() if v > 0)


def expected_log_score_gain(world: dict, known: list, probe_scen: int,
                            target_scen: int, prior: dict | None) -> float:
    """Exact expected improvement in the target scenario's log score from learning the
    maker's draw on the probe scenario: the mutual information between the probe answer
    and the target choice under the exact posterior, i.e. the expected reduction in the
    target predictive's entropy (non-negative; exactly zero for a probe whose answer is
    already in the record). The reader's own predictive is the right weighting for an
    expected improvement; weighting by the maker's true distribution is not an expected
    gain and came out negative on every world in the smoke test."""
    post0 = reference_posterior(world, known, prior)
    pred0 = predictive_from_posterior(world, target_scen, post0)
    if probe_scen in known:
        return 0.0
    probe_pred = predictive_from_posterior(world, probe_scen, post0)
    h0 = _entropy(pred0)
    exp_h1 = 0.0
    for ans, pa in probe_pred.items():
        if pa <= 0:
            continue
        w2 = json.loads(json.dumps(world))
        w2["scenarios"][probe_scen]["draw"] = ans
        post1 = reference_posterior(w2, list(known) + [probe_scen], prior)
        pred1 = predictive_from_posterior(w2, target_scen, post1)
        exp_h1 += pa * _entropy(pred1)
    return max(0.0, h0 - exp_h1)


def _cond_probs(world: dict, scen_i: int, profile: str) -> dict:
    s = world["scenarios"][scen_i]
    probs = choice_probs(s["utilities"], PROFILE_W[profile])
    z = sum(p for p, ax in zip(probs, AXES) if ax in s["feasible"])
    return {ax: (p / z if ax in s["feasible"] else 0.0) for p, ax in zip(probs, AXES)}


def expected_gain_pair(world: dict, known: list, pair: tuple, target_scen: int,
                       prior: dict | None) -> float:
    """Mutual information between the answers to a PAIR of probe decisions and the
    target choice, under the exact posterior (the pair form doubles the information a
    single draw carries at TEMP 0.35, where one draw is worth about 0.03 nats)."""
    s1, s2 = pair
    if s1 in known and s2 in known:
        return 0.0
    post0 = reference_posterior(world, known, prior)
    h0 = _entropy(predictive_from_posterior(world, target_scen, post0))
    c1 = {p: _cond_probs(world, s1, p) for p in AXES}
    c2 = {p: _cond_probs(world, s2, p) for p in AXES}
    exp_h1 = 0.0
    for a1 in AXES:
        for a2 in AXES:
            pa = sum(post0[p] * c1[p][a1] * c2[p][a2] for p in AXES)
            if pa <= 1e-12:
                continue
            w2 = json.loads(json.dumps(world))
            w2["scenarios"][s1]["draw"] = a1
            w2["scenarios"][s2]["draw"] = a2
            post1 = reference_posterior(w2, list(known) + [s1, s2], prior)
            exp_h1 += pa * _entropy(predictive_from_posterior(w2, target_scen, post1))
    return max(0.0, h0 - exp_h1)


PROBE_MARGIN = 0.02      # frozen from the exact ruler's information structure (2026-08-27)


def _pair_text(world: dict, pair: tuple) -> str:
    a, b = (world["scenarios"][i]["context"].rstrip(".") for i in pair)
    return (f"What did the maker choose when {a[0].lower() + a[1:]}, and when "
            f"{b[0].lower() + b[1:]}?")


def build_probe_menu(world: dict, known: list, target_scen: int, prior: dict | None,
                     margin: float = PROBE_MARGIN) -> dict | None:
    """C03: informative / redundant / irrelevant probes with exact gains; None when the
    discrimination gate fails (a flat menu). Probes ask about a pair of decisions; the
    redundant probe pairs two decisions already in the record (gain exactly zero)."""
    assert len(known) >= 2, "the redundant probe needs two recorded decisions"
    cands = [si for si in range(N_SCEN) if si not in known and si != target_scen]
    pairs = [(a, b) for i, a in enumerate(cands) for b in cands[i + 1:]]
    gains = {pr: expected_gain_pair(world, known, pr, target_scen, prior) for pr in pairs}
    best = max(gains, key=gains.get)
    redundant = (known[0], known[1])
    if gains[best] - 0.0 < margin:
        return None
    return {"informative": {"scens": list(best), "text": _pair_text(world, best),
                            "gain": gains[best]},
            "redundant": {"scens": list(redundant), "text": _pair_text(world, redundant),
                          "gain": 0.0},
            "irrelevant": {"scens": None, "text": "Which of the maker's daily habits is true?",
                           "gain": 0.0}}


# ── A track: appraisal worlds ─────────────────────────────────────────────────────────

_HAZARDS = {"workshop": ["a crack in the main beam", "a mislabeled batch of glaze",
                         "damp in the timber store", "a loose hoist chain"],
            "civic": ["a scoured pier footing", "a blocked culvert grate",
                      "a cracked reservoir stair", "a sagging market roof truss"]}
ACTIONS = ("posted a warning and halted use", "sent word that all was well",
           "ordered a quiet inspection first", "cleared the site and called the crew")
VALUATIONS = ("alarmed", "uneasy", "unconcerned", "relieved")
AUDIENCE_ACTS = ("stop and stay away", "carry on as usual", "inspect before use",
                 "come and help repair")
FACT_STATES = ("the hazard is real and serious", "the hazard is real but minor",
               "there is no hazard", "cannot be determined from what is given")
# the target's next decision (A02/A03): a four-rung ladder of caution, no affective word
# in any label; the rung is the fact state's severity plus one for a risk-averse maker
NEXT_ACTS = ("do nothing further", "reopen after a look", "post a warning and wait",
             "order a full repair")
SEVERITY = {FACT_STATES[2]: 0, FACT_STATES[3]: 1, FACT_STATES[1]: 2, FACT_STATES[0]: 3}


def make_appraisal_world(lid: str, domain: str) -> dict:
    """A situation with an observed communicative action, the maker's stakes and revealed
    risk preference (grounding the appraisal), a communicative aim independent of the
    appraisal, a factual state, and four balanced questions. The affect word in the
    message is register-neutral and independent of the truth."""
    rng = _rng(lid, "appraisal")
    inst = institution_name(domain, rng)
    hazard = rng.choice(_HAZARDS[domain])
    # crossed factors, rotated so answer frequencies balance across worlds
    k = hash_stable(lid) % 4
    stakes = ("high", "none")[k % 2]                        # does the maker lose if real?
    aim = ("caution", "calm")[(k // 2) % 2]                 # what the maker wants felt
    fact_state = FACT_STATES[hash_stable(lid + "f") % 4]
    withheld = fact_state == FACT_STATES[3]
    # appraisal grounded in stakes and revealed preference: high stakes + risk-averse
    # record -> alarmed/uneasy; none -> unconcerned/relieved
    risk_averse = stakes == "high" and (hash_stable(lid + "r") % 3 != 0)
    valuation = ("alarmed" if risk_averse and "serious" in fact_state else
                 "uneasy" if risk_averse else
                 "relieved" if "no hazard" in fact_state else "unconcerned")
    action = (ACTIONS[0] if aim == "caution" and rng.random() < 0.7 else
              ACTIONS[3] if aim == "caution" else
              ACTIONS[1] if rng.random() < 0.7 else ACTIONS[2])
    audience_act = (AUDIENCE_ACTS[0] if aim == "caution" and action == ACTIONS[0] else
                    AUDIENCE_ACTS[3] if aim == "caution" else
                    AUDIENCE_ACTS[1] if action == ACTIONS[1] else AUDIENCE_ACTS[2])
    prior_choices = ("It has twice paid for load tests nobody required and once refused a "
                     "contract over an uncertified beam." if risk_averse else
                     "It has twice skipped optional inspections and once shipped a piece "
                     "the day a flaw was reported.")
    stake_line = (f"If {hazard} turns out real, the maker bears the loss."
                  if stakes == "high" else
                  f"If {hazard} turns out real, the maker loses nothing; the risk falls on others.")
    affect = AFFECT_WORDS[hash_stable(lid + "a") % 4]
    message = (f"{inst.capitalize()} {affect} {hazard} to its people and {action}. "
               f"It chose to show them one case: " +
               ("the collapse of a similar structure two towns over." if aim == "caution"
                else "a similar structure that stood for fifty years untroubled."))
    situation = (f"{message}\n{stake_line}\n{prior_choices}\n" +
                 ("" if withheld else f"Independent survey: {fact_state}."))
    qs = {
        "action": {"question": "What did the maker actually do?",
                   "options": {a: a for a in ACTIONS}, "truth": action},
        "valuation": {"question": "How did the maker itself judge the situation?",
                      "options": {v: v for v in VALUATIONS}, "truth": valuation},
        "audience": {"question": "What did the maker want its people to do?",
                     "options": {a: a for a in AUDIENCE_ACTS}, "truth": audience_act},
        "fact": {"question": "What is the factual state of the hazard?",
                 "options": {f: f for f in FACT_STATES}, "truth": fact_state},
    }
    return {"lineage_id": lid, "domain": domain, "institution": inst, "hazard": hazard,
            "stakes": stakes, "aim": aim, "risk_averse": risk_averse,
            "valuation": valuation, "action": action, "audience_act": audience_act,
            "fact_state": fact_state, "withheld": withheld, "message": message,
            "situation": situation, "questions": qs,
            "propagandist": stakes == "none" and aim == "caution",
            "worried_reassurer": risk_averse and aim == "calm",
            # the target's next choice (A02/A03): a KNOWN answer set by the fact state
            # and the maker's revealed risk preference (one rung more cautious when
            # risk-averse), so the appraisal sign and the correct action are crossed
            # inside three of the four answers and a steer that always favors caution
            # cannot pass as target-specific prediction (the smoke's version drew this
            # label from a hash, which no reader could have predicted)
            "next_choice": {"question": "Which will the maker do next about the hazard?",
                            "options": {a: a for a in NEXT_ACTS},
                            "truth": NEXT_ACTS[min(3, SEVERITY[fact_state]
                                                   + (1 if risk_averse else 0))],
                            "truth_provenance": "construction"}}


# ── T track: decision lessons ─────────────────────────────────────────────────────────

_RULE_WORLDS = [
    ("seed lots", ("red", "blue"), "germinate in cold soil", "need warm soil",
     "germinated in cold soil", "needed warm soil"),
    ("dye vats", ("copper", "tin"), "hold color through washing", "fade after one wash",
     "held its color through washing", "faded after one wash"),
    ("mortar mixes", ("grey", "buff"), "set under rain", "wash out under rain",
     "set under rain", "washed out under rain"),
    ("rope grades", ("tarred", "plain"), "hold a full load wet", "part when wet",
     "held a full load wet", "parted when wet"),
]
_RULE_BY_KIND = {f[0]: f for f in _RULE_WORLDS}
CASE_ACTIONS = ("use it as it is", "hold it back for now", "swap for the other kind",
                "test a small batch first")
DELAY_ACTIONS = (CASE_ACTIONS[1], CASE_ACTIONS[3])     # payoff-neutral, never disastrous
GOAL_OPTIONS = {"honest_helpful": "the source stated a rule and advised what that rule implies",
                "honest_mistaken": "the source was wrong but believed what it said",
                "knowing_misleading": "the source steered you away from what its own rule implies",
                "unknown": "cannot be told from the message"}


def make_lesson_world(lid: str, domain: str) -> dict:
    """A rule world: a true rule (which tag is the good one), a recipient case, the
    source's latent knowledge state, and the action an inducing source pushes. The eight
    message cells (truth x intent x support) are rendered by lesson_message on this one
    world, so every cell is paired. The source's knowledge is stored apart from what it
    states; alignment is derived from payoffs, never asserted."""
    rng = _rng(lid, "lesson")
    kind, tags = rng.choice(_RULE_WORLDS)[:2]
    true_tag = rng.choice(tags)                                  # the tag that is good
    other = tags[1] if true_tag == tags[0] else tags[0]
    case_tag = rng.choice(tags)
    condition = rng.choice(["cold, wet conditions", "the usual conditions"])
    # payoff-optimal action for the recipient under the TRUE rule
    optimal = CASE_ACTIONS[0] if case_tag == true_tag else CASE_ACTIONS[2]
    # a false-rule source is mistaken or lying, half and half; never identifiable from
    # the message, so the goal question's truth never depends on it (see lesson_message)
    knowledge = "correct" if rng.random() < 0.5 else "mistaken"
    return {"lineage_id": lid, "domain": domain, "kind": kind, "tags": list(tags),
            "true_tag": true_tag, "other_tag": other, "case_tag": case_tag,
            "condition": condition, "knowledge": knowledge, "optimal": optimal,
            "delay_action": DELAY_ACTIONS[hash_stable(lid + "d") % 2],
            # the novel lot always carries the OTHER tag from the recipient's own, so the
            # taught action for it is never the message's advice: applying the rule and
            # echoing the advice give different answers in every world (the loop smoke's
            # readers echoed the advice on 99 percent of novel cases)
            "novel_case_tag": tags[1] if case_tag == tags[0] else tags[0],
            "goal_options": dict(GOAL_OPTIONS),
            "relay_schema": {"good_tag": "<tag>", "bad_tag": "<tag>"}}


def lesson_message(w: dict, truth: str, intent: str, support: str) -> dict:
    """One message cell. The stated rule is the true rule or its reverse. A benefit
    source advises what its own stated rule implies for the recipient's lot; an inducing
    source pushes the world's delay action instead (its own agenda: a payoff-neutral
    hold or test), so intent is realized in EVERY world (the smoke's version made
    benefit and induce identical whenever the recipient's tag was the good one, and
    let a benefit source contradict its own rule). Support adds a worked example and a
    plain restatement of the same rule (same factual payload). The goal truth is the
    label the message plus the later outcome can support: consistent advice under a
    rule that proved true is honest_helpful; advice that deviates from the source's own
    rule is knowing_misleading (steering, whatever the source knew); consistent advice
    under a rule that proved false is 'unknown', because mistaken and lying sources are
    indistinguishable from the message (brief T02: no reward for confident intention
    assignment where the observations do not distinguish the sources)."""
    kind, tags = w["kind"], tuple(w["tags"])
    true_tag = w["true_tag"]
    other = tags[1] if true_tag == tags[0] else tags[0]
    stated_tag = true_tag if truth == "true" else other
    stated_bad = other if stated_tag == true_tag else true_tag
    fam = _RULE_BY_KIND[kind]
    good, bad, good_past = fam[2], fam[3], fam[4]
    rule_text = f"{kind.capitalize()} tagged {stated_tag} {good}; those tagged {stated_bad} {bad}."
    # comprehension support is a worked ACTION mapping (what was done with a lot of each
    # tag, and how it turned out) plus a plain restatement: the same factual payload as
    # the rule, in the form the novel-case question will need (the loop smoke's version,
    # an outcome anecdote alone, moved no reader's application at all)
    example = (f" For instance, last season a {stated_tag}-tagged lot came in and we used it as "
               f"it was, and it {good_past}; a {stated_bad}-tagged lot came in and we swapped it "
               f"for a {stated_tag}-tagged one, because {stated_bad} lots {bad}. In short: "
               f"{stated_tag} is the tag to use and {stated_bad} the tag to avoid."
               if support == "supported" else "")
    implied = CASE_ACTIONS[0] if w["case_tag"] == stated_tag else CASE_ACTIONS[2]
    recommended = implied if intent == "benefit" else w["delay_action"]
    aligned = recommended == w["optimal"]
    knowledge = w["knowledge"] if truth == "false" else "correct"
    goal_truth = ("honest_helpful" if truth == "true" and intent == "benefit" else
                  "knowing_misleading" if intent == "induce" else "unknown")
    message = (f"{rule_text}{example} Your lot is tagged {w['case_tag']} and faces "
               f"{w['condition']}. My advice: {recommended}.")
    return {"message": message, "rule_text": rule_text, "recommended": recommended,
            "implied_by_rule": implied, "aligned": aligned, "goal_truth": goal_truth,
            "knowledge": knowledge, "steering": intent == "induce",
            "relay_truth": {"good_tag": stated_tag, "bad_tag": stated_bad}}


def lesson_novel_case(world: dict, stated_good_tag: str | None = None) -> dict:
    """The novel case. 'truth' is the action the TRUE rule makes optimal; when the
    stated tag is given, 'truth_taught' is the action the LESSON implies (the learning
    outcome T01 scores as primary, so a well-learned false lesson counts as learned and
    its cost shows in the payoff outcome, not in the learning score)."""
    tag = world["novel_case_tag"]
    truth = CASE_ACTIONS[0] if tag == world["true_tag"] else CASE_ACTIONS[2]
    out = {"question": f"A different lot of {world['kind']}, tagged {tag} (not your "
                       f"{world['case_tag']}-tagged lot), now arrives under the same conditions. "
                       f"Going by the rule in the lesson, what should be done with this "
                       f"{tag}-tagged lot?",
           "options": {a: a for a in CASE_ACTIONS}, "truth": truth,
           "truth_provenance": "construction"}
    if stated_good_tag is not None:
        out["truth_taught"] = CASE_ACTIONS[0] if tag == stated_good_tag else CASE_ACTIONS[2]
    return out


# T02: pools with stochastic outcomes (a good-tag lot turns out good four times in
# five, a bad-tag lot twice in five), so an inducing source has good-outcome lots of
# the recipient's own tag to cherry-pick, and the selection rule is a fact about which
# lots were shown rather than a restatement of the rule
POOL_PER_TAG = 5
GOOD_TAG_GOOD = 4
BAD_TAG_GOOD = 2
RULE_OPTIONS = {"representative": "picked cases at random from the lots it had",
                "benefit": "picked the cases most typical of your own tag",
                "induce": "picked only the good-outcome cases of your own tag",
                "unknown": "cannot be told from what is shown"}


def _pool(tags, true_tag: str, rng: random.Random) -> list[dict]:
    pool = []
    for tag in tags:
        n_good = GOOD_TAG_GOOD if tag == true_tag else BAD_TAG_GOOD
        outs = ["good"] * n_good + ["bad"] * (POOL_PER_TAG - n_good)
        rng.shuffle(outs)
        pool += [{"tag": tag, "outcome": o} for o in outs]
    rng.shuffle(pool)
    for i, c in enumerate(pool):
        c["i"] = i
    return pool


def _select(pool: list[dict], rule: str, recipient_tag: str, rng: random.Random) -> list[dict]:
    mine = [c for c in pool if c["tag"] == recipient_tag]
    if rule == "representative":
        return rng.sample(pool, 2)
    if rule == "benefit":          # the recipient's own tag, its typical outcome first
        n_good = sum(c["outcome"] == "good" for c in mine)
        maj = "good" if 2 * n_good > len(mine) else "bad"
        typical = [c for c in mine if c["outcome"] == maj]
        rest = [c for c in mine if c["outcome"] != maj]
        return (typical + rest)[:2]
    return [c for c in mine if c["outcome"] == "good"][:2]     # induce: cherry-pick


def selection_world(world: dict, rule: str, visible: bool, rng: random.Random) -> dict:
    """T02's current case: the source shows two lots of the recipient's kind chosen by
    its rule from a pool of ten; visible = the whole pool with outcomes is listed (the
    opportunity set the source had), hidden = only the two shown lots."""
    pool = _pool(world["tags"], world["true_tag"], rng)
    shown = _select(pool, rule, world["case_tag"], rng)
    lines = [f"- a {c['tag']}-tagged lot that turned out {c['outcome']}" for c in shown]
    text = "The source showed you these earlier lots of the same kind:\n" + "\n".join(lines)
    if visible:
        text += ("\nThe source could have shown you any of these ten lots: " +
                 ", ".join(f"{c['tag']} ({c['outcome']})" for c in pool) + ".")
    return {"rule": rule, "visible": visible, "shown": shown, "pool": pool, "text": text,
            "rule_options": dict(RULE_OPTIONS)}


def source_records(world: dict, rule: str, rng: random.Random) -> str:
    """Three earlier selections by the same source, on lots of OTHER kinds, each with
    the pool the source could draw on (outcomes known in hindsight) and what it showed
    that lot's recipient; the recipient's tag was the poorer one in two of the three, so
    a benefit source is seen showing the failing lots and an inducing source the
    cherry-picked good ones. Nothing here bears on the current kind's rule (the smoke's
    version showed the current kind's own pool with outcomes, which handed every route
    the answer)."""
    others = [f for f in _RULE_WORLDS if f[0] != world["kind"]]
    lines = []
    for j in range(3):
        fam = others[j % len(others)]
        tags = fam[1]
        true_tag = tags[j % 2]
        rec_tag = tags[1 - (j % 2)] if j < 2 else true_tag
        pool = _pool(tags, true_tag, rng)
        shown = _select(pool, rule, rec_tag, rng)
        lines.append(f"- {fam[0]}, for a recipient whose lot was tagged {rec_tag}; the lots the "
                     f"source could draw on (as they turned out): " +
                     ", ".join(f"{c['tag']} {c['outcome']}" for c in pool) +
                     "; it showed: " + ", ".join(f"{c['tag']} {c['outcome']}" for c in shown))
    return "\n".join(lines)


# ── H01: relay chains ─────────────────────────────────────────────────────────────────

PLAN_ITEMS = ("materials", "labor", "inspection", "transport")


def make_chain_world(lid: str, domain: str) -> dict:
    """Hop 0's brief: a primary constraint (a budget share floor on one item, verifiable
    from the plan JSON) and a local elaboration preference (an item the maker favors)."""
    rng = _rng(lid, "chain")
    inst = institution_name(domain, rng)
    item = rng.choice(_ITEMS[domain])
    constrained = rng.choice(PLAN_ITEMS)
    # floors calibrated on the discarded smoke lineage: the makers that comply land
    # exactly on the floor, and 0.45 was never met within the attempt cap
    floor = rng.choice([0.30, 0.35, 0.40])
    local_pref = rng.choice([p for p in PLAN_ITEMS if p != constrained])
    return {"lineage_id": lid, "domain": domain, "institution": inst, "item": item,
            "constrained_item": constrained, "floor": floor, "local_pref": local_pref,
            "flipped_item": rng.choice([p for p in PLAN_ITEMS if p != constrained])}


def plan_satisfies(plan: dict, item: str, floor: float) -> bool:
    try:
        shares = {k: float(plan[k]) for k in PLAN_ITEMS}
    except Exception:                                                            # noqa: BLE001
        return False
    total = sum(shares.values())
    if total <= 0:
        return False
    return shares[item] / total >= floor - 1e-9


def parse_plan(text: str) -> dict | None:
    import re                                                                     # noqa: PLC0415
    for m in re.finditer(r"\{[^{}]*\}", text or ""):
        try:
            obj = json.loads(m.group(0))
        except Exception:                                                        # noqa: BLE001
            continue
        if isinstance(obj, dict) and all(k in obj for k in PLAN_ITEMS):
            return obj
    return None


# ── H02: weight histories ─────────────────────────────────────────────────────────────

HISTORY_TYPES = ("stable", "gradual", "abrupt", "marker_removed", "fresh_final")


def make_history_world(lid: str, domain: str, htype: str, n_steps: int = 12) -> dict:
    """A record of n_steps realized draws under a weight trajectory with one primary
    axis pinned high and subsidiary weights following the history type. Weights are
    relative (normalized over the subsidiary axes); temperature is the environment's
    fixed TEMP, so scale and decision noise are not separately identified and only
    relative weights are estimands."""
    # the axes, institution, and item are drawn WITHOUT the history type in the salt, so
    # the five histories of one lineage share every utility and every draw the weights
    # allow: stable and marker_removed then share all twelve draws and differ only in
    # their explicit markers (the exact collision H02's control needs), and abrupt and
    # fresh_final share the second half
    rng = _rng(lid, "hist")
    primary = rng.choice(AXES)
    subs = [ax for ax in AXES if ax != primary]
    early = rng.choice(subs)
    late = rng.choice([s for s in subs if s != early])

    def weights(t):
        w = {ax: 0.15 for ax in AXES}
        w[primary] = 1.0
        if htype in ("stable", "marker_removed"):
            w[early] = 0.6
        elif htype == "gradual":
            frac = t / (n_steps - 1)
            w[early] = 0.6 * (1 - frac) + 0.15 * frac
            w[late] = 0.15 * (1 - frac) + 0.6 * frac
        elif htype == "abrupt":
            if t < n_steps // 2:
                w[early] = 0.6
            else:
                w[late] = 0.6
        elif htype == "fresh_final":
            w[late] = 0.6
        return tuple(w[ax] for ax in AXES)

    inst = institution_name(domain, rng)
    item = rng.choice(_ITEMS[domain])
    steps = []
    for t in range(n_steps):
        si = t % N_SCEN
        ctx, opts = scenario_text(domain, inst, item, si)
        U = world_utilities(lid, t)
        w = weights(t)
        draw = draw_choice(U, w, _rng(lid, f"hdraw{t}"))
        marker = ""
        if htype != "fresh_final" and t < n_steps // 2:
            marker = f" (stated aim: keep {early} in view)"
        if htype == "marker_removed" and t >= n_steps // 2:
            marker = ""
        if htype in ("stable",) and t >= n_steps // 2:
            marker = f" (stated aim: keep {early} in view)"
        steps.append({"t": t, "context": ctx, "options": opts, "utilities": U,
                      "w": list(w), "draw": draw, "marker": marker})
    return {"lineage_id": lid, "domain": domain, "history_type": htype,
            "primary": primary, "early": early, "late": late, "steps": steps,
            "institution": inst, "item": item}


def history_record(world: dict, upto: int, with_markers: bool = True) -> str:
    lines = []
    for s in world["steps"][:upto]:
        mk = s["marker"] if with_markers else ""
        lines.append(f"- {s['context']} It chose: {s['options'][s['draw']]}.{mk}")
    return "\n".join(lines)


def weight_grid_posterior(world: dict, upto: int) -> dict:
    """Exact posterior over a grid of subsidiary weights (early axis weight in
    {0.15, 0.375, 0.6}) for the first half and second half separately: which subsidiary
    axis was elevated when. Returns per-window posteriors over the three subsidiary axes
    plus 'none'."""
    primary = world["primary"]
    subs = [ax for ax in AXES if ax != primary]
    out = {}
    for name, rng_t in (("first_half", range(0, upto // 2)),
                        ("second_half", range(upto // 2, upto))):
        logp = {}
        for cand in subs + ["none"]:
            w = {ax: 0.15 for ax in AXES}
            w[primary] = 1.0
            if cand != "none":
                w[cand] = 0.6
            wt = tuple(w[ax] for ax in AXES)
            lp = 0.0
            for t in rng_t:
                s = world["steps"][t]
                probs = choice_probs(s["utilities"], wt)
                lp += math.log(max(probs[AXES.index(s["draw"])], 1e-12))
            logp[cand] = lp
        m = max(logp.values())
        exps = {k: math.exp(v - m) for k, v in logp.items()}
        z = sum(exps.values())
        out[name] = {k: v / z for k, v in exps.items()}
    return out


# ── self-tests ────────────────────────────────────────────────────────────────────────

def self_test(n: int = 30) -> None:
    labels_seen: dict = {}
    for domain in DOMAINS4:
        for i in range(n):
            lid = f"TEST|{domain}|s{i % 3}|w{i:04d}|pilot"
            w = make_world(lid, domain)
            check_equal_information(w)
            for s in w["scenarios"]:
                assert len(s["feasible"]) >= 2, (lid, s["i"])
                assert s["draw"] in s["feasible"]
                assert abs(sum(s["distribution"].values()) - 1) < 1e-9
                labels_seen.setdefault(("c", domain), set()).add(s["draw"])
            # determinism
            w2 = make_world(lid, domain)
            assert json.dumps(w) == json.dumps(w2)
            # C03 menu exists for most worlds (a flat menu is an instrument event)
            menu = build_probe_menu(w, [0, 1], 9, w["prior"])
            if menu is not None:
                assert menu["informative"]["gain"] >= menu["redundant"]["gain"] + PROBE_MARGIN
                assert expected_gain_pair(w, [0, 1], (0, 1), 9, w["prior"]) == 0.0
            # the step question has exactly one correct option whatever is blocked
            sq = step_question(w, _rng(lid, "sq"))
            if "ruled out" in sq["question"]:
                assert sum(o in w["blocked_steps"] for o in sq["options"]) == 1, (lid, sq)
            else:
                assert sum(o in w["feasible_steps"] for o in sq["options"].values()) == 1, (lid, sq)
            a = make_appraisal_world(lid, domain)
            for q in list(a["questions"].values()) + [a["next_choice"]]:
                assert q["truth"] in q["options"], (lid, q)
                labels_seen.setdefault(("a", q["question"]), set()).add(q["truth"])
            t = make_lesson_world(lid, domain)
            cells = {}
            for truth in ("true", "false"):
                for intent in ("benefit", "induce"):
                    for support in ("bare", "supported"):
                        v = lesson_message(t, truth, intent, support)
                        assert v["relay_truth"]["good_tag"] != v["relay_truth"]["bad_tag"]
                        cells[(truth, intent, support)] = v
                        labels_seen.setdefault(("t", "goal"), set()).add(v["goal_truth"])
                        nc = lesson_novel_case(t, v["relay_truth"]["good_tag"])
                        assert nc["truth"] in CASE_ACTIONS and nc["truth_taught"] in CASE_ACTIONS
                # intent is realized in every world: benefit and induce never coincide
                assert cells[(truth, "benefit", "bare")]["message"] != cells[(truth, "induce", "bare")]["message"]
                assert cells[(truth, "benefit", "bare")]["recommended"] == cells[(truth, "benefit", "bare")]["implied_by_rule"]
            assert cells[("true", "benefit", "bare")]["aligned"] and not cells[("false", "benefit", "bare")]["aligned"]
            for rule in ("representative", "benefit", "induce"):
                sel = selection_world(t, rule, True, _rng(lid, "sel" + rule))
                assert len(sel["shown"]) == 2 and len(sel["pool"]) == 2 * POOL_PER_TAG, (lid, rule)
                assert t["kind"] not in source_records(t, rule, _rng(lid, "rec" + rule))
            ch = make_chain_world(lid, domain)
            good_plan = {k: 0.1 for k in PLAN_ITEMS} | {ch["constrained_item"]: 0.7}
            bad_plan = {k: 0.3 for k in PLAN_ITEMS} | {ch["constrained_item"]: 0.1}
            assert plan_satisfies(good_plan, ch["constrained_item"], ch["floor"])
            assert not plan_satisfies(bad_plan, ch["constrained_item"], ch["floor"])
            assert parse_plan('plan: {"materials": 0.4, "labor": 0.3, "inspection": 0.2, '
                              '"transport": 0.1}') is not None
            for ht in HISTORY_TYPES:
                h = make_history_world(lid, domain, ht)
                post = weight_grid_posterior(h, 12)
                assert abs(sum(post["first_half"].values()) - 1) < 1e-9
            # the exact collision H02 needs: stable and marker_removed share every draw
            # and differ only in markers, so their artifact-only records are identical
            h_st = make_history_world(lid, domain, "stable")
            h_mr = make_history_world(lid, domain, "marker_removed")
            assert [s["draw"] for s in h_st["steps"]] == [s["draw"] for s in h_mr["steps"]], lid
            assert history_record(h_st, 9, False) == history_record(h_mr, 9, False), lid
            assert history_record(h_st, 9, True) != history_record(h_mr, 9, True), lid
    # truth-marginal gate: no constant answer sets
    for key, seen in labels_seen.items():
        assert len(seen) >= 2, (key, seen)
    print(f"s4_worlds self-tests pass: {2 * n} worlds per constructor, "
          f"{len(labels_seen)} answer sets all varied")


if __name__ == "__main__":
    self_test()
