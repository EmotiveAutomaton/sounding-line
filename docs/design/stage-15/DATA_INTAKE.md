# Initial public-data intake

The commission permits Part 3.1/3.2 intake before Friday's packet. This first
bounded pass downloads the public DICES-350 and Community Alignment releases
from their official repositories, with no account, paid call or acceptance of
gated terms. License notices were read directly; both specify CC-BY-4.0.
Pinned revisions, URLs and source hashes are retained locally with the raw bytes.

The job is serial, with a 4 GiB ceiling per CSV, a three-hour maximum and the
same host resource floors as Phase 0. It records only parseable row counts and
column names. It does not compute outcome distributions, train models, join maker
identities, expose raw text or declare a scientific adapter admitted. Future
cards must freeze target and exposure rules before analysis. No public artifact
contains row-level data or maker identifiers.

Important admission distinctions from the official source documentation:

- [DICES-350](https://github.com/google-research-datasets/dices-dataset/blob/main/350/README.md)
  releases 123 raters, while its paper analyses generally use 104 after quality
  exclusions. Preserve both denominators and freeze the quality sensitivity before
  modeling; do not quietly select the subset with the preferred result. Its ratings
  concern perceived safety, not independently established personal values.
- [Community Alignment](https://huggingface.co/datasets/facebook/community-alignment-dataset/blob/main/README.md)
  v1.1 consolidates the formerly filtered release and adds a collection wave.
  A CSV conversation count is not its number of turn-level comparisons. Confirm
  the codebook and actual usable maker/turn fields before implementing an adapter.

This is source acquisition, not a statistical result. Successful intake requires
manifest verification and internal recording before its completion event is ACKed.
