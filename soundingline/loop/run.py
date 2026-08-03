"""The §3 loop. A loop, not a chain — and the trajectory is the data.

SPEC §3, which is the part of the architecture nobody else is doing:

    bounded goal hypotheses ──→ posterior over purpose
              ↑                          │
              │                          ↓
    re-weight posterior          extract the decision chain
    given what the method   ←──  visible under that purpose
    reveals about purpose               │
                                        ↓
                            implied values: what was optimised,
                            what was traded away to get it

    Run the loop to convergence and record the trajectory, not just the endpoint. How fast it
    converges, and whether it converges at all, is data — a real maker should tighten the loop
    quickly; an artifact with no coherent maker should either oscillate or settle into a
    confident answer that DIFFERS ON EVERY RUN, which is the E2 signature.

Three findings from the simulation are load-bearing in the code below and each is marked where
it applies:

* **E36** — pinning what someone was *for* roughly doubles how much of their *method* you
  recover. That is why stage B is handed the leading purpose instead of re-deriving it, and it
  is the reason the loop is worth running at all rather than reading purpose and method once
  each, independently.
* **E56** — method accrues continuously from the first line; purpose resolves late. So the
  trajectory of the *posterior* is informative and the trajectory of the *decision count* is
  much less so. The convergence test watches the posterior.
* **V6's values layer** — values are read off the recovered goal, so they cannot arrive before
  it. Stage D therefore runs exactly once, after the loop settles, and never inside it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from soundingline.family.loader import load_family
from soundingline.probe import render
from soundingline.probe.client import ProbeClient, ProbeResult
from soundingline.probe.render import Artifact
from soundingline.probe.schema import (
    AudiencePosterior,
    PurposePosterior,
    Reading,
    StageAOut,
    StageBOut,
    StageCOut,
    StageDOut,
)

# The loop stops when the posterior stops moving. `tol` is L1 distance over the joint
# (purpose, audience) distribution; `max_iters` bounds an artifact that never settles.
#
# An artifact that hits `max_iters` is NOT a failure to be retried — it is the oscillation
# signature SPEC §3 describes, and `converged=False` is the finding.
DEFAULT_TOL = 0.04
DEFAULT_MAX_ITERS = 4


def _l1(a: dict[str, float], b: dict[str, float]) -> float:
    """L1 distance between two distributions over the same support.

    L1 rather than KL: it is bounded, symmetric, and defined when a component is zero — and the
    probe emits zeros routinely, because a bounded family means most hypotheses are usually
    dead.
    """
    return sum(abs(a[k] - b.get(k, 0.0)) for k in a)


@dataclass
class Step:
    """One turn of the loop, with everything needed to plot the trajectory."""
    iteration: int
    purpose: PurposePosterior
    audience: AudiencePosterior
    n_decisions: int
    movement: float          # L1 movement of the joint posterior since the previous step
    changed_because: str = ""


@dataclass
class LoopRun:
    """One complete pass of the loop over one artifact — a single sample.

    A LoopRun is NOT a measurement. Convergence (SPEC §5) is defined across k independent
    LoopRuns, so a measurement needs k of these. See `soundingline.measures`.
    """
    artifact_id: str
    reading: Reading
    trajectory: list[Step]
    converged: bool
    arm: str
    model: str
    seed: int | None
    calls: list[ProbeResult] = field(default_factory=list)

    @property
    def iterations(self) -> int:
        return len(self.trajectory)

    @property
    def settling_rate(self) -> float:
        """How fast the loop tightened, as total movement per iteration.

        SPEC §3 predicts a real maker tightens the loop quickly. Low total movement over few
        iterations is the coherent-maker signature; high movement that never falls below `tol`
        is the oscillation signature. Reported alongside `converged` because the two say
        different things — a loop can converge slowly or fail to converge fast.
        """
        if not self.trajectory:
            return 0.0
        return sum(s.movement for s in self.trajectory) / len(self.trajectory)


def _decision_summary(decisions) -> str:
    """Render stage B's output for stage C, compactly.

    Stage C is asked to re-weight on what the METHOD revealed, so it gets the decisions and the
    alternatives — not the evidence spans, which would just re-present the artifact and let the
    stage re-read rather than re-weight.
    """
    if not decisions:
        return "No decisions were recoverable. Nothing in the artifact showed a maker choosing one thing over an available alternative."
    return "\n".join(
        f"  - [level {d.level}] chose: {d.what_was_chosen}  |  rejected: {d.alternative_rejected}"
        for d in decisions
    )


def run_loop(
    client: ProbeClient,
    artifact: Artifact,
    *,
    max_iters: int = DEFAULT_MAX_ITERS,
    tol: float = DEFAULT_TOL,
    seed: int | None = None,
) -> LoopRun:
    """Run the §3 loop to convergence on one artifact, recording the trajectory."""
    fam = load_family()
    system = render.bounded_system()
    calls: list[ProbeResult] = []

    # ── Stage A: bounded goal hypotheses → posterior ─────────────────────────────────────────
    a = client.read(system, render.stage_a(artifact), StageAOut)
    calls.append(a)
    stage_a: StageAOut = a.parsed  # type: ignore[assignment]

    purpose, audience = stage_a.purpose, stage_a.audience
    confidence = stage_a.confidence_100
    trajectory = [Step(0, purpose, audience, n_decisions=0, movement=0.0)]

    decisions: tuple = ()
    converged = False

    for i in range(1, max_iters + 1):
        # ── Stage B: the decision chain visible UNDER the leading purpose ────────────────────
        # E36: the purpose is SUPPLIED, not re-derived. Pinning what the maker was for is what
        # roughly doubles method recovery, and supplying it is what makes this a loop rather
        # than two independent readings averaged together.
        b = client.read(
            system,
            render.stage_b(artifact, purpose.best, audience.best),
            StageBOut,
        )
        calls.append(b)
        decisions = b.parsed.decisions  # type: ignore[union-attr]

        # ── Stage C: re-weight the posterior on what the method revealed ─────────────────────
        c = client.read(
            system,
            render.stage_c(artifact, _decision_summary(decisions)),
            StageCOut,
        )
        calls.append(c)
        stage_c: StageCOut = c.parsed  # type: ignore[assignment]

        movement = (
            _l1(stage_c.purpose.distribution, purpose.distribution)
            + _l1(stage_c.audience.distribution, audience.distribution)
        )
        purpose, audience = stage_c.purpose, stage_c.audience
        trajectory.append(
            Step(i, purpose, audience, len(decisions), movement, stage_c.changed_because)
        )

        if movement < tol:
            converged = True
            break

    # ── Stage D: trade-offs, once, after the loop settles ────────────────────────────────────
    # V6's values layer: values are read off the recovered goal, so they cannot arrive before
    # it. Running this inside the loop would let a trade-off reading feed back into the purpose
    # posterior, which is the one direction the theory says the information does not flow.
    settled = (
        f"purpose = {purpose.best} ({fam.gloss('purpose', purpose.best)}); "
        f"audience = {audience.best} ({fam.gloss('audience', audience.best)}); "
        f"{len(decisions)} decisions recovered, deepest at level "
        f"{max((d.level for d in decisions), default=0)}"
    )
    d = client.read(system, render.stage_d(artifact, settled), StageDOut)
    calls.append(d)
    stage_d: StageDOut = d.parsed  # type: ignore[assignment]

    reading = Reading(
        purpose=purpose,
        audience=audience,
        decisions=decisions,
        cost_borne=stage_d.cost_borne,
        artifact_effort=stage_d.artifact_effort,
        demonstrated_work=stage_d.demonstrated_work,
        trade_offs=stage_d.trade_offs,
        confidence_100=confidence,
        account=stage_d.account,
    )

    return LoopRun(
        artifact_id=artifact.source_id,
        reading=reading,
        trajectory=trajectory,
        converged=converged,
        arm=client.arm,
        model=client.model,
        seed=seed,
        calls=calls,
    )
