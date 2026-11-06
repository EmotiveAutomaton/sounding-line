# Public source intake

DESIGN CHECK: LESSONS 2-5 and CONTROLS 6-7. Valid source bytes must replay exactly;
missing fields, licence ambiguity, changed hashes and unsafe archive paths refuse.
No scientific contrast is computed by intake. Missing support is not a null.

Process I1, I2, I3 serially, preserving failures and original downloaded bytes in
the ignored raw area. Never upload source data. Record the exact public URL,
version, size, SHA-256, HTTP outcome and licence. Download limits are 256 MiB per
file and 512 MiB total for these three sources; archive expansion is capped at
1 GiB with traversal and symlink rejection. Stop at the campaign's resource floors
and clock. A source failure holds its dependent cards but not independent work.

I1 uses Dryad version 227569, DOI 10.5061/dryad.prr4xgxkk, CC0. Bind downloaded
README and ZIP to the repository's supplied SHA-256 hashes. Read the README and
MATLAB script before mapping trials. Inventory fields and counts, fixed start,
rating times and first-play support before TD1-TD3. Do not infer first play from
file order or invent unobserved counterfactual rewards.

I2 uses the raw parquet from `google-research-datasets/go_emotions`, revision
`add492243ff905527e67aeb8b80c082af02207c3`, Apache-2.0. Read only an explicit
column allowlist: text, comment id, subreddit, rater id, unclear flag and the 28
label columns. **Never decode or access the author column.** Reject missing
columns, nonbinary labels, duplicate comment-rater keys and inconsistent comment
text/subreddit. Exclude unclear ratings and retain disposition counts. Preserve
the documented 58,011 versus official README's 58,009 discrepancy; actual support
is determined from the pinned raw data, without editing rows to match a headline.

I3 uses NRC Emotion Intensity v1 and VAD v2.1 official ZIP files. Their
noncommercial research terms permit this analysis and prohibit raw redistribution.
Read the packaged licence/version/schema before use. No lexicon entries, raw
text or identifiers enter Git; only source hashes, aggregated checks and results.

An independently executed verification pass rehashes every downloaded source and
recomputes intake counts with the same explicit author exclusion. Metadata and
archive retrieval alone do not admit a scientific model. Pending mappings and
source refusals remain explicit, with their dependent work held.
