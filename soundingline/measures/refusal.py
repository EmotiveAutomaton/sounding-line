"""Measure what the reader could NOT do.

── THE REFRAME, AND WHY IT IS NOT A CONSOLATION PRIZE ────────────────────────────────────────

`docs/WHERE_WE_ARE.md` §4. Every measure this project has built and lost measured what a reader
EXTRACTED. The two clearest positive results are both about what a reader could not do:

  * the bounded arm handed 14KB of gzip returned `valid=0/5` — a refusal, and information the
    free-form arm structurally cannot produce, because it has no state for "I was handed nothing";
  * the curator's first signal, ahead of everything else, is *"an odd decision I can't find an
    explanation for"* — a **local failure to explain**, not an extraction.

And the wall — E37, the most theoretically load-bearing idea here — has always been a refusal
described as though it were a reading. *Legible and empty* means **the reader could not build a
maker**, not that it built a poor one.

    Depth is not how many decisions were recovered.
    Depth is how much of this artifact RESISTS a maker-shaped explanation.

── WHY THIS SURVIVES WHAT KILLED THE OTHERS ──────────────────────────────────────────────────

The simulation's finding on the unlock ratio was that the reader's belief about the maker's
execution mode stays diffuse throughout — entropy at 96.5% of maximum, never below 75% in 288
steps. **A count has to threshold a posterior that never crosses a threshold.**

A refusal needs no threshold. It is an event: the quote did not locate, the alternative was not
nameable, the schema rejected the sample, the independent readings did not converge. Each is
recorded, each is binary or bounded, and none requires deciding how confident is confident enough.

── AND IT COSTS NOTHING, BECAUSE THE DATA ALREADY EXISTS ─────────────────────────────────────

Every component below was already recorded by Gate 3 — as a DEFECT. Fourteen hours of GPU produced
a primary nobody may report and, in the same files, a refusal profile nobody has looked at.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

# A reading is "refused" on a component when that component is at or above this. Used only for the
# coarse `n_refused` count; every component is also reported continuously, because collapsing to a
# threshold is the mistake this module exists to avoid.
STRONG = 0.5


@dataclass(frozen=True)
class Refusal:
    """Five ways a reading declines to explain, all bounded in [0, 1], all higher = more refused.

    Reported as a panel and never summed into one number. `docs/GATES.md`: the reading is the
    tuple. That rule applied to recovery; there is no reason it stops applying to its inverse.
    """
    unnameable: float          # decisions where no alternative could be named
    unconcentrated: float      # purpose posterior entropy — failure to commit to a purpose
    unconverged: float         # independent readings that did not agree on a purpose
    unattempted: float         # samples the schema rejected outright
    unmoved: float             # the loop settled without the posterior ever re-weighting

    @property
    def components(self) -> dict[str, float]:
        return {"unnameable": self.unnameable, "unconcentrated": self.unconcentrated,
                "unconverged": self.unconverged, "unattempted": self.unattempted,
                "unmoved": self.unmoved}

    @property
    def n_refused(self) -> int:
        """How many of the five are strongly refused. A count of KINDS, not of decisions.

        This is the one place a threshold appears, and it is on the panel rather than inside a
        measure — "this reading failed in three different ways" is a statement about the shape of a
        failure, not a graded quantity pretending to be one.
        """
        return sum(1 for v in self.components.values() if v >= STRONG)


def from_profile(bounded: dict, k_expected: int = 5) -> Refusal:
    """Build the panel from a Gate 3 `bounded` profile. No re-reading required.

    Every field here was stored as a diagnostic of something going wrong. `named_alternative_rate`
    was recorded to check the probe was finding alternatives; its complement is the measurement.
    `purpose_agreement` was recorded to check convergence; its complement is E2's *confident mutual
    disagreement*, which is the wall's own signature.
    """
    k = bounded.get("k", 0)
    return Refusal(
        unnameable=1.0 - float(bounded.get("named_alternative_rate", 0.0)),
        unconcentrated=float(bounded.get("purpose_breadth", 0.0)),
        unconverged=1.0 - float(bounded.get("purpose_agreement", 0.0)),
        unattempted=1.0 - (k / k_expected if k_expected else 0.0),
        unmoved=1.0 if bounded.get("unlock_trivial") else 0.0,
    )


def summarise(rs: list[Refusal]) -> dict:
    if not rs:
        return {}
    keys = rs[0].components
    return {**{k: statistics.fmean(r.components[k] for r in rs) for k in keys},
            "n_refused": statistics.fmean(r.n_refused for r in rs),
            "n": len(rs)}
