"""A scripted probe. No model, no network, fully deterministic.

The pipeline must be testable without a model, for three reasons and the third is the one that
matters:

1. CI has no GPU and no credential.
2. A model in the loop makes every test flaky and every failure ambiguous.
3. **SPEC §8's nulls are claims about the ARCHITECTURE, not about the model.** N4 ("the probe
   process makes zero network calls") and N5 ("the probe returns only the constrained schema")
   are properties of the code. Testing them against a live model would test the model's
   politeness instead of the boundary.

`FakeProbe` implements the ProbeClient protocol and returns whatever the scenario dictates,
including deliberately malformed and adversarial outputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import BaseModel

from soundingline.family.loader import load_family
from soundingline.probe.client import ProbeResult
from soundingline.probe.schema import (
    Reading,
    StageAOut,
    StageBOut,
    StageCOut,
    StageDOut,
)

FAM = load_family()


def flat_purpose() -> dict[str, float]:
    """Uniform — the bounded family landed nowhere. The wall."""
    n = len(FAM.purposes)
    return {p: 1.0 / n for p in FAM.purposes}


def peaked_purpose(winner: str = "inform", mass: float = 0.7) -> dict[str, float]:
    rest = (1.0 - mass) / (len(FAM.purposes) - 1)
    return {p: (mass if p == winner else rest) for p in FAM.purposes}


def peaked_audience(winner: str = "general_public", mass: float = 0.7) -> dict[str, float]:
    rest = (1.0 - mass) / (len(FAM.audiences) - 1)
    return {a: (mass if a == winner else rest) for a in FAM.audiences}


def evidence(quote: str, start: int = 0):
    return {"quote": quote, "start": start, "end": start + len(quote)}


@dataclass
class Script:
    """What the fake probe should return, per stage.

    `purpose_sequence` lets a test drive the loop's trajectory: the first entry is stage A, and
    each subsequent entry is one stage C. A sequence that stops moving makes the loop converge;
    one that keeps moving makes it hit `max_iters`, which is the oscillation signature.
    """
    purpose_sequence: list[dict[str, float]]
    audience: dict[str, float] = field(default_factory=peaked_audience)
    decisions: list[dict] = field(default_factory=list)
    trade_offs: list[dict] = field(default_factory=list)
    cost_borne: int = 1
    confidence: float = 0.5
    account: str = ""


class FakeProbe:
    """Implements ProbeClient. Records every call so tests can assert on the stage order."""

    arm = "fake"
    model = "scripted"

    def __init__(self, script: Script) -> None:
        self.script = script
        self.calls: list[str] = []
        self._c_index = 0

    def read(self, system: str, prompt: str,
             schema: type[BaseModel] = Reading) -> ProbeResult:
        self.calls.append(schema.__name__)
        s = self.script

        if schema is StageAOut:
            parsed = StageAOut(
                purpose={"distribution": s.purpose_sequence[0]},
                audience={"distribution": s.audience},
                self_reported_confidence=s.confidence,
            )
        elif schema is StageBOut:
            parsed = StageBOut(decisions=tuple(s.decisions))
        elif schema is StageCOut:
            self._c_index += 1
            idx = min(self._c_index, len(s.purpose_sequence) - 1)
            parsed = StageCOut(
                purpose={"distribution": s.purpose_sequence[idx]},
                audience={"distribution": s.audience},
                changed_because="scripted",
            )
        elif schema is StageDOut:
            parsed = StageDOut(
                cost_borne=s.cost_borne,
                trade_offs=tuple(s.trade_offs),
                account=s.account,
            )
        else:
            raise AssertionError(f"unexpected schema {schema!r}")

        return ProbeResult(
            parsed=parsed,
            model=self.model,
            arm=self.arm,
            prompt_sha256="0" * 64,
            response_sha256="0" * 64,
            latency_s=0.0,
        )
