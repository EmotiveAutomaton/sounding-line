"""The constrained schema the probe returns. SPEC §8, and it is not a serialisation convenience.

    The probe model gets no tools. It reads and returns a constrained schema. It cannot fetch,
    write, execute, or call anything. Structured output only — never free-form action.

Every field here is a value the bounded family allows. There is no free-text field that feeds any
measurement: the two prose fields that exist (`evidence` spans and `account`) are quotations from
the artifact and an explicitly-marked illustration respectively, and neither is an input to fit,
convergence, depth, or the audience posterior.

That separation is D-2's risk made structural. The account is what makes the instrument
pointable; the numbers are what make it a measurement; and the account has no severity check
behind it, so it must not be able to move a number.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from soundingline.family.loader import load_family

_FAMILY = load_family()

Probability = Annotated[float, Field(ge=0.0, le=1.0)]

# Confidence is asked for on the SAME 0-100 scale as the point allocations, then divided.
# Mixing conventions in one response is what broke the first three live runs: having been told
# to distribute 100 points, the model reported confidence as 94. One scale throughout is easier
# for the model to hold and easier for a human to check.
Confidence100 = Annotated[int, Field(ge=0, le=100)]

# ── ON SIMPLEX VIOLATIONS, WHICH ARE ROUTINE AND INFORMATIVE ─────────────────────────────────
#
# Grammar-constrained decoding guarantees the SHAPE of the JSON. It cannot guarantee that eight
# numbers sum to one, because JSON Schema has no way to say so. Observed in the first live run:
# an audience distribution summing to 2.50.
#
# Three options were available and only one is honest:
#
#   reject the reading  -> silently biases the sample toward artifacts the model finds easy to be
#                          tidy about, which is exactly the wrong direction for an instrument
#                          whose subject is content that defeats tidy readings.
#   widen the tolerance -> 2.50 is not a rounding artefact and pretending otherwise is a lie.
#   renormalise + record-> keeps every reading, and turns the violation into a measurement.
#
# So: renormalise, and record how far off it was. `simplex_deviation` is a free diagnostic of
# how much the model was actually tracking the constraint rather than pattern-matching the shape
# of an answer, and it belongs in the record for the same reason the trajectory does.
_SIMPLEX_TOL = 0.02          # below this, treat as rounding and do not flag
#
# There is deliberately NO hard rejection threshold. An earlier version refused any allocation
# more than 0.5 off, and it threw away a live reading whose points summed to 1.63 — the probe
# slipping back to the fractional convention mid-run, not the probe failing to distribute.
#
# Refusing it would have discarded a perfectly readable posterior, and the reasoning against
# that is already written above: rejecting readings biases the sample toward artifacts the model
# finds easy to be tidy about. That argument does not stop applying when the untidiness is the
# model's arithmetic rather than the artifact's content.
#
# Every positive allocation is therefore normalised and kept. What is recorded is which
# convention the probe used and how far off it was, which is strictly more information than a
# rejection would have carried.


# The probe is asked for INTEGER POINTS OUT OF 100, not probabilities.
#
# This is not cosmetic. Asked for floats summing to 1.0, the model emitted (live, in order):
# a distribution summing to 2.50; then one omitting `discharge_obligation` entirely; then one
# summing to 100 because it had silently switched to percentages. Numeric `maximum` constraints
# in the JSON Schema did not bind — grammar-constrained decoding enforces shape, not range.
#
# "Distribute 100 points across these options" is a task models do reliably and humans find
# natural to check. The normalisation below still divides by the actual total, so a probe that
# hands back 97 or 104 is accommodated rather than rejected, and the miss is recorded.
_POINTS = 100.0


def _renormalise(dist: dict[str, float]) -> tuple[dict[str, float], float]:
    """Return (normalised distribution, fractional deviation of the original from 100 points)."""
    # Negative allocations are clamped rather than rejected. `minimum` is not honoured by
    # Ollama's sampler and is refused outright by the Claude API ("for 'integer' type, property
    # 'minimum' is not supported"), so it cannot be enforced in the grammar on either arm — and
    # both arms must compile the SAME schema or the reference comparison measures the schema
    # difference instead of the models. A negative point count is the probe failing to allocate,
    # which is what `simplex_deviation` already exists to record.
    dist = {k: max(0.0, v) for k, v in dist.items()}
    total = sum(dist.values())
    if total <= 0:
        raise ValueError("distribution sums to zero; nothing was distributed")
    # Recognise both conventions rather than punishing one. `_POINTS` is what was asked for;
    # a total near 1.0 is the probe reverting to fractions, which is a slip worth recording and
    # not a reading worth destroying.
    reference = _POINTS if abs(total - _POINTS) <= abs(total - 1.0) else 1.0
    deviation = abs(total - reference) / reference
    return {k: v / total for k, v in dist.items()}, deviation


class _Strict(BaseModel):
    """Extra fields are an error, not a curiosity.

    If the probe returns a key the family did not define, the instrument has been steered — by
    the artifact, by prompt drift, or by a model update — and that is exactly the condition
    N5 exists to catch. Silently ignoring it is how a compromised reading gets recorded as a
    clean one.
    """
    model_config = ConfigDict(extra="forbid", frozen=True)


class Evidence(_Strict):
    """A verbatim quote from the artifact. Offsets are computed by code, never by the model.

    ── WHY THE MODEL NO LONGER SUPPLIES OFFSETS ──────────────────────────────────────────────
    The first Gate 1 run failed on this field more than any other — one sample produced 26
    validation errors, all of them `end <= start`. Asking a language model for character offsets
    is asking it to count characters, which it cannot do, and no amount of prompting fixes an
    arithmetic capability the architecture does not have.

    The requirement was right and the implementation was wrong. What the measurement actually
    needs is *checkability*: can this claim be traced to text that is really there? The model
    supplies the quote; `locate()` finds it. A quote that cannot be found is the fabrication
    signal, and it is now a cleaner signal than before, because a failure to locate means the
    text is absent rather than that the model mis-counted.
    """
    # Empty is permitted for the same reason as `alternative_rejected`: an empty quote cannot
    # be located, `locate()` returns None, and `fit.grounding` counts it against the reading.
    # The gap is scored where it belongs instead of destroying every other claim in the sample.
    quote: str = Field(default="", max_length=2000)

    def locate(self, artifact_text: str, *, threshold: float = 0.80
               ) -> tuple[int, int, float] | None:
        """Best match for this quote in the artifact: (start, end, similarity), or None.

        ── WHY THIS IS GRADED RATHER THAN EXACT ──────────────────────────────────────────────
        The first Gate 1 run scored item A at 0.00 grounding — not one offered quote located —
        while the thinner item B scored 0.33 on the same measure. Exact substring matching was
        collapsing hardest on the densest prose, which meant `fit` was penalising artifacts that
        are hard to quote back verbatim. That correlates with careful revision, so the headline
        measure was punishing exactly the property the instrument exists to detect.

        Models paraphrase lightly while quoting: a dropped article, a normalised dash, a joined
        clause. That is a model transcribing text it genuinely read. Inventing a sentence that is
        not there is a different act, and the gap between them is wide — so similarity is scored
        continuously and the threshold marks where transcription ends and fabrication begins.

        Whitespace and case are normalised before comparison; nothing else is forgiven.
        """
        import difflib
        import re

        needle = re.sub(r"\s+", " ", self.quote).strip().lower()
        hay = re.sub(r"\s+", " ", artifact_text).strip().lower()
        if not needle:
            return None
        i = hay.find(needle)
        if i >= 0:
            return (i, i + len(needle), 1.0)

        # No exact hit: find the window of the artifact this quote best corresponds to.
        # Windows are stepped at a quarter of the quote length so a match cannot fall between
        # two of them, and each is scored by matched characters over quote length.
        n = len(needle)
        best = (0, 0, 0.0)
        step = max(1, n // 4)
        for start in range(0, max(1, len(hay) - n + 1), step):
            window = hay[start:start + int(n * 1.3)]
            ratio = difflib.SequenceMatcher(None, needle, window, autojunk=False).ratio()
            if ratio > best[2]:
                best = (start, start + len(window), ratio)
        return best if best[2] >= threshold else None

class PurposePosterior(_Strict):
    """Distribution over the family's purpose dimension. Keys are exactly the family's ids."""
    distribution: dict[str, Probability]
    simplex_deviation: float = 0.0

    @model_validator(mode="before")
    @classmethod
    def _normalise(cls, data):
        if isinstance(data, dict) and isinstance(data.get("distribution"), dict):
            dist, dev = _renormalise(data["distribution"])
            data = {**data, "distribution": dist, "simplex_deviation": dev}
        return data

    @model_validator(mode="after")
    def _matches_family_and_sums(self):
        expected = set(_FAMILY.purposes)
        got = set(self.distribution)
        if got != expected:
            raise ValueError(
                f"purpose distribution must cover exactly the family's purposes; "
                f"missing={sorted(expected - got)} unexpected={sorted(got - expected)}"
            )
        return self

    @property
    def best(self) -> str:
        return max(self.distribution, key=self.distribution.__getitem__)


class AudiencePosterior(_Strict):
    """Distribution over the family's audience dimension.

    `machine` is the quantity SPEC §5 reports. It is a hypothesis in the family with a
    probability attached, never an accusation, and it is reported only as part of the tuple.
    """
    distribution: dict[str, Probability]
    simplex_deviation: float = 0.0

    @model_validator(mode="before")
    @classmethod
    def _normalise(cls, data):
        if isinstance(data, dict) and isinstance(data.get("distribution"), dict):
            dist, dev = _renormalise(data["distribution"])
            data = {**data, "distribution": dist, "simplex_deviation": dev}
        return data

    @model_validator(mode="after")
    def _matches_family_and_sums(self):
        expected = set(_FAMILY.audiences)
        got = set(self.distribution)
        if got != expected:
            raise ValueError(
                f"audience distribution must cover exactly the family's audiences; "
                f"missing={sorted(expected - got)} unexpected={sorted(got - expected)}"
            )
        return self

    @property
    def machine(self) -> float:
        return self.distribution["machine"]

    @property
    def best(self) -> str:
        return max(self.distribution, key=self.distribution.__getitem__)


class Decision(_Strict):
    """One recovered decision in the maker's chain, at a stated level of the depth dimension.

    `alternative_rejected` is the field that makes this a decision rather than a description. A
    choice with no visible alternative is not a decision; it is a property of the artifact. This
    is where the instrument earns the word `depth`.
    """
    level: int
    what_was_chosen: str = Field(max_length=1200)

    # Deliberately allowed to be EMPTY, and that is the measurement rather than a defect.
    #
    # An earlier version required at least one character. Gate 1 then threw away entire readings
    # because one decision in six came back with no alternative named — five recovered decisions
    # discarded to punish the sixth. That is the same sample-biasing mistake as rejecting an
    # untidy distribution, and the same answer applies: keep the reading, score the gap.
    #
    # An empty `alternative_rejected` means the probe could not name what else the maker could
    # have done. Under SPEC §4 that is not a decision at all — it is a property of the artifact —
    # so it is counted as unsupported by `fit.support` and costs the reading there, which is
    # where it should cost it.
    alternative_rejected: str = Field(default="", max_length=1200)
    evidence: Evidence

    @model_validator(mode="after")
    def _level_in_family(self):
        if self.level not in _FAMILY.depth_levels:
            raise ValueError(
                f"depth level {self.level} is not in the family {_FAMILY.depth_levels}"
            )
        return self


class DecisionV6(Decision):
    """A decision, plus WHAT IT WAS AIMED AT. v6 only; `Decision` is unchanged and still locked.

    `docs/theory/SURFACE_AND_DEPTH.md` defines surface and depth as one primitive — decision
    density — separated by target:

        surface   decisions aimed at THE READER'S ATTENTION. Contrast, rhythm, the punchy opener,
                  the acronym dropped to signal membership, the professional veneer.
        depth     decisions aimed at THE ARTIFACT'S CONTENT. What to include, what to cut, which
                  abstraction, which case to handle, which claim to defend.

    Nothing in v1-v5 distinguishes them, so the two-axis reading the curator produced for all ten
    artifacts of session 01 has no counterpart in anything the probe emits. This field is that
    counterpart, and it is what S-1 through S-4 need.

    `both` is a real answer and is not a hedge: an example chosen because it is the clearest case
    AND because it will land is genuinely aimed at both, and forcing a choice would push those
    into whichever bucket the model happened to prefer.
    """
    targets: Literal["surface", "depth", "both"]


class StageBOutV6(_Strict):
    """Stage B under v6 — the same chain, with each decision's target recorded."""
    decisions: tuple[DecisionV6, ...] = Field(max_length=20)


