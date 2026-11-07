# AT covariates: literal-empty orphan reopen recovery

The v2 full source attempt stops when a literal-empty `suggestion-reopen`
appears before any nonempty suggestion display. The canonical event replay
reconstructs that session's full document with no document errors, while
retaining a separate orphan-reopen correspondence warning. The source bytes,
failed attempt, completed prefix and original recovery modules remain intact.

## DESIGN CHECK

**Case and check.** Screen exposure concerns words actually displayed before
the target's first insertion. A literal empty list adds zero displayed words,
whether or not a prior menu exists. It cannot justify filling an unobserved
menu from a later display. The separate v3 successor accepts literal-empty
reopens as zero added exposure and audits their ordinal, prior-display flag
and orphan correspondence warning. It preserves every raw delta, timestamp
and occurrence. The prediction snapshot still precedes the event's own delta
and any same-event newly shown suggestions. Existing prior exposure stays;
no prior exposure is invented.

The actual raw-JSONL/P6 handler fixture covers an orphan empty reopen that
also inserts text, later first display, a later empty reopen with prior display,
strict current/future exclusion and the unshown option-original exclusion.
An independent constructed zero-display oracle preserves delta and ordinal
and must match every covariate exactly. Missing, encoded-empty and malformed
suggestions, and literal-empty new opens, remain refused. Full handler execute
and a separate fresh replay pass. The human source still requires its own
complete independent replay before use.

**Smaller route.** This is an engineering recovery of the same full source and
estimand; no population, covariate or timing criterion changes. Charge the
failed attempt, fixture, new execution and fresh verifier to AT. The owner
dispatches the separate v3 plan; the child builder does not rerun human work.
Raw identifiers and the session-level diagnosis remain private.
