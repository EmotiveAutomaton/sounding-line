# GO2 historical byte decoding and explicit unknown-version gaps

The first source correction reached a historical blob with a byte that is not
valid UTF8. On Windows, Python's subprocess reader thread raised a decode
exception while Git itself exited successfully; the caller received no text.
The original attempt and first correction remain preserved. The exact failed
document contains 12 such versions among its 35 same-document revisions, with
no encoding declaration. No score was computed or used in this diagnosis.

**DESIGN CHECK.** LESSONS 2–5 reread November 7. Capture Git stdout as bytes
before decoding, so a reader-thread failure cannot appear to be successful
text. Decode UTF8 (including its optional byte-order mark) strictly. If that
fails, accept only an explicit header/footer declaration naming UTF8, Latin1
or Windows-1252 through a fixed alias map. Conflicting, absent or unsupported
declarations and invalid declared byte sequences are counted exclusions.
Binary blobs are separately counted. There is no heuristic charset guess or
replacement-character decoding. Every raw Git object remains available.

Preserve the first correction's copy-target start, rename tracking and deletion
handling. An unavailable text version breaks both adjacent-version differences
and before/after text windows; windows cannot jump across unknown history.
This explicit source support disposition is determined before analysis and
applies equally to missing licensed sections and undecodable versions. Bulk
commits and markup-only changes remain their existing exclusions. All other
goal-change, lexical-added-text, author, source-pin and license rules remain.

**Case and check.** The actual constructed Git fixture includes a copy event,
an undeclared legacy-byte version, an explicitly declared Latin1 version and a
UTF8 successor. It executes the complete real source loop, its bounded pause,
and fresh native replay. Tests separately exercise UTF8/BOM, strict rejection,
declared legacy decoding and both directions of an unknown-version barrier.
The resulting counts must distinguish each source disposition; the unknown
version must never be silently treated as valid text or an observed zero edit.

**Cost and smaller route.** Unchanged GO2 card and GO family ceilings, 72-of-1,440
document pilot and per-document seals. Both prior failures stay charged. The
successor starts in a new output root with new module bindings; no old seal is
rewritten. Complete source projection and independent replay remain prerequisites
for GO2 inference and first-version GO1 companions. The owner reviews the actual
pilot forecast and retains the declared source-scope exclusions in the final
packet. No new model, network, paid or GPU authority is required.
