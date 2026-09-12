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
