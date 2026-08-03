"""The free-form baseline. A-2, and it decides whether the project is a contribution.

SPEC §7 names this as the ablation that matters most:

    the one that matters most: a model asked, free-form, WHY WAS THIS MADE. If unbounded
    attribution matches bounded inference, the boundedness bought nothing and §2 is wrong.

Gate 0's amendment A-2 promoted it from a Gate 3 ablation to a Gate 1 arm running in parallel,
because bounded-family Bayesian inversion turned out to be prior art and bounded-versus-unbounded
on artifacts is therefore the load-bearing novelty.

**It had not been run. Not once.** The prompts existed from the first build and no runner
referenced them, so every Gate 1 result so far describes the bounded arm against nothing. That is
an unmet pre-registered commitment and this module is the repair.

── ON NOT SANDBAGGING THIS ─────────────────────────────────────────────────────────────────────

It is trivially easy to weaken the baseline and then report that boundedness won, and the result
would be worthless. So the free-form arm gets:

  * the same artifact, the same delimiter, the same injection warning;
  * the same model, the same arm, the same k;
  * the same two-stage shape — reason in prose, then coerce — which is the treatment the bounded
    arm now gets and which the format-tax literature says is the stronger path;
  * measurement by the same code, with no special casing anywhere downstream.

What it does NOT get is the bounded family in its reasoning step. That single difference is the
experiment. The coercion step sees only the account and never the artifact, so the family cannot
leak backwards and quietly make the two arms agree.
"""

from __future__ import annotations

from soundingline.loop.run import LoopRun, Step
from soundingline.probe import render
from soundingline.probe.client import ProbeClient
from soundingline.probe.render import Artifact
from soundingline.probe.schema import Reading


def run_freeform(client: ProbeClient, artifact: Artifact, *, seed: int | None = None) -> LoopRun:
    """Ask the open question, coerce the answer, return a comparable LoopRun.

    There is no loop here and that is the point — the bounded arm's recursion (SPEC §3) is part
    of what is being tested. The trajectory has a single step and `converged` is True by
    construction, so any convergence difference between the arms is a difference in the readings
    rather than an artefact of one arm being allowed to iterate.
    """
    # Stage 1: the open question, wholly unconstrained. No family, no hypothesis set, no
    # schema, no grammar — the bounded arm's stage 1 is equally free, and equality here is the
    # experiment's only load-bearing requirement.
    account = client.read_text(
        render.freeform_system(),
        render.freeform_ask(artifact),
    )
    if not account:
        raise ValueError("free-form arm returned no account")

    # Stage 2: coerce. Sees the account only — never the artifact.
    r2 = client.read(
        "You convert a reader's prose account into a fixed structured form.",
        render.freeform_coerce(account),
        Reading,
        two_stage=False,
    )
    reading: Reading = r2.parsed  # type: ignore[assignment]

    return LoopRun(
        artifact_id=artifact.source_id,
        reading=reading,
        trajectory=[Step(0, reading.purpose, reading.audience,
                         n_decisions=len(reading.decisions), movement=0.0)],
        converged=True,
        arm=f"{client.arm}-freeform",
        model=client.model,
        seed=seed,
        calls=[r2],
    )
