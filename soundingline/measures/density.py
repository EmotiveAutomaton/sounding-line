"""E49's density, measured across scales. The one instrument the theory specifies and nobody built.

── WHY THIS AND NOT ANOTHER BORROWED TECHNIQUE ───────────────────────────────────────────────

`docs/ANTI_CONVENTION.md`. Every technique this project has imported came with the ceiling of the
field that built it, and function-word stylometry's ceiling is author identification, which sits
below the question.

`ghost-scale-sim/EVIDENCE.md` ran a retrospective literature check and found four rows where
**nobody has asked the question.** One of them:

    E49 · Artfulness is DENSITY -- hierarchy per unit of observable extent -- which is what lets a
    readymade be dense rather than empty.
    Published: compression-based complexity tracks human judgements of visual complexity
    (EPJ Data Science 2023); Kolmogorov complexity differentiates schools of iconography.
    **"The measure is established. The bimodality prediction is not tested anywhere."**

So the measurement apparatus exists and is validated, **and the specific prediction the theory
makes with it has never been run.** That is the rarest combination available: a tool that works
pointed at a question nobody has pointed it at.

── WHAT THE THEORY ACTUALLY SAYS, AND WHY ONE NUMBER WILL NOT DO ─────────────────────────────

    Art is compressed intent... Decisions are counted individually, INCLUDING subordinate and
    previously addressed solutions. Baked-in HIERARCHICAL compression.
    Simplicity without a dense underlying decision tree is just empty data; simplicity born from
    extreme compression is a masterpiece.

Two things are load-bearing there and a single compression ratio destroys both.

**Hierarchy.** Decisions nest. A measure taken at one scale cannot see nesting — it sees whatever
that scale happens to expose. **So compress at several scales and keep the profile.**

**And the two ends look identical to a scalar.** *Empty data* and *extreme compression* both
compress well. The Zen circle and the blank page have the same file size. **What separates them is
how compressibility CHANGES as the window grows**: structure that repeats at every scale is empty,
structure that only appears at larger scales is nested.

    A flat artifact:      local redundancy, and no more structure at larger windows.
    A nested artifact:    less local redundancy, and MORE structure as the window grows, because
                          the larger units are themselves organised.

── THE MEASURE ───────────────────────────────────────────────────────────────────────────────

For windows of increasing size, compress and record the ratio. Two quantities come out:

    compressibility   how redundant the text is at each scale
    scale_gain        how much compressibility IMPROVES as the window grows

`scale_gain` is the density estimate. Redundancy that only becomes visible at larger windows is
organisation above the sentence — which is what "hierarchical decisions" means when it is written
down rather than gestured at.

── DISQUALIFIED 2026-08-04. READ THIS BEFORE USING ANYTHING BELOW ────────────────────────────

**`scale_gain` is type-token ratio.** rho = -0.879 against TTR, and the human/no-maker gap survives
WORD SHUFFLING unchanged (+0.0775 intact, +0.0725 shuffled). Shuffling preserves vocabulary and
destroys all order, so the measure is not reading hierarchy, structure, or anything the theory
meant by density. `results/controls/VERDICT.md`.

Retained rather than deleted because the failure is instructive and because `bimodality()` may be
worth reusing on a measure that survives its controls. **E49's prediction remains untested.**

── AND THE HONEST PART ───────────────────────────────────────────────────────────────────────

gzip is a lexical compressor. It sees repeated substrings, not repeated *ideas*. It will find that
a page repeats "mattress" and will not find that an essay repeats a structural move.

**That is a real ceiling and it is stated rather than discovered later.** The version of this that
could reach the question uses a language model's own predictions as the compressor — surprisal per
token, which is compression against a model of meaning rather than of substrings. That needs the
GPU and is `run_density.py --model`. The gzip version is the cheap floor, run first to see whether
the shape exists at all before spending anything on it.
"""

from __future__ import annotations

import re
import statistics
import zlib
from dataclasses import dataclass

_WS = re.compile(r"\s+")

