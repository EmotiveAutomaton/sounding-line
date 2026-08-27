"""Stage 3 shared experimental library. One home for the decision environment, episode
generation, mechanical verification, scoring wrappers, and statistics that the S, L, E,
M, C, and V trunks all consume. One filename convention, one helper (the L133 rule).

THE DECISION ENVIRONMENT. A scenario poses a project choice with four options, one shaped
by each tradeoff axis: ROBUST (reliability/safety), CHEAP (cost), FAST (speed), PRECEDENT
(track record). Numeric utilities are generated so that each option is the argmax under
its own axis profile in every scenario — no option is globally dominant, which designs out
the item-attractiveness failure that killed the Stage-2 ecology (L169) instead of testing
for it afterward. A maker with profile w chooses via softmax(w . u / TEMP); the REALIZED
choice is mechanical (exactly one option anchor present in the artifact). Choice-set
strength (V01) is computed exactly from the utility matrix: the same option chosen from a
set where it barely wins is weak evidence; chosen despite a large utility deficit on the
rival axis it is strong evidence.

LESSONS wired in here once, for every consumer: accept-time realization; unique anchors
self-tested at import; declared opportunity denominators; sign-flip permutation with its
seed recorded; score-short-hypothesis-given-long-evidence direction only; ollama and HF
retries; the gpulock is taken by RUNNERS, never by this library.
"""

from __future__ import annotations

import json
import random
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

AXES = ("robust", "cheap", "fast", "precedent")
TEMP = 0.35        # softmax temperature for maker choice realization