class TradeOff(_Strict):
    """What was gained, and what was given up to get it. D-3 holds v1 to this and no further.

    Values are visible in what was sacrificed, not in what was claimed. No named value may
    appear here — the output is the pair, and rendering it as a value statement belongs to the
    reader.
    """
    gained: str = Field(default="", max_length=1200)
    given_up: str = Field(default="", max_length=1200)
    evidence: Evidence


class Reading(_Strict):
    """One complete pass of the probe over one artifact.

    A single Reading is NOT a result. SPEC §5's four quantities include convergence, which is
    defined across independent reconstructions — so a measurement requires k of these. The type
    that carries a measurement is `soundingline.measures.Measurement`, never this.
    """
    purpose: PurposePosterior
    audience: AudiencePosterior
    # 12, not 40. A sample truncated mid-object at line 1070 of generated JSON: the model kept
    # enumerating decisions until it ran out of budget. Twelve is more than any artifact in the
    # calibration set produced, and a cap that fits in the generation budget beats a cap that
    # only fits in principle.
    decisions: tuple[Decision, ...] = Field(max_length=20)
    cost_borne: int

    # v2. Two dimensions, not one — the curator split them before they were built
    # (CALIBRATION_02 §5). Collapsing them would destroy the distinction between a postmortem
    # and the work it describes, which is where the depth construct attaches for reportage.
    artifact_effort: int
    demonstrated_work: int

    # 24, not 10. The counterfactual stage B makes the probe more expansive downstream, and
    # readings were being discarded for exceeding a cap chosen before that prompt existed.
    # Discarding a reading over a length limit is the same sample-biasing error as discarding one
    # over an untidy distribution.
    trade_offs: tuple[TradeOff, ...] = Field(max_length=24)

    # Self-reported, and used ONLY as a diagnostic. Fit is computed by the measures module from
    # the posterior's shape and the evidence's coverage, never taken from the model's word for
    # it. A model asked to grade its own explanation grades it well.
    #
    # On the 0-100 scale, like every other allocation the probe makes. One scale throughout is
    # easier for the model to hold; mixing them is what broke the first live runs.
    confidence_100: Confidence100 = 50

    @property
    def self_reported_confidence(self) -> float:
        return self.confidence_100 / 100.0

    # D-2: the account is illustration, clearly marked, and feeds nothing.
    #
    # TRUNCATED, never rejected. A field that feeds no measurement must never be able to destroy
    # a reading — and this one did, on a paid API sample, over 2000 characters of prose that no
    # number depends on. The rule that falls out and now applies generally: fields that feed a
    # measurement are validated; fields that do not are clipped.
    account: str = ""

    @model_validator(mode="before")
    @classmethod
    def _clip_account(cls, data):
        if isinstance(data, dict) and isinstance(data.get("account"), str):
            data = {**data, "account": data["account"][:4000]}
        return data

    @model_validator(mode="after")
    def _ordinals_in_family(self):
        for field, levels in (
            ("cost_borne", _FAMILY.cost_levels),
            ("artifact_effort", _FAMILY.artifact_effort_levels),
            ("demonstrated_work", _FAMILY.demonstrated_work_levels),
        ):
            if getattr(self, field) not in levels:
                raise ValueError(f"{field} {getattr(self, field)} is not in the family {levels}")
        return self

    @property
    def reports_on_work(self) -> int:
        """How much more work the artifact REPORTS ON than it took to write.

        The postmortem signature: a cheap document about an expensive thing. Large and positive
        means an account of real activity; zero-and-low means an account of nothing.
        """
        return self.demonstrated_work - self.artifact_effort

    @property
    def max_depth(self) -> int:
        """Deepest level at which any decision was recovered. 0 if none were."""
        return max((d.level for d in self.decisions), default=0)

    @property
    def depth_profile(self) -> dict[int, int]:
        """Count of recovered decisions per level.

        The profile rather than the maximum is what SPEC §4 means by "how many levels of
        decision are visible" — one lucky level-4 decision under an otherwise flat artifact is
        not the same object as decisions recovered at every level.
        """
        return {lvl: sum(1 for d in self.decisions if d.level == lvl)
                for lvl in _FAMILY.depth_levels}


