# D30 correction timing input labels

Implements the already commissioned mid-run section 2.7 split as a source
dependency for the remaining D30 comparisons. Preserve every original occurrence
and every revision event from the completed 1,399-session source pass.

Use the original P6 clock: consecutive logged text deltas, including API deltas,
not inferred individual keypresses. Anchor each occurrence at its last production
delta. The first subsequent gap of **at least two seconds** begins the next
burst; an edit at that boundary is later. A deletion before that boundary is
immediate. Preserve a word with both immediate and later edits in both flags;
never keep only its first revision. This is a deterministic logged-edit proxy,
not an independent identification of a psychological typing burst or attention.

Keep user deletions before the boundary, user edits after it, user insertion-only
changes before it, and non-user changes separate. In particular, API deletion
does not become human correction, and an insertion-only change before the
boundary does not become a later edit merely because it is not a deletion.
Retain the timing flag and original event kind/source for every change.
Scientific consumers must declare which fields they use; this pass computes no
primary contrast, probability, personal-specificity claim or attention verdict.

Require authenticated completed source and its independently verified landing;
refuse changed source outputs and population mismatch. Freeze classifier code,
the completed source outputs, their upstream pins and the validation receipts
at dispatch. Preserve immutable checkpoints and fully replay classification in
a fresh process. Use one counted CPU slot, BelowNormal priority, at most two
numerical-library threads, and retain the demo reservation. GPU and paid readers
are unused. Output cap: 512 MiB. Main execution plus verification cap: 900 seconds,
charged together with all prior source/native validation against the existing
single S4 maximum of 7,200 seconds. No additional doubling is introduced.

**DESIGN CHECK.** LESSONS 3-5 and CONTROLS 1-6 reread for this build. Under either
scientific null or alternative, constructed chronology fixes the timing labels:
1.999-second gaps are before, 2.000-second gaps are after; a chain of shorter
gaps stays one burst even if total elapsed time exceeds two seconds. Known
edits must reproduce both timing classes; unchanged inputs retain all rows and
no changes. Source/time/character tampering and unsupported scopes refuse.
Fifteen targeted checks precede a complete four-session native known-answer
rehearsal; its four change categories must each occur once. Only a passed native
rehearsal admits the full source-labeling pass. The initial test attempt's three
scratch-directory permission errors remain recorded; the same tests pass using
a new scratch path inside the workspace, without changing classifier code.
