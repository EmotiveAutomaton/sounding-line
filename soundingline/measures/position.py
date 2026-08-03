"""Where in the artifact the decisions are — the axis nothing here has ever measured.

── WHY THIS EXISTS ───────────────────────────────────────────────────────────────────────────

Every quantity the probe emits is an artifact-level scalar. Reading session 01 produced, for all
ten artifacts, a two-part assessment that no scalar can hold:

    5 was thin to start but got thicker as it went down... but it stayed equivalently thick
    throughout on the bottom. **There was depth to it, but the surface level shifted.**

    it does imply that the surface level over time, as you tend to open up with a style and then
    drift towards a natural style, seems like a pretty common pattern I'm seeing here.

    surface thickness gets thinner over time as people get lazy while their depth remains
    constant. **That surface thickness is a conscious behaviour that is cognitively effortful.**

`docs/theory/SURFACE_AND_DEPTH.md` derives the asymmetry from automaticity: an expert's content
decisions are practised and cached, so they cost little and have no reason to decay across one
artifact; an expert's surface decisions are a performance held consciously for a specific
audience, and under a metabolic budget a consciously held performance is exactly what degrades.

**The claim being tested is the asymmetry, not the direction.** The session showed surface moving
both ways — two artifacts started plain and thickened, and the curator's revision says thick-to-thin
is more common. What was stable in every case is that the surface moved and the depth did not.

    S-1   depth density varies LESS across thirds than surface density does.
    S-2   machine artifacts show FLAT surface across thirds — no maker to tire, no natural
          register to drift toward. The sharper prediction, and it locates the machine without
          any surface-quality judgement, which is what E40 says a quality judgement cannot do.
    S-4   surface variance is LARGER in less practised makers, since an expert has partly
          automatised the performance too. This one cuts against a naive reading of the theory,
          where expertise means more of everything.

If both densities move equally, the surface/depth distinction is not real and the theory document
is wrong. That is the whole point of measuring it.
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass

# A third that is shorter than this cannot carry a decision count worth comparing.
MIN_SLICE_CHARS = 400
_PARA = re.compile(r"\n\s*\n")


def thirds(text: str) -> list[str]:
    """Split into three contiguous slices at paragraph boundaries.

    On paragraph boundaries rather than character counts because a decision's evidence is a
    quoted span, and a split through the middle of a paragraph would cut spans in half and
    manufacture a position effect out of the slicing.

    Returns fewer than three slices if the artifact cannot support three — the caller must check,
    because a two-slice variance is not comparable to a three-slice one.
    """
    paras = [p for p in _PARA.split(text) if p.strip()]
    if not paras:
        return []
    total = sum(len(p) for p in paras)
    if total < 3 * MIN_SLICE_CHARS:
        return []

    target, out, buf, acc = total / 3.0, [], [], 0
    for p in paras:
        buf.append(p)
        acc += len(p)
        if acc >= target and len(out) < 2:
            out.append("\n\n".join(buf))
            buf, acc = [], 0
    if buf:
        out.append("\n\n".join(buf))
    return out if len(out) == 3 else []


@dataclass(frozen=True)
class SliceProfile:
    """One slice's decision densities, per 1,000 characters."""
    index: int
    n_chars: int
    surface: float
    depth: float
    n_decisions: int


@dataclass(frozen=True)
class PositionProfile:
    """The position reading. Both trajectories and both variances, never one of them.

    `surface_moves_more` is the S-1 verdict for a single artifact and is deliberately not a
    p-value: one artifact is one observation, and the test is across a corpus.
    """
    slices: tuple[SliceProfile, ...]
    surface_sd: float
    depth_sd: float
    surface_trend: float          # last slice minus first; negative = the decay the theory predicts
    depth_trend: float

    @property
    def surface_moves_more(self) -> bool:
        return self.surface_sd > self.depth_sd


def _densities(decisions, n_chars: int) -> tuple[float, float, int]:
    """Surface and depth density per 1,000 characters.

    `both` counts toward BOTH, at full weight rather than a half. A decision genuinely aimed at
    attention and at content was made twice over, and splitting it would understate an artifact
    that does the two at once — which is precisely what the curator described as the hard skill:
    "a controlled expertise or controlled personality that was itself attractive."
    """
    s = sum(1 for d in decisions if d.targets in ("surface", "both"))
    d_ = sum(1 for d in decisions if d.targets in ("depth", "both"))
    scale = max(n_chars, 1) / 1000.0
    return s / scale, d_ / scale, len(decisions)


def position_profile(slice_decisions: list[tuple[str, list]]) -> PositionProfile:
    """Build the profile from [(slice_text, [DecisionV6, ...]), ...] in document order."""
    if len(slice_decisions) < 2:
        raise ValueError("a position profile needs at least two slices")

    slices = []
    for i, (text, decs) in enumerate(slice_decisions):
        s, d_, n = _densities(decs, len(text))
        slices.append(SliceProfile(index=i, n_chars=len(text), surface=s, depth=d_,
                                   n_decisions=n))

    su = [x.surface for x in slices]
    de = [x.depth for x in slices]
    return PositionProfile(
        slices=tuple(slices),
        surface_sd=statistics.pstdev(su),
        depth_sd=statistics.pstdev(de),
        surface_trend=su[-1] - su[0],
        depth_trend=de[-1] - de[0],
    )