# 24 scenario frames: (context sentence, {axis: (anchor phrase, option sentence)})
# Anchors are unique across the whole bank (asserted at import).
_TOPICS = [
    ("The town must replace its aging footbridge.", "bridge",
     {"robust": "steel truss rated far beyond code",
      "cheap": "refurbished modular span at half price",
      "fast": "prefabricated deck installed in nine days",
      "precedent": "same design three neighboring towns use"}),
    ("The library is choosing new catalog software.", "catalog",
     {"robust": "system with a decade of uptime records",
      "cheap": "open-source suite with no license fees",
      "fast": "vendor promising go-live within a month",
      "precedent": "platform every regional branch already runs"}),
    ("The bakery needs a second oven line.", "oven",
     {"robust": "cast-iron units known to outlast owners",
      "cheap": "auction equipment at forty percent of list",
      "fast": "floor models deliverable this week",
      "precedent": "the exact line the flagship store uses"}),
    ("The clinic is picking a records vendor.", "records",
     {"robust": "audited system with certified failover",
      "cheap": "tiered plan cheapest in the county",
      "fast": "migration completed over one weekend",
      "precedent": "vendor serving the two nearest clinics"}),
    ("The school must pick a bus contractor.", "bus",
     {"robust": "fleet with the best inspection scores statewide",
      "cheap": "bid twenty percent under every rival",
      "fast": "contractor able to start Monday",
      "precedent": "company the district used for a decade"}),
    ("The farm is choosing an irrigation upgrade.", "irrigation",
     {"robust": "buried lines warrantied for thirty years",
      "cheap": "surface drip at a third of the cost",
      "fast": "kit the crew can lay before the dry month",
      "precedent": "layout the neighboring farms standardized on"}),
    ("The museum needs climate control for the archive.", "climate",
     {"robust": "redundant chillers with dual sensors",
      "cheap": "single-unit system within this year's budget",
      "fast": "portable units running by Friday",
      "precedent": "the configuration the national archive uses"}),
    ("The startup must choose a build server.", "buildserver",
     {"robust": "cluster with automatic failover nodes",
      "cheap": "spot instances at minimal monthly cost",
      "fast": "managed service live this afternoon",
      "precedent": "stack their last company shipped on"}),
    ("The port is selecting a crane refit.", "crane",
     {"robust": "drivetrain rated for double the load",
      "cheap": "rebuilt assembly from the salvage yard",
      "fast": "retrofit finished between two sailings",
      "precedent": "refit identical to the north dock's"}),
    ("The theater must replace stage rigging.", "rigging",
     {"robust": "motorized system with triple interlocks",
      "cheap": "manual counterweights at minimal outlay",
      "fast": "install completed during the dark week",
      "precedent": "rigging every touring house expects"}),
    ("The lab is choosing a freezer supplier.", "freezer",
     {"robust": "units with independent alarm circuits",
      "cheap": "surplus stock from a closing facility",
      "fast": "delivery guaranteed within three days",
      "precedent": "the model the parent institute stocks"}),
    ("The village must fix the flood culvert.", "culvert",
     {"robust": "box culvert sized for the century storm",
      "cheap": "relined pipe at a fraction of the bid",
      "fast": "crew that can pour before the rains",
      "precedent": "the fix the county applied upstream"}),
]
# second domain: personnel/process decisions (same axes, different surface conventions)
_TOPICS2 = [
    ("The journal must clear its review backlog.", "backlog",
     {"robust": "double-review with an adjudicating editor",
      "cheap": "volunteer pool at no added budget",
      "fast": "triage sprint clearing half in a week",
      "precedent": "the process the sister journal adopted"}),
    ("The team must onboard six new hires.", "onboard",
     {"robust": "mentor pairing with weekly checkpoints",
      "cheap": "self-serve wiki costing nothing new",
      "fast": "one intensive bootcamp week",
      "precedent": "the program the Berlin office runs"}),
    ("The kitchen must cover the holiday rush.", "rush",
     {"robust": "cross-trained floaters on every shift",
      "cheap": "adjusted rotas without new hires",
      "fast": "agency staff starting tomorrow",
      "precedent": "the plan that worked last December"}),
    ("The council must handle permit delays.", "permit",
     {"robust": "audited checklist with dual sign-off",
      "cheap": "reordered queue at zero cost",
      "fast": "temporary fast-lane for simple cases",
      "precedent": "the workflow the neighboring council uses"}),
    ("The choir must prepare the festival program.", "choir",
     {"robust": "sectional rehearsals with recorded checks",
      "cheap": "existing repertoire needing no new scores",
      "fast": "two full-ensemble weekends",
      "precedent": "the running order from the winning year"}),
    ("The clinic must reduce appointment no-shows.", "noshow",
     {"robust": "confirmed double-reminder protocol",
      "cheap": "text reminders on the current system",
      "fast": "overbooking pilot starting this week",
      "precedent": "the scheme the dental wing settled on"}),
    ("The warehouse must cut picking errors.", "picking",
     {"robust": "scan-verified pick with two-step checks",
      "cheap": "relabeled shelves at printing cost only",
      "fast": "hot-zone reshuffle done overnight",
      "precedent": "the layout the flagship depot proved"}),
    ("The department must assign thesis advisors.", "advisor",
     {"robust": "matched pairs with a written backup plan",
      "cheap": "load-balanced list with no new lines",
      "fast": "first-come assignment closing Friday",
      "precedent": "the rotation the physics wing follows"}),
    ("The station must schedule winter maintenance.", "wintermx",
     {"robust": "staggered overhauls with spare coverage",
      "cheap": "deferred noncritical work to spring",
      "fast": "blitz week with all bays open",
      "precedent": "the calendar the coastal line keeps"}),
    ("The bakery co-op must set delivery routes.", "routes",
     {"robust": "buffered routes with backup drivers",
      "cheap": "existing vans on tightened loops",
      "fast": "software reroute live tomorrow",
      "precedent": "the map the dairy co-op standardized"}),
    ("The gallery must plan the opening night.", "opening",
     {"robust": "staffed stations with a run-through",
      "cheap": "member volunteers and potluck catering",
      "fast": "turnkey event firm on short notice",
      "precedent": "the format of the spring opening"}),
    ("The school must revise exam invigilation.", "invigilate",
     {"robust": "double-invigilator rooms with logs",
      "cheap": "reshuffled staff at no added cost",
      "fast": "single large-hall sitting next week",
      "precedent": "the arrangement the sixth form used"}),
]

