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
    StageAOut, StageZeroOut,
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

    # ── E36's temporal result, and the reason the loop gained an extra pass ──────────────────
    #
    # "Within a single reading, process recovery before the goal settles is 0.050 and after it is
    # 0.130 — RESOLVING_THE_GOAL_UNLOCKS_THE_PROCESS."
    #
    # The loop used to STOP the moment the posterior settled, which is precisely the moment E36
    # says the payoff begins. It was quitting at the start of the interesting part. So after
    # convergence it now runs one more stage B under the settled purpose, and these two fields
    # are the before/after that E36 compares.
    arm: str
    model: str
    seed: int | None
    anomalies: tuple = ()
    decisions_before_settle: float = 0.0
    decisions_after_settle: int = 0
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
    anomaly_pass: bool = False,
) -> LoopRun:
    """Run the §3 loop to convergence on one artifact, recording the trajectory.

    ``anomaly_pass`` (v6) runs stage ZERO first and supplies its output to stage A. OFF by
    default, and the default path renders bounded_v5 exactly as before — a prompt that changes
    under a running gate is the drift Gate 0 named as this project's likeliest undocumented
    change, so the new stage is opt-in rather than a new default.
    """
    fam = load_family()
    system = render.bounded_system()
    calls: list[ProbeResult] = []

    # ── Stage ZERO: what does not fit (v6, opt-in) ───────────────────────────────────────────
    #
    # The curator entered every successful reading of session 01 through a specific oddity
    # rather than through the artifact as a whole, and an anomaly is by construction the part a
    # whole-artifact summary averages away. Its output is a set of COMPETING maker-hypotheses,
    # supplied to stage A as hypotheses rather than as findings.
    anomalies = None
    if anomaly_pass:
        z = client.read(system, render.stage_zero(artifact), StageZeroOut)
        calls.append(z)
        anomalies = z.parsed.anomalies          # type: ignore[union-attr]

    # ── Stage A: bounded goal hypotheses → posterior ─────────────────────────────────────────
    a = client.read(system, render.stage_a(artifact, anomalies), StageAOut)
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

    # The baseline is the FIRST stage-B pass — method recovered under stage A's un-refined
    # purpose — not a mean over iterations. E36's comparison is recovery under an unpinned goal
    # against recovery under a pinned one, and averaging across iterations blends the two.
    mean_before = float(trajectory[1].n_decisions) if len(trajectory) > 1 else 0.0

    # ── The unlock pass. One extra stage B, under the now-settled purpose. ───────────────────
    # E36's between-reader form failed in the simulation and its within-reading form held, so
    # this is deliberately a comparison inside a single reading rather than across samples —
    # which also routes around E38, since cross-sample agreement is what a machine-matched
    # reader degrades on.
    unlock = client.read(
        system,
        render.stage_b(artifact, purpose.best, audience.best),
        StageBOut,
    )
    calls.append(unlock)
    after_decisions = unlock.parsed.decisions          # type: ignore[union-attr]
    if len(after_decisions) > len(decisions):
        # Keep the richer chain. The unlock pass reads under a settled purpose and E36 predicts
        # it recovers more; when it does, that is the reading rather than a duplicate of it.
        decisions = after_decisions

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
        anomalies=tuple(anomalies or ()),
        decisions_before_settle=mean_before,
        decisions_after_settle=len(after_decisions),
        arm=client.arm,
        model=client.model,
        seed=seed,
        calls=calls,
    )