# ---------------------------------------------------------------------------------------------
# Per-stage schemas for the §3 loop.
#
# Each stage of the loop returns only what that stage is entitled to say. Stage B recovers
# decisions and does NOT get to revise the purpose posterior; stage C revises the posterior and
# does NOT get to invent new decisions. That separation is what makes the loop a loop with
# measurable state rather than four chances to rewrite the whole reading.

class Anomaly(_Strict):
    """One thing in the artifact that demands an explanation. v6, stage zero.

    THE FIELD THAT MAKES THIS WORTH RUNNING is `candidate_explanations`, plural. An anomaly with
    one explanation is a conclusion wearing a question's clothes, and the whole point of running
    this before stage A is to OPEN the space of maker-states rather than to close it. A pass that
    returns one confident story per anomaly has re-implemented stage A one stage early.

    `is_absence` is separated because absences are the valuable kind and the easy kind to miss.
    The curator's three successful entries were an absence, a confession, and an ordering — and
    the absence (a technical piece with no jargon anywhere) is the one no surface scan finds.
    """
    what: str = Field(max_length=600)
    is_absence: bool = False
    why_it_does_not_fit: str = Field(max_length=600)
    # Two or more wanted; one is permitted rather than rejected, for the same reason an empty
    # `alternative_rejected` is permitted — the gap is scored, not punished by discarding the
    # reading around it.
    candidate_explanations: tuple[str, ...] = Field(default=(), max_length=4)
    evidence: Evidence