# third domain (V04/X4): community events and programming decisions, same axes
_TOPICS3 = [
    ("The town must plan the harvest festival.", "festival",
     {"robust": "weatherproofed stages with backup generators",
      "cheap": "borrowed equipment from the school district",
      "fast": "vendor package bookable by Friday",
      "precedent": "the exact layout of last year's festival"}),
    ("The library must launch a reading program.", "readingprog",
     {"robust": "piloted curriculum with trained facilitators",
      "cheap": "volunteer-led circles at zero budget",
      "fast": "ready-made kit launching next week",
      "precedent": "the program the county branch popularized"}),
    ("The rink must schedule public skating.", "rink",
     {"robust": "supervised sessions with certified marshals",
      "cheap": "unstaffed hours with waiver signage",
      "fast": "open-tomorrow trial timetable",
      "precedent": "the slots the old rink always kept"}),
    ("The museum must mount the summer exhibit.", "exhibit",
     {"robust": "conservator-approved mounts and casework",
      "cheap": "repurposed display stock from storage",
      "fast": "modular walls installable in a weekend",
      "precedent": "the hang the touring show specified"}),
    ("The orchestra must set the season opener.", "opener",
     {"robust": "double-rehearsed program with cover soloists",
      "cheap": "repertoire the players already know cold",
      "fast": "a gala assembled in ten days",
      "precedent": "the overture that opened the last five seasons"}),
    ("The market must handle vendor allocation.", "vendors",
     {"robust": "juried stalls with insurance verification",
      "cheap": "first-come pitches at a flat token fee",
      "fast": "same-day signup at the gate",
      "precedent": "the pitch map the summer market kept"}),
    ("The school must stage the spring play.", "play",
     {"robust": "understudied cast with a fire-marshal walkthrough",
      "cheap": "costumes and sets from the drama closet",
      "fast": "one-act showcase ready in a fortnight",
      "precedent": "the production the class of ninety-nine made famous"}),
    ("The parish must organize the charity drive.", "charitydrive",
     {"robust": "audited collection with dual counters",
      "cheap": "donation jars at existing counters",
      "fast": "flash appeal over one weekend",
      "precedent": "the drive format the diocese circulates"}),
    ("The club must run the regatta.", "regatta",
     {"robust": "safety boats with licensed crews on every leg",
      "cheap": "member-volunteer patrols and shared fuel",
      "fast": "sprint course markable by Thursday",
      "precedent": "the course chart framed in the clubhouse"}),
    ("The cinema must program the retrospective.", "retrospective",
     {"robust": "archival prints with a projection engineer",
      "cheap": "licensed digital files at bundle rates",
      "fast": "a lineup lockable this afternoon",
      "precedent": "the series the film society reveres"}),
    ("The council must site the night market.", "nightmarket",
     {"robust": "lit lot with marshalled crossings",
      "cheap": "the unused depot forecourt as-is",
      "fast": "the plaza cleared by tomorrow evening",
      "precedent": "the block the old night fair occupied"}),
    ("The band must plan the reunion tour.", "reunion",
     {"robust": "seated venues with full technical riders",
      "cheap": "club dates with house equipment",
      "fast": "four cities announced this week",
      "precedent": "the route of the farewell tour"}),
]

DOMAINS = {"infra": _TOPICS, "process": _TOPICS2, "events": _TOPICS3}


def scenarios(domain: str = "infra"):
    return DOMAINS[domain]


def utilities(scen_i: int, seed: int, domain: str = "infra"):
    """4x4 utility matrix (option x axis). Option i leads on axis i by construction;
    off-axis values are seeded noise, so profiles disagree across scenarios but no
    option dominates. Deterministic per (scenario, seed, domain)."""
    rng = random.Random(hash_stable(f"{domain}|{scen_i}|{seed}"))
    U = [[rng.uniform(0.15, 0.55) for _ in AXES] for _ in AXES]
    for i in range(4):
        U[i][i] = rng.uniform(0.8, 1.0)
    return U


def hash_stable(s: str) -> int:
    import hashlib
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)


def choice_probs(U, w, temp: float = TEMP):
    import math
    vals = [sum(wi * u for wi, u in zip(w, row)) for row in U]
    m = max(vals)
    exps = [math.exp((v - m) / temp) for v in vals]
    z = sum(exps)
    return [e / z for e in exps]


def realized_choice(text: str, scen_i: int, domain: str = "infra"):
    _, _, opts = scenarios(domain)[scen_i]
    low = text.lower()
    hits = [ax for ax in AXES if opts[ax].lower()[:24] in low]
    return hits[0] if len(hits) == 1 else None


def episode_prompt(scen_i: int, domain: str = "infra", policy_line: str = "") -> str:
    ctx, _, opts = scenarios(domain)[scen_i]
    letters = dict(zip("ABCD", AXES))
    body = "\n".join(f"{letter}) the {opts[ax]}" for letter, ax in letters.items())
    pol = f"\nYour standing approach: {policy_line}\n" if policy_line else "\n"
    return (f"Decision: {ctx}\nOptions:\n{body}\n{pol}"
            f"Write a short recommendation (40 to 110 words) committing to exactly one "
            f"option and working its full key phrase into your text. Do not mention the "
            f"other options' key phrases.\n\nRecommendation:")


