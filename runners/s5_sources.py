"""Stage 5 source-regime worlds (brief §4.2, the A track): a public notice or a workshop
memo whose seven hidden factors are crossed, never labeled, and whose surface is matched
so that "honest warning", "sincere fanatic", "strategic propagandist", and "neutral
report" are DERIVED regions of the factorial rather than templates with telltale words.

DESIGN CHECK (2026-08-29)
lessons read: LESSONS §3 (assigned is not realized: every hidden factor is realized either
  in the surface by construction or in a BEHAVIOR the reader predicts; a compliance pilot
  before a generated factorial, which is why this construction is templated and not
  maker-generated; count the identity space against the unit count; the criterion must be
  able to fail), CONTROLS §6 (surface collisions as the abstention control; leakage
  baselines before any reader).
gates and bands:
  - liveness gate (I03): every factor takes both (or all four) levels within each lane and
    the derived regions are all populated; NULL: live; ALTERNATIVE: a dead level, which
    voids the attribution that needs it rather than reporting a null on it.
  - leakage gate (I03): a bag-of-words linear classifier from the surface text to each
    HIDDEN factor (private belief, willingness to correct) sits within 0.10 of chance on
    held-out worlds; NULL: no leak; ALTERNATIVE: the hidden factor is in the words, which
    closes that attribution as leaked. Surface factors (intensity, arousal comparison,
    call to action, what was shown) are meant to be readable and are not gated.
  - collision gate (A02): every lineage carries a TWIN with the identical surface and the
    hidden factors flipped; NULL (an abstaining reader): mass on unknown or split across
    the twin pair for the hidden factors; ALTERNATIVE: confident opposite answers on
    identical text, which is projection, scored as such. Bands: unknown mass above 0.5 or
    a split within 0.2 counts as abstention; anything else is a confident call.
  - the communication criterion (§7.3): a regime call passes only through predicting a
    behavior on which the hidden states diverge (selection under a fresh opportunity,
    correction after counterevidence, the private action); surface classification alone
    never passes.
"""

from __future__ import annotations

import os
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners.s3_lib import hash_stable                                            # noqa: E402
from runners.s5_worlds import balanced_code, enumerate_identity                   # noqa: E402

SOURCE_DOMAINS = ("notice", "memo")
FACTORS = {"belief": ("low", "high"), "support": ("low", "high"),
           "arousal_goal": ("low", "high"), "action_goal": ("absent", "present"),
           "selection": ("representative", "cherry", "fabricated", "uncertain"),
           "correction": ("low", "high"), "intensity": ("low", "high")}
HIDDEN = ("belief", "correction")            # never in the surface; only in predicted behavior
TOPICS = {
    "notice": [("the footbridge over the mill race", "its timbers are rotten through", "crossing it", "kept off it"),
               ("the well on the common", "its water has turned foul", "drinking from it", "stopped drawing from it"),
               ("the north culvert", "it is close to collapse", "walking the bank above it", "fenced its own plot off from it"),
               ("the market hall roof", "its trusses are failing", "trading under it", "moved its own stall out"),
               ("the school wing stair", "its treads are cracked", "using it", "sent its own children round the other way"),
               ("the harbor wall steps", "they are undermined", "landing there", "moored its own boat elsewhere"),
               ("the flood gate", "it will not hold a spring tide", "leaving goods below it", "moved its own stores uphill"),
               ("the old bell tower", "its frame is rotten", "ringing it", "stopped its own ringers")],
    "memo": [("the new glue from the eastern supplier", "it fails in damp", "using it on joints", "kept its own joints on the old glue"),
             ("the copper sheet from the second foundry", "it cracks on the first bend", "using it for fittings", "kept its own fittings in the old sheet"),
             ("the winter-felled timber lot", "it warps as it dries", "using it for frames", "set its own frames aside from it"),
             ("the pale varnish", "it stays tacky for a month", "using it on finished work", "kept its own work on the amber"),
             ("the tarred rope from the new chandler", "it parts when wet", "rigging with it", "kept its own hoists on the old rope"),
             ("the river clay batch", "it slumps on the wheel", "throwing with it", "kept its own throwing to the pit clay"),
             ("the alum-tanned hides", "they crack at the first frost", "cutting from them", "kept its own cutting to the oak-tanned"),
             ("the coke-smelted bars", "they crack at the weld", "welding them", "kept its own welding to the charcoal bars")],
}
CASE_PLACES = {"notice": ["Ashford", "Calder", "Marrow", "Fennick", "Holloway", "Brightwater", "Quill", "Dunmere"],
               "memo": ["the Bindery", "the Foundry", "the Loomworks", "the Glassworks", "the Joinery", "the Press", "the Pottery", "the Forge"]}