class StageZeroOut(_Strict):
    """The anomaly pass. Zero anomalies is a real answer and must stay representable."""
    anomalies: tuple[Anomaly, ...] = Field(default=(), max_length=5)


# The affective dimension lives only in family v3. It is loaded BY PATH here rather than from
# `_FAMILY`, so that a run under v1 or v2 — which have no such dimension — cannot silently acquire
# one, and so that the default family stays exactly what it was.
_V3_PATH = Path(__file__).resolve().parents[1] / "family" / "family_v3.yaml"


@lru_cache(maxsize=1)
def _affect_ids() -> tuple[str, ...]:
    return load_family(_V3_PATH).affects


class AffectPosterior(_Strict):
    """Distribution over family v3's `performed_affect`. PERFORMED, never felt.

    `none_legible` is a first-class value rather than the residual, because the wall has to be
    something the instrument can SAY, not something it backs into by giving everything else a low
    number. N-AFF is checked against this distribution's entropy.
    """
    distribution: dict[str, Probability]
    simplex_deviation: float = 0.0

    @model_validator(mode="before")
    @classmethod
    def _normalise(cls, data):
        if isinstance(data, dict) and isinstance(data.get("distribution"), dict):
            dist, dev = _renormalise(data["distribution"])
            data = {**data, "distribution": dist, "simplex_deviation": dev}
        return data

    @model_validator(mode="after")
    def _matches_family(self):
        expected = set(_affect_ids())
        got = set(self.distribution)
        if got != expected:
            raise ValueError(
                f"affect distribution must cover exactly family v3's affects; "
                f"missing={sorted(expected - got)} unexpected={sorted(got - expected)}"
            )
        return self

    @property
    def best(self) -> str:
        return max(self.distribution, key=self.distribution.__getitem__)

    @property
    def none_recoverable(self) -> float:
        """A fact about the reading, not a claim that the maker had no stance."""
        return self.distribution["none_recoverable"]


