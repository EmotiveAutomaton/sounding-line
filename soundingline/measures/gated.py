"""Unlock, conditioned on whether there is a maker to unlock — the E55 Reader 4 shape.

── THE PROBLEM THIS EXISTS TO FIX ────────────────────────────────────────────────────────────

Gate 2 ran the closest thing this project has to E36's null N28 and it failed:

    row 2, human and careful   1.283
    row 5                      1.093
    GENERATED, no maker        1.111
    row 3, commercial          0.917

Artifacts with no reconstructible maker unlock MORE than competent commercial work, and nearly as
much as careful human work. If unlock measured method recovery that could not happen: with no
execution chain behind the artifact there is nothing for a settled purpose to unlock, and the
ratio should sit at 1.0. E36 states the consequence without qualification — *if recovery moves
where there is no process, the measure is reading something else and every number above it is
uninterpretable.*

Three artifacts, no significance, and not a refutation. But it says plainly that **unlock cannot
currently tell "no maker" from "maker"**, and that is a problem that will follow this instrument
into every gate after Gate 3.

── WHY IT HAPPENS, AND WHY THE FIX IS NOT A FOURTH DISCRIMINATOR ─────────────────────────────

E38 accounts for it. The probe is a machine-matched reader — 1.000 on machine content against
0.280 on human — so generated text is the material it finds *easiest*. A second pass over easy
material yields more of everything, including decisions, and none of that is a maker being
recovered.

So unlock is not wrong. It is **ungated**. It asks *did the second pass yield more* and never asks
*is there anyone back there to yield it*. That second question is E37's wall — legible and empty —
and per version 9's ablation programme it is the one finding that requires the reader to hold a
distribution rather than a best guess, which is exactly the machinery this probe has and exactly
the machinery Gate 3's A/B split does not need.

The shape of the fix is E55's Reader 4: **absorption scaled by how well the maker was recovered.**
Here, unlock scaled by reconstructibility.

── WHAT RECONSTRUCTIBILITY IS MADE OF, AND WHY NOT THE OBVIOUS THINGS ────────────────────────

**Not purpose agreement.** E36 is explicit that purpose is constructed flat, and C-22 predicts
agreement on purpose is *higher* for flattened commercial work. It is the wrong quantity twice
over.

**Not grounding alone.** E37's whole point is that the wall is *legible*. Quotes locate fine in
empty content; that is the signature, not its absence.

**Cross-seed agreement on WHICH DECISIONS, matched by where in the artifact they are evidenced.**
Nobody has measured this. Under E2, content with no maker read under a human claim produces
readers who are *confident and mutually contradictory* — every reading names decisions, no two
name the same ones. Under a real maker the decisions are in the artifact, so independent readings
should keep landing on the same spans.

**THE PREDICTION, STATED BEFORE THIS IS RUN ON ANYTHING.** E2 and E38 disagree about what this
should do on generated content, and that disagreement is the reason to build it rather than argue
about it. E2 predicts low decision agreement (no maker to converge on). E38 predicts high (a
matched reader finds its own kind easy and will be consistent about it). They apply to different
things and this probe is both.

    So: the first job of this measure is the control that unlock failed. If decision agreement on
    the three locked generated artifacts is not clearly lower than on human artifacts, THIS IS NOT
    THE DISCRIMINATOR EITHER, and it should be reported as failing rather than tuned until it
    passes.

Written down here so that outcome is a result and not an embarrassment.
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass
from itertools import combinations

from soundingline.loop.run import LoopRun

# Two decisions are "the same decision" if their evidence spans overlap by at least this much,
# by intersection-over-union. Loose on purpose: the claim is that two readings pointed at the same
# part of the artifact, not that they quoted identical strings.
SPAN_IOU = 0.30
_WORD = re.compile(r"[a-z0-9']+")


def _tokens(s: str) -> set[str]:
    return set(_WORD.findall(s.lower()))


@dataclass(frozen=True)
class Reconstructibility:
    """The three components, reported separately. There is no aggregate on this object either.

    SPEC §5's rule holds here for the same reason it holds for `fit`: an artifact that is well
    grounded and mutually contradictory is a different object from one that is poorly grounded and
    consistent, and one number describes neither.
    """
    span_agreement: float       # cross-seed agreement on which decisions, by evidence span
    grounding: float            # fraction of decision evidence that locates in the artifact
    counterfactual: float       # fraction of named alternatives that are not restatements
    n_pairs: int
    n_decisions: float

    @property
    def gate(self) -> float:
        """The scalar the gate applies, and the ONLY place these are combined.

        Grounding is a precondition rather than a term: evidence that does not locate in the
        artifact was invented, and an invented decision agreeing with another invented decision is
        not evidence of a maker. So it multiplies, and span agreement carries the signal.
        """
        return float(self.span_agreement * self.grounding)


def _spans(run: LoopRun, artifact_text: str) -> list[tuple[int, int]]:
    out = []
    for d in run.reading.decisions:
        loc = d.evidence.locate(artifact_text)
        if loc is not None:
            out.append((loc[0], loc[1]))
    return out


def _iou(a: tuple[int, int], b: tuple[int, int]) -> float:
    lo, hi = max(a[0], b[0]), min(a[1], b[1])
    inter = max(0, hi - lo)
    union = (a[1] - a[0]) + (b[1] - b[0]) - inter
    return inter / union if union > 0 else 0.0


def _pair_agreement(x: list[tuple[int, int]], y: list[tuple[int, int]]) -> float:
    """Jaccard over greedily matched spans. Symmetric, and 0 when either side is empty.

    Empty means the reading recovered no locatable decision at all, which is the wall's strongest
    form, so it must score zero rather than be dropped from the average.
    """
    if not x or not y:
        return 0.0
    used, matched = set(), 0
    for i, a in enumerate(x):
        best, best_j = SPAN_IOU, None
        for j, b in enumerate(y):
            if j in used:
                continue
            v = _iou(a, b)
            if v >= best:
                best, best_j = v, j
        if best_j is not None:
            used.add(best_j)
            matched += 1
    return matched / (len(x) + len(y) - matched)


def reconstructibility(runs: list[LoopRun], artifact_text: str) -> Reconstructibility:
    """How much of a maker the k readings agree is there."""
    if len(runs) < 2:
        raise ValueError("reconstructibility is defined across k >= 2 readings")

    spans = [_spans(r, artifact_text) for r in runs]
    pairs = [_pair_agreement(a, b) for a, b in combinations(spans, 2)]

    located = total = 0
    counter = restate = 0
    for r in runs:
        for d in r.reading.decisions:
            total += 1
            if d.evidence.locate(artifact_text) is not None:
                located += 1
            alt = d.alternative_rejected.strip()
            if not alt:
                continue
            counter += 1
            # A "rejected alternative" that mostly repeats what was chosen is a restatement, not a
            # counterfactual. bounded_v5 asks for moves the maker COULD have made and did not;
            # this is where that instruction is checked rather than trusted.
            ta, tc = _tokens(alt), _tokens(d.what_was_chosen)
            if ta and tc and len(ta & tc) / len(ta | tc) > 0.60:
                restate += 1

    return Reconstructibility(
        span_agreement=statistics.fmean(pairs) if pairs else 0.0,
        grounding=located / total if total else 0.0,
        counterfactual=(counter - restate) / counter if counter else 0.0,
        n_pairs=len(pairs),
        n_decisions=total / len(runs),
    )


@dataclass(frozen=True)
class GatedUnlock:
    """Unlock beside its gate, and the product — all three, never the product alone.

    `raw` is exactly the quantity Gate 3 tests, recomputed here unchanged so the two can be
    compared on the same artifacts without re-reading anything.
    """
    raw: float
    reconstructibility: Reconstructibility
    gated: float

    may_not_claim: tuple[str, ...] = (
        "that a low gate means a machine wrote this — it means k readings did not agree on "
        "which decisions are in the artifact, which is also what a badly-read human artifact "
        "looks like",
        "the gated number alone; it is uninterpretable without the gate that produced it",
        "that this has passed the control unlock failed, until it has been run on the three "
        "locked generated artifacts and reported either way",
    )


def gated_unlock(runs: list[LoopRun], artifact_text: str) -> GatedUnlock:
    ratios = [(r.decisions_after_settle / r.decisions_before_settle)
              if r.decisions_before_settle > 0.05 else 1.0 for r in runs]
    raw = statistics.fmean(ratios)
    rec = reconstructibility(runs, artifact_text)
    return GatedUnlock(raw=raw, reconstructibility=rec, gated=raw * rec.gate)
