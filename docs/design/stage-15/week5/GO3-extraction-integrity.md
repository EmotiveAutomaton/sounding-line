# GO3 extraction integrity before source parsing

The original GO3 source reuses Posts and PostHistory XML whenever both paths
exist. File existence does not distinguish a completed extraction from one
interrupted after creating both files. This source-only engineering successor
closes that admission gap. The original source and all previous attempts stay
immutable; no corpus or scientific outcome is changed.

`week5_go3_source_integrity` retains the original archive SHA-256 pins, licence
notice check, source columns, salted joins, labels, ordering, exclusions,
before/after text and independent full-row replay. Only extraction changes.

The pinned archive must contain one non-directory instance of each required
XML member with an explicit size and CRC. Fresh decode verifies both values,
then records SHA-256 values in a private EXTRACTION receipt bound to the full
archive SHA and member metadata. Reuse requires that receipt, both exact
member sizes and both SHA values. Missing, redirected or changed members
refuse before XML parsing. Existing target files without a complete receipt
also refuse, even if they look readable; the failed attempt retains them and
a fresh immutable attempt is required. No partial file is silently overwritten.
No Users/profile member is extracted or read.

## DESIGN CHECK

- **Case and check:** both XML paths can exist despite an incomplete or stale
  decode. Constructed native 7z fixtures exercise truncated files, same-size
  mutations, missing seals, wrong archive binding, sealed reentry and actual
  full source execute/verify with exact comparison to the original projection.
  The five actual pinned archives were inspected only for member metadata;
  all ten required members have explicit sizes and CRC values. No human
  extraction or source prefix was launched by the builder.
- **Smaller route:** retain refusal evidence and start a separately admitted
  fresh source attempt. The original 250,000 CPU-second GO3 and 600,000 family
  ceilings include extraction/hash/replay cost. Per-site source timing is a
  counted admission stage. The original source remains a whole-site unit;
  a measured forecast requiring a resumable 5% pilot needs a separately
  reviewed checkpointed source before whole-site admission.

This guard qualifies source bytes, not scientific evidence or a new licence.
Raw XML, extraction receipts and participant identifiers remain private and
ignored. Native fixture source data are entirely constructed.
