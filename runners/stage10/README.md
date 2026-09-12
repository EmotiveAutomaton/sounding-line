# Stage 10 reader prototype

The [current context](../../docs/design/PHASE_2_4_STAGE_10_CONTEXT.md) adopts the
curator's Stage 10 specification. Stage 9 modules and frozen results remain intact.

`contracts.py` is the public task and forecast boundary. Only declared evidence,
choices and the prediction question enter a model request. Source identities,
group allocation and evaluation answers belong in a separate evaluator record.
`ollama.py` saves each literal request and raw response before parsing, with the
actual model digest, settings and server timing. Its probabilities are elicited
forecasts, not token likelihoods or a claim about an internal posterior.

Each attempt has its own directory. Existing attempts are immutable; a resume
may validate and reuse a completed attempt but must retain failed attempts too.
Record all calls, invalid outputs and costs. Never silently replace a malformed
forecast with a uniform distribution. Score whole frozen comparison cells only.

New source adapters must validate chronology, contributor roles, allocation and
the exact public evidence before execution. Run discarded literal interface
checks before a branch's first scientific cohort. One branch's repair does not
prevent another validated branch from running. Preserve CPU cooling limits,
GPU ownership and final-produce guards. Routine watches are thirty to sixty
minutes apart; failures and drained queues may wake the owner immediately.

`deliberation.py` implements R2 with two 384-token direct calls. `proposal.py`,
`executor.py`, `executor_worker.py` and `structured.py` implement two bounded
R3 proposal/execution rounds through unchanged exported Ghost APIs. R3 retains
the generated choice separately from its uniform likelihood-weighted candidate
mixture; those probabilities are conditional on proposed support, and are a
distinct instrument requiring development calibration. Impossible evidence
stays a mismatch. The current opportunity interface passes; the reading
proposal repeats a library after the one clarification and remains diagnostic.

`ghost_source.py` joins only frozen training cases to actual recorded enacted
outcomes. `opportunity_chain.py` runs the finite common development producers.
Source-case grouping, discarded exclusions and historical exposure stay visible;
selected cases are not automatically independent makers. Completed checkpoint
replay is verified; partial-run ownership recovery remains a limitation.
