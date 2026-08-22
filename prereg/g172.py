"""G172 (Phase 2.4 root P24-S0) — the creator-reader similarity matrix: are outputs easier
to invert when the reader is the exact maker checkpoint, a same-family sibling, or a
cross-family model, on goals whose realization is verified mechanically at accept time?

Construction. Four open-weight makers (two families, two checkpoints each) generate short
informative paragraphs under assigned entity-and-order goals: mention A first and B later,
avoid C and D, from a per-topic four-entity pool. All four candidate goals for a topic name
ALL FOUR entities (the avoid clause names the excluded pair), so the candidate set is
lexically matched and discrimination requires relating roles to the artifact, never spotting
words. Realization is verified inside the generation accept loop (LESSONS §3, assigned is not
realized: word-boundary presence of A and B in order, absence of C and D, length band,
anti-echo guard), so every accepted artifact carries a mechanically TRUE goal — the
process-aware ceiling is 1.0 by construction and the corpus needs no adjudicator.

Reading. Nine readers score each artifact against its four candidates with the
conditional-likelihood reader (neutral-subtracted mean per-token log-probability — the
non-generative form Wing G's HURTS verdict mandates). Raw likelihoods never cross
tokenizers; every statistic is within-reader (margin, rank, top-1).

DESIGN CHECK (2026-08-22, at design time). Lessons read for this design: LESSONS §3
(assigned-is-not-realized L137, accept-time verification L156, known-answer rulers, floors
follow marginals, exhaustive bands, failure directions), §4 (record environment versions,
determinism pins), §5 (produces guards, gpulock once per invocation, manifests withheld
below 90 percent yield, 2-3x runtime underestimates). Gates, each with null and alternative
and the guarded failure direction:

    YIELD: >= 90 percent of (maker, topic, goal, trial) cells filled within the attempt
      budget, else the manifest is withheld and the stage fails for retry. Null: base models
      may not comply; failure direction DOWN (thin corpus frozen by a premature manifest —
      the L108/2026-08-17 class). One predeclared repair: redraw the one-shot example and
      raise attempts to 24 for the failing maker; a second failure retires that maker from
      the matrix rather than lowering the bar.
    KNOWN-ANSWER (per reader): on 16 echo probes (condition quotes the artifact's own first
      sentence vs three other artifacts' first sentences) top-1 >= 0.90. Under the null of a
      broken scorer this sits at 0.25; failure direction DOWN means the reader's scores are
      noise and its matrix row is uninterpretable (INSTRUMENT-FAIL for that reader).
    EXACT-EQUIVALENCE (per reader): a duplicated candidate ties itself within 1e-6 on 8
      probes. Any spread is nondeterminism in the plumbing; failure direction ANY.
    SHUFFLE FLOOR (per reader): with candidate labels shuffled within topic, pooled top-1
      inside [0.15, 0.35] around the 0.25 chance floor. Failure direction UP means a leak
      in scoring or assembly (the truth reachable without the candidate content).

Primary statistic, frozen: the per-artifact MARGIN = score(true candidate) minus the mean
of the three decoys, per reader. Relation cells: EXACT (reader is the maker checkpoint),
SIBLING (same family, different checkpoint, instruct variant included), CROSS (different
family). Predeclared contrasts, pooled over makers, paired per artifact, sign-flip
permutation with 20000 draws at seed SEED0+9:

    C1: margin(EXACT) - mean margin(CROSS)     per artifact
    C2: mean margin(SIBLING) - mean margin(CROSS)

Verdict bands, exhaustive:
    SIMILARITY-GRADED   C1 > 0 at p < 0.05 AND C2 > 0 at p < 0.05
    EXACT-ONLY          C1 > 0 at p < 0.05, C2 not
    FLAT                neither contrast at p < 0.05 (the null expectation: mechanically
                        decidable goals may read equally in likelihood space for everyone)
    REVERSED            C1 < 0 at p < 0.05 (stronger cross-family readers win; the capacity
                        world, routed to E24-S05, never suppressed)

What this card does NOT adjudicate, by declaration: fingerprint-vs-organization (that is
E24-S02 trace erasure, which inflates C1/C2 UP and is the standing rival for any positive);
capacity (reported as a covariate, adjudicated in E24-S05); any human claim (context §9's
licensed-claim boundary). Routing on each band is context §9's table, binding.
"""

from __future__ import annotations

import re

SEED0 = 17200

MAKERS = [
    "Qwen/Qwen2.5-0.5B",
    "Qwen/Qwen2.5-1.5B",
    "EleutherAI/pythia-410m",
    "EleutherAI/pythia-1.4b",
]

READERS = MAKERS + [
    "Qwen/Qwen2.5-3B",
    "EleutherAI/pythia-2.8b",
    "openai-community/gpt2-large",
    "HuggingFaceTB/SmolLM2-1.7B",
    "Qwen/Qwen2.5-1.5B-Instruct",
]

