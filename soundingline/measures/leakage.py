"""The leaked layer, measured from function words rather than from a model's opinion.

── WHY THIS IS NOT ANOTHER PROMPT ────────────────────────────────────────────────────────────

`docs/theory/LEAKAGE.md`. Function words — pronouns, articles, prepositions, conjunctions,
auxiliaries, negations, quantifiers — are:

  * produced NON-CONSCIOUSLY, which is why authorship attribution works at all;
  * topic-independent, so they survive a change of subject;
  * very hard to fake, which is why they defeat forgery;
  * under 0.1% of vocabulary and about 60% of tokens used;
  * and they track psychological STATE, not only identity — first-person-singular frequency
    predicts depression better than negative-emotion words do, and liars use fewer first-person
    singulars and fewer exclusives.

Content-word choice is the deliberate layer. Function words are not chosen in the same sense.

**So stage E cannot reach the leaked layer.** Asking a language model *what stance is performed*
returns a content-word judgement on both of its outputs. That is an emblematic instrument, and no
rewording changes it. This module is the other half.

── WHAT THIS DOES NOT DO ─────────────────────────────────────────────────────────────────────

**It does not emit affect labels.** `docs/theory/AFFECT_LITERATURE.md` established that no
published mapping exists from primary-process affective systems to textual signatures, and this
module is not going to invent one silently. It emits a FEATURE VECTOR and deviations from a
baseline. Mapping that vector to the family's eight values is a separate, supervised problem, and
it is exactly what option D exists to do properly.

That restraint is the point. The vector is also what D needs as its emission model, so building
the honest version and building the useful version are the same work.

── THE BASELINE PROBLEM, STATED ──────────────────────────────────────────────────────────────

A raw function-word rate means nothing on its own: registers differ more than makers do. Every
quantity here is therefore a DEVIATION from a supplied baseline, and the caller has to say what
the baseline is. Two honest options:

  * the corpus mean — answers "unusual for this collection"
  * one maker's other artifacts — answers "unusual for this person", which is the real question
    and which needs a corpus organised by maker that this project does not have

The second is better and is not yet available. Recorded rather than glossed.
"""

from __future__ import annotations

import math
import re
import statistics
from dataclasses import dataclass, field

_TOKEN = re.compile(r"[a-z][a-z']*")

# ── The categories ────────────────────────────────────────────────────────────────────────────
#
# Hand-written from the published psycholinguistic categories rather than imported: LIWC's
# dictionaries are licensed, and a category list a reader can audit in the file is worth more here
# than one behind a paywall. These are the well-attested function-word classes, and the specific
# ones with documented state effects are marked.
CATEGORIES: dict[str, frozenset[str]] = {
    # THE MOST DOCUMENTED SINGLE SIGNAL. `I`-frequency tracks depression, low status, and honesty,
    # and does so better than negative-emotion words.
    "i": frozenset("i me my mine myself i'm i've i'd i'll".split()),
    "we": frozenset("we us our ours ourselves we're we've we'd we'll".split()),
    "you": frozenset("you your yours yourself yourselves you're you've you'd you'll".split()),
    "shehe": frozenset("he him his himself she her hers herself he's she's".split()),
    "they": frozenset("they them their theirs themselves they're they've they'd".split()),
    "impersonal": frozenset("it its itself this that these those there something anything "
                            "nothing everything someone anyone no-one everyone".split()),
    "article": frozenset("a an the".split()),
    "prep": frozenset("about above across after against along among around at before behind "
                      "below beneath beside between beyond by down during for from in inside "
                      "into near of off on onto out outside over past through to toward under "
                      "until up upon with within without".split()),
    "conj": frozenset("and or but so because although though while whereas since unless if "
                      "then therefore thus however moreover furthermore nevertheless".split()),
    "auxverb": frozenset("am is are was were be been being have has had do does did will "
                         "would shall should can could may might must".split()),
    "negation": frozenset("no not never none nor neither cannot can't don't doesn't didn't "
                          "won't wouldn't shouldn't couldn't isn't aren't wasn't weren't "
                          "hasn't haven't hadn't without".split()),
    # EXCLUSIVES. Documented in the deception literature: liars use FEWER of these, because
    # excluding a possibility requires having modelled it.
    "exclusive": frozenset("but except without exclude excluding unless rather instead "
                           "although however whereas otherwise".split()),
    "tentative": frozenset("maybe perhaps possibly probably seem seems seemed likely unlikely "
                           "somewhat rather guess suppose apparently arguably roughly "
                           "approximately might could".split()),
    "certainty": frozenset("always never all every none absolutely certainly definitely clearly "
                           "obviously must undoubtedly entirely completely totally".split()),
    "quantifier": frozenset("many much more most less least few several some any enough lot "
                            "lots plenty little".split()),
    "comparison": frozenset("than as like unlike similar similarly greater smaller better worse "
                            "best worst same different".split()),
    # CAUSAL and INSIGHT: the cognitive-process categories. Not function words strictly, but they
    # are produced with about as little deliberation and they are the closest thing here to a
    # marker of reasoning actually happening rather than being reported.
    "causal": frozenset("because cause caused causes effect since therefore thus hence "
                        "consequently result results resulting leads led".split()),
    "insight": frozenset("think thought know knew realise realised realize realized understand "
                         "understood consider considered notice noticed found figure figured "
                         "wonder wondered".split()),
}

