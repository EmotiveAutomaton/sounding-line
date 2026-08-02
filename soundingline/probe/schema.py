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

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from soundingline.family.loader import load_family

_FAMILY = load_family()

Probability = Annotated[float, Field(ge=0.0, le=1.0)]

# Distributions are allowed to be off by this much before we reject. Model-emitted probabilities
# do not sum to one, and rejecting a whole reading over a rounding artefact would silently bias
# the sample toward whatever the model finds easy to be tidy about.
_SIMPLEX_TOL = 0.02


class _Strict(BaseModel):
    """Extra fields are an error, not a curiosity.

    If the probe returns a key the family did not define, the instrument has been steered — by
    the artifact, by prompt drift, or by a model update — and that is exactly the condition
    N5 exists to catch. Silently ignoring it is how a compromised reading gets recorded as a
    clean one.
    """
    model_config = ConfigDict(extra="forbid", frozen=True)


class Evidence(_Strict):
    """A verbatim span from the artifact, with its character offsets.

    Offsets rather than free text so a claim can be checked against the stored artifact. A probe
    that cannot point at where it saw something has not recovered a decision; it has produced an
    impression.
    """
    quote: str = Field(min_length=1, max_length=600)
    start: int = Field(ge=0)
    end: int = Field(ge=0)

    @model_validator(mode="after")
    def _ordered(self):
        if self.end <= self.start:
            raise ValueError("evidence span must have end > start")
        return self


class PurposePosterior(_Strict):
    """Distribution over the family's purpose dimension. Keys are exactly the family's ids."""
    distribution: dict[str, Probability]

    @model_validator(mode="after")
    def _matches_family_and_sums(self):
        expected = set(_FAMILY.purposes)
        got = set(self.distribution)
        if got != expected:
            raise ValueError(
                f"purpose distribution must cover exactly the family's purposes; "
                f"missing={sorted(expected - got)} unexpected={sorted(got - expected)}"
            )
        total = sum(self.distribution.values())
        if abs(total - 1.0) > _SIMPLEX_TOL:
            raise ValueError(f"purpose distribution sums to {total:.4f}, not 1")
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

    @model_validator(mode="after")
    def _matches_family_and_sums(self):
        expected = set(_FAMILY.audiences)
        got = set(self.distribution)
        if got != expected:
            raise ValueError(
                f"audience distribution must cover exactly the family's audiences; "
                f"missing={sorted(expected - got)} unexpected={sorted(got - expected)}"
            )
        total = sum(self.distribution.values())
        if abs(total - 1.0) > _SIMPLEX_TOL:
            raise ValueError(f"audience distribution sums to {total:.4f}, not 1")
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
    what_was_chosen: str = Field(min_length=1, max_length=400)
    alternative_rejected: str = Field(min_length=1, max_length=400)
    evidence: Evidence

    @model_validator(mode="after")
    def _level_in_family(self):
        if self.level not in _FAMILY.depth_levels:
            raise ValueError(
                f"depth level {self.level} is not in the family {_FAMILY.depth_levels}"
            )
        return self


class TradeOff(_Strict):
    """What was gained, and what was given up to get it. D-3 holds v1 to this and no further.

    Values are visible in what was sacrificed, not in what was claimed. No named value may
    appear here — the output is the pair, and rendering it as a value statement belongs to the
    reader.
    """
    gained: str = Field(min_length=1, max_length=400)
    given_up: str = Field(min_length=1, max_length=400)
    evidence: Evidence


class Reading(_Strict):
    """One complete pass of the probe over one artifact.

    A single Reading is NOT a result. SPEC §5's four quantities include convergence, which is
    defined across independent reconstructions — so a measurement requires k of these. The type
    that carries a measurement is `soundingline.measures.Measurement`, never this.
    """
    purpose: PurposePosterior
    audience: AudiencePosterior
    decisions: tuple[Decision, ...] = Field(max_length=40)
    cost_borne: int
    trade_offs: tuple[TradeOff, ...] = Field(max_length=10)

    # Self-reported, and used ONLY as a diagnostic. Fit is computed by the measures module from
    # the posterior's shape and the evidence's coverage, never taken from the model's word for
    # it. A model asked to grade its own explanation grades it well.
    self_reported_confidence: Probability

    # D-2: the account is illustration, clearly marked, and feeds nothing.
    account: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def _cost_in_family(self):
        if self.cost_borne not in _FAMILY.cost_levels:
            raise ValueError(
                f"cost_borne {self.cost_borne} is not in the family {_FAMILY.cost_levels}"
            )
        return self

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

class StageAOut(_Strict):
    """Bounded goal hypotheses → posterior over purpose and audience."""
    purpose: PurposePosterior
    audience: AudiencePosterior
    self_reported_confidence: Probability


class StageBOut(_Strict):
    """The decision chain visible under a supplied purpose."""
    decisions: tuple[Decision, ...] = Field(max_length=40)


class StageCOut(_Strict):
    """The posterior, re-weighted on what the method revealed.

    `changed_because` is required and is the one place the loop asks for prose. It is a
    diagnostic — it never enters a measurement — but requiring it means an unchanged posterior
    has to be asserted rather than defaulted into.
    """
    purpose: PurposePosterior
    audience: AudiencePosterior
    changed_because: str = Field(min_length=1, max_length=800)


class StageDOut(_Strict):
    """Trade-offs and cost borne, read off the settled purpose. D-3 stops here."""
    cost_borne: int
    trade_offs: tuple[TradeOff, ...] = Field(max_length=10)
    account: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def _cost_in_family(self):
        if self.cost_borne not in _FAMILY.cost_levels:
            raise ValueError(
                f"cost_borne {self.cost_borne} is not in the family {_FAMILY.cost_levels}"
            )
        return self


def json_schema(model_cls: type[BaseModel] = Reading) -> dict:
    """The schema handed to the model for constrained decoding.

    Derived from the family at call time rather than written out, so the family file remains the
    single definition of what the instrument can say.
    """
    return model_cls.model_json_schema()
