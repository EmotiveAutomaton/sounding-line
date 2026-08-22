"""G174 (Phase 2.4 root P24-A0) — the open-weight causal emotion-concept ruler: does a small
open model carry abstract, cross-context affect representations that causally influence a
benign behavior, under honest controls?

The reproduction target is bounded (context §2.1): the published result reports abstract
emotion representations in a frontier model that generalize beyond emotion words and causally
influence behavior. At 1.5B the expected outcome is honestly open; a decoding-only or
lexical-only result routes as the card's own bands say and is an instrument boundary, never
evidence against the human theory (context §9's G174 routing, binding).

Construction. Directions are fitted from EXPLICIT emotion-word sentences only, then tested on
SCRUBBED situations that contain no word from the frozen emotion lexicon (asserted at load),
under three actor frames. That split is the abstractness claim: a lexical feature fitted on
emotion words has nothing to match in the scrubbed set, while an abstract representation
should transfer. The causal half amplifies or ablates the fear and joy directions during
reading of ambiguous scenarios and measures the shift between matched approach and withdraw
continuations — a benign preference, no harmful-behavior reproduction (context §9).

DESIGN CHECK (2026-08-22, at design time). Lessons read: LESSONS §3 (validate the ruler on
known answers first; the criterion must be able to fail; shuffled-label nulls; exhaustive
bands with failure directions; n<<d caution), §4 (record versions; determinism pins;
assert-what-was-measured), §5 (produces guards, gpulock once, runtime underestimates).
Gates, each with null and alternative and the guarded direction:

    LEXICON: no scrubbed situation contains a lexicon word (load-time assertion; a leak
      voids the abstractness claim before any model call). Failure direction: any hit.
    DECODING: six-class accuracy on held-out scrubbed situations (argmax over concept
      projections at the dev-selected block) must exceed BOTH the shuffled-label null's
      95th percentile AND the lexical baseline (bag-of-words logistic fitted on the same
      explicit set, applied to the same scrubbed test set). Null expectation: lexical
      baseline near chance on scrubbed text (nothing to match), directions at chance if
      the representation is lexical. Failure DOWN = no abstract representation readable
      at this scale (band DECODES-NOT).
    ACTOR/TOPIC TRANSFER: accuracy within 0.15 of the unframed scrubbed accuracy under
      each actor frame. Failure DOWN = actor-position feature, not situation affect.
    CAUSAL SIGN PAIR (fear, joy separately): amplification moves the continuation
      preference in the frozen direction (fear: toward withdraw; joy: toward approach)
      with paired permutation p < 0.05 over the 12 scenarios; ablation moves opposite in
      sign (its p reported, sign required). Null: no movement. Failure directions: no
      movement = no causal use at this dose range; movement WITHOUT the opposite-sign
      ablation = dose artifact, not a usable handle.
    CONTROL QUIET: rank-matched random-orthonormal and shuffled-label bases move the same
      preference by less than half the affect basis's absolute effect. Failure UP (controls
      move comparably) = generic steering, band GENERIC.
    CAPABILITY: mean per-token log-probability on eight neutral passages changes by less
      than 5 percent under the operating dose. Failure = capability lesion; one predeclared
      repair (halve the dose), then stop.
    SECOND SEED: the full battery repeats at SEED_B (fresh dev/test split and permutation
      stream); the causal sign pair must hold in both seeds to claim the band.

Verdict bands, exhaustive: RULER-STANDS (decoding + transfer + causal + controls + both
seeds) · DECODES-ONLY (decoding and transfer pass, causal fails) · LEXICAL-ONLY (decoding
fails against the lexical baseline or transfer fails) · GENERIC (controls move) ·
INSTRUMENT-FAIL (a load-time or capability gate fails). Block choice and dose are selected
on the dev split only, by the frozen rule: the block with the highest dev decoding accuracy;
the smallest dose whose dev causal effect is nonzero. One repair total, named above.
"""

from __future__ import annotations