FAMILY = {
    "Qwen/Qwen2.5-0.5B": "qwen", "Qwen/Qwen2.5-1.5B": "qwen", "Qwen/Qwen2.5-3B": "qwen",
    "Qwen/Qwen2.5-1.5B-Instruct": "qwen",
    "EleutherAI/pythia-410m": "pythia", "EleutherAI/pythia-1.4b": "pythia",
    "EleutherAI/pythia-2.8b": "pythia",
    "openai-community/gpt2-large": "gpt2", "HuggingFaceTB/SmolLM2-1.7B": "smollm",
}


def short(name: str) -> str:
    return name.split("/")[-1].replace(".", "").replace("-", "_").lower()


def relation(maker: str, reader: str) -> str:
    if maker == reader:
        return "exact"
    if FAMILY[maker] == FAMILY[reader]:
        return "sibling"
    return "cross"


# topic -> four-entity pool [e1, e2, e3, e4]; goals pair (e1,e2) or (e3,e4) in both orders
TOPICS = [
    ("gardening", ["compost", "mulch", "pruning", "watering"]),
    ("cycling", ["helmet", "gears", "tires", "brakes"]),
    ("cooking", ["garlic", "onions", "simmering", "seasoning"]),
    ("astronomy", ["telescope", "nebula", "craters", "orbit"]),
    ("swimming", ["breathing", "kicking", "goggles", "laps"]),
    ("carpentry", ["sawing", "sanding", "varnish", "joints"]),
    ("photography", ["aperture", "shutter", "tripod", "lighting"]),
    ("camping", ["tent", "campfire", "lantern", "trail"]),
]

N_GOALS = 4          # (pair 1-2, order AB), (pair 1-2, order BA), (pair 3-4, AB), (pair 3-4, BA)
TRIALS = 2
ATTEMPTS = 16
WORD_BAND = (50, 190)
TEMPERATURE = 0.8
TOP_P = 0.95
MAX_NEW_TOKENS = 230

# one-shot example: its topic and entities never appear in TOPICS
_EXAMPLE = (
    "Example task: Write one short informative paragraph about bread baking. The paragraph "
    "must mention yeast first and kneading later, and must not mention crust or oven.\n\n"
    "Example paragraph: Good bread starts with yeast, which needs warm water and a little "
    "sugar to wake up. Once the dough comes together, kneading develops the gluten that gives "
    "the loaf its structure, and patient resting lets the flavor deepen fully.\n\n"
)


def goal_entities(topic_i: int, goal_i: int) -> tuple[str, str, list[str]]:
    """(first_entity, later_entity, avoid_pair) for one goal cell."""
    pool = TOPICS[topic_i][1]
    pair, order = divmod(goal_i, 2)
    a, b = (pool[0], pool[1]) if pair == 0 else (pool[2], pool[3])
    if order == 1:
        a, b = b, a
    avoid = [pool[2], pool[3]] if pair == 0 else [pool[0], pool[1]]
    return a, b, avoid


def gen_prompt(topic_i: int, goal_i: int) -> str:
    topic = TOPICS[topic_i][0]
    a, b, avoid = goal_entities(topic_i, goal_i)
    task = (f"Task: Write one short informative paragraph about {topic}. The paragraph must "
            f"mention {a} first and {b} later, and must not mention {avoid[0]} or {avoid[1]}.")
    return f"{task}\n\n{_EXAMPLE}Now the task again: {task}\n\nParagraph:"


def candidate(topic_i: int, goal_i: int) -> str:
    """Reading condition; all four candidates for a topic name all four entities."""
    a, b, avoid = goal_entities(topic_i, goal_i)
    return (f"This passage was written to bring up {a} first and {b} later, "
            f"while leaving out {avoid[0]} and {avoid[1]}.")


def _pos(word: str, text: str) -> int:
    m = re.search(r"\b" + re.escape(word.rstrip("s")) + r"\w*", text, re.IGNORECASE)
    return m.start() if m else -1


def realized(text: str, topic_i: int, goal_i: int) -> bool:
    """Accept-time verification: A before B, no avoid entities, band, anti-echo."""
    a, b, avoid = goal_entities(topic_i, goal_i)
    words = len(text.split())
    if not (WORD_BAND[0] <= words <= WORD_BAND[1]):
        return False
    low = text.lower()
    if "must mention" in low or "must not mention" in low or "task:" in low:
        return False
    pa, pb = _pos(a, text), _pos(b, text)
    if pa < 0 or pb < 0 or pa >= pb:
        return False
    return all(_pos(w, text) < 0 for w in avoid)


BANDS = ("SIMILARITY-GRADED", "EXACT-ONLY", "FLAT", "REVERSED")
N_PERMUTATIONS = 20000
ALPHA = 0.05
YIELD_FLOOR = 0.90
KNOWN_ANSWER_FLOOR = 0.90
SHUFFLE_BAND = (0.15, 0.35)
TIE_TOL = 1e-6