class StageEOut(_Strict):
    """The affect pass. v6 + family v3 only. TWO LAYERS, and the gap between them is the point.

        leaked_inferred  the model's OPINION about what got through unchosen.
        emblematic       what was displayed on purpose.

    ── WHY THE FIRST FIELD IS NAMED `leaked_inferred` AND NOT `leaked` (option C) ────────────

    Asking a language model "what stance is being performed" returns a CONTENT-WORD judgement.
    That is an emblematic-class instrument, and it is emblematic-class on BOTH of its outputs --
    no rewording changes what kind of thing a prompt can see. `docs/theory/LEAKAGE.md`.

    The leaked layer is measured by `measures/leakage.py`, from function-word distributions:
    non-conscious, topic-independent, hard to fake, and validated for sixty years as the channel
    that carries what a writer did not choose to say.

    So this field is retained under an honest name. It is the model's inference about a layer it
    cannot observe, and keeping it makes a real test available: does the model's guess about
    leakage track the measured leakage? That is A-1 in `AFFECT_ARCHITECTURE.md` -- whether a
    system with a generative model of affect and no interoception can predict the thing it has no
    access to.

    They usually agree — "if you have something felt, you kind of want to perform it, it's hard
    not to" — so `divergence` is the interesting quantity precisely because it is usually small.
    Leaked without emblematic is concealment; emblematic without leaked is pure performance. One
    distribution cannot tell those apart, and telling them apart is why there are two.

    `evidence` is required for every value above 10 points in either layer, on the same terms as
    `alternative_rejected`: an affect that cannot be pointed at was supplied by the reader. This
    is the whole safeguard for the dimensions most likely to confabulate, so it is a field rather
    than a hope.
    """
    leaked_inferred: AffectPosterior
    emblematic: AffectPosterior
    evidence: tuple[Evidence, ...] = Field(default=(), max_length=6)

    @property
    def divergence(self) -> float:
        """Total variation distance between the two layers. 0 = felt and shown agree.

        NOTE THE ASYMMETRY THIS QUANTITY NOW CARRIES. `emblematic` is measured by an instrument of
        the right class; `leaked_inferred` is not. A divergence computed from these two is a
        divergence between a measurement and an opinion, and the honest version compares
        `emblematic` against the FUNCTION-WORD profile instead. Kept because comparing the two is
        itself the test of whether the model can infer what it cannot measure.
        """
        a, b = self.leaked_inferred.distribution, self.emblematic.distribution
        return 0.5 * sum(abs(a[k] - b.get(k, 0.0)) for k in a)


