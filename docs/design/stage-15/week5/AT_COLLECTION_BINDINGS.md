# AT complete-bank binding successor

The original source and scoring outputs remain unchanged. The new
`week5_at_collect_v2` wraps the original collector with stricter admission:
each verified score plan must name the exact source chunk, context and context
length; each summary must identify the same model, revision and context; and
the saved score binding must equal the digest of the complete actual chunk,
manifest and scoring condition. All chunks for one model must have one revision.
The full bank's existing coverage and per-word hash checks still run afterward.
Byte-identical chunks copied into a whole-writer scope remain reusable; path
equality alone is neither necessary nor sufficient for score identity.

## DESIGN CHECK

Method LESSONS sections 3–5 informed this source-integrity repair. The native
fixture runs the actual wrapper and original collector in both phases on a
complete constructed bank, and requires refusal of changed source bindings,
mixed context lengths, plan/output mismatch and internally consistent chunks
from different model revisions. No fake native completion is manufactured.
It changes no score, support rule, estimator, model selection or threshold.

Use explicit `context='final'` or `'at_typing'` and `context_length` of 64, 256
or 1,024. Empty or partial banks remain refused. The same whole-writer sample
route and AT family ceiling apply; collection and independent replay are
charged to their parent card. A failed binding is an engineering fault and
cannot be interpreted as a scientific null.