MODEL = "Qwen/Qwen2.5-1.5B"
SEED_A = 17400
SEED_B = 17401
CONCEPTS = ("fear", "anger", "sadness", "joy", "disgust", "surprise")
DOSES = (1.0, 2.0, 4.0)         # amplification alpha grid, dev-selected; ablation runs at 1.0
DEV_PER_CONCEPT = 3             # scrubbed situations per concept in dev; the rest are test

LEXICON = frozenset("""
fear afraid scared scare terrified terror dread anxious anxiety panic worried worry frighten
frightened horror angry anger furious fury rage mad outraged outrage irritated annoyed resent
resentful sad sadness sorrow sorrowful grief grieving mourn mourning heartbroken depressed
gloomy unhappy joy joyful happy happiness delighted delight glad cheerful thrilled excited
excitement elated disgust disgusted disgusting revolted revolting gross nauseous nausea
nauseated sicken sickened surprise surprised surprising astonished astonish amazed amazement
shocked shock stunned emotion emotional feeling feelings
""".split())

SCRUBBED = {
    "fear": [
        "The brakes felt soft as the car picked up speed on the long hill.",
        "Halfway across the old rope bridge, several planks shifted under his weight.",
        "The doctor called after hours and asked her to come in first thing tomorrow.",
        "Something large moved in the water just beyond where the children were swimming.",
        "The smoke detector went off at two in the morning, and the hallway smelled of burning.",
        "Footsteps followed her turn for turn through the empty parking garage.",
        "The pilot announced they would attempt the landing despite the strong crosswind.",
        "His hands would not stop trembling as he opened the letter from the court.",
    ],
    "anger": [
        "The contractor paved over the garden she had spent ten years building, without asking.",
        "He discovered his coworker had presented the project as entirely his own work.",
        "The referee waved off the goal after the whistle had clearly sounded late.",
        "Someone had parked across both accessible spaces again, engine idling.",
        "The landlord kept the whole deposit and stopped answering calls.",
        "Her little brother read her diary aloud at the dinner table.",
        "The committee cut the program's funding and spent it on new office furniture.",
        "The driver sped through the puddle, soaking the schoolchildren, and drove on.",
    ],
    "sadness": [
        "The house sold quickly, and the new owners cut down the oak his father had planted.",
        "She kept the leash by the door for weeks after the old dog was gone.",
        "The last letter arrived a day after the funeral.",
        "The playground where they had met was fenced off and scheduled for demolition.",
        "He set the table for two out of habit, then quietly put one plate back.",
        "The choir sang her mother's most loved hymn at the service.",
        "The photographs in the flood-damaged album would not come apart without tearing.",
        "Her closest friend's moving truck pulled away just before the streetlights came on.",
    ],
    "joy": [
        "The acceptance letter arrived on her birthday, with a scholarship attached.",
        "After two years away, his daughter walked through the arrivals gate.",
        "The test came back clear, and the doctor shook both their hands.",
        "The whole street came out to welcome the family's new baby home.",
        "She fit into her grandmother's wedding dress on the first try.",
        "The rescue dog rolled over and over in the grass of its first real yard.",
        "The band called his name to come up and play the encore with them.",
        "The rain finally came after the long dry season, and the farmers stood out in it.",
    ],
    "disgust": [
        "The milk had curdled into lumps, and he had already taken a large swallow.",
        "Under the sink, the leak had grown a slick black film across the boards.",
        "The kitchen inspection found mouse droppings in the flour bins.",
        "She lifted the couch cushion and found month-old food fused to the fabric.",
        "The restroom floor was wet, and the sole of her shoe stuck slightly with each step.",
        "The refrigerator at the rental had been left full and unplugged all summer.",
        "He bit into the apple and found half a worm in the remaining piece.",
        "The dumpster behind the restaurant leaked something dark across the sidewalk.",
    ],
    "surprise": [
        "She opened the front door and forty people stood silently in her living room.",
        "The vending machine dropped twelve bars instead of one.",
        "His quiet accountant handed in a resignation and a plane ticket to Patagonia.",
        "The number drawn on the radio matched the ticket taped to their refrigerator.",
        "The statue in the town square turned out to be a living performer.",
        "Mid-lecture, the professor's identical twin walked in and continued the sentence.",
        "The old painting from the attic was signed by a name from the textbooks.",
        "He turned the key of the junkyard car and the engine started at once.",
    ],
}