ALARM_LINE = {"notice": "Remember what happened at {p}, where the same fault was ignored until it took lives.",
              "memo": "Remember the {p} job, where the same fault cost a season's work and the client."}
CALM_LINE = {"notice": "Remember {p}, where the same fault was watched for a year and did no harm.",
             "memo": "Remember the {p} job, where the same fault was worked around without loss."}
CALL_LINE = {"notice": "Keep off it until further notice.", "memo": "Stop using it on any job from today."}
INTENSE = {"low": ("", "It should be looked at."), "high": ("This cannot be overstated: ", "It must be dealt with at once.")}
# design 2 (L284): the closers state gravity without asking for anything, so only the action
# factor's call line carries a directive; both levels were imperatives before
if os.environ.get("S5_DESIGN", "1") == "2":
    INTENSE = {"low": ("", "It is a small matter."), "high": ("This cannot be overstated: ", "It is a grave matter.")}
POOL_N = 6
SHOW_N = 2
ACTION_OPTIONS = ("keep away from it", "carry on as before", "check it before deciding", "help put it right")
AUDIENCE_GOALS = {"alarm_act": "to alarm people and get them to act",
                  "alarm_only": "to alarm people without asking anything of them",
                  "calm_act": "to reassure people while still getting them to act",
                  "calm_only": "to reassure people and ask nothing"}
APPRAISALS = {"believed_grave": "it believed the claim and judged the matter grave",
              "believed_mild": "it believed the claim and judged the matter mild",
              "doubted_grave": "it doubted the claim but presented the matter as grave",
              "doubted_mild": "it doubted the claim and presented the matter as mild"}
SUPPORT_OPTIONS = {"high": "most of the record bears the claim out", "low": "little of the record bears the claim out"}
SELECTION_OPTIONS = {"representative": "it would show cases picked at random from what it has",
                     "cherry": "it would show only the cases that bear the claim out",
                     "fabricated": "it would show a case that never happened alongside a real one",
                     "uncertain": "it would show no cases and say reports vary"}
CORRECTION_OPTIONS = {"high": "it would post a correction", "low": "it would repeat the claim unchanged"}
PRIVATE_OPTIONS = {"high": "it acted on the claim itself, privately", "low": "it did not act on the claim itself"}
COMM_GOALS = ("inform", "warn", "mislead", "conceal")


def _rng(lid: str, salt: str) -> random.Random:
    return random.Random(hash_stable(lid + "|" + salt))


SURFACE_FACTORS = ("support", "arousal_goal", "action_goal", "selection", "intensity")
SURFACE_SPACE = 8 * 2 * 2 * 2 * 4 * 2          # 512 surfaces per domain; 170 per lane block
HIDDEN_SPACE = 4                                # belief x correction, balanced, never in the surface


