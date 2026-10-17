# T3 revision-shape extraction

DESIGN CHECK: LESSONS 2–5. Duplicate/missing revisions, incomplete pagination or
changed source bytes stop publication. A repeated immediate hash is a no-op;
returning to an older, non-immediate content hash is an identity revert. Tags
indicating a revision was reverted are counted separately from reversion acts.
These counts describe the retained snapshot and do not identify edit intent.

Use all 105 retained article histories through the intake's frozen timestamp.
Registered editor identity is the numeric user ID; anonymous identity is the
visible username/IP string. Hidden identities remain missing and are reported,
never treated as one person. Public records contain distributions, not identities.
Identity reverts use the recorded SHA-1 within each article; report missing hashes,
immediate no-ops and `mw-reverted` tags separately. Revert fraction uses all
retained revisions as denominator, with missingness explicit.

Summary coverage excludes empty/section-header-only comments, the documented
rollback/undo tags, and comments starting with the fixed automatic-summary forms
`Undid revision`, `Reverted edits`, `Reverted revision`, `Automatic`, or `Robot`.
This is a declared automatic-summary heuristic, not proof of human authorship.
Also report raw nonempty coverage and hidden-comment counts; no discarded rows.

The source revision anchor is the last retained **Wikipedia content SHA-1** for
Empathy, with its numeric revision URL, explicitly not a Git commit. The source
summary additionally binds the entire acquisition manifest, every retained API
response and all latest article revision IDs/hashes. The single anchor does not
stand in for those full-snapshot bindings. Ghost must review this API-native
source identity before treating it as equivalent to a Git-backed release.
No simulated or human mechanism claim is made. Full revision text/diffs remain
unacquired and D8 is not made runnable by this metadata summary.