EXPLICIT_WORDS = {
    "fear": ["afraid", "frightened", "terrified", "anxious"],
    "anger": ["angry", "furious", "outraged", "resentful"],
    "sadness": ["sad", "heartbroken", "sorrowful", "gloomy"],
    "joy": ["happy", "delighted", "joyful", "thrilled"],
    "disgust": ["disgusted", "revolted", "sickened", "nauseated"],
    "surprise": ["surprised", "astonished", "amazed", "stunned"],
}


def explicit_sentences(concept: str) -> list[str]:
    out = []
    for w in EXPLICIT_WORDS[concept]:
        out.append(f"She felt deeply {w} about what had just happened.")
        out.append(f"He told his friend the news had left him completely {w}.")
    return out


ACTOR_FRAMES = ("", "This happened to me last year: ", "Imagine this is happening to you right now: ")

# causal half: ambiguous scenario, (approach continuation, withdraw continuation)
SCENARIOS = [
    ("A letter with no return address sat on the doorstep.",
     "She opened it right away.", "She left it where it lay."),
    ("The path split, one branch leading down into the dark trees.",
     "He took the shaded branch.", "He turned back toward the road."),
    ("A stranger at the bus stop offered to share his umbrella.",
     "She stepped under it and said thanks.", "She said no and moved down the bench."),
    ("The old elevator doors opened with a long creak.",
     "He stepped in and pressed the button.", "He took the stairs instead."),
    ("The phone rang from an unknown number at midnight.",
     "She answered on the second ring.", "She let it ring through."),
    ("A dog with no collar trotted up to the picnic table.",
     "He held out his hand to it.", "He picked up the food and stepped away."),
    ("The neighbors invited them to the party through the fence.",
     "They walked over that evening.", "They said another time, maybe."),
    ("A box marked with her name waited at the post office counter.",
     "She signed for it and opened it there.", "She asked the clerk to hold it a few days."),
    ("The water in the cove was still and very deep.",
     "He dove in from the low rock.", "He stayed on the sand and watched."),
    ("A new colleague asked him to join the lunch table.",
     "He carried his tray over.", "He said he had work to finish."),
    ("The cellar door stood open, the light switch just inside.",
     "She reached in and flipped the switch.", "She closed the door and bolted it."),
    ("The roller coaster line was suddenly short.",
     "They jumped in line for the front car.", "They wandered toward the carousel."),
]

# frozen causal predictions: concept -> preference direction under AMPLIFICATION
CAUSAL_PREDICTIONS = {"fear": "withdraw", "joy": "approach"}

NEUTRAL_PASSAGES = [
    "The library reopens at nine on weekdays and closes at six.",
    "Copper conducts electricity better than iron at room temperature.",
    "The recipe calls for two cups of flour and one of water.",
    "Most commuter trains on this line stop at every station before noon.",
    "The bridge was repainted last spring and inspected in the fall.",
    "A standard chessboard has sixty-four squares in eight rows.",
    "The museum's east wing holds the maps and the west wing the pottery.",
    "Rainfall this month measured slightly above the ten-year average.",
]

TRANSFER_TOL = 0.15
CONTROL_RATIO = 0.5
CAPABILITY_TOL = 0.05
N_SHUFFLES = 200
N_PERMUTATIONS = 20000
ALPHA_P = 0.05
BANDS = ("RULER-STANDS", "DECODES-ONLY", "LEXICAL-ONLY", "GENERIC", "INSTRUMENT-FAIL")


def assert_lexicon_clean() -> None:
    import re
    for concept, sents in SCRUBBED.items():
        for s in sents:
            for w in re.findall(r"[a-z]+", s.lower()):
                assert w not in LEXICON, f"lexicon leak: {w!r} in {concept}: {s}"
    for _, (sc, a, wd) in enumerate(SCENARIOS):
        for text in (sc, a, wd):
            for w in re.findall(r"[a-z]+", text.lower()):
                assert w not in LEXICON, f"lexicon leak in scenario: {w!r} in {text}"