def decode(code: int, hcode: int) -> dict:
    f = {"topic_i": code % 8}
    code //= 8
    for name in SURFACE_FACTORS:
        levels = FACTORS[name]
        f[name] = levels[code % len(levels)]
        code //= len(levels)
    f["belief"] = FACTORS["belief"][hcode % 2]
    f["correction"] = FACTORS["correction"][hcode // 2]
    return f


SPACE = SURFACE_SPACE


def region(f: dict) -> str:
    """Derived, never a template: the four named regions are conjunctions of factors."""
    if f["belief"] == "high" and f["support"] == "high" and f["selection"] == "representative" and f["correction"] == "high":
        return "honest_warning"
    if f["belief"] == "high" and f["support"] == "low" and f["selection"] in ("cherry", "fabricated") and f["correction"] == "low":
        return "sincere_fanatic"
    if f["belief"] == "low" and f["arousal_goal"] == "high" and f["action_goal"] == "present" and f["selection"] in ("cherry", "fabricated") and f["correction"] == "low":
        return "strategic_propagandist"
    if f["arousal_goal"] == "low" and f["action_goal"] == "absent" and f["intensity"] == "low" and f["selection"] in ("representative", "uncertain"):
        return "neutral_report"
    return "other"


def communicative_goal(f: dict) -> str:
    if f["selection"] == "fabricated" or (f["belief"] == "low" and f["selection"] == "cherry"):
        return "mislead"
    if f["selection"] == "uncertain" and f["belief"] == "high" and f["support"] == "high":
        return "conceal"
    if f["arousal_goal"] == "high" or f["action_goal"] == "present":
        return "warn"
    return "inform"


def make_source_world(lid: str, domain: str, hidden_override: dict | None = None) -> dict:
    """One notice or memo. The pool of six prior cases realizes the support level (five
    or one of six bear the claim out); what the source SHOWS realizes the selection rule;
    the arousal comparison, the call, and the register are surface factors; private
    belief and willingness to correct are hidden and realized only as behaviors the
    reader is asked to predict. `hidden_override` builds the collision twin: identical
    surface, hidden factors flipped."""
    code = enumerate_identity(lid, SURFACE_SPACE, f"source|{domain}", blocks=3)
    hcode = balanced_code(lid, HIDDEN_SPACE, f"hidden|{domain}")
    f = decode(code, hcode)
    if hidden_override:
        f.update(hidden_override)
    rng = _rng(lid, "source")
    thing, claim, use, private_act = TOPICS[domain][f["topic_i"]]
    n_true = 5 if f["support"] == "high" else 1
    outcomes = ["confirmed"] * n_true + ["not confirmed"] * (POOL_N - n_true)
    rng.shuffle(outcomes)
    places = rng.sample(CASE_PLACES[domain], POOL_N + 1)
    pool = [{"i": i, "place": places[i], "outcome": o} for i, o in enumerate(outcomes)]
    fab_place = places[POOL_N]
    sel = f["selection"]
    if sel == "representative":
        shown = rng.sample(pool, SHOW_N)
    elif sel == "cherry":
        conf = [c for c in pool if c["outcome"] == "confirmed"]
        shown = conf[:SHOW_N] if len(conf) >= SHOW_N else conf + [{"i": -1, "place": "others", "outcome": "confirmed", "vague": True}]
    elif sel == "fabricated":
        conf = [c for c in pool if c["outcome"] == "confirmed"]
        shown = [{"i": -2, "place": fab_place, "outcome": "confirmed", "fabricated": True}] + conf[:1]
    else:
        shown = []
    if sel == "uncertain":
        evidence = "Reports of it vary and none is settled."
    else:
        parts = []
        for c in shown:
            if c.get("vague"):
                parts.append("and others besides")
            else:
                parts.append(f"at {c['place']} the same fault was {'borne out' if c['outcome'] == 'confirmed' else 'not borne out'}")
        evidence = "Of the cases known: " + "; ".join(parts) + "."
    cmp_place = rng.choice(CASE_PLACES[domain])
    if domain == "memo" and cmp_place.startswith("the "):
        cmp_place = cmp_place[4:]
    comparison = (ALARM_LINE if f["arousal_goal"] == "high" else CALM_LINE)[domain].format(p=cmp_place)
    lead, close = INTENSE[f["intensity"]]
    call = CALL_LINE[domain] if f["action_goal"] == "present" else ""
    text = f"{lead}Concerning {thing}: {claim}. {evidence} {comparison} {close} {call}".replace("  ", " ").strip()
    # behaviors the reader predicts (hidden factors realized as construction facts)
    return {"lineage_id": lid, "domain": domain, "factors": f, "region": region(f),
            "communicative_goal": communicative_goal(f), "thing": thing, "claim": claim, "use": use,
            "pool": pool, "shown": shown, "text": text, "surface_key": text,
            "private_action_text": private_act,
            # counterevidence is counterevidence whatever the support: a later survey that
            # contradicts the claim; the hidden factor is what the source does about it
            "counterevidence": f"A later independent survey of {thing} found the claim overstated and not borne out.",
            "audience_goal": ("alarm" if f["arousal_goal"] == "high" else "calm") + ("_act" if f["action_goal"] == "present" else "_only"),
            "appraisal": ("believed" if f["belief"] == "high" else "doubted") + ("_grave" if f["intensity"] == "high" else "_mild"),
            "true_advice": (f["support"] == "high"),
            "twin": bool(hidden_override)}


def collision_twin(world: dict) -> dict:
    f = world["factors"]
    flipped = {"belief": "low" if f["belief"] == "high" else "high",
               "correction": "low" if f["correction"] == "high" else "high"}
    return make_source_world(world["lineage_id"], world["domain"], hidden_override=flipped)


def history_block(lid: str, domain: str, reliable: bool) -> str:
    """A05: three earlier notices from the same source with their revealed outcomes."""
    rng = _rng(lid, "history")
    topics = rng.sample(range(8), 3)
    truths = [True, True, True] if reliable else [True, False, False]
    rng.shuffle(truths)
    lines = []
    for t, ok in zip(topics, truths):
        thing, claim, _, _ = TOPICS[domain][t]
        lines.append(f"- It once said of {thing} that {claim}; that {'proved right' if ok else 'proved wrong'}.")
    return "The same source's earlier notices, and how they turned out:\n" + "\n".join(lines)


def fresh_pool_text(lid: str, domain: str) -> tuple[str, list]:
    """A02: a fresh opportunity pool the READER sees in full, to predict what the source
    would show from it."""
    rng = _rng(lid, "freshpool")
    places = rng.sample(CASE_PLACES[domain], POOL_N)
    outs = ["confirmed", "confirmed", "not confirmed", "not confirmed", "confirmed", "not confirmed"]
    rng.shuffle(outs)
    pool = [{"place": p, "outcome": o} for p, o in zip(places, outs)]
    text = "Suppose the source now had these six new cases in hand: " + "; ".join(
        f"{c['place']} ({'borne out' if c['outcome'] == 'confirmed' else 'not borne out'})" for c in pool) + "."
    return text, pool


def self_test(n: int = 96) -> None:
    for domain in SOURCE_DOMAINS:
        seen = set()
        levels = {k: set() for k in FACTORS}
        regions = set()
        for i in range(n):
            lid = f"A01|{domain}|s{i % 3}|w{i:04d}|discovery"
            w = make_source_world(lid, domain)
            # roots are distinct by CONTENT (factors and text); two roots may share a surface
            # (a representative pick that happens to be all-confirming reads like a cherry
            # pick; under the uncertain selection nothing is shown at all), which is a
            # construction fact I03 counts and A02's behavior prediction is built for
            key = w["text"] + "|" + "|".join(f"{k}={v}" for k, v in sorted(w["factors"].items()))
            assert key not in seen, (domain, i)
            seen.add(key)
            for k in FACTORS:
                levels[k].add(w["factors"][k])
            regions.add(w["region"])
            t = collision_twin(w)
            assert t["text"] == w["text"], "twin surface differs"
            assert t["factors"]["belief"] != w["factors"]["belief"] and t["factors"]["correction"] != w["factors"]["correction"]
            for hid in HIDDEN:
                assert w["factors"][hid] not in w["text"].split(), "a hidden level word is in the surface"
            assert w["region"] in ("honest_warning", "sincere_fanatic", "strategic_propagandist", "neutral_report", "other")
            assert w["communicative_goal"] in COMM_GOALS
            if w["factors"]["selection"] == "fabricated":
                assert any(c.get("fabricated") for c in w["shown"])
        for k, lv in levels.items():
            assert len(lv) == len(FACTORS[k]), (domain, k, lv)
        assert {"honest_warning", "sincere_fanatic", "strategic_propagandist", "neutral_report"} <= regions or n < 96, (domain, regions)
        raised = False
        try:
            make_source_world(f"A01|{domain}|s0|w{SURFACE_SPACE // 3:04d}|discovery", domain)
        except ValueError:
            raised = True
        assert raised
    print(f"s5_sources self-tests pass: {2 * n} source worlds, twins surface-identical, factors live, regions populated")


if __name__ == "__main__":
    self_test()