class StageAOut(_Strict):
    """Bounded goal hypotheses → posterior over purpose and audience."""
    purpose: PurposePosterior
    audience: AudiencePosterior
    confidence_100: Confidence100

    @property
    def self_reported_confidence(self) -> float:
        """0-1, for everything downstream. Diagnostic only — it feeds no measurement."""
        return self.confidence_100 / 100.0


class StageBOut(_Strict):
    """The decision chain visible under a supplied purpose."""
    # 12, not 40. A sample truncated mid-object at line 1070 of generated JSON: the model kept
    # enumerating decisions until it ran out of budget. Twelve is more than any artifact in the
    # calibration set produced, and a cap that fits in the generation budget beats a cap that
    # only fits in principle.
    decisions: tuple[Decision, ...] = Field(max_length=20)


class StageCOut(_Strict):
    """The posterior, re-weighted on what the method revealed.

    `changed_because` is required and is the one place the loop asks for prose. It is a
    diagnostic — it never enters a measurement — but requiring it means an unchanged posterior
    has to be asserted rather than defaulted into.
    """
    purpose: PurposePosterior
    audience: AudiencePosterior
    # Empty is legitimate: it means the method revealed nothing that bears on purpose, and an
    # unchanged posterior is a real outcome the loop records rather than an omission.
    changed_because: str = Field(default="", max_length=4000)