POLICY_LINES = {
    "robust": "you weight reliability and safety far above cost, speed, or habit.",
    "cheap": "you weight cost savings far above reliability, speed, or habit.",
    "fast": "you weight schedule and speed far above cost, reliability, or habit.",
    "precedent": "you weight proven track records far above cost, speed, or novelty.",
}

PROFILE_W = {"robust": (1.0, 0.15, 0.15, 0.15), "cheap": (0.15, 1.0, 0.15, 0.15),
             "fast": (0.15, 0.15, 1.0, 0.15), "precedent": (0.15, 0.15, 0.15, 1.0)}


def bayes_profile_posterior(choices, scen_ids, seed, domain="infra",
                            profiles=PROFILE_W):
    """Records-aware known-answer reader: exact posterior over profiles from realized
    choices via the environment's own likelihood. No model involved."""
    import math
    logp = {name: 0.0 for name in profiles}
    for ch, si in zip(choices, scen_ids):
        U = utilities(si, seed, domain)
        idx = AXES.index(ch)
        for name, w in profiles.items():
            logp[name] += math.log(max(choice_probs(U, w)[idx], 1e-12))
    m = max(logp.values())
    exps = {k: math.exp(v - m) for k, v in logp.items()}
    z = sum(exps.values())
    return {k: v / z for k, v in exps.items()}


def perm_p(diffs, seed: int, n: int = 20000):
    rng = random.Random(seed)
    obs = sum(diffs) / len(diffs)
    ge = sum(1 for _ in range(n)
             if abs(sum(d * rng.choice((1, -1)) for d in diffs) / len(diffs))
             >= abs(obs))
    return obs, (ge + 1) / (n + 1)


def chat_gen(model, tok, prompt: str, seed: int, max_new: int = 220) -> str:
    from runners.scout_stage2_s import _chat_generate                            # noqa: PLC0415
    return _chat_generate(model, tok, prompt, seed, max_new=max_new)


def ollama_gen(prompt: str, system: str = "You follow instructions precisely.",
               retries: int = 5) -> str | None:
    from soundingline.probe.client import LocalClient                            # noqa: PLC0415
    client = LocalClient()
    for att in range(retries):
        try:
            return client.read_text(system, prompt).strip()
        except Exception as e:                                                   # noqa: BLE001
            print(f"  ollama retry {att}: {e}")
            time.sleep(4 * (att + 1))
    return None


def self_test() -> None:
    seen = set()
    for domain, topics in DOMAINS.items():
        for si, (ctx, tag, opts) in enumerate(topics):
            assert set(opts) == set(AXES), (domain, si)
            for ax, phrase in opts.items():
                key = phrase.lower()[:24]
                assert key not in seen, f"anchor collision: {phrase}"
                seen.add(key)
                fake = f"I recommend the {phrase} because it fits."
                assert realized_choice(fake, si, domain) == ax, (domain, si, ax)
    # utility construction: option i is argmax under profile i, every scenario/seed probe
    for domain in DOMAINS:
        for si in range(len(DOMAINS[domain])):
            for seed in (1, 2):
                U = utilities(si, seed, domain)
                for i, ax in enumerate(AXES):
                    probs = choice_probs(U, PROFILE_W[ax])
                    assert max(range(4), key=lambda j: probs[j]) == i, (domain, si, ax)
    # bayes reader recovers a profile from its own argmax choices
    rng = random.Random(7)
    for ax in AXES:
        sids = [rng.randrange(12) for _ in range(10)]
        chs = []
        for si in sids:
            U = utilities(si, 1, "infra")
            probs = choice_probs(U, PROFILE_W[ax])
            chs.append(AXES[max(range(4), key=lambda j: probs[j])])
        post = bayes_profile_posterior(chs, sids, 1, "infra")
        assert max(post, key=post.get) == ax, (ax, post)
    print("s3_lib self-tests pass:", sum(len(t) for t in DOMAINS.values()),
          "scenarios,", len(seen), "unique anchors")


if __name__ == "__main__":
    self_test()
