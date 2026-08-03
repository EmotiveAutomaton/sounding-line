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
    """How much maker-state was recovered, and how well it is evidenced. **No aggregate.**

    **Low fit is the wall** (SPEC §5) — familiar surface, no recoverable maker-state behind it.

    ── WHY THERE IS NO `combined` FIELD ──────────────────────────────────────────────────────
    There was one. It was a geometric mean of three components, C-18 ranked artifacts on it, and
    every one of the three turned out to be measuring the wrong object:

      * `support` detected the word "alternative" rather than the structure of a decision;
      * `grounding` scored an empty artifact the same as an invented reading — the wall and E2
        collapsed into a single number;
      * `concentration` rewarded artifacts with ONE purpose, so a rich artifact that genuinely
        informs and persuades and expresses scored lowest, and the scalar ranked it last while
        four other dimensions ranked it first.

    SPEC §5 warned about precisely this: *the reading is the tuple... a single number invites the
    overclaim.* A scalar was the defect, not the particular arithmetic, so the scalar is gone
    rather than reweighted. Comparison between artifacts uses `dominates()`, which is a partial
    order — artifacts that trade off against each other come back INCOMPARABLE, which is the
    true answer and one no weighting scheme can express.

    `concentration` is no longer part of fit at all. It measures how single-purposed an artifact
    is, which is a property of the artifact rather than of the recovery, and it is reported
    beside fit as a diagnostic rather than folded into it.
    """
    grounding: float          # of the claims made, how many trace to text that is really there
    support: float            # of the decisions found, how many name a road not taken
    recovery: float           # how much was recovered at all, per 1k chars, capped at 1.0
    unverifiable_quotes: int
    verifiable: bool

    GROUNDING_FLOOR = 0.30

    @property
    def components(self) -> dict[str, float]:
        return {"grounding": self.grounding, "support": self.support, "recovery": self.recovery}


def dominates(a: Fit, b: Fit) -> bool:
    """True when `a` is at least as good on every component and better on at least one.

    Pareto dominance. Two artifacts that each win on something are incomparable, and the
    instrument says so instead of inventing a winner via weights nobody agreed on.
    """
    ca, cb = a.components, b.components
    return all(ca[k] >= cb[k] for k in ca) and any(ca[k] > cb[k] for k in ca)


def fit(run: LoopRun, artifact_text: str) -> Fit:
    r = run.reading

    quotes = [d.evidence for d in r.decisions] + [t.evidence for t in r.trade_offs]
    if quotes:
        located = [e.locate(artifact_text) for e in quotes]
        grounding = sum(loc[2] for loc in located if loc) / len(quotes)
        unverifiable = sum(1 for loc in located if loc is None)
    else:
        # Nothing offered is not the same as nothing verified. An artifact from which no claim
        # was made has vacuous grounding, and `recovery` is where its emptiness registers.
        grounding = 0.0
        unverifiable = 0

    if r.decisions:
        support = sum(
            1 for d in r.decisions
            if d.alternative_rejected.strip()
            and _normalise_quote(d.alternative_rejected) != _normalise_quote(d.what_was_chosen)
        ) / len(r.decisions)
    else:
        support = 0.0

    # Recovery: decisions per 1k characters, capped. Deliberately length-normalised, because
    # SPEC §7's third falsifier is that depth is just length and an un-normalised count would
    # walk straight into it. The cap is at 4 per 1k, above which more decisions stop meaning
    # more recovered intent and start meaning padding — which is the failure mode the stage-B
    # prompt explicitly warns the probe against.
    chars = max(1, len(artifact_text))
    recovery = min(1.0, (len(r.decisions) / chars * 1000) / 4.0)

    verifiable = (not quotes) or grounding >= Fit.GROUNDING_FLOOR
    return Fit(grounding, support, recovery, unverifiable, verifiable)


# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class MethodUnlock:
    """E36's temporal result, made into a measure. **The quantity this project should have been
    measuring from the start.**

    ── WHY THIS EXISTS ───────────────────────────────────────────────────────────────────────
    V6's E36, in the simulation's own words:

        Every measure of what a reader takes on, in every version of this project, has scored
        how much of the maker's PURPOSE it got. Depth is built so the purpose is equally readable
        however deep the work is, so that measure could not move with depth whatever was true...
        On the maker's method, depth moves uptake: 0.179 [0.099, 0.267]. On the maker's purpose,
        measured on the same cells, it does not: -0.028 [-0.116, 0.058].
        **The experiment was not wrong; it was pointed at the wrong quantity.**

    Every discriminator Gate 2 used was a purpose measure, and Gate 2 failed. This measures
    method instead: how much of the maker's execution chain becomes visible once the purpose is
    pinned.

    Two properties matter beyond that:

    * **It is within-reading.** E36's BETWEEN-reader form failed in the simulation as well
      (0.047 against a required 0.15); only the temporal, within-reading form held. Cross-sample
      agreement is also exactly what E38 says a machine-matched reader degrades on — so a
      within-reading measure routes around the reader problem rather than fighting it.
    * **It is not constructed flat.** Purpose is equally readable at every depth by design.
      Method is not, which is why it can move at all.

    **Known limit, recorded rather than hidden:** where the posterior settles on the first
    iteration, the "before" and "after" purposes are the same and the ratio is trivially 1.0.
    That is not a defect so much as a boundary — an artifact whose purpose was obvious from the
    first pass has no refinement to unlock anything — but it means the measure is informative on
    a SUBSET of artifacts, and the subset is not random. `settled` travels with every reading so
    the subset can be identified rather than averaged over silently.
    """
    before: float          # decisions recovered under stage A's UN-REFINED purpose
    after: int             # decisions recovered in the pass after it settled
    unlock: float          # after / before — the ratio E36 reports as 0.130 / 0.050
    settled: bool          # did the posterior settle at all? an unsettled loop has no "after"

    @property
    def gained(self) -> float:
        return self.after - self.before


def method_unlock(runs: list[LoopRun]) -> MethodUnlock:
    """Mean unlock across independent readings of one artifact."""
    before = mean(r.decisions_before_settle for r in runs)
    after = mean(r.decisions_after_settle for r in runs)
    # A guard rather than a silent zero: an artifact from which nothing was recovered before
    # settling has no baseline to divide by, and reporting an infinite unlock would be a lie
    # about an artifact the probe found nothing in.
    ratio = (after / before) if before > 0.05 else 0.0
    return MethodUnlock(before=before, after=int(round(after)), unlock=ratio,
                        settled=any(r.converged for r in runs))


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
    method: MethodUnlock
    # Reported beside fit, never inside it. How single-purposed the artifact is — a property of
    # the artifact rather than of the recovery, and the component whose inclusion in fit ranked
    # the richest artifact in the Gate 1 set dead last.
    purpose_breadth: float
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
        method=method_unlock(runs),
        purpose_breadth=_normalised_entropy(runs[0].reading.purpose.distribution),
        convergence=convergence(runs),
        depth=depth(runs[0], artifact_text),
        audience=audience(runs),
        arm=runs[0].arm,
        model=runs[0].model,
        k=len(runs),
    )