class StageDOut(_Strict):
    """Trade-offs, cost, and the two effort dimensions, read off the settled purpose."""
    cost_borne: int
    artifact_effort: int
    demonstrated_work: int
    # 24, not 10. The counterfactual stage B makes the probe more expansive downstream, and
    # readings were being discarded for exceeding a cap chosen before that prompt existed.
    # Discarding a reading over a length limit is the same sample-biasing error as discarding one
    # over an untidy distribution.
    trade_offs: tuple[TradeOff, ...] = Field(max_length=24)
    account: str = ""

    @model_validator(mode="before")
    @classmethod
    def _clip_account(cls, data):
        if isinstance(data, dict) and isinstance(data.get("account"), str):
            data = {**data, "account": data["account"][:4000]}
        return data

    @model_validator(mode="after")
    def _ordinals_in_family(self):
        for field, levels in (
            ("cost_borne", _FAMILY.cost_levels),
            ("artifact_effort", _FAMILY.artifact_effort_levels),
            ("demonstrated_work", _FAMILY.demonstrated_work_levels),
        ):
            if getattr(self, field) not in levels:
                raise ValueError(f"{field} {getattr(self, field)} is not in the family {levels}")
        return self


def _explicit_distribution(ids) -> dict:
    """A JSON Schema object that NAMES every family value and requires all of them.

    Pydantic renders `dict[str, Probability]` as an open object, and an open object lets
    grammar-constrained decoding emit any subset of the keys. Observed on the first live run:
    a purpose distribution missing `discharge_obligation`, and an audience distribution missing
    both `machine` and `nobody_in_particular` — the two the family exists to keep apart.

    Values are integer POINTS OUT OF 100 (see `_renormalise`), not probabilities.

    Silently dropping a hypothesis is worse than getting it wrong. A missing key is not a low
    probability, it is the probe declining to consider the option at all, and for `machine` that
    would quietly remove the measurement SPEC §5 reports. So the grammar is made to enforce what
    the validator was catching after the fact.
    """
    return {
        "type": "object",
        "properties": {i: {"type": "integer"} for i in ids},
        "required": list(ids),
        "additionalProperties": False,
    }


def _inline_refs(node, defs):
    """Resolve every $ref inline and drop $defs entirely.

    Ollama's grammar compiler rejected the referenced form outright — "failed to initialize
    samplers: failed to parse grammar" — on every stage that contained a nested model. A schema
    the sampler cannot compile is not a constraint, it is an outage, so the schema handed to the
    model is now self-contained.
    """
    if isinstance(node, list):
        return [_inline_refs(n, defs) for n in node]
    if not isinstance(node, dict):
        return node
    if "$ref" in node:
        name = node["$ref"].rsplit("/", 1)[-1]
        return _inline_refs({k: v for k, v in defs[name].items()}, defs)
    return {k: _inline_refs(v, defs) for k, v in node.items() if k != "$defs"}