# Windows in words. Spans a sentence, a paragraph, a section, and a chapter -- the scales at which
# a maker's decisions plausibly nest.
SCALES = (25, 100, 400, 1600)


def _ratio(text: str) -> float:
    """Compressed size over raw size. Lower means more redundant.

    Level 9 and the default window, so the compressor is given every chance to find structure --
    a weak setting would understate large-scale redundancy, which is precisely the signal.
    """
    raw = text.encode("utf-8")
    if len(raw) < 32:
        return 1.0
    return len(zlib.compress(raw, 9)) / len(raw)


@dataclass(frozen=True)
class DensityProfile:
    """Compressibility at each scale, and how it changes."""
    scales: tuple[int, ...]
    compressibility: tuple[float, ...]      # 1 - ratio, so higher = more redundant
    n_words: int

    @property
    def scale_gain(self) -> float:
        """Compressibility at the largest usable scale minus the smallest.

        THE DENSITY ESTIMATE. Positive means redundancy that only appears once the window is big
        enough to contain it -- organisation above the sentence. Near zero means whatever structure
        exists is already visible in a sentence, which is what flat text looks like.
        """
        c = [x for x in self.compressibility if x is not None]
        return c[-1] - c[0] if len(c) >= 2 else float("nan")

    @property
    def local(self) -> float:
        """Compressibility at the smallest scale. Local redundancy: boilerplate, filler, repetition."""
        return self.compressibility[0]

    def as_dict(self) -> dict:
        return {"scales": list(self.scales), "compressibility": list(self.compressibility),
                "scale_gain": self.scale_gain, "local": self.local, "n_words": self.n_words}


def density(text: str, scales: tuple[int, ...] = SCALES, cap: int = 24) -> DensityProfile:
    """Compressibility across nested window sizes.

    Windows are sampled evenly rather than taken from the head, so a document with a boilerplate
    header does not have its smallest scale dominated by the header. Capped per scale so a long
    document does not have its large-scale estimate averaged over hundreds of windows while its
    small-scale estimate comes from a handful.
    """
    words = _WS.split(text.strip())
    n = len(words)
    out = []
    for s in scales:
        if n < s * 2:
            out.append(out[-1] if out else 1.0 - _ratio(text))
            continue
        starts = range(0, n - s + 1, s)
        picks = list(starts)
        if len(picks) > cap:
            step = len(picks) / cap
            picks = [picks[int(i * step)] for i in range(cap)]
        out.append(statistics.fmean(1.0 - _ratio(" ".join(words[i:i + s])) for i in picks))
    return DensityProfile(scales=scales, compressibility=tuple(out), n_words=n)


def bimodality(values: list[float], n_bins: int = 12) -> dict:
    """E49's untested prediction: is the distribution of density BIMODAL?

    The theory says a readymade can be dense and a blank page empty, so artifacts should not pile
    up in the middle — they should separate into organised and flat, with a dip between.

    Measured with the **bimodality coefficient**, (skew^2 + 1) / kurtosis, which exceeds 5/9 ≈ 0.555
    for a bimodal distribution and sits below it for a unimodal one. Hand-rolled because the
    arithmetic should be visible: this is the first time anyone has run the prediction, and a
    reader should be able to check it without trusting a library.
    """
    n = len(values)
    if n < 8:
        return {"n": n, "bimodality_coefficient": float("nan"), "verdict": "too few"}
    m = statistics.fmean(values)
    sd = statistics.pstdev(values) or 1e-9
    skew = statistics.fmean(((v - m) / sd) ** 3 for v in values)
    kurt = statistics.fmean(((v - m) / sd) ** 4 for v in values)
    # Sample-corrected form; the excess-kurtosis convention subtracts 3.
    bc = (skew ** 2 + 1) / max(kurt, 1e-9)
    return {"n": n, "skew": skew, "kurtosis": kurt, "bimodality_coefficient": bc,
            "threshold": 5 / 9,
            "verdict": "BIMODAL" if bc > 5 / 9 else "unimodal"}