# Signals with a documented direction, kept separate from the raw categories so nobody mistakes
# the rest for validated psychology.
DOCUMENTED = ("i", "exclusive", "negation", "certainty", "tentative")


@dataclass(frozen=True)
class FunctionProfile:
    """Rates per 1,000 tokens, plus the raw counts that produced them."""
    n_tokens: int
    rates: dict[str, float]
    counts: dict[str, int] = field(default_factory=dict)

    def vector(self, keys: tuple[str, ...] | None = None) -> list[float]:
        ks = keys or tuple(sorted(self.rates))
        return [self.rates.get(k, 0.0) for k in ks]


def profile(text: str) -> FunctionProfile:
    """Function-word rates for one artifact.

    Tokenised on lowercase alphabetic runs including apostrophes, so contractions survive — the
    contraction rate is itself one of the more stable stylistic markers and splitting `don't` into
    `don` and `t` would destroy it.
    """
    toks = _TOKEN.findall(text.lower())
    n = len(toks)
    counts = {name: 0 for name in CATEGORIES}
    for t in toks:
        for name, words in CATEGORIES.items():
            if t in words:
                counts[name] += 1
    scale = max(n, 1) / 1000.0
    return FunctionProfile(n_tokens=n,
                           rates={k: v / scale for k, v in counts.items()},
                           counts=counts)


@dataclass(frozen=True)
class Baseline:
    """Per-category mean and spread over a reference set."""
    mean: dict[str, float]
    sd: dict[str, float]
    n: int

    @classmethod
    def over(cls, texts) -> "Baseline":
        profs = [profile(t) for t in texts]
        if len(profs) < 3:
            raise ValueError("a baseline over fewer than three artifacts is not a baseline")
        mean, sd = {}, {}
        for k in CATEGORIES:
            vals = [p.rates[k] for p in profs]
            mean[k] = statistics.fmean(vals)
            sd[k] = statistics.pstdev(vals)
        return cls(mean=mean, sd=sd, n=len(profs))


@dataclass(frozen=True)
class Leakage:
    """One artifact against a baseline. Signed z per category, and how far out it sits overall.

    `magnitude` is Euclidean distance in z-space — how unusual this artifact's non-conscious
    profile is, without saying in which direction. It is NOT an affect reading and must not be
    reported as one.
    """
    z: dict[str, float]
    magnitude: float
    documented: dict[str, float]

    def most_deviant(self, k: int = 3) -> list[tuple[str, float]]:
        return sorted(self.z.items(), key=lambda kv: -abs(kv[1]))[:k]


# Below this, a category's spread is too small for a z-score to mean anything and it is skipped
# rather than producing an enormous number from a rounding difference.
_MIN_SD = 1e-6


def leakage(text: str, baseline: Baseline) -> Leakage:
    p = profile(text)
    z = {}
    for k in CATEGORIES:
        sd = baseline.sd.get(k, 0.0)
        if sd <= _MIN_SD:
            continue
        z[k] = (p.rates[k] - baseline.mean[k]) / sd
    mag = math.sqrt(sum(v * v for v in z.values())) / math.sqrt(max(len(z), 1))
    return Leakage(z=z, magnitude=mag,
                   documented={k: z[k] for k in DOCUMENTED if k in z})


def separability(groups: dict[str, list[str]]) -> dict:
    """D-0's statistic: do function-word vectors separate these groups?

    Between-group variance over within-group variance, per category, and averaged. This is a crude
    F-like ratio and it is deliberately crude — D-0 is a go/no-go, not a result. A ratio near 1
    means the categories carry no group information and the feature channel is wrong.

    Reported per category as well as aggregated, because "which categories carry the signal" is the
    thing that tells you whether the answer is real or an artefact of length.
    """
    profs = {g: [profile(t) for t in ts] for g, ts in groups.items() if len(ts) >= 2}
    if len(profs) < 2:
        raise ValueError("separability needs at least two groups with two artifacts each")

    out = {}
    for k in CATEGORIES:
        per_group = {g: [p.rates[k] for p in ps] for g, ps in profs.items()}
        grand = statistics.fmean([v for vs in per_group.values() for v in vs])
        between = statistics.fmean([(statistics.fmean(vs) - grand) ** 2
                                    for vs in per_group.values()])
        within = statistics.fmean([statistics.pvariance(vs) for vs in per_group.values()])
        out[k] = between / within if within > _MIN_SD else float("inf")

    finite = [v for v in out.values() if math.isfinite(v)]
    return {
        "per_category": out,
        "mean_ratio": statistics.fmean(finite) if finite else float("nan"),
        "n_groups": len(profs),
        "n_per_group": {g: len(ps) for g, ps in profs.items()},
        "top": sorted(((k, v) for k, v in out.items() if math.isfinite(v)),
                      key=lambda kv: -kv[1])[:5],
    }