def _apply_family_ordinals(node, fam):
    """Replace bare integer fields with explicit enums of the family's levels.

    A bare `{"type": "integer"}` let the probe return depth level 5 against a family that stops
    at 4. An ordinal whose allowed values are known should be enumerated in the grammar rather
    than checked afterwards — the validator catching it destroys the whole reading, and the
    grammar preventing it costs nothing.
    """
    ordinals = {
        "level": fam.depth_levels,
        "cost_borne": fam.cost_levels,
        "artifact_effort": fam.artifact_effort_levels,
        "demonstrated_work": fam.demonstrated_work_levels,
    }
    if isinstance(node, list):
        return [_apply_family_ordinals(n, fam) for n in node]
    if not isinstance(node, dict):
        return node
    out = {}
    for k, v in node.items():
        if k == "properties" and isinstance(v, dict):
            props = {}
            for pname, pschema in v.items():
                if pname in ordinals and ordinals[pname]:
                    props[pname] = {"type": "integer", "enum": list(ordinals[pname])}
                else:
                    props[pname] = _apply_family_ordinals(pschema, fam)
            out[k] = props
        else:
            out[k] = _apply_family_ordinals(v, fam)
    return out


# Keys the grammar compiler is allowed to see. Everything else is documentation or a constraint
# the sampler does not honour anyway, and both are actively harmful here.
#
# Pydantic emits every docstring as a `description`, so the schema for one stage carried several
# kilobytes of prose — em-dashes, blank lines, the lot — and Ollama answered "failed to parse
# grammar" on the stage with the most of it, while compiling the same schema fine in isolation
# with a short prompt. The model is told what the fields mean by the PROMPT; the grammar only
# needs to know the shape.
#
# Length and range constraints are dropped for a different reason: bring-up showed `maximum` does
# not bind in the sampler, so leaving them in advertises a guarantee that is not delivered.
# Pydantic still enforces every one of them on the way back in, where they actually hold.
_GRAMMAR_KEYS = {
    "type", "properties", "required", "items", "enum", "additionalProperties",
}


def _strip_to_grammar(node):
    """Reduce a JSON Schema to the subset the sampler needs, recursively."""
    if isinstance(node, list):
        return [_strip_to_grammar(n) for n in node]
    if not isinstance(node, dict):
        return node
    out = {}
    for k, v in node.items():
        if k == "properties" and isinstance(v, dict):
            out[k] = {pk: _strip_to_grammar(pv) for pk, pv in v.items()}
        elif k in _GRAMMAR_KEYS:
            out[k] = _strip_to_grammar(v)
    return out


def json_schema(model_cls: type[BaseModel] = Reading) -> dict:
    """The schema handed to the model for constrained decoding.

    Derived from the family at call time rather than written out, so the family file remains the
    single definition of what the instrument can say — including, now, at the grammar level.
    """
    schema = model_cls.model_json_schema()
    for defname, ids in (
        ("PurposePosterior", _FAMILY.purposes),
        ("AudiencePosterior", _FAMILY.audiences),
        # v3 only. Harmless on every other schema: the loop skips a $def that is not present.
        ("AffectPosterior", _affect_ids()),
    ):
        d = schema.get("$defs", {}).get(defname)
        if d and "distribution" in d.get("properties", {}):
            d["properties"]["distribution"] = _explicit_distribution(ids)
            # simplex_deviation is computed by the validator, never emitted by the model.
            d["properties"].pop("simplex_deviation", None)
            d["required"] = [r for r in d.get("required", []) if r != "simplex_deviation"]

    defs = schema.get("$defs", {})
    schema = _inline_refs(schema, defs)
    schema = _apply_family_ordinals(schema, _FAMILY)
    return _strip_to_grammar(schema)
