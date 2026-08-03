"""The four quantities. SPEC §5, and the reading is the tuple.

    Four quantities, and the reading is the combination. None alone is sufficient.
    Report all four always — the simulation's whole methodology is that a single number invites
    the overclaim.

That last sentence is enforced by the type: `Measurement` has no single headline field, and
`may_not_claim` travels with it. There is deliberately no `.score` property, and adding one
would be a change to what the instrument claims rather than a convenience.

── WHY NONE OF THESE READS THE MODEL'S SELF-REPORT ───────────────────────────────────────────

`Reading.self_reported_confidence` exists and feeds nothing. A model asked to grade its own
explanation grades it well, and on hollow content it grades it *confidently* well — that is E2,
the project's central observation, and building the instrument on top of it would be running
the failure mode on the instrument instead of on the subject.

So fit is computed from the posterior's shape and from evidence that can be checked against the
stored artifact. The check is the important half: a probe that quotes text which is not in the
artifact has fabricated, and fabrication is measurable here rather than inferred.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from statistics import mean, pstdev

from soundingline.family.loader import load_family
from soundingline.loop.run import LoopRun


def _normalised_entropy(dist: dict[str, float]) -> float:
    """Shannon entropy over the support, scaled to [0, 1].

    Normalised by log(k) so a family with eight purposes and one with five audiences are
    comparable. 0 = all mass on one hypothesis; 1 = uniform, meaning the bounded family
    explained nothing in particular.
    """
    k = len(dist)
    if k <= 1:
        return 0.0
    h = -sum(p * math.log(p) for p in dist.values() if p > 0)
    return h / math.log(k)


def _normalise_quote(s: str) -> str:
    """Collapse whitespace and fold case before checking a quote against the artifact.

    Deliberately forgiving about whitespace and case, and unforgiving about everything else. A
    model that re-wraps a line has still seen the text; a model that paraphrases has not.
    """
    return re.sub(r"\s+", " ", s).strip().lower()


# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Fit:
    """How well the best hypothesis in the bounded family explains the artifact.

    **Low fit is the wall** (SPEC §5) — familiar surface, no recoverable maker-state behind it.
    E37: the wall is a missing inversion, not a vocabulary deficit, so fit must be able to be
    low on text the probe reads perfectly well. Every component below is therefore about
    RECOVERY, and none is about readability.

    Three components, reported separately as well as combined, because they fail differently:

    * `concentration` — did the bounded family land anywhere? Uniform posterior = no hypothesis
      in the human-shaped family explained this.
    * `grounding` — of the claims made, how many point at text that is actually there? This is
      the fabrication check and it is the one component with no charitable reading: an
      unverifiable quote was invented.
    * `support` — were decisions recovered at all, and did they name rejected alternatives?
      A "decision" with no visible alternative is a property of the artifact, not a decision.
    """
    concentration: float
    grounding: float
    support: float
    combined: float
    unverifiable_quotes: int

    # `verifiable` is a REPORTING flag, not a gate on the number. False means the reading made
    # claims and they could not be traced, so `combined` is low because the reading is
    # unsupported — as distinct from low because the artifact is empty. Both are low fit; they
    # are low for opposite reasons and a reader of the results needs to know which.
    verifiable: bool

    # Chosen, not derived, and recorded here rather than buried so it can be argued with.
    GROUNDING_FLOOR = 0.30


def fit(run: LoopRun, artifact_text: str) -> Fit:
    r = run.reading
    haystack = _normalise_quote(artifact_text)

    concentration = 1.0 - _normalised_entropy(r.purpose.distribution)

    quotes = [d.evidence for d in r.decisions] + [t.evidence for t in r.trade_offs]
    if quotes:
        # locate() is authoritative: the model supplies the quote, the code finds it. A quote
        # that cannot be located is fabrication, and that is now the only thing this can mean.
        # Graded, not binary. Each quote contributes its own similarity to the artifact, so a
        # lightly-paraphrased transcription costs a little and an invented sentence costs
        # everything. `unverifiable_quotes` still counts outright misses, which is the number
        # that means fabrication.
        located = [e.locate(artifact_text) for e in quotes]
        grounding = sum(loc[2] for loc in located if loc) / len(quotes)
        unverifiable = sum(1 for loc in located if loc is None)
    else:
        # No claims made is not the same as claims that failed to check out. An artifact from
        # which nothing was recovered has no grounding to measure, and scoring it 1.0 would
        # reward silence. Scored 0 and distinguished from fabrication by `unverifiable_quotes`.
        grounding = 0.0
        unverifiable = 0

    if r.decisions:
        # A decision must name what was NOT done. The schema requires the field to be non-empty,
        # so this catches the degenerate case where it is filled with a restatement of the
        # choice rather than an alternative.
        # A decision counts only if an alternative was actually named AND it differs from what
        # was chosen. An empty alternative is the probe reporting that nothing else was visible,
        # which under SPEC §4 means this was never a decision — so it lowers support rather than
        # invalidating the reading it appears in.
        distinct = sum(
            1 for d in r.decisions
            if d.alternative_rejected.strip()
            and _normalise_quote(d.alternative_rejected) != _normalise_quote(d.what_was_chosen)
        )
        support = distinct / len(r.decisions)
    else:
        support = 0.0

    # ── SILENCE AND FABRICATION ARE DIFFERENT, AND ONLY ONE IS A LOW GROUNDING ──────────────
    #
    # Grounding stays a component. An explanation that cannot be tied to the text IS a worse
    # explanation, and once matching became graded (Evidence.locate) a zero here means the
    # claims genuinely are not in the artifact — which is fabrication, and fit should collapse.
    #
    # What has to be separated is the case where NO claim was offered at all. An artifact from
    # which nothing was recovered has nothing to verify: its grounding is vacuous, not failed.
    # Feeding a vacuous 0.0 into the product punishes an artifact for being empty in exactly the
    # same way it punishes a reading for being invented, and those are the two states this
    # instrument exists to tell apart — the wall versus E2.
    #
    # So: claims offered -> grounding participates. No claims offered -> it drops out, and the
    # reading scores low anyway through support, which is where emptiness belongs.
    if quotes:
        combined = (concentration * grounding * support) ** (1 / 3)
    else:
        combined = (concentration * support) ** 0.5
    verifiable = (not quotes) or grounding >= Fit.GROUNDING_FLOOR
    return Fit(concentration, grounding, support, combined, unverifiable, verifiable)


# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Convergence:
    """Agreement across independent reconstructions. SPEC §5.

    The simulation's most robust finding is that hollow content produces **confident mutual
    disagreement**. Convergence needs no ground truth, which is what makes it deployable on real
    text where none exists.

    This is semantic entropy / SelfCheckGPT applied to a new object. Gate 0 §4: everyone
    measures that quantity over *factual claims*; this measures it over *intent attributions*,
    and E20 already predicts where it peaks along the readability axis (~a tenth readable).

    `confident_disagreement` is the E2 signature made into a number: high self-reported
    confidence combined with low agreement. It is the one place the model's self-report is
    read — and it is read as a *symptom*, never as evidence that the reading is good.
    """
    purpose_agreement: float
    audience_agreement: float
    posterior_dispersion: float
    settling_rate_spread: float
    non_convergent_fraction: float
    confident_disagreement: float
    k: int


def convergence(runs: list[LoopRun]) -> Convergence:
    if len(runs) < 2:
        raise ValueError(
            "convergence is defined across independent reconstructions; k must be at least 2. "
            "A single LoopRun is a sample, not a measurement (SPEC §5)."
        )

    purposes = [r.reading.purpose.best for r in runs]
    audiences = [r.reading.audience.best for r in runs]

    def _modal_share(labels: list[str]) -> float:
        return max(labels.count(x) for x in set(labels)) / len(labels)

    purpose_agreement = _modal_share(purposes)
    audience_agreement = _modal_share(audiences)

    # Mean per-hypothesis standard deviation across runs. Catches the case the argmax misses:
    # every run naming the same winner while disagreeing wildly about everything else.
    keys = list(runs[0].reading.purpose.distribution)
    dispersion = mean(
        pstdev([r.reading.purpose.distribution[key] for r in runs]) for key in keys
    ) if keys else 0.0

    rates = [r.settling_rate for r in runs]
    settling_spread = pstdev(rates) if len(rates) > 1 else 0.0
    non_convergent = sum(1 for r in runs if not r.converged) / len(runs)

    confidence = mean(r.reading.self_reported_confidence for r in runs)
    confident_disagreement = confidence * (1.0 - purpose_agreement)

    return Convergence(
        purpose_agreement=purpose_agreement,
        audience_agreement=audience_agreement,
        posterior_dispersion=dispersion,
        settling_rate_spread=settling_spread,
        non_convergent_fraction=non_convergent,
        confident_disagreement=confident_disagreement,
        k=len(runs),
    )


# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Depth:
    """How many levels of decision are recoverable. SPEC §5's §1 reframe, made numerical.

    Ranks a carefully directed model output above human filler, which is the entire claim.

    `per_1k_chars` exists because of SPEC §7's third falsifier — **depth is just length** —
    which is "trivially confounded, trivially checked, and embarrassing if missed". Length is
    carried alongside every depth number so no depth claim can be reported without it. At Gate
    1's n=7 the check has no power, which is why N3 is pre-registered as a null the project
    expects to FAIL, retained so the failure is visible and the powered Gate 2 version is
    forced.
    """
    max_level: int
    levels_reached: int
    profile: dict[int, int]
    n_decisions: int
    artifact_chars: int
    per_1k_chars: float


def depth(run: LoopRun, artifact_text: str) -> Depth:
    r = run.reading
    profile = r.depth_profile
    chars = len(artifact_text)
    return Depth(
        max_level=r.max_depth,
        levels_reached=sum(1 for n in profile.values() if n > 0),
        profile=profile,
        n_decisions=len(r.decisions),
        artifact_chars=chars,
        per_1k_chars=(len(r.decisions) / chars * 1000) if chars else 0.0,
    )


# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class AudienceReading:
    """Probability the intended reader was not a person. SPEC §5.

    Says the socially useful thing without ever making an accusation about authorship.

    `machine` and `no_audience_modelled` are reported separately and must never be summed into
    a single "not a human reader" number. Presence of a non-human audience model and absence of
    any audience model are different findings (SPEC §4), and merging them would collapse the
    grooming case into the filler case — which is the distinction the instrument exists to make.
    """
    machine: float
    no_audience_modelled: float
    human: float
    spread: float


def audience(runs: list[LoopRun]) -> AudienceReading:
    def _avg(key: str) -> float:
        return mean(r.reading.audience.distribution[key] for r in runs)

    machine = _avg("machine")
    nobody = _avg("nobody_in_particular")
    human = 1.0 - machine - nobody
    spread = (
        pstdev([r.reading.audience.distribution["machine"] for r in runs])
        if len(runs) > 1 else 0.0
    )
    return AudienceReading(machine, nobody, max(0.0, human), spread)


# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Measurement:
    """The reading. All four quantities, always, and no headline number.

    There is no `.score`. SPEC §5 says the reading IS the tuple, and the simulation's
    methodology is that a single number invites the overclaim. If a future caller wants one
    number, that is a change to what the instrument claims and belongs in a deviation entry,
    not a convenience property.
    """
    artifact_id: str
    fit: Fit
    convergence: Convergence
    depth: Depth
    audience: AudienceReading
    arm: str
    model: str
    k: int

    may_not_claim: tuple[str, ...] = (
        "that a machine wrote this — the instrument makes no claim about authorship",
        "any one of the four quantities alone",
        "that a machine-audience posterior is an accusation; it is a hypothesis with a "
        "probability attached",
        "that low depth means low value — it means few decisions are RECOVERABLE",
    )


def measure(runs: list[LoopRun], artifact_text: str) -> Measurement:
    """Combine k independent LoopRuns over one artifact into one Measurement.

    Fit and depth are computed on the *first* run and the others contribute through
    convergence. That is deliberate: averaging fit across runs would hide exactly the
    variability that convergence exists to report, and a mean fit over mutually contradictory
    readings describes no reading that was actually produced.
    """
    if not runs:
        raise ValueError("no runs to measure")
    ids = {r.artifact_id for r in runs}
    if len(ids) != 1:
        raise ValueError(f"runs span multiple artifacts: {sorted(ids)}")

    return Measurement(
        artifact_id=runs[0].artifact_id,
        fit=fit(runs[0], artifact_text),
        convergence=convergence(runs),
        depth=depth(runs[0], artifact_text),
        audience=audience(runs),
        arm=runs[0].arm,
        model=runs[0].model,
        k=len(runs),
    )
